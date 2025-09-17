from setuptools import setup, find_packages

setup(
    name='pdf2md-skale',
    version='0.4.6',
    packages=find_packages(),
    install_requires=[
        'python-dotenv',
        # Add CLI library if needed, e.g. 'click' or 'argparse'
    ],
    extras_require={
        'pdfplumber': ['pdfplumber'],
        'pypdf2': ['PyPDF2'],
        'pymupdf': ['pymupdf'],
        'llamaparse': ['llama_parse', 'llama-index-core'],
        'ocr': ['pytesseract', 'pdf2image'],
        'easyocr': ['easyocr'],
        'docling': ['docling'],
        'marker': ['marker-pdf'],
        'all': [
            'pdfplumber', 'PyPDF2', 'pymupdf', 'llama_parse', 'llama-index-core',
            'pytesseract', 'pdf2image', 'easyocr', 'docling', 'marker-pdf'
        ]
    },
    entry_points={
        'console_scripts': [
            'pdf2md=pdf2md.main:main'
        ]
    },
    author='Johann Waldherr',
    author_email='dev@skale.dev',
    description='A package to convert PDF files to Markdown using various extractors.',
    url='https://github.com/devskale/python-utils.git#subdirectory=packages/md2pdf.skale',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
