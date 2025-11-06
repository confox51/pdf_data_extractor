# PDF Table Extractor

## Overview

This is a Streamlit-based web application that extracts tables from PDF files and allows users to export them to various formats. The application uses pdfplumber for PDF parsing and provides an interactive interface for selecting specific pages and previewing extracted tables before export.

**Core Purpose**: Simplify the process of extracting tabular data from PDF documents and converting them into structured formats (Excel, CSV) for further analysis.

**Key Technologies**:
- Streamlit (Web UI framework)
- pdfplumber (PDF parsing and table extraction)
- pandas (Data manipulation and export)
- xlsxwriter (Excel file generation)

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework**: Streamlit-based single-page application
- **Session State Management**: Uses Streamlit's session state to persist extracted tables and PDF metadata across reruns
- **Layout**: Wide layout configuration for better table visibility
- **Interactive Components**: File uploader, page selector, table preview, and export buttons

**Key Design Decisions**:
- Session state stores `extracted_tables` (list of dicts with id, page, original_headers, and dataframe), `edited_tables` (dict mapping table IDs to edited DataFrames), `merge_config` (merge settings), and `merged_preview` (preview of merged result)
- This allows users to extract tables once, edit them, configure merges, and perform multiple exports without re-processing
- Each table gets a unique ID for tracking edits across session reruns

### Backend Architecture

**Table Extraction Pipeline**:
1. **PDF Processing**: pdfplumber opens and parses PDF files
2. **Page Selection**: Users can select specific pages or process all pages
3. **Table Detection**: Automatic table detection per page using pdfplumber's `extract_tables()` method
4. **Data Cleaning**: 
   - First row is treated as header
   - Empty columns and rows are automatically removed
   - Converts raw table data to pandas DataFrame for structured manipulation

**Data Flow**:
```
PDF Upload → Page Selection → Table Extraction → DataFrame Conversion → Data Cleaning → Session Storage → Table Editing → (Optional) Table Merging → Export
```

**Table Editing Features** (Added November 2025):
- Inline editing of column headers and cell values using Streamlit's data_editor
- Real-time updates stored in session state
- Tab-based interface for editing multiple tables simultaneously

**Table Merging Features** (Added November 2025):
- Smart column mapping wizard for combining multiple tables
- Auto-matching of columns with identical names
- Manual column mapping via dropdown selectors
- Merge preview before download
- Handles tables with different column structures

**Error Handling Approach**:
- Page number validation (0-indexed internally, 1-indexed for display)
- Empty table filtering to avoid storing meaningless data
- DataFrame validation before storage

### Data Storage

**In-Memory Storage Only**:
- No persistent database
- Session state manages temporary data during user session
- All data is lost when session ends (by design for privacy/security)

**Data Structures**:
- `extracted_tables`: List[Dict[str, Any]] - stores table metadata including id, page number, original headers, and DataFrame
- `edited_tables`: Dict[int, pd.DataFrame] - stores user-edited versions of tables by table ID
- `pdf_pages`: int - tracks total pages in uploaded PDF
- `merge_config`: Dict - configuration for merged tables including selected tables and column mappings
- `merged_preview`: pd.DataFrame - preview of merged table result

### Export Functionality

**Supported Formats**:
- Excel (.xlsx) - using xlsxwriter engine
- CSV - using pandas native export

**Export Strategy**:
- Multi-table PDFs: Each table exported to separate sheets (Excel) or separate files (CSV)
- In-memory buffer generation using io.BytesIO for downloads
- No server-side file storage

## External Dependencies

### Python Libraries

1. **streamlit** - Web application framework
   - Purpose: Provides UI components and session management
   - Why chosen: Rapid development, built-in file handling, automatic reruns

2. **pdfplumber** - PDF parsing library
   - Purpose: Extract tables and text from PDF files
   - Why chosen: Superior table detection compared to alternatives (PyPDF2, pdfminer)
   - Handles complex table layouts with cell spanning

3. **pandas** - Data manipulation library
   - Purpose: Structure table data, clean data, export to various formats
   - Why chosen: Industry standard for tabular data operations

4. **xlsxwriter** - Excel file generation
   - Purpose: Create .xlsx files with pandas
   - Why chosen: Reliable Excel export, no Excel installation required

### Infrastructure

**Deployment Target**: Replit platform
- Python runtime environment
- No external databases or storage services
- Stateless architecture (suitable for serverless/container deployment)

**File I/O**:
- All file operations are in-memory (io.BytesIO)
- No local filesystem writes
- Downloads served directly from memory buffers

### Future Integration Considerations

The current architecture is self-contained with no external API integrations. Potential future integrations might include:
- Cloud storage (S3, Google Drive) for persistent exports
- OCR services for scanned PDFs
- Authentication services if multi-user features are added