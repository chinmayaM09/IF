import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import io
import re

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Product Inquiry Form",
    page_icon="📋",
    layout="centered"
)

st.title("📋 Product Inquiry Form")
st.markdown("Please fill in **all** fields below. Every field is **mandatory**.")
st.markdown("---")

# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Basic phone validation — allows digits, spaces, +, -, ()."""
    phone = phone.strip()
    if len(phone) < 7 or len(phone) > 20:
        return False
    pattern = r'^[\d\s\+\-\(\)]+$'
    return re.match(pattern, phone) is not None


def create_excel(data_dict: dict) -> io.BytesIO:
    """
    Create a styled Excel file from the data dictionary.
    Returns a BytesIO buffer positioned at 0.
    """
    column_order = [
        "Timestamp", "Name", "Email", "Phone",
        "Product", "CAS", "Quantity", "UOM",
        "Packing", "Lead Time", "Other Requirements"
    ]
    df = pd.DataFrame([data_dict], columns=column_order)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Inquiry', index=False)

        # Auto-adjust column widths
        worksheet = writer.sheets['Inquiry']
        for idx, column in enumerate(worksheet.columns, 1):
            max_length = max(
                (len(str(cell.value)) for cell in column),
                default=10
            )
            worksheet.column_dimensions[
                column[0].column_letter
            ].width = max(max_length + 4, 14)

        # Bold header row
        from openpyxl.styles import Font
        for cell in worksheet[1]:
            cell.font = Font(bold=True)

    buffer.seek(0)
    return buffer


def send_email_with_excel(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    smtp_server: str,
    smtp_port: int,
    subject: str,
    body: str,
    excel_buffer: io.BytesIO,
    filename: str
):
    """Send an email with an Excel attachment via SMTP."""
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Attach the Excel file
    part = MIMEBase(
        'application',
        'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    part.set_payload(excel_buffer.read())
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename="{filename}"'
    )
    msg.attach(part)

    # Connect and send
    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    else:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()


# ──────────────────────────────────────────────
# Form UI
# ──────────────────────────────────────────────

with st.form("inquiry_form", clear_on_submit=False):

    st.subheader("👤 Contact Information")
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "Name *",
            placeholder="Enter your full name"
        )
        email = st.text_input(
            "Email *",
            placeholder="you@example.com"
        )
        phone = st.text_input(
            "Phone *",
            placeholder="+91 98765 43210"
        )

    with col2:
        product = st.text_input(
            "Product *",
            placeholder="Product name"
        )
        cas = st.text_input(
            "CAS Number *",
            placeholder="e.g., 64-17-5"
        )
        quantity = st.number_input(
            "Quantity *",
            min_value=0.0,
            step=0.1,
            format="%.2f"
        )

    uom = st.selectbox(
        "UOM (Unit of Measure) *",
        ["Kg", "gm", "litre", "MT", "kilolitre"]
    )

    st.subheader("📦 Additional Details")
    col3, col4 = st.columns(2)

    with col3:
        packing = st.text_input(
            "Packing *",
            placeholder="e.g., 25 Kg drum"
        )

    with col4:
        lead_time = st.text_input(
            "Lead Time *",
            placeholder="e.g., 7 days"
        )

    other_req = st.text_area(
        "Any Other Requirements *",
        placeholder="Specify any additional requirements, specifications, etc.",
        height=100
    )

    submitted = st.form_submit_button(
        "Submit Inquiry",
        type="primary",
        use_container_width=True
    )

# ──────────────────────────────────────────────
# Form Validation & Processing
# ──────────────────────────────────────────────

if submitted:
    errors = []

    # --- Mandatory field checks ---
    if not name.strip():
        errors.append("• **Name** is required.")
    if not email.strip():
        errors.append("• **Email** is required.")
    elif not validate_email(email.strip()):
        errors.append("• Please enter a **valid email address**.")
    if not phone.strip():
        errors.append("• **Phone** is required.")
    elif not validate_phone(phone.strip()):
        errors.append("• Please enter a **valid phone number**.")
    if not product.strip():
        errors.append("• **Product** is required.")
    if not cas.strip():
        errors.append("• **CAS number** is required.")
    if quantity <= 0:
        errors.append("• **Quantity** must be greater than 0.")
    if not packing.strip():
        errors.append("• **Packing** is required.")
    if not lead_time.strip():
        errors.append("• **Lead time** is required.")
    if not other_req.strip():
        errors.append("• **Other requirements** cannot be empty.")

    # --- Show errors or process ---
    if errors:
        st.error("Please fix the following errors:")
        for err in errors:
            st.markdown(err)
    else:
        # Build data dictionary
        data_dict = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": name.strip(),
            "Email": email.strip(),
            "Phone": phone.strip(),
            "Product": product.strip(),
            "CAS": cas.strip(),
            "Quantity": quantity,
            "UOM": uom,
            "Packing": packing.strip(),
            "Lead Time": lead_time.strip(),
            "Other Requirements": other_req.strip()
        }

        try:
            # ── Load secrets from Replit ──
            sender_email    = st.secrets["EMAIL_ADDRESS"]
            sender_password = st.secrets["EMAIL_PASSWORD"]
            recipient_email = st.secrets.get("RECIPIENT_EMAIL", sender_email)
            smtp_server     = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
            smtp_port       = int(st.secrets.get("SMTP_PORT", 587))

            # ── Create Excel attachment ──
            excel_buffer = create_excel(data_dict)
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '', name.strip().replace(' ', '_'))
            filename = f"inquiry_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            # ── Compose email ──
            subject = f"🧪 New Product Inquiry: {product.strip()} (CAS: {cas.strip()})"

            body = f"""\
New product inquiry received via the online form.

═══════════════════════════════════════════
  INQUIRY DETAILS
═══════════════════════════════════════════

  Name            : {data_dict['Name']}
  Email           : {data_dict['Email']}
  Phone           : {data_dict['Phone']}
  Product         : {data_dict['Product']}
  CAS Number      : {data_dict['CAS']}
  Quantity        : {data_dict['Quantity']} {data_dict['UOM']}
  Packing         : {data_dict['Packing']}
  Lead Time       : {data_dict['Lead Time']}
  Other Req.      : {data_dict['Other Requirements']}
  Timestamp       : {data_dict['Timestamp']}

═══════════════════════════════════════════

An Excel sheet with the above details is attached.
"""

            # ── Send email ──
            with st.spinner("📤 Sending your inquiry..."):
                send_email_with_excel(
                    sender_email=sender_email,
                    sender_password=sender_password,
                    recipient_email=recipient_email,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    subject=subject,
                    body=body,
                    excel_buffer=excel_buffer,
                    filename=filename
                )

            st.success(
                "✅ Your inquiry has been submitted successfully! "
                "An email with the Excel sheet has been sent."
            )

            # Show submitted summary
            with st.expander("📋 View Submitted Details"):
                st.json(data_dict)

        except KeyError as e:
            st.error(
                f"⚙️ Configuration error: Missing secret key `{str(e)}`. "
                "Please configure all required secrets in Replit "
                "(see setup instructions below)."
            )
        except smtplib.SMTPAuthenticationError:
            st.error(
                "🔐 Email authentication failed. If using Gmail, ensure you "
                "are using an **App Password** (not your regular password) "
                "and that 2-Step Verification is enabled."
            )
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: `{str(e)}`")

