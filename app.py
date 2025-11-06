import streamlit as st
import pdfplumber
import pandas as pd
import io
from typing import List, Tuple
import xlsxwriter

# Configure page
st.set_page_config(
    page_title="PDF Table Extractor",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'extracted_tables' not in st.session_state:
    st.session_state.extracted_tables = []
if 'pdf_pages' not in st.session_state:
    st.session_state.pdf_pages = 0

def extract_tables_from_pdf(pdf_file, selected_pages=None) -> List[Tuple[int, pd.DataFrame]]:
    """
    Extract tables from PDF file.
    
    Args:
        pdf_file: Uploaded PDF file
        selected_pages: List of page numbers to extract from (0-indexed), or None for all pages
    
    Returns:
        List of tuples containing (page_number, dataframe)
    """
    tables_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        pages_to_process = selected_pages if selected_pages else range(len(pdf.pages))
        
        for page_num in pages_to_process:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                tables = page.extract_tables()
                
                for table_idx, table in enumerate(tables):
                    if table and len(table) > 0:
                        # Convert to DataFrame
                        df = pd.DataFrame(table[1:], columns=table[0])
                        # Clean up empty columns and rows
                        df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                        
                        if not df.empty:
                            tables_data.append((page_num + 1, df))  # Store 1-indexed page number
    
    return tables_data

def create_excel_file(tables_data: List[Tuple[int, pd.DataFrame]], merge_tables=False) -> bytes:
    """
    Create Excel file from extracted tables.
    
    Args:
        tables_data: List of tuples containing (page_number, dataframe)
        merge_tables: If True, merge all tables into one sheet
    
    Returns:
        Excel file as bytes
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if merge_tables and len(tables_data) > 0:
            # Merge all tables into one DataFrame
            merged_df = pd.concat([df for _, df in tables_data], ignore_index=True)
            merged_df.to_excel(writer, sheet_name='All Tables', index=False)
        else:
            # Create separate sheet for each table
            for idx, (page_num, df) in enumerate(tables_data):
                sheet_name = f'Page {page_num} Table {idx + 1}'[:31]  # Excel sheet name limit
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()

def create_csv_file(tables_data: List[Tuple[int, pd.DataFrame]], merge_tables=False) -> bytes:
    """
    Create CSV file from extracted tables.
    
    Args:
        tables_data: List of tuples containing (page_number, dataframe)
        merge_tables: If True, merge all tables into one CSV
    
    Returns:
        CSV file as bytes
    """
    output = io.StringIO()
    
    if merge_tables and len(tables_data) > 0:
        # Merge all tables into one DataFrame
        merged_df = pd.concat([df for _, df in tables_data], ignore_index=True)
        merged_df.to_csv(output, index=False)
    else:
        # Concatenate all tables with separators
        for idx, (page_num, df) in enumerate(tables_data):
            if idx > 0:
                output.write(f"\n\n--- Page {page_num} Table {idx + 1} ---\n")
            else:
                output.write(f"--- Page {page_num} Table {idx + 1} ---\n")
            df.to_csv(output, index=False)
    
    return output.getvalue().encode('utf-8')

# App UI
st.title("📄 PDF Table Extractor")
st.markdown("""
Welcome! This tool helps you extract tables from PDF files easily.

### How to use:
1. **Upload** your PDF file using the file uploader below
2. **Select pages** (optional) - choose specific pages or extract from all pages
3. **Preview** the extracted tables to verify the data
4. **Download** your data in CSV or Excel format

Let's get started! 👇
""")

st.divider()

# File upload section
uploaded_file = st.file_uploader(
    "Upload your PDF file",
    type=['pdf'],
    help="Select a PDF file that contains tables you want to extract"
)

if uploaded_file is not None:
    # Display file info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.success(f"✅ File uploaded: **{uploaded_file.name}**")
    
    # Get PDF information
    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        st.session_state.pdf_pages = total_pages
    
    with col2:
        st.info(f"📄 Total pages: **{total_pages}**")
    
    st.divider()
    
    # Page selection section
    st.subheader("📑 Page Selection")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        extraction_mode = st.radio(
            "Extract from:",
            ["All pages", "Specific pages"],
            help="Choose whether to extract tables from all pages or only selected pages"
        )
    
    selected_pages = None
    if extraction_mode == "Specific pages":
        with col2:
            st.markdown("**Select page numbers:**")
            page_input = st.text_input(
                "Enter page numbers",
                placeholder="e.g., 1,3,5-7",
                help="Enter page numbers separated by commas. You can use ranges like '5-7' for pages 5, 6, and 7."
            )
            
            if page_input:
                try:
                    # Parse page numbers
                    pages = []
                    parts = page_input.split(',')
                    for part in parts:
                        part = part.strip()
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            pages.extend(range(start - 1, end))  # Convert to 0-indexed
                        else:
                            pages.append(int(part) - 1)  # Convert to 0-indexed
                    
                    # Filter valid pages
                    selected_pages = [p for p in pages if 0 <= p < total_pages]
                    
                    if selected_pages:
                        st.success(f"Will extract from {len(selected_pages)} page(s): {', '.join(str(p+1) for p in sorted(selected_pages))}")
                    else:
                        st.warning("No valid page numbers entered.")
                except ValueError:
                    st.error("Invalid format. Please use numbers separated by commas (e.g., 1,3,5-7)")
    
    st.divider()
    
    # Extract button
    if st.button("🔍 Extract Tables", type="primary", use_container_width=True):
        with st.spinner("Extracting tables from PDF..."):
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Extract tables
            tables_data = extract_tables_from_pdf(uploaded_file, selected_pages)
            st.session_state.extracted_tables = tables_data
            
            if len(tables_data) > 0:
                st.success(f"✅ Successfully extracted **{len(tables_data)}** table(s)!")
            else:
                st.warning("⚠️ No tables found in the selected pages. The PDF might not contain recognizable tables.")
    
    # Display extracted tables
    if len(st.session_state.extracted_tables) > 0:
        st.divider()
        st.subheader("📊 Extracted Tables Preview")
        
        # Create tabs for each table
        for idx, (page_num, df) in enumerate(st.session_state.extracted_tables):
            with st.expander(f"📄 Table {idx + 1} (from Page {page_num}) - {len(df)} rows × {len(df.columns)} columns", expanded=(idx == 0)):
                st.dataframe(df, use_container_width=True)
        
        st.divider()
        
        # Download section
        st.subheader("💾 Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            merge_tables = st.checkbox(
                "Merge all tables",
                value=False,
                help="Combine all tables into a single file/sheet"
            )
        
        with col2:
            download_format = st.selectbox(
                "File format",
                ["Excel (.xlsx)", "CSV (.csv)"],
                help="Choose the format for downloading the extracted data"
            )
        
        st.markdown("---")
        
        # Generate download buttons
        col1, col2 = st.columns(2)
        
        if download_format == "Excel (.xlsx)":
            with col1:
                excel_data = create_excel_file(st.session_state.extracted_tables, merge_tables)
                filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_tables.xlsx"
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                if merge_tables:
                    st.info("All tables will be in one sheet")
                else:
                    st.info(f"Each table will be in a separate sheet ({len(st.session_state.extracted_tables)} sheets)")
        
        else:  # CSV
            with col1:
                csv_data = create_csv_file(st.session_state.extracted_tables, merge_tables)
                filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_tables.csv"
                st.download_button(
                    label="📥 Download CSV File",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                if merge_tables:
                    st.info("All tables will be merged into one CSV")
                else:
                    st.info(f"All tables will be in one CSV with separators")

else:
    # Show helpful tips when no file is uploaded
    st.info("👆 Please upload a PDF file to get started")
    
    with st.expander("💡 Tips for best results"):
        st.markdown("""
        - **Use PDFs with clear table structures** - Tables with visible borders work best
        - **Check your PDF** - Make sure tables aren't images (scanned PDFs may not work)
        - **Page selection** - If you have a large PDF, extract only the pages you need
        - **Preview before downloading** - Always check the preview to ensure data was extracted correctly
        - **Format choice** - Use Excel for multiple sheets, CSV for simple data
        """)
