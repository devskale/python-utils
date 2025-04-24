import os
import re
import sys
import random
import time
from colorama import init, Fore, Back, Style
import curses  # Replace keyboard with curses for input handling

# Initialize colorama for cross-platform color support
init()

# Constants for the terminal pager
PAGE_SIZE = 30  # Number of lines per page
ENTITY_COLORS = [
    Fore.RED, Fore.GREEN, Fore.BLUE, Fore.YELLOW, Fore.MAGENTA, Fore.CYAN,
    Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTBLUE_EX,
    Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX
]

# Define curses color pairs to match our colorama colors
CURSES_COLORS = [
    (curses.COLOR_RED, 1),
    (curses.COLOR_GREEN, 2),
    (curses.COLOR_BLUE, 3),
    (curses.COLOR_YELLOW, 4),
    (curses.COLOR_MAGENTA, 5),
    (curses.COLOR_CYAN, 6),
    (curses.COLOR_RED, 7),      # Light red approximation
    (curses.COLOR_GREEN, 8),    # Light green approximation
    (curses.COLOR_BLUE, 9),     # Light blue approximation
    (curses.COLOR_YELLOW, 10),  # Light yellow approximation
    (curses.COLOR_MAGENTA, 11),  # Light magenta approximation
    (curses.COLOR_CYAN, 12)     # Light cyan approximation
]


def get_entity_types(content):
    """Extract unique entity types from the content."""
    # Extract entity types from placeholders like [[Type]] or [[Type // Value]]
    entity_pattern = r'\[\[([^/\]]+?)(?:\s//\s[^\]]+)?\]\]'
    entity_types = set(re.findall(entity_pattern, content))
    return sorted(list(entity_types))


def assign_colors_to_entities(entity_types):
    """Assign colors to each entity type."""
    color_map = {}
    for i, entity_type in enumerate(entity_types):
        color_map[entity_type] = ENTITY_COLORS[i % len(ENTITY_COLORS)]
    return color_map


def colorize_entity(text, color_map):
    """Colorize entity placeholders in the text."""
    # Process hybrid format: [[EntityType // Value]]
    pattern_hybrid = r'\[\[([^/\]]+?)\s//\s([^\]]+)\]\]'

    def replace_hybrid(match):
        entity_type = match.group(1).strip()
        value = match.group(2)
        color = color_map.get(entity_type, Fore.WHITE)
        return f"{color}{match.group(0)}{Style.RESET_ALL}"

    # Process standard format: [[EntityType]]
    pattern_standard = r'\[\[([^/\]]+?)\]\]'

    def replace_standard(match):
        entity_type = match.group(1).strip()
        color = color_map.get(entity_type, Fore.WHITE)
        return f"{color}{match.group(0)}{Style.RESET_ALL}"

    # Apply replacements (hybrid first, then standard)
    text = re.sub(pattern_hybrid, replace_hybrid, text)
    text = re.sub(pattern_standard, replace_standard, text)

    return text


