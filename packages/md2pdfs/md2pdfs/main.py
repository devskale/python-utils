import argparse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import os
import re
from bs4 import BeautifulSoup
from markdown import markdown
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
    html_content = markdown(md_content, extensions=['nl2br', 'tables'])

    # Parse HTML with BeautifulSoup for better handling
    soup = BeautifulSoup(html_content, 'html.parser')

    # Replace each image with an IMAGE placeholder paragraph
    for img in soup.find_all('img'):
        placeholder = soup.new_tag('p')
        placeholder.string = 'IMAGE'
        img.replace_with(placeholder)

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
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'blockquote', 'table']):
        if element.name in ['h1', 'h2', 'h3', 'h4', 'p']:
            # Handle headers and paragraphs, passing HTML directly
            # ReportLab's Paragraph can interpret basic HTML tags like <b>, <i>, <br>
            story.append(Paragraph(str(element), tag_styles.get(
                element.name, styles['Normal'])))
        elif element.name in ['ul', 'ol']:
            # Handle lists, passing HTML directly
            for li in element.find_all('li'):
                # For lists, we might want to prepend a bullet or number if not handled by markdown
                # However, ReportLab's Paragraph can handle <li> tags if they are part of a larger HTML block
                # For simplicity, we'll pass the li content as is, assuming markdown handles bullets.
                story.append(Paragraph(str(li), tag_styles['li']))
        elif element.name == 'blockquote':
            # Handle blockquotes, passing HTML directly
            story.append(
                Paragraph(f'<i>{str(element.decode_contents())}</i>', styles['Italic']))
        elif element.name == 'table':
            table_data = []
            # Extract header row once
            first_row = element.find('tr')
            if first_row:
                headers = [th.get_text().strip()
                           for th in first_row.find_all('th')]
                if headers:
                    table_data.append(headers)
            # Extract data rows: only <td> rows to avoid re-adding header
            for row in element.find_all('tr'):
                data_cells = row.find_all('td')
                if data_cells:
                    cols = [td.get_text().strip() for td in data_cells]
                    table_data.append(cols)

            if table_data:
                table = Table(table_data)
                # Add some basic table styling
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.transparent),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)

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
                        # Debugging line
                        print(f"Applying color {value} to {selector}")
                        try:
                            style.textColor = colors.HexColor(value)
                        except Exception as e:
                            # Debugging line
                            print(
                                f"Error applying color {value} to {selector}: {e}")
                    elif value.lower() in colors.getAllNamedColors():
                        # Debugging line
                        print(f"Applying named color {value} to {selector}")
                        style.textColor = colors.getAllNamedColors()[
                            value.lower()]
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
                        style.leading = style.fontSize * 1.2  # Adjust leading based on font size
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
                        help='Input Markdown file (required if no indir).')
    parser.add_argument('--output', '-o', type=str,
                        help='Output PDF file. If not provided, uses input filename with .pdf extension.')
    parser.add_argument('--css', '-c', type=str,
                        help='Optional CSS file for styling.')
    parser.add_argument('--indir', '-di', type=str,
                        help='Input directory containing markdown files.')
    parser.add_argument('--outdir', '-do', type=str,
                        help='Output directory for generated PDFs.')
    parser.add_argument('--filter', '-f', type=str,
                        help='Filter tag for markdown filenames.')

    args = parser.parse_args()

    # enforce that either a single input or a directory is specified
    if not args.indir and not args.input:
        parser.error('Either --input/-i or --indir/-di must be provided.')

    # Use default.css if no CSS file is provided
    css_file_path = args.css
    if not css_file_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        css_file_path = os.path.join(script_dir, 'default.css')

    # Batch conversion if input directory is provided
    if args.indir:
        in_dir = args.indir
        out_dir = args.outdir if args.outdir else in_dir
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        for filename in os.listdir(in_dir):
            if filename.endswith('.md') and (not args.filter or args.filter in filename):
                input_path = os.path.join(in_dir, filename)
                base = os.path.splitext(filename)[0]
                output_path = os.path.join(out_dir, base + '.pdf')
                convert_md_to_pdf(input_path, output_path, css_file_path)
        return

    # single-file conversion: set default output if missing
    if not args.output:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}.pdf"

    convert_md_to_pdf(args.input, args.output, css_file_path)


if __name__ == '__main__':
    main()
