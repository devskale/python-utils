import argparse
from markdown import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup
import re
import os
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register a default font to avoid errors with non-standard characters
pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'Arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Italic', 'Arialbi.ttf'))
pdfmetrics.registerFont(TTFont('Arial-BoldItalic', 'Arialbi.ttf'))


def convert_md_to_pdf(input_file, output_file, css_file=None):
    """
    Converts a markdown file to a PDF file with basic formatting.
    Handles headers, paragraphs, and basic text formatting.
    """
    # Read markdown content
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert markdown to HTML, preserving newlines as <br> tags
    html_content = markdown(md_content, extensions=['nl2br'])


    # Parse HTML with BeautifulSoup for better handling
    soup = BeautifulSoup(html_content, 'html.parser')

    # Create PDF document
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Load CSS styles if provided
    css_styles = {}
    if css_file and os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        css_styles = parse_css(css_content)

    # Apply CSS styles to ReportLab styles
    apply_css_to_styles(styles, css_styles)

    # Map HTML tags to ReportLab styles
    tag_styles = {
        'h1': styles['h1'],
        'h2': styles['h2'],
        'h3': styles['h3'],
        'h4': styles['h4'],
        'p': styles['Normal'],
        'li': styles['Normal'],
        'strong': styles['Normal'],  # Bold will be handled by the HTML parser
        'em': styles['Normal'],  # Italics will be handled by the HTML parser
    }

    # Process each HTML element
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'blockquote']):
        if element.name in ['h1', 'h2', 'h3', 'h4', 'p']:
            # Handle headers and paragraphs, passing HTML directly
            # ReportLab's Paragraph can interpret basic HTML tags like <b>, <i>, <br>
            story.append(Paragraph(str(element), tag_styles.get(element.name, styles['Normal'])))
        elif element.name in ['ul', 'ol']:
            # Handle lists, passing HTML directly
            for li in element.find_all('li'):
                # For lists, we might want to prepend a bullet or number if not handled by markdown
                # However, ReportLab's Paragraph can handle <li> tags if they are part of a larger HTML block
                # For simplicity, we'll pass the li content as is, assuming markdown handles bullets.
                story.append(Paragraph(str(li), tag_styles['li']))
        elif element.name == 'blockquote':
            # Handle blockquotes, passing HTML directly
            story.append(Paragraph(f'<i>{str(element.decode_contents())}</i>', styles['Italic']))

        # Add a spacer after each block element for better visual separation
        story.append(Spacer(1, 12))

    # Build the PDF
    doc.build(story)
    print(f"Successfully converted {input_file} to {output_file}")

def parse_css(css_content):
    styles = {}
    # Basic regex to parse CSS rules (e.g., "selector { property: value; }")
    # This is a simplified parser and might not handle all CSS complexities.
    rules = re.findall(r'([a-zA-Z0-9\s\.\#\-\_]+)\s*\{([^\}]+)\}', css_content)
    for selector, declarations in rules:
        selector = selector.strip()
        styles[selector] = {}
        for declaration in declarations.split(';')[:-1]:
            if ':' in declaration:
                prop, value = declaration.split(':', 1)
                styles[selector][prop.strip()] = value.strip()
    return styles

def apply_css_to_styles(reportlab_styles, css_styles):
    # Ensure default heading styles are available for mapping
    for i in range(1, 5):
        if f'h{i}' not in reportlab_styles:
            reportlab_styles[f'h{i}'] = reportlab_styles['Heading' + str(i)]

    for selector, declarations in css_styles.items():
        if selector in reportlab_styles:
            style = reportlab_styles[selector]
            for prop, value in declarations.items():
                if prop == 'font-size':
                    style.fontSize = float(value.replace('pt', ''))
                elif prop == 'color':
                    # Basic color parsing (hex only for now)
                    if re.match(r'^#([0-9a-fA-F]{3}){1,2}$', value):
                        print(f"Applying color {value} to {selector}") # Debugging line
                        try:
                            style.textColor = colors.HexColor(value)
                        except Exception as e:
                            print(f"Error applying color {value} to {selector}: {e}") # Debugging line
                    elif value.lower() in colors.getAllNamedColors():
                        print(f"Applying named color {value} to {selector}") # Debugging line
                        style.textColor = colors.getAllNamedColors()[value.lower()]
                elif prop == 'text-align':
                    if value == 'left':
                        style.alignment = TA_LEFT
                    elif value == 'center':
                        style.alignment = TA_CENTER
                    elif value == 'right':
                        style.alignment = TA_RIGHT
                    elif value == 'justify':
                        style.alignment = TA_JUSTIFY
                elif prop == 'font-family':
                    # This is a simplified mapping. ReportLab needs font registration.
                    # For now, we'll just set the font name if it's 'Arial' or similar.
                    if 'Arial' in value:
                        style.fontName = 'Arial'
                        style.leading = style.fontSize * 1.2 # Adjust leading based on font size
                elif prop == 'line-height':
                    style.leading = style.fontSize * float(value)
                elif prop == 'margin':
                    # ReportLab handles margins at the document level or with frames.
                    # This is a simplification and might not fully apply CSS margins.
                    pass

def main():
    """
    Main function to parse arguments and initiate markdown to PDF conversion.
    """
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF.')
    parser.add_argument('--input', '-i', type=str,
                        required=True, help='Input Markdown file.')
    parser.add_argument('--output', '-o', type=str,
                        help='Output PDF file. If not provided, uses input filename with .pdf extension.')
    parser.add_argument('--css', '-c', type=str,
                        help='Optional CSS file for styling.')

    args = parser.parse_args()

    # Set default output filename if not provided
    if not args.output:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}.pdf"

    # Use default.css if no CSS file is provided
    css_file_path = args.css
    if not css_file_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        css_file_path = os.path.join(script_dir, 'default.css')

    convert_md_to_pdf(args.input, args.output, css_file_path)


if __name__ == '__main__':
    main()
