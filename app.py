import streamlit as st
import pdfplumber
import pandas as pd
import io
from typing import List, Tuple, Dict, Any, Optional
import xlsxwriter
import tabula

# Try to import camelot - make it optional in case it's not available on deployment
CAMELOT_AVAILABLE = False
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError as e:
    # Camelot not available - app will still work with other engines
    pass

# Configure page
st.set_page_config(
    page_title="PDF Table Extractor",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'extracted_tables' not in st.session_state:
    st.session_state.extracted_tables = []
if 'edited_tables' not in st.session_state:
    st.session_state.edited_tables = {}
if 'pdf_pages' not in st.session_state:
    st.session_state.pdf_pages = 0
if 'merge_config' not in st.session_state:
    st.session_state.merge_config = None
if 'merged_preview' not in st.session_state:
    st.session_state.merged_preview = None
if 'extraction_method' not in st.session_state:
    st.session_state.extraction_method = None
if 'selected_engine' not in st.session_state:
    st.session_state.selected_engine = 'pdfplumber'

def extract_tables_from_pdf(pdf_file, selected_pages: Optional[List[int]] = None, use_first_row_as_header: bool = True, engine: str = 'pdfplumber') -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract tables from PDF file using the specified extraction engine.
    
    Args:
        pdf_file: Uploaded PDF file
        selected_pages: List of page numbers to extract from (0-indexed), or None for all pages
        use_first_row_as_header: If True, use first row as headers; if False, use generic headers (Column_0, Column_1, etc.)
        engine: Extraction engine to use ('pdfplumber', 'tabula-py', 'camelot-lattice', 'camelot-stream')
    
    Returns:
        Tuple of (List of dictionaries containing table metadata and data, extraction method used)
    """
    # Route to the appropriate extraction method based on engine
    if engine.startswith('camelot'):
        flavor = 'lattice' if engine == 'camelot-lattice' else 'stream'
        return extract_with_camelot(pdf_file, selected_pages, use_first_row_as_header, flavor)
    elif engine == 'tabula-py':
        # Use tabula-py directly
        return extract_with_tabula(pdf_file, selected_pages, use_first_row_as_header)
    else:
        # Default to pdfplumber
        return extract_with_pdfplumber(pdf_file, selected_pages, use_first_row_as_header)

def extract_with_pdfplumber(pdf_file, selected_pages: Optional[List[int]] = None, use_first_row_as_header: bool = True) -> Tuple[List[Dict[str, Any]], str]:
    """Extract tables using pdfplumber."""
    tables_data = []
    table_id = 0
    extraction_method = "pdfplumber"
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            pages_to_process = selected_pages if selected_pages else range(len(pdf.pages))
            
            for page_num in pages_to_process:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if table and len(table) > 0:
                            try:
                                if use_first_row_as_header:
                                    # Handle None values in headers
                                    headers = [str(h) if h is not None else f"Column_{i}" for i, h in enumerate(table[0])]
                                    # Create DataFrame with first row as headers
                                    if len(table) > 1:
                                        df = pd.DataFrame(table[1:], columns=headers)
                                    else:
                                        # Single row table - treat as header-only, create empty DataFrame with those columns
                                        df = pd.DataFrame(columns=headers)
                                else:
                                    # Use generic headers and include all rows as data
                                    num_cols = len(table[0]) if table else 0
                                    headers = [f"Column_{i}" for i in range(num_cols)]
                                    df = pd.DataFrame(table, columns=headers)
                                
                                # Clean up empty rows and columns only if we have data rows
                                # For header-only tables, preserve the column structure
                                if len(df) > 0:
                                    df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                                
                                # Store table even if empty (header-only) to allow user to fill in data
                                tables_data.append({
                                    'id': table_id,
                                    'page': page_num + 1,  # 1-indexed for display
                                    'original_headers': list(df.columns),
                                    'dataframe': df.copy(),
                                    'method': 'pdfplumber'
                                })
                                table_id += 1
                            except Exception as e:
                                continue
    except Exception as e:
        extraction_method = f"pdfplumber (failed: {str(e)[:50]})"
    
    return tables_data, extraction_method

def extract_with_tabula(pdf_file, selected_pages: Optional[List[int]] = None, use_first_row_as_header: bool = True) -> Tuple[List[Dict[str, Any]], str]:
    """Extract tables using tabula-py."""
    tables_data = []
    table_id = 0
    extraction_method = "tabula-py"
    
    try:
        pdf_file.seek(0)
        
        # Determine which pages to extract
        if selected_pages:
            page_list = [p + 1 for p in selected_pages]  # tabula uses 1-indexed pages
        else:
            page_list = "all"
        
        # Extract tables using tabula
        # tabula.read_pdf has a 'header' parameter: None means no header row
        if use_first_row_as_header:
            tabula_tables = tabula.read_pdf(
                pdf_file,
                pages=page_list,
                multiple_tables=True,
                silent=True
            )
        else:
            # Extract without treating first row as header
            tabula_tables = tabula.read_pdf(
                pdf_file,
                pages=page_list,
                multiple_tables=True,
                silent=True,
                pandas_options={'header': None}
            )
        
        # Process tabula results
        for idx, df in enumerate(tabula_tables):
            if df is not None:
                # If not using first row as header, apply generic column names
                if not use_first_row_as_header and df.columns.dtype == 'int64':
                    df.columns = [f"Column_{i}" for i in range(len(df.columns))]
                
                # Clean up the dataframe only if we have data rows
                # For header-only tables, preserve the column structure
                if len(df) > 0:
                    df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                
                # Store table even if empty (header-only) to allow user to fill in data
                # Try to determine which page this table came from
                page_num = selected_pages[min(idx, len(selected_pages) - 1)] + 1 if selected_pages else idx + 1
                
                tables_data.append({
                    'id': table_id,
                    'page': page_num,
                    'original_headers': list(df.columns),
                    'dataframe': df.copy(),
                    'method': 'tabula-py'
                })
                table_id += 1
    except Exception as e:
        extraction_method = f"tabula-py (failed: {str(e)[:50]})"
    
    return tables_data, extraction_method

def extract_with_camelot(pdf_file, selected_pages: Optional[List[int]] = None, use_first_row_as_header: bool = True, flavor: str = 'lattice') -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract tables from PDF file using Camelot.
    
    Args:
        pdf_file: Uploaded PDF file
        selected_pages: List of page numbers to extract from (0-indexed), or None for all pages
        use_first_row_as_header: If True, use first row as headers; if False, use generic headers
        flavor: Camelot flavor to use ('lattice' or 'stream')
    
    Returns:
        Tuple of (List of dictionaries containing table metadata and data, extraction method used)
    """
    # Check if Camelot is available
    if not CAMELOT_AVAILABLE:
        return [], f"camelot-{flavor} (not available)"
    
    tables_data = []
    table_id = 0
    extraction_method = f"camelot-{flavor}"
    
    try:
        # Camelot requires a file path, so we need to save the uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Determine which pages to extract
            if selected_pages:
                # Camelot uses 1-indexed pages, comma-separated string
                page_list = ','.join([str(p + 1) for p in selected_pages])
            else:
                page_list = 'all'
            
            # Extract tables using camelot
            tables = camelot.read_pdf(tmp_path, pages=page_list, flavor=flavor, suppress_stdout=True)
            
            # Process camelot results
            for table in tables:
                df = table.df
                
                if df is not None and not df.empty:
                    if use_first_row_as_header:
                        # Use first row as headers
                        if len(df) > 0:
                            headers = [str(h) if h != '' else f"Column_{i}" for i, h in enumerate(df.iloc[0])]
                            if len(df) > 1:
                                df = pd.DataFrame(df.iloc[1:].values, columns=headers)
                            else:
                                # Single row table - treat as header-only
                                df = pd.DataFrame(columns=headers)
                    else:
                        # Use generic headers
                        df.columns = [f"Column_{i}" for i in range(len(df.columns))]
                    
                    # Clean up empty rows and columns only if we have data rows
                    if len(df) > 0:
                        df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                    
                    # Get page number from table
                    page_num = table.page
                    
                    tables_data.append({
                        'id': table_id,
                        'page': page_num,  # Already 1-indexed from camelot
                        'original_headers': list(df.columns),
                        'dataframe': df.copy(),
                        'method': f'camelot-{flavor}'
                    })
                    table_id += 1
        finally:
            # Clean up temporary file
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        extraction_method = f"camelot-{flavor} (failed: {str(e)[:50]})"
    
    return tables_data, extraction_method

def merge_tables_with_mapping(tables: List[Dict[str, Any]], column_mapping: Dict[str, Dict[int, str]]) -> pd.DataFrame:
    """
    Merge selected tables using the provided column mapping.
    
    Args:
        tables: List of table dictionaries to merge
        column_mapping: Dict mapping target columns to {table_id: source_column}
    
    Returns:
        Merged DataFrame
    """
    all_data = []
    
    for table in tables:
        table_id = table['id']
        df = st.session_state.edited_tables.get(table_id, table['dataframe']).copy()
        
        # Create a new DataFrame with standardized columns
        standardized_df = pd.DataFrame()
        
        for target_col, source_mapping in column_mapping.items():
            if table_id in source_mapping:
                source_col = source_mapping[table_id]
                if source_col in df.columns:
                    standardized_df[target_col] = df[source_col]
                else:
                    standardized_df[target_col] = None
            else:
                standardized_df[target_col] = None
        
        all_data.append(standardized_df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

def create_excel_file(tables_data: List[Tuple[int, pd.DataFrame]], merge_tables: bool = False) -> bytes:
    """Create Excel file from tables."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:  # type: ignore
        if merge_tables and len(tables_data) > 0:
            merged_df = pd.concat([df for _, df in tables_data], ignore_index=True)
            merged_df.to_excel(writer, sheet_name='All Tables', index=False)
        else:
            for idx, (page_num, df) in enumerate(tables_data):
                sheet_name = f'Page {page_num} Table {idx + 1}'[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()

def create_csv_file(tables_data: List[Tuple[int, pd.DataFrame]], merge_tables: bool = False) -> bytes:
    """Create CSV file from tables."""
    output = io.StringIO()
    
    if merge_tables and len(tables_data) > 0:
        merged_df = pd.concat([df for _, df in tables_data], ignore_index=True)
        merged_df.to_csv(output, index=False)
    else:
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
Welcome! This tool helps you extract, edit, and merge tables from PDF files.

### How to use:
1. **Select extraction engine** - choose your preferred PDF parsing method
2. **Upload** your PDF file
3. **Select pages** to extract from (optional)
4. **Edit tables** - modify headers and data as needed
5. **Merge tables** - combine multiple tables with smart column mapping (optional)
6. **Download** your data in CSV or Excel format
""")

st.divider()

# Engine Selection
st.subheader("🔧 Select Extraction Engine")
st.markdown("""
Choose the PDF parsing engine that works best for your document:
""")

# Determine number of columns based on Camelot availability
if CAMELOT_AVAILABLE:
    col1, col2, col3, col4 = st.columns(4)
else:
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("📘 PDFPlumber", use_container_width=True, type="primary" if st.session_state.selected_engine == 'pdfplumber' else "secondary"):
        st.session_state.selected_engine = 'pdfplumber'

with col2:
    if st.button("📗 Tabula", use_container_width=True, type="primary" if st.session_state.selected_engine == 'tabula-py' else "secondary"):
        st.session_state.selected_engine = 'tabula-py'

if CAMELOT_AVAILABLE:
    with col3:
        if st.button("📙 Camelot (Lattice)", use_container_width=True, type="primary" if st.session_state.selected_engine == 'camelot-lattice' else "secondary"):
            st.session_state.selected_engine = 'camelot-lattice'

    with col4:
        if st.button("📕 Camelot (Stream)", use_container_width=True, type="primary" if st.session_state.selected_engine == 'camelot-stream' else "secondary"):
            st.session_state.selected_engine = 'camelot-stream'

# Display info about selected engine
engine_info = {
    'pdfplumber': "**PDFPlumber** - Good general-purpose extractor, works well with most PDFs",
    'tabula-py': "**Tabula-py** - Java-based extractor, good for complex tables",
}

if CAMELOT_AVAILABLE:
    engine_info['camelot-lattice'] = "**Camelot Lattice** - Best for tables with visible borders/lines"
    engine_info['camelot-stream'] = "**Camelot Stream** - Best for tables without visible borders"

# If selected engine is camelot but camelot is not available, fall back to pdfplumber
if st.session_state.selected_engine.startswith('camelot') and not CAMELOT_AVAILABLE:
    st.session_state.selected_engine = 'pdfplumber'
    st.warning("⚠️ Camelot is not available on this platform. Defaulting to PDFPlumber.")

st.info(f"**Selected:** {engine_info[st.session_state.selected_engine]}")

st.divider()

# File upload section
uploaded_file = st.file_uploader(
    "Upload your PDF file",
    type=['pdf'],
    help="Select a PDF file that contains tables you want to extract"
)

if uploaded_file is not None:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.success(f"✅ File uploaded: **{uploaded_file.name}**")
    
    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        st.session_state.pdf_pages = total_pages
    
    with col2:
        st.info(f"📄 Total pages: **{total_pages}**")
    
    st.divider()
    
    # Page selection and extraction settings
    st.subheader("📑 Extraction Settings")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        extraction_mode = st.radio(
            "Extract from:",
            ["All pages", "Specific pages"],
            help="Choose whether to extract tables from all pages or only selected pages"
        )
    
    with col2:
        use_first_row_as_header = st.checkbox(
            "First row contains headers",
            value=True,
            help="When checked, the first row of each table will be used as column headers. Uncheck to use generic headers (Column_0, Column_1, etc.) and keep all data rows."
        )
    
    selected_pages = None
    if extraction_mode == "Specific pages":
        st.markdown("**Select page numbers:**")
        page_input = st.text_input(
            "Enter page numbers",
            placeholder="e.g., 1,3,5-7",
            help="Enter page numbers separated by commas. You can use ranges like '5-7'."
        )
        
        if page_input:
            try:
                pages = []
                parts = page_input.split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        pages.extend(range(start - 1, end))
                    else:
                        pages.append(int(part) - 1)
                
                selected_pages = [p for p in pages if 0 <= p < total_pages]
                
                if selected_pages:
                    st.success(f"Will extract from {len(selected_pages)} page(s): {', '.join(str(p+1) for p in sorted(selected_pages))}")
                else:
                    st.warning("No valid page numbers entered.")
            except ValueError:
                st.error("Invalid format. Use numbers separated by commas (e.g., 1,3,5-7)")
    
    st.divider()
    
    # Extract button
    if st.button("🔍 Extract Tables", type="primary", use_container_width=True):
        with st.spinner(f"Extracting tables from PDF using {st.session_state.selected_engine}..."):
            uploaded_file.seek(0)
            tables_data, extraction_method = extract_tables_from_pdf(
                uploaded_file, 
                selected_pages, 
                use_first_row_as_header,
                engine=st.session_state.selected_engine
            )
            st.session_state.extracted_tables = tables_data
            st.session_state.edited_tables = {}
            st.session_state.merge_config = None
            st.session_state.merged_preview = None
            st.session_state.extraction_method = extraction_method
            st.session_state.use_first_row_as_header = use_first_row_as_header
            
            if len(tables_data) > 0:
                st.success(f"✅ Successfully extracted **{len(tables_data)}** table(s) using **{extraction_method}**!")
            else:
                if "failed" in extraction_method:
                    st.error(f"⚠️ No tables found. {extraction_method}")
                    st.info("💡 Tip: Try a different extraction engine or check if the PDF contains tables in image format (scanned PDF).")
                else:
                    st.warning("⚠️ No tables found. The PDF might not contain recognizable tables, or the tables might be in image format (scanned PDF).")
    
    # Display and edit tables
    if len(st.session_state.extracted_tables) > 0:
        st.divider()
        st.subheader("✏️ Edit Tables")
        st.markdown("You can edit column headers and cell values directly in the tables below.")
        
        # Create tabs for each table
        tabs = st.tabs([f"Table {idx + 1} (Page {table['page']})" for idx, table in enumerate(st.session_state.extracted_tables)])
        
        for idx, (tab, table) in enumerate(zip(tabs, st.session_state.extracted_tables)):
            with tab:
                table_id = table['id']
                
                # Get current version (edited or original)
                if table_id in st.session_state.edited_tables:
                    current_df = st.session_state.edited_tables[table_id]
                else:
                    current_df = table['dataframe']
                
                st.markdown(f"**Table {idx + 1}** from Page {table['page']} - {len(current_df)} rows × {len(current_df.columns)} columns")
                
                # Editable data editor
                edited_df = st.data_editor(
                    current_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    key=f"editor_{table_id}"
                )
                
                # Store edited version
                st.session_state.edited_tables[table_id] = edited_df
        
        st.divider()
        
        # Merge Tables Section (only show for 2-5 tables)
        if 1 < len(st.session_state.extracted_tables) <= 5:
            st.subheader("🔀 Merge Tables (Optional)")
            
            with st.expander("Configure Table Merge", expanded=False):
                st.markdown("""
                Merge multiple tables into one by mapping columns. Columns with the same name will be automatically matched.
                You can also manually map different column names to combine them.
                """)
                
                # Table selection
                st.markdown("#### Step 1: Select Tables to Merge")
                selected_table_ids = []
                
                cols = st.columns(min(3, len(st.session_state.extracted_tables)))
                for idx, table in enumerate(st.session_state.extracted_tables):
                    with cols[idx % 3]:
                        if st.checkbox(
                            f"Table {idx + 1} (Page {table['page']})",
                            value=True,
                            key=f"select_{table['id']}"
                        ):
                            selected_table_ids.append(table['id'])
                
                if len(selected_table_ids) > 1:
                    st.divider()
                    st.markdown("#### Step 2: Column Mapping")
                    
                    selected_tables = [t for t in st.session_state.extracted_tables if t['id'] in selected_table_ids]
                    
                    # Get all unique columns from selected tables
                    all_columns_by_table = {}
                    all_unique_columns = set()
                    
                    for table in selected_tables:
                        df = st.session_state.edited_tables.get(table['id'], table['dataframe'])
                        all_columns_by_table[table['id']] = list(df.columns)
                        all_unique_columns.update(df.columns)
                    
                    # Auto-match columns with same names
                    st.info(f"📊 Found {len(all_unique_columns)} unique column(s) across selected tables")
                    
                    # Show column mapping interface
                    column_mapping = {}
                    
                    for col_name in sorted(all_unique_columns):
                        with st.container():
                            st.markdown(f"**Target Column: `{col_name}`**")
                            
                            mapping_for_col = {}
                            cols = st.columns(len(selected_tables))
                            
                            for idx, (col, table) in enumerate(zip(cols, selected_tables)):
                                with col:
                                    table_id = table['id']
                                    table_cols = all_columns_by_table[table_id]
                                    
                                    # Default to same column name if it exists
                                    default_idx = table_cols.index(col_name) if col_name in table_cols else 0
                                    
                                    # Add "Skip" option
                                    options = ["(Skip)"] + table_cols
                                    default_selection = default_idx + 1 if col_name in table_cols else 0
                                    
                                    selected = st.selectbox(
                                        f"Table {idx + 1}",
                                        options=options,
                                        index=default_selection,
                                        key=f"map_{col_name}_{table_id}"
                                    )
                                    
                                    if selected != "(Skip)":
                                        mapping_for_col[table_id] = selected
                            
                            if mapping_for_col:
                                column_mapping[col_name] = mapping_for_col
                    
                    st.divider()
                    
                    # Preview merged table
                    if st.button("🔍 Preview Merged Table", use_container_width=True):
                        with st.spinner("Creating merge preview..."):
                            try:
                                merged_df = merge_tables_with_mapping(selected_tables, column_mapping)
                                st.session_state.merged_preview = merged_df
                                st.session_state.merge_config = {
                                    'tables': selected_tables,
                                    'mapping': column_mapping
                                }
                                st.success("✅ Merge preview created!")
                            except Exception as e:
                                st.error(f"Error creating merge preview: {str(e)}")
                    
                    if st.session_state.merged_preview is not None:
                        st.markdown("#### Merged Table Preview")
                        st.dataframe(st.session_state.merged_preview, use_container_width=True)
                        st.info(f"📊 Merged table: {len(st.session_state.merged_preview)} rows × {len(st.session_state.merged_preview.columns)} columns")
                
                elif len(selected_table_ids) == 1:
                    st.warning("Select at least 2 tables to merge")
                else:
                    st.warning("No tables selected")
        
        st.divider()
        
        # Download section
        st.subheader("💾 Download Options")
        
        # Check if we have many tables (>5)
        many_tables = len(st.session_state.extracted_tables) > 5
        
        if many_tables:
            # For >5 tables, simplify the download - just concatenate all
            st.info(f"📊 You have {len(st.session_state.extracted_tables)} tables. All tables will be automatically stacked vertically in a single sheet/file.")
            
            format_choice = st.selectbox("File format", ["Excel (.xlsx)", "CSV (.csv)"])
            
            # Prepare edited tables for download (all concatenated)
            tables_for_download = []
            for table in st.session_state.extracted_tables:
                table_id = table['id']
                df = st.session_state.edited_tables.get(table_id, table['dataframe'])
                tables_for_download.append((table['page'], df))
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            if format_choice == "Excel (.xlsx)":
                with col1:
                    excel_data = create_excel_file(tables_for_download, merge_tables=True)
                    st.download_button(
                        label="📥 Download All Tables (Excel)",
                        data=excel_data,
                        file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_all_tables.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                with col2:
                    st.info(f"All {len(tables_for_download)} tables stacked in one sheet")
            else:
                with col1:
                    csv_data = create_csv_file(tables_for_download, merge_tables=True)
                    st.download_button(
                        label="📥 Download All Tables (CSV)",
                        data=csv_data,
                        file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_all_tables.csv",
                        mime="text/csv",
                        type="primary",
                        use_container_width=True
                    )
                with col2:
                    st.info(f"All {len(tables_for_download)} tables stacked in one file")
        else:
            # For <=5 tables, keep the current merge/individual choice
            # Determine what to download
            if len(st.session_state.extracted_tables) > 1:
                download_mode = st.radio(
                    "What would you like to download?",
                    ["Individual tables (edited)", "Merged table (if configured)"],
                    help="Choose whether to download individual tables or the merged result"
                )
            else:
                # Only one table, no merge option needed
                download_mode = "Individual tables (edited)"
            
            if download_mode == "Merged table (if configured)":
                if st.session_state.merged_preview is not None:
                    st.success("✅ Merged table is ready for download")
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        format_choice = st.selectbox("File format", ["Excel (.xlsx)", "CSV (.csv)"])
                    
                    # Prepare data
                    merged_df = st.session_state.merged_preview
                    tables_for_download = [(1, merged_df)]  # Single merged table
                    
                    col1, col2 = st.columns(2)
                    
                    if format_choice == "Excel (.xlsx)":
                        with col1:
                            excel_data = create_excel_file(tables_for_download, merge_tables=True)
                            st.download_button(
                                label="📥 Download Merged Excel",
                                data=excel_data,
                                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_merged.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary",
                                use_container_width=True
                            )
                    else:
                        with col1:
                            csv_data = create_csv_file(tables_for_download, merge_tables=True)
                            st.download_button(
                                label="📥 Download Merged CSV",
                                data=csv_data,
                                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_merged.csv",
                                mime="text/csv",
                                type="primary",
                                use_container_width=True
                            )
                else:
                    st.warning("⚠️ No merged table configured. Please create a merge preview first.")
            
            else:  # Individual tables
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    merge_individual = st.checkbox(
                        "Combine all individual tables",
                        value=False,
                        help="Merge all tables into one file/sheet (simple concatenation)"
                    )
                
                with col2:
                    format_choice = st.selectbox("File format", ["Excel (.xlsx)", "CSV (.csv)"])
                
                # Prepare edited tables for download
                tables_for_download = []
                for table in st.session_state.extracted_tables:
                    table_id = table['id']
                    df = st.session_state.edited_tables.get(table_id, table['dataframe'])
                    tables_for_download.append((table['page'], df))
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                if format_choice == "Excel (.xlsx)":
                    with col1:
                        excel_data = create_excel_file(tables_for_download, merge_individual)
                        st.download_button(
                            label="📥 Download Excel File",
                            data=excel_data,
                            file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_tables.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            use_container_width=True
                        )
                    with col2:
                        if merge_individual:
                            st.info("All tables in one sheet")
                        else:
                            st.info(f"Each table in separate sheet ({len(tables_for_download)} sheets)")
                else:
                    with col1:
                        csv_data = create_csv_file(tables_for_download, merge_individual)
                        st.download_button(
                            label="📥 Download CSV File",
                            data=csv_data,
                            file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_tables.csv",
                            mime="text/csv",
                            type="primary",
                            use_container_width=True
                        )
                    with col2:
                        if merge_individual:
                            st.info("All tables merged in CSV")
                        else:
                            st.info("All tables in CSV with separators")

else:
    st.info("👆 Please upload a PDF file to get started")
    
    with st.expander("💡 Tips for best results"):
        st.markdown("""
        - **Use PDFs with clear table structures** - Tables with visible borders work best
        - **Check your PDF** - Make sure tables aren't images (scanned PDFs may not work)
        - **Edit tables** - Fix any extraction errors by editing headers and data directly
        - **Smart merging** - Automatically align columns with the same name across tables
        - **Preview before downloading** - Always check the preview to ensure data is correct
        """)
