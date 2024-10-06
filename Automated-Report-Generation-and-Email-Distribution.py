import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import pandas as pd
import requests
import sqlite3
from fpdf import FPDF
import os
from datetime import datetime

# Configuration
DATABASE_PATH = 'business.db'
API_URL = 'https://api.example.com/data'
EMAIL_SENDER = 'your_email@gmail.com'
EMAIL_PASSWORD = 'your_password'
EMAIL_RECIPIENTS = ['recipient1@example.com', 'recipient2@example.com']
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Functions
def fetch_api_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def fetch_db_data(db_path, query):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def generate_excel_report(data_frames, sheet_names, output_path):
    with pd.ExcelWriter(output_path) as writer:
        for df, sheet in zip(data_frames, sheet_names):
            df.to_excel(writer, sheet_name=sheet, index=False)
    print(f"Excel report generated at {output_path}")

def generate_pdf_summary(summary_data, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for key, value in summary_data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
    
    pdf.output(output_path)
    print(f"PDF summary generated at {output_path}")

def send_email(subject, body, attachments, recipients):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    for file_path in attachments:
        with open(file_path, 'rb') as file:
            part = MIMEApplication(file.read(), Name=os.path.basename(file_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        msg.attach(part)
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Main Workflow
def main():
    # Step 1: Fetch Data
    api_data = fetch_api_data(API_URL)
    db_query = "SELECT * FROM sales WHERE date = DATE('now')"
    db_data = fetch_db_data(DATABASE_PATH, db_query)
    
    # Step 2: Generate Reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_report = f"report_{timestamp}.xlsx"
    generate_excel_report([pd.DataFrame(api_data), db_data], ['API_Data', 'DB_Sales'], excel_report)
    
    summary = {
        "Report Date": datetime.now().strftime("%Y-%m-%d"),
        "Total API Records": len(api_data),
        "Total Sales": db_data['amount'].sum()
    }
    pdf_summary = f"summary_{timestamp}.pdf"
    generate_pdf_summary(summary, pdf_summary)
    
    # Step 3: Send Email
    subject = f"Daily Business Report - {datetime.now().strftime('%Y-%m-%d')}"
    body = "Please find attached the daily business reports."
    attachments = [excel_report, pdf_summary]
    send_email(subject, body, attachments, EMAIL_RECIPIENTS)
    
    # Cleanup (optional)
    os.remove(excel_report)
    os.remove(pdf_summary)

if __name__ == "__main__":
    main()