def display_terminal_pager_curses(stdscr, content, color_map):
    """Display a terminal-based pager for content using curses for navigation."""
    # Configure curses
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    stdscr.refresh()

    # Setup colors if terminal supports them
    curses.start_color()
    curses.use_default_colors()

    # Initialize color pairs
    for i, (color, pair_num) in enumerate(CURSES_COLORS):
        curses.init_pair(pair_num, color, -1)  # -1 means default background

    # Create a mapping from entity types to curses color pairs
    curses_entity_colors = {}
    for i, entity_type in enumerate(color_map.keys()):
        pair_num = CURSES_COLORS[i % len(CURSES_COLORS)][1]
        curses_entity_colors[entity_type] = curses.color_pair(pair_num)

    # Split content into lines
    lines = content.splitlines()
    total_pages = (len(lines) + PAGE_SIZE - 1) // PAGE_SIZE  # Ceiling division
    current_page = 0

    # Function to display the current page
    def show_current_page():
        stdscr.clear()

        # Get terminal size
        max_y, max_x = stdscr.getmaxyx()

        # Display header with color
        header_text = f"=== PAGE {current_page + 1}/{total_pages} ==="
        stdscr.addstr(0, 0, header_text, curses.A_BOLD)
        controls_text = "Controls: RIGHT next page, LEFT previous page, q to quit, g to go to page, h for help"
        stdscr.addstr(1, 0, controls_text)

        # Display legend with colors
        legend_line = 3
        stdscr.addstr(legend_line, 0, "Entity Types:", curses.A_BOLD)

        # Display entity types with their colors
        legend_items_per_row = 3
        legend_rows = (len(curses_entity_colors) +
                       legend_items_per_row - 1) // legend_items_per_row
        entity_types = list(curses_entity_colors.keys())

        for row in range(min(3, legend_rows)):  # Limit to max 3 rows
            for col in range(legend_items_per_row):
                idx = row * legend_items_per_row + col
                if idx < len(entity_types):
                    entity_type = entity_types[idx]
                    color_attr = curses_entity_colors[entity_type]
                    col_pos = col * 25  # Each column is 25 chars wide
                    if col_pos + len(entity_type) + 3 < max_x:  # Check if it fits
                        stdscr.addstr(legend_line + row + 1,
                                      col_pos, "■ ", color_attr)
                        stdscr.addstr(legend_line + row + 1,
                                      col_pos + 2, entity_type[:20])

        # Content starts after legend
        content_start_line = legend_line + min(4, legend_rows) + 1

        # Display content for current page
        start_line = current_page * PAGE_SIZE
        end_line = min(start_line + PAGE_SIZE, len(lines))

        # Calculate how many lines we can display for content
        max_content_lines = max_y - content_start_line - 2  # Reserve 2 lines for footer
        displayable_lines = min(end_line - start_line, max_content_lines)

        for i in range(displayable_lines):
            line_index = start_line + i
            if line_index < len(lines):
                # Display the line with colorized entities
                line = lines[line_index]
                line_position = content_start_line + i
                current_x = 0

                # Find all entity placeholders in the line
                standard_entities = list(
                    re.finditer(r'\[\[([^/\]]+?)\]\]', line))
                hybrid_entities = list(re.finditer(
                    r'\[\[([^/\]]+?)\s//\s([^\]]+)\]\]', line))
                all_entities = standard_entities + hybrid_entities

                # Sort all entities by their position in the line
                all_entities.sort(key=lambda m: m.start())

                # If no entities, just print the line
                if not all_entities:
                    stdscr.addstr(line_position, 0, line[:max_x-1])
                    continue

                # Print line with colorized entities
                last_end = 0
                for match in all_entities:
                    # Print text before the entity
                    if match.start() > last_end:
                        stdscr.addstr(line_position, current_x,
                                      line[last_end:match.start()])
                        current_x += match.start() - last_end

                    # Print the entity with its color
                    entity_text = match.group(0)
                    entity_type = match.group(1).strip()
                    color_attr = curses_entity_colors.get(
                        entity_type, curses.A_NORMAL)

                    # Make sure we don't exceed screen width
                    if current_x + len(entity_text) >= max_x:
                        break

                    stdscr.addstr(line_position, current_x,
                                  entity_text, color_attr | curses.A_BOLD)
                    current_x += len(entity_text)
                    last_end = match.end()

                # Print text after the last entity
                if last_end < len(line) and current_x < max_x:
                    remaining_text = line[last_end:min(
                        len(line), last_end + (max_x - current_x))]
                    stdscr.addstr(line_position, current_x, remaining_text)

        # Footer navigation hint
        footer_text = "=== Use LEFT/RIGHT arrow keys to navigate, 'q' to quit ==="
        if max_y > content_start_line + displayable_lines + 1:
            stdscr.addstr(max_y-1, 0, footer_text[:max_x-1], curses.A_BOLD)

        stdscr.refresh()

    # Show initial page
    show_current_page()

    # Main event loop for handling keyboard input
    while True:
        key = stdscr.getch()

        if key == ord('q'):
            break
        elif key == curses.KEY_RIGHT and current_page < total_pages - 1:
            current_page += 1
            show_current_page()
        elif key == curses.KEY_LEFT and current_page > 0:
            current_page -= 1
            show_current_page()
        elif key == ord('g'):
            # Enter page number mode
            curses.echo()  # Show typing
            stdscr.addstr(PAGE_SIZE + 4, 0,
                          f"Enter page number (1-{total_pages}): ")
            stdscr.refresh()

            # Create an input window
            input_win = curses.newwin(
                1, 10, PAGE_SIZE + 4, len(f"Enter page number (1-{total_pages}): "))
            input_win.refresh()

            # Get string input
            curses.curs_set(1)  # Show cursor
            page_str = ""
            while True:
                try:
                    ch = input_win.getch()
                    if ch == 10:  # Enter key
                        break
                    elif ch == 27:  # Escape key
                        page_str = ""
                        break
                    elif 48 <= ch <= 57:  # Numbers 0-9
                        page_str += chr(ch)
                    elif ch == 127 or ch == 8:  # Backspace
                        page_str = page_str[:-1]

                    # Redraw input
                    input_win.clear()
                    input_win.addstr(0, 0, page_str)
                    input_win.refresh()
                except Exception:
                    break

            curses.noecho()
            curses.curs_set(0)  # Hide cursor

            # Process input
            try:
                if page_str:
                    page_num = int(page_str) - 1  # Convert to 0-based
                    if 0 <= page_num < total_pages:
                        current_page = page_num
            except ValueError:
                pass  # Invalid input, do nothing

            show_current_page()

        elif key == ord('h'):
            # Help screen
            stdscr.clear()
            stdscr.addstr(0, 0, "=== HELP ===")
            stdscr.addstr(2, 0, "RIGHT ARROW : Go to next page")
            stdscr.addstr(3, 0, "LEFT ARROW : Go to previous page")
            stdscr.addstr(4, 0, "g : Enter a page number to jump to")
            stdscr.addstr(5, 0, "q : Quit the pager")
            stdscr.addstr(6, 0, "h : Show this help screen")
            stdscr.addstr(8, 0, "Press any key to continue...")
            stdscr.refresh()
            stdscr.getch()  # Wait for any key
            show_current_page()


def main():
    # Process command line arguments
    if len(sys.argv) != 2:
        print("Usage: python blankview_s4.py filename_base")
        print("Example: python blankview_s4.py ausschreibung")
        sys.exit(1)

    filename_base = sys.argv[1]

    # Define file paths
    input_dir = "/Users/johannwaldherr/code/ww/ww_private/anonymizer/data"
    blank_filename = f"{filename_base}.blank.md"
    blank_filepath = os.path.join(input_dir, blank_filename)

    print(f"Reading blanked content from: {blank_filepath}")

    try:
        with open(blank_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Blanked input file not found at {blank_filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading blanked input file: {e}")
        sys.exit(1)

    print("Analyzing entity types and assigning colors...")
    entity_types = get_entity_types(content)
    color_map = assign_colors_to_entities(entity_types)
    print(f"Found {len(entity_types)} unique entity types")

    print("Press Enter to start the terminal pager...")
    input()

    # Use curses wrapper to handle terminal setup and teardown
    try:
        curses.wrapper(display_terminal_pager_curses, content, color_map)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error in terminal pager: {e}")

    print("Thank you for using the terminal pager.")


if __name__ == "__main__":
    main()
