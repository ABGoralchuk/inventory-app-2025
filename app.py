import streamlit as st
from ai_handler import GeminiHandler
from sheets_handler import SheetHandler
import pandas as pd

# --- Page Config ---
st.set_page_config(
    page_title="Lab Inventory Scanner",
    page_icon="lab_icon.png",
    layout="centered"
)

# --- Mobile Icon Fix ---
# Inject HTML to try and force the mobile home screen icon
ICON_URL = "https://raw.githubusercontent.com/ABGoralchuk/inventory-app-2025/main/lab_icon.png"
st.markdown(f"""
    <head>
        <link rel="apple-touch-icon" href="{ICON_URL}">
        <link rel="icon" type="image/png" href="{ICON_URL}">
    </head>
    """, unsafe_allow_html=True)

# --- Custom CSS for Premium Feel ---
st.markdown("""
    <style>
    /* Global Styles */
    .main {
        background-color: #ffffff;
        font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #333333;
    }
    
    /* Top Border / Brand Line */
    header {
        border-top: 45px solid #004C9B; /* TMU Blue */
    }
    
    /* Headers - Academic Style */
    h1 {
        font-family: 'Merriweather', 'Georgia', serif;
        color: #004C9B; /* TMU Blue */
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.2rem;
        padding-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 1.2rem; /* Smaller font to fit on one line */
        line-height: 1.3;
    }
    
    /* Subheader / Branding */
    .lab-subtitle {
        text-align: center;
        font-family: 'Open Sans', sans-serif;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid #eee;
        padding-bottom: 1rem;
        font-weight: 400;
    }
    
    /* Buttons - TMU Style */
    .stButton>button {
        width: 100%;
        border-radius: 0px; /* More academic/square */
        height: 3em;
        background-color: #004C9B; /* TMU Blue */
        color: white;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: none;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #003366; /* Darker Blue */
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        border-radius: 0px;
        border: 1px solid #ccc;
        padding: 0.5rem;
    }
    
    /* Data Editor / Tables */
    .stDataFrame {
        border: 1px solid #eee;
    }
    
    /* Success/Info Messages */
    .stAlert {
        border-radius: 0px;
        border-left: 5px solid #004C9B;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Title & Branding ---
# --- Title & Branding ---
# --- Title & Branding ---
# --- Title & Branding ---
# --- Title & Branding ---
st.markdown("<h1>Food and Soft Materials Research Group</h1>", unsafe_allow_html=True)
st.markdown("<div class='lab-subtitle'>Inventory System</div>", unsafe_allow_html=True)

# --- Initialize Handlers ---
if 'ai_handler' not in st.session_state:
    st.session_state.ai_handler = GeminiHandler()
if 'sheet_handler' not in st.session_state:
    st.session_state.sheet_handler = SheetHandler()

# --- Sidebar Configuration ---
# --- Constants ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_MxKxXLU4jOsLu2gKkCOr2k2NspcWinZPaW2Udcw0F4/edit?gid=2119641818#gid=2119641818"



# --- Main Logic ---

# --- Main Logic ---
import time

# 1. Input Method
input_method = st.radio("Select Input Method", ["Camera", "Upload Images (Batch)"], horizontal=True)

image_data_list = []

if input_method == "Camera":
    image_file = st.camera_input("Take a photo")
    if image_file:
        image_data_list.append({"name": "Camera Photo", "bytes": image_file.getvalue()})
else:
    image_files = st.file_uploader("Upload images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    if image_files:
        for img in image_files:
            image_data_list.append({"name": img.name, "bytes": img.getvalue()})

# 2. Process Images
if image_data_list:
    if st.button(f"🔍 Extract Data from {len(image_data_list)} Image(s)"):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        batch_results = []
        
        for i, img_item in enumerate(image_data_list):
            status_text.text(f"Processing {i+1}/{len(image_data_list)}: {img_item['name']}...")
            
            # Extract data
            extracted = st.session_state.ai_handler.extract_data(img_item['bytes'])
            
            if extracted:
                # Add to results
                batch_results.append({
                    "ingredient": extracted.get("ingredient", ""),
                    "manufacturer": extracted.get("manufacturer", ""),
                    "quantity_g": extracted.get("quantity_g", "")
                })
            else:
                # Add empty placeholder if failed
                batch_results.append({
                    "ingredient": "ERROR",
                    "manufacturer": "Failed to extract",
                    "quantity_g": ""
                })
            
            # Update progress
            progress_bar.progress((i + 1) / len(image_data_list))
            
            # Smart Queue Delay (to avoid API limits)
            if i < len(image_data_list) - 1:
                time.sleep(4) # 4 seconds delay between requests
        
        st.session_state.batch_data = batch_results
        status_text.text("✅ Processing complete!")
        st.success(f"Processed {len(image_data_list)} images.")

# 3. Review & Edit (Batch)
if 'batch_data' in st.session_state and st.session_state.batch_data:
    st.divider()
    st.subheader("📝 Review & Edit All Items")
    st.info("You can edit the data directly in the table below before saving.")
    
    # Editable Dataframe
    edited_df = st.data_editor(
        pd.DataFrame(st.session_state.batch_data),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "ingredient": "Ingredient Name",
            "manufacturer": "Manufacturer",
            "quantity_g": "Quantity (g)"
        }
    )
    
    if st.button("💾 Save ALL to 'Stock_In'"):
        # Convert back to list of dicts
        final_data_list = edited_df.to_dict('records')
        
        with st.spinner("Saving batch to Google Sheets..."):
            success = st.session_state.sheet_handler.batch_append_data(SHEET_URL, final_data_list)
            
            if success:
                st.success(f"✅ Successfully saved {len(final_data_list)} items!")
                # Clear state
                del st.session_state.batch_data
                time.sleep(2)
                st.rerun()


