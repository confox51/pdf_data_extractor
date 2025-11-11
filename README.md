# PDF Table Extractor

A Streamlit web application that extracts tables from PDF files and allows users to edit, merge, and export them to Excel or CSV formats.

## Features

- 🔧 **Multiple extraction engines** - choose between PDFPlumber, Tabula, Camelot (Lattice), or Camelot (Stream) based on your PDF type
- 📄 **Extract tables from PDFs** - select the engine that works best for your document
- ✏️ **Edit tables** - modify column headers and cell values directly in the browser
- 🔀 **Merge tables** - combine multiple tables with smart column mapping
- 💾 **Export** to Excel (.xlsx) or CSV formats
- 🎯 **Page selection** - extract tables from specific pages or all pages
- 🎨 **Interactive preview** - see extracted tables before downloading

## Extraction Engines

Choose the PDF parsing engine that works best for your document:

- **PDFPlumber** - Good general-purpose extractor, works well with most PDFs
- **Tabula-py** - Java-based extractor, good for complex tables
- **Camelot (Lattice)** - Best for tables with visible borders/lines
- **Camelot (Stream)** - Best for tables without visible borders

## Deployment on Streamlit Community Cloud

This application is ready to be deployed on [Streamlit Community Cloud](https://streamlit.io/cloud).

### Prerequisites

- A GitHub account
- Your repository containing this code

### Deployment Steps

1. **Fork or Clone** this repository to your GitHub account

2. **Go to Streamlit Community Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

3. **Deploy the App**
   - Click "New app"
   - Select your repository: `your-username/pdf_data_extractor` (replace `your-username` with your GitHub username)
   - Set the main file path: `app.py`
   - Click "Deploy"

4. **Wait for Deployment**
   - Streamlit Cloud will automatically:
     - Install Python dependencies from `requirements.txt`
     - Install system packages from `packages.txt` (Java for tabula-py, Ghostscript for Camelot)
     - Start your app

### Configuration Files

The following files are configured for Streamlit Community Cloud deployment:

- **`requirements.txt`** - Python dependencies (includes pdfplumber, tabula-py, camelot-py)
- **`packages.txt`** - System dependencies (Java Runtime for tabula-py, Ghostscript for Camelot)
- **`.streamlit/config.toml`** - Streamlit configuration for production

## Local Development

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pdf_data_extractor.git
cd pdf_data_extractor

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies
# On Ubuntu/Debian:
sudo apt-get install default-jre-headless ghostscript

# On macOS:
brew install openjdk ghostscript
```

### Running Locally

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## Technologies Used

- **Streamlit** - Web application framework
- **pdfplumber** - PDF table extraction library
- **tabula-py** - Java-based PDF table extraction (requires Java)
- **camelot-py** - Advanced PDF table extraction with CV support (requires Ghostscript)
- **pandas** - Data manipulation and export
- **xlsxwriter** - Excel file generation
- **openpyxl** - Excel file support

## How to Use

1. **Select extraction engine** - choose the PDF parsing method that works best for your document
2. **Upload** your PDF file
3. **Select pages** to extract from (optional - defaults to all pages)
4. **Choose header option** - whether the first row contains headers
5. **Extract tables** - click the "Extract Tables" button
6. **Edit tables** - modify data directly in the browser if needed
7. **Merge tables** (optional) - combine multiple tables with column mapping
8. **Download** - export to Excel or CSV format

## Tips for Best Results

- **Choose the right engine** for your PDF type:
  - Use **Camelot Lattice** for tables with visible borders
  - Use **Camelot Stream** for tables without visible borders
  - Use **PDFPlumber** as a general-purpose extractor
  - Use **Tabula** for complex tables or when other engines fail
- Make sure tables aren't images (scanned PDFs may require OCR preprocessing)
- Edit tables directly to fix any extraction errors
- Use smart merging to automatically align columns with the same name across tables
- Always preview before downloading to ensure data is correct

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
