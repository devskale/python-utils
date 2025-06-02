import argparse
from markdown import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup
import re
import os


def convert_md_to_pdf(input_file, output_file):
    """
    Converts a markdown file to a PDF file with basic formatting.
    Handles headers, paragraphs, and basic text formatting.
    """
    # Read markdown content
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert markdown to HTML
    html_content = markdown(md_content)

    # Parse HTML with BeautifulSoup for better handling
    soup = BeautifulSoup(html_content, 'html.parser')

    # Create PDF document
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Map HTML tags to ReportLab styles
    tag_styles = {
        'h1': styles['Heading1'],
        'h2': styles['Heading2'],
        'h3': styles['Heading3'],
        'h4': styles['Heading4'],
        'p': styles['Normal'],
        'li': styles['Normal'],
        'strong': styles['Normal'],  # Bold will be handled by the HTML parser
        # Italics will be handled by the HTML parser
        'em': styles['Normal'],
    }

    # Process each HTML element
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'blockquote']):
        if element.name in ['h1', 'h2', 'h3', 'h4', 'p']:
            # Handle headers and paragraphs
            text = element.get_text()
            style = tag_styles.get(element.name, styles['Normal'])
            story.append(Paragraph(text, style))
            story.append(Spacer(1, 12))
        elif element.name in ['ul', 'ol']:
            # Handle lists
            for li in element.find_all('li'):
                text = f"• {li.get_text()}" if element.name == 'ul' else li.get_text()
                story.append(Paragraph(text, tag_styles['li']))
                story.append(Spacer(1, 6))
            story.append(Spacer(1, 12))
        elif element.name == 'blockquote':
            # Handle blockquotes
            text = f'<i>{element.get_text()}</i>'
            story.append(Paragraph(text, styles['Italic']))
            story.append(Spacer(1, 12))

    # Build the PDF
    doc.build(story)
    print(f"Successfully converted {input_file} to {output_file}")


def main():
    """
    Main function to parse arguments and initiate markdown to PDF conversion.
    """
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF.')
    parser.add_argument('--input', '-i', type=str,
                        required=True, help='Input Markdown file.')
    parser.add_argument('--output', '-o', type=str,
                        help='Output PDF file. If not provided, uses input filename with .pdf extension.')

    args = parser.parse_args()

    # Set default output filename if not provided
    if not args.output:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}.pdf"

    convert_md_to_pdf(args.input, args.output)


if __name__ == '__main__':
    main()
