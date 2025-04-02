
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import streamlit as st  
import pandas as pd  
import uuid  
import os  
import qrcode  
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image  
import io  
from langchain.prompts import PromptTemplate,ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from dotenv import find_dotenv ,load_dotenv
load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
chat_model=ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp" ,temperature=0.7)
def generate_msg(ticket_data):
    template="""
        Craft a personalized ticket confirmation message with:
        1. Warm greeting addressing {email}
        2. Highlight the ticket ID: {ticket_id} 
        3. Brief instructions about QR code usage
        4. Closing with event details: {event_name}
        
        Keep it under 100 words. Tone: professional yet excited.
        """
    prompt=PromptTemplate(template=template,input_variables=['email','ticket_id','event_name'])
    chain=prompt|chat_model
    return chain.invoke({
        "email":ticket_data['Email'],
        'ticket_id':ticket_data['Ticket ID'],
        'event_name':'Annual Dinner'
        
    })
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_email_with_qr(email, message, qr_path):
    """Send email with embedded QR code"""
    
    SMTP_SERVER = "smtp.gmail.com"  
    SMTP_PORT = 587
    SENDER_EMAIL = os.getenv("SENDER_EMAIL") 
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")  
    
    if not all([SMTP_SERVER, SENDER_EMAIL, SENDER_PASSWORD]):
        st.error("Email configuration incomplete. Check your .env file")
        return False

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg['Subject'] = "Your Event Ticket"
    
    # Create HTML email with embedded image
    html = f"""
    <html>
        <body>
            <p>{message.replace('\n', '<br>')}</p>
            <p><strong>Your QR Code:</strong></p>
            <img src="cid:qrcode" width="200">
        </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    
    # Attach QR code image
    try:
        with open(qr_path, 'rb') as f:
            img_data = f.read()
        image = MIMEImage(img_data, name=os.path.basename(qr_path))
        image.add_header('Content-ID', '<qrcode>')
        msg.attach(image)
    except Exception as e:
        st.error(f"Failed to attach QR code: {e}")
        return False
    
    # Send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except smtplib.SMTPException as e:
        st.error(f"SMTP Error: {e}")
    except Exception as e:
        st.error(f"Error sending email: {e}")
    return False
# Ensure the QR code directory exists
os.makedirs("qrcodes", exist_ok=True)

# Initialize or load existing tickets
if not os.path.exists("tickets.csv"):
    pd.DataFrame(columns=['Email', 'Ticket ID']).to_csv("tickets.csv", index=False)

# Function to generate ticket IDs for new emails only
def generate_ticket_ids(email_list):
    # Load existing tickets
    try:
        existing_tickets = pd.read_csv("tickets.csv")
    except:
        existing_tickets = pd.DataFrame(columns=['Email', 'Ticket ID'])
    
    # Filter out emails that already have tickets
    new_emails = [email for email in email_list if email not in existing_tickets['Email'].values]
    
    # Generate tickets for new emails only
    new_tickets = {email: str(uuid.uuid4()) for email in new_emails}
    
    return new_tickets

# Function to generate QR codes
def generate_qr_code(ticket_id, email):
    qr = qrcode.make(ticket_id)
    qr_filename = f"qrcodes/{email.replace('@', '_')}.png"
    qr.save(qr_filename)
    return qr_filename

# Function to scan and decode QR codes
def scan_qr_code(uploaded_qr):
    image = Image.open(io.BytesIO(uploaded_qr.getvalue())).convert("RGB")
    img_array = np.array(image)

    # Convert to BGR and then grayscale
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Decode QR code
    decoded_data = decode(gray)

    if decoded_data:
        ticket_id = decoded_data[0].data.decode('utf-8').strip()
        return ticket_id

    return None
