import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import pdfplumber
from PIL import Image

# ==========================================
# 🔑 CONFIGURATION & ENGINE SETTINGS
# ==========================================
_NEXUS_CORE_KEY = "AIzaSyBeIZZWg0GNHjPT2IO95s1lybBAGkAUV3o"
MODEL_NAME = "gemini-2.5-flash" 

st.set_page_config(page_title="ALPHA MERGE ENGINE", page_icon="💠", layout="wide")

# --- 1. UI STYLING (FUTURISTIC DARK THEME) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle at center, #001524, #000000); color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: rgba(0, 10, 20, 0.95); border-right: 2px solid #00f2ff; }
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 242, 255, 0.3) !important;
        border-radius: 15px !important; padding: 25px !important;
    }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif; color: #00f2ff !important; letter-spacing: 3px; text-shadow: 0 0 10px #00f2ff; }
    .stButton > button {
        width: 100%; border-radius: 4px; background: transparent; color: #00f2ff;
        border: 1px solid #00f2ff; font-weight: bold; padding: 12px; transition: 0.4s; text-transform: uppercase;
    }
    .stButton > button:hover { background: #00f2ff; color: #000; box-shadow: 0 0 30px #00f2ff; transform: scale(1.01); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. UTILITY: HEADER REPAIR ENGINE ---
def fix_duplicate_headers(columns):
    new_cols = []
    counts = {}
    for col in columns:
        col_str = str(col).strip() if col else "Unnamed"
        if col_str in counts:
            counts[col_str] += 1
            new_cols.append(f"{col_str}_{counts[col_str]}")
        else:
            counts[col_str] = 0
            new_cols.append(col_str)
    return new_cols

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>💠 ALPHA MERGE ENGINE</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    MODE_OCR = "📷 IMAGE TO EXCEL"
    MODE_PDF_CONVERT = "📡 PDF TO EXCEL"
    MODE_DATA = "🛰️ EXCEL MERGE"
    
    app_mode = st.selectbox("SELECT MODULE", [MODE_OCR, MODE_PDF_CONVERT, MODE_DATA])
    
    st.markdown("---")
    st.info(f"Active System: {MODEL_NAME}")
    if st.button("☣️ SYSTEM RESET"):
        st.session_state.clear()
        st.rerun()

st.markdown(f"<h1 style='text-align: center;'>{app_mode}</h1>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 📡 MODULE: PDF TO EXCEL (FIXED)
# ==========================================
if app_mode == MODE_PDF_CONVERT:
    uploaded_pdf = st.file_uploader("Upload PDF Document", type=['pdf'])
    
    if uploaded_pdf:
        if st.button("⚡ EXTRACT TABLES FROM PDF"):
            all_tables = []
            try:
                with pdfplumber.open(uploaded_pdf) as pdf:
                    with st.spinner(f"Analyzing {len(pdf.pages)} pages..."):
                        for page in pdf.pages:
                            table = page.extract_table()
                            if table:
                                # Fix duplicate headers to prevent Reindexing Error
                                clean_headers = fix_duplicate_headers(table[0])
                                df_page = pd.DataFrame(table[1:], columns=clean_headers)
                                all_tables.append(df_page)
                
                if all_tables:
                    final_df = pd.concat(all_tables, ignore_index=True)
                    st.session_state['pdf_result'] = final_df
                    st.success("Extraction Complete!")
                else:
                    st.warning("No digital tables found. If this is a scanned PDF, use the IMAGE TO EXCEL module.")
            except Exception as e:
                st.error(f"Extraction Error: {e}")

    if 'pdf_result' in st.session_state:
        st.dataframe(st.session_state['pdf_result'], use_container_width=True)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            st.session_state['pdf_result'].to_excel(writer, index=False)
        st.download_button("📥 DOWNLOAD EXCEL", buffer.getvalue(), "pdf_data.xlsx")

# ==========================================
# 📷 MODULE: IMAGE TO EXCEL (OCR)
# ==========================================
elif app_mode == MODE_OCR:
    uploaded_img = st.file_uploader("Upload Table Image", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_img:
        col1, col2 = st.columns(2)
        with col1: st.image(uploaded_img, use_container_width=True)
        
        with col2:
            if st.button("⚡ NEURAL OCR EXTRACTION"):
                try:
                    genai.configure(api_key=_NEXUS_CORE_KEY)
                    model = genai.GenerativeModel(MODEL_NAME)
                    img = Image.open(uploaded_img)
                    prompt = "Extract the table data into CSV format. Return ONLY the raw CSV text. No markdown, no conversation."
                    
                    with st.spinner("🌀 AI ANALYZING IMAGE..."):
                        response = model.generate_content([prompt, img])
                        csv_text = response.text.strip().replace("```csv", "").replace("```", "")
                        df = pd.read_csv(io.StringIO(csv_text))
                        df.columns = fix_duplicate_headers(df.columns)
                        st.session_state['ocr_data'] = df
                except Exception as e:
                    st.error(f"Neural Error: {e}")

    if 'ocr_data' in st.session_state:
        st.dataframe(st.session_state['ocr_data'], use_container_width=True)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            st.session_state['ocr_data'].to_excel(writer, index=False)
        st.download_button("📥 DOWNLOAD EXCEL", buf.getvalue(), "ocr_extracted.xlsx")

# ==========================================
# 📊 MODULE: EXCEL MERGE
# ==========================================
elif app_mode == MODE_DATA:
    f1 = st.file_uploader("Upload File Alpha", type=['csv', 'xlsx'])
    f2 = st.file_uploader("Upload File Beta", type=['csv', 'xlsx'])
    
    if f1 and f2:
        df1 = pd.read_csv(f1) if f1.name.endswith('.csv') else pd.read_excel(f1)
        df2 = pd.read_csv(f2) if f2.name.endswith('.csv') else pd.read_excel(f2)
        
        # Repair headers for both files
        df1.columns = fix_duplicate_headers(df1.columns)
        df2.columns = fix_duplicate_headers(df2.columns)
        
        c1, c2 = st.columns(2)
        k1 = c1.selectbox("Join Column (Alpha)", df1.columns)
        k2 = c2.selectbox("Join Column (Beta)", df2.columns)
        
        if st.button("🔗 EXECUTE MERGE"):
            merged_df = pd.merge(df1, df2, left_on=k1, right_on=k2, how='outer')
            st.dataframe(merged_df, use_container_width=True)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                merged_df.to_excel(writer, index=False)

            st.download_button("📥 DOWNLOAD MERGED FILE", buf.getvalue(), "merged_result.xlsx")
