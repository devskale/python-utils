from setuptools import setup, find_packages

setup(
    name='pdf2md-skale',
    version='0.2.5',
    packages=find_packages(),
    install_requires=[
        'pdfplumber',
        'PyPDF2',
        'pymupdf',
        'python-dotenv',
        'llama_parse',
        'pytesseract',
        'docling',
        'easyocr',
        'pdf2image',
        'llama-index-core',
        'marker-pdf'
    ],
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
