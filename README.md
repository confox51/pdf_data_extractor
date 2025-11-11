# PDF Table Extractor

A Streamlit web application that extracts tables from PDF files and allows users to edit, merge, and export them to Excel or CSV formats.

## Features

- 📄 **Extract tables from PDFs** using pdfplumber (with tabula-py as fallback)
- ✏️ **Edit tables** - modify column headers and cell values directly in the browser
- 🔀 **Merge tables** - combine multiple tables with smart column mapping
- 💾 **Export** to Excel (.xlsx) or CSV formats
- 🎯 **Page selection** - extract tables from specific pages or all pages
- 🎨 **Interactive preview** - see extracted tables before downloading

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
     - Install system packages from `packages.txt` (Java for tabula-py)
     - Start your app

### Configuration Files

The following files are configured for Streamlit Community Cloud deployment:

- **`requirements.txt`** - Python dependencies
- **`packages.txt`** - System dependencies (Java Runtime for tabula-py)
- **`.streamlit/config.toml`** - Streamlit configuration for production

## Local Development

### Installation

```bash
# Clone the repository
git clone https://github.com/confox51/pdf_data_extractor.git
cd pdf_data_extractor

# Install Python dependencies
pip install -r requirements.txt

# Install Java (required for tabula-py)
# On Ubuntu/Debian:
sudo apt-get install default-jre-headless

# On macOS:
brew install openjdk
```

### Running Locally

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## Technologies Used

- **Streamlit** - Web application framework
- **pdfplumber** - Primary PDF table extraction
- **tabula-py** - Fallback PDF table extraction (requires Java)
- **pandas** - Data manipulation and export
- **xlsxwriter** - Excel file generation
- **openpyxl** - Excel file support

## How to Use

1. **Upload** your PDF file
2. **Select pages** to extract from (optional - defaults to all pages)
3. **Choose header option** - whether the first row contains headers
4. **Extract tables** - click the "Extract Tables" button
5. **Edit tables** - modify data directly in the browser if needed
6. **Merge tables** (optional) - combine multiple tables with column mapping
7. **Download** - export to Excel or CSV format

## Tips for Best Results

- Use PDFs with clear table structures - tables with visible borders work best
- Make sure tables aren't images (scanned PDFs may require OCR preprocessing)
- Edit tables directly to fix any extraction errors
- Use smart merging to automatically align columns with the same name across tables
- Always preview before downloading to ensure data is correct

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
