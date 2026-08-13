import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from io import BytesIO
import pandas as pd
import streamlit as st

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="GBV - Product Inquiry",
    page_icon="🧪",
    layout="centered",
)

# ---------- Custom CSS for Beautification ----------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    h1 {
        font-weight: 700 !important;
        color: #1f3a5f !important;
        text-align: center;
        margin-bottom: 10px !important;
    }
    .subheader {
        text-align: center;
        color: #5c6b7c;
        font-size: 18px;
        margin-bottom: 30px;
    }

    /* Form Card Styling */
    .stForm {
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        padding: 40px !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1) !important;
    }

    /* Input Fields */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {
        border-radius: 10px !important;
        border: 1px solid #e0e5ec !important;
        padding: 12px !important;
        background-color: #f9fafc !important;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus, 
    .stTextArea > div > div > textarea:focus {
        border-color: #1f3a5f !important;
        box-shadow: 0 0 0 3px rgba(31, 58, 95, 0.1) !important;
    }
    
    /* Labels */
    .st-emotion-cache-1ueww6k, .st-emotion-cache-16txtl3 {
        font-weight: 600 !important;
        color: #2c3e50 !important;
        margin-bottom: 8px !important;
    }

    /* Submit Button */
    .stButton > button {
        background: linear-gradient(90deg, #1f3a5f 0%, #2c5278 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        height: 55px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        width: 100% !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(31, 58, 95, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(31, 58, 95, 0.4) !important;
    }
    
    /* Alerts */
    .stAlert {
        border-radius: 12px !important;
        font-weight: 500 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Retrieve Owner's Secrets ----------
# These are fetched securely from Replit Secrets
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL") # xyz@bvg.com is stored here
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

# Safety check to ensure owner configured secrets properly
if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
    st.error("⚠️ **Configuration Error:** The app owner has not set email credentials in Replit Secrets.")
    st.stop()

# ---------- UI Layout ----------
st.markdown("<h1>🧪 Product Inquiry Form</h1>", unsafe_allow_html=True)
st.markdown("<div class='subheader'>Please fill in all details below. <b>All fields are strictly mandatory.</b></div>", unsafe_allow_html=True)

with st.form("inquiry_form", clear_on_submit=False):
    
    st.markdown("#### 👤 Contact Details")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *")
    with col2:
        # THIS is where the END USER enters their email
        user_email = st.text_input("Your Email ID *")

    phone = st.text_input("Phone Number *")

    st.markdown("#### 📦 Product Details")
    col3, col4 = st.columns(2)
    with col3:
        product = st.text_input("Product Name *")
    with col4:
        cas_no = st.text_input("CAS NO. *")
    
    col5, col6 = st.columns(2)
    with col5:
        import_domestic = st.selectbox("For Import or Domestic *", ["", "Import", "Domestic"])
    with col6:
        req_type = st.selectbox("Firm Requirement or Budgetary *", ["", "Firm Requirement", "Budgetary"])

    st.markdown("#### 📋 Order Specifics")
    col7, col8 = st.columns(2)
    with col7:
        payment_terms = st.text_input("Expected Payment Terms *")
    with col8:
        timelines = st.text_input("Anticipated Timelines *")

    packing_req = st.text_input("Packing Requirement *")
    comments = st.text_area("Comments / Additional Info *", height=120)

    submit_btn = st.form_submit_button("Submit Inquiry 🚀")

# ---------- Validation & Processing ----------
if submit_btn:
    # 1. Strict Mandatory Validation
    errors = []
    if not name.strip(): errors.append("Full Name")
    if not user_email.strip() or "@" not in user_email: errors.append("Valid Your Email ID")
    if not phone.strip(): errors.append("Phone Number")
    if not product.strip(): errors.append("Product Name")
    if not cas_no.strip(): errors.append("CAS NO.")
    if not import_domestic: errors.append("Import/Domestic selection")
    if not req_type: errors.append("Requirement Type selection")
    if not payment_terms.strip(): errors.append("Payment Terms")
    if not timelines.strip(): errors.append("Anticipated Timelines")
    if not packing_req.strip(): errors.append("Packing Requirement")
    if not comments.strip(): errors.append("Comments")

    if errors:
        st.error(f"⚠️ **Submission Blocked!** Please fill out the following mandatory field(s):\n\n- {', '.join(errors)}")
    else:
        try:
            # 2. Create DataFrame
            inquiry_data = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Name": name.strip(),
                "Email ID": user_email.strip(),
                "Phone Number": phone.strip(),
                "Product": product.strip(),
                "CAS NO.": cas_no.strip(),
                "Import/Domestic": import_domestic,
                "Requirement Type": req_type,
                "Payment Terms": payment_terms.strip(),
                "Anticipated Timelines": timelines.strip(),
                "Packing Requirement": packing_req.strip(),
                "Comments": comments.strip()
            }
            df = pd.DataFrame([inquiry_data])

            # 3. Generate Excel file in memory (BytesIO) to attach to email
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False, engine="openpyxl")
            excel_buffer.seek(0)

            # 4. Save to Master Excel locally on Replit
            master_file = "inquiries_master.xlsx"
            if os.path.exists(master_file):
                existing_df = pd.read_excel(master_file, engine="openpyxl")
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df.to_excel(master_file, index=False, engine="openpyxl")
            else:
                df.to_excel(master_file, index=False, engine="openpyxl")

            # 5. Send Email to xyz@bvg.com
            subject = f"New Product Inquiry – {product.strip()} ({cas_no.strip()})"
            body = f"""
Hello Team,

A new product inquiry has been submitted. Please find the details attached as an Excel file.

Regards,
Inquiry Bot
"""
            msg = MIMEMultipart()
            msg["From"] = SENDER_EMAIL
            msg["To"] = RECEIVER_EMAIL  # Goes to xyz@bvg.com
            msg["Reply-To"] = user_email.strip() # If you hit reply, it goes to the end user!
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Attach the in-memory Excel file
            part = MIMEBase("application", "octet-stream")
            part.set_payload(excel_buffer.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename="Inquiry_Details.xlsx")
            msg.attach(part)

            # Connect to SMTP and send
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            st.success("✅ **Thank you!** Your inquiry has been successfully submitted and emailed to our team.")
            st.balloons()

        except Exception as e:
            st.error(f"❌ **An error occurred while processing your request:** {str(e)}")
