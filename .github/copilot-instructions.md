# Copilot Instructions for PDF Data Extractor

## Project Overview

This is a Streamlit web application that extracts tables from PDF files and allows users to edit, merge, and export them to Excel or CSV formats.

## Key Technologies

- **Streamlit** (v1.28+) - Web application framework for the UI
- **pdfplumber** (v0.11+) - Primary PDF table extraction library
- **tabula-py** (v2.9+) - Fallback PDF extraction (requires Java Runtime)
- **pandas** (v2.2+) - Data manipulation and DataFrame operations
- **xlsxwriter** & **openpyxl** - Excel file generation and support

## Architecture

- **Single-file application**: All logic is in `app.py` (639 lines)
- **Session state management**: Uses Streamlit's session state for extracted tables, edits, and merge configurations
- **Dual extraction strategy**: Primary extraction with pdfplumber, fallback to tabula-py if no tables found

## Code Patterns and Conventions

### Python Style
- Use type hints for function parameters and returns (e.g., `List[int]`, `Optional[str]`, `Dict[str, Any]`)
- Follow PEP 8 conventions
- Use descriptive variable names (e.g., `extracted_tables`, `use_first_row_as_header`)

### Streamlit Patterns
- Session state keys use snake_case: `st.session_state.extracted_tables`, `st.session_state.edited_tables`
- Initialize all session state variables at the top of the file
- Use Streamlit's column layout for better UI organization
- Page configuration is set with wide layout and appropriate icon

### Data Processing
- Tables are stored as dictionaries with metadata:
  - `id`: Unique table identifier
  - `page`: Page number (1-indexed for display)
  - `original_headers`: List of column names
  - `dataframe`: pandas DataFrame with table data
  - `method`: Extraction method used ('pdfplumber' or 'tabula-py')
- Clean empty rows/columns only for tables with data rows
- Preserve header-only tables to allow user data entry

### Error Handling
- Use try-except blocks for PDF extraction operations
- Fallback gracefully from pdfplumber to tabula-py
- Continue processing on individual table errors rather than failing entirely

## Testing Approach

Currently, this project does not have automated tests. When adding tests:
- Focus on critical functions: `extract_tables_from_pdf`, `merge_tables`, export functions
- Mock file uploads and PDF processing
- Test edge cases: empty PDFs, malformed tables, single-row tables

## Build and Deployment

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Dependencies
- Python 3.11+ (specified in pyproject.toml)
- Java Runtime Environment (for tabula-py fallback)

### Deployment
- Configured for Streamlit Community Cloud
- `requirements.txt`: Python dependencies
- `packages.txt`: System dependencies (Java)
- `.streamlit/config.toml`: Production configuration

## Important Notes

- **No tests currently exist** - Don't try to run pytest or similar
- **No linting configuration** - No flake8, black, or similar tools configured
- **Single monolithic file** - All code is in `app.py`; keep it that way unless refactoring
- **Streamlit-specific** - This is not a general Python library; it's a web app
- **Java dependency** - tabula-py requires JRE; this is handled via `packages.txt` on deployment

## Common Tasks

### Adding a new feature
1. Update session state initialization if needed (top of `app.py`)
2. Add UI elements using Streamlit components
3. Implement logic inline or as a helper function
4. Test manually by running `streamlit run app.py`

### Modifying table extraction
- Primary logic is in `extract_tables_from_pdf()` function
- Remember the dual strategy: pdfplumber first, tabula-py fallback
- Maintain backward compatibility with stored table metadata structure

### Changing export functionality
- Excel export uses `xlsxwriter`
- CSV export uses pandas' `to_csv()`
- Both create in-memory buffers for download

## Dependencies Management

- Primary dependency file: `requirements.txt`
- Also has `pyproject.toml` (for uv package manager)
- Keep version constraints loose (>=) unless specific version needed
- `uv.lock` is auto-generated; don't edit manually
