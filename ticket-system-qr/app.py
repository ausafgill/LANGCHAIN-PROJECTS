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
from helper import generate_msg, send_email_with_qr, generate_ticket_ids, generate_qr_code, scan_qr_code

# Streamlit UI
st.title("🎟️ Ticket Creation & QR Code Validation System")

# Initialize session state for messages
if 'generated_messages' not in st.session_state:
    st.session_state.generated_messages = []

# Section: Upload emails and generate tickets
st.header("Generate Tickets")
uploaded_file = st.file_uploader("Upload a CSV file with emails", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    emails = df[df.columns[0]].tolist()

    ticket_data = generate_ticket_ids(emails)

    if ticket_data:
        for email, ticket_id in ticket_data.items():
            generate_qr_code(ticket_id, email)

        new_tickets_df = pd.DataFrame(ticket_data.items(), columns=['Email', 'Ticket ID'])
        
        if os.path.exists("tickets.csv") and os.path.getsize("tickets.csv") > 0:
            existing_tickets = pd.read_csv("tickets.csv")
            updated_tickets = pd.concat([existing_tickets, new_tickets_df], ignore_index=True)
        else:
            updated_tickets = new_tickets_df
            
        updated_tickets.to_csv("tickets.csv", index=False)

        st.success(f"✅ Generated {len(ticket_data)} new tickets!")
        
        st.download_button(
            "Download All Tickets CSV",
            data=updated_tickets.to_csv(index=False),
            file_name="tickets.csv",
            mime="text/csv"
        )
        
        st.download_button(
            "Download New Tickets CSV",
            data=new_tickets_df.to_csv(index=False),
            file_name="new_tickets.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ All emails already have tickets assigned.")
        
# --- Message Generation and Sending ---
st.header("✉️ Send Personalized Ticket Messages")

if st.button("Generate & Preview Messages"):
    st.session_state.generated_messages = []  # Clear previous messages
    
    if os.path.exists("tickets.csv") and os.path.getsize("tickets.csv") > 0:
        tickets_df = pd.read_csv("tickets.csv")
        
        with st.spinner("Generating messages..."):
            for _, row in tickets_df.iterrows():
                ticket_data = {
                    "Email": row['Email'],
                    "Ticket ID": row['Ticket ID']
                }
                message = generate_msg(ticket_data)
                qr_path = f"qrcodes/{row['Email'].replace('@', '_')}.png"
                
                st.session_state.generated_messages.append({
                    "email": row['Email'],
                    "message": message.content,
                    "qr_path": qr_path
                })
        
        # Display all previews
        for msg in st.session_state.generated_messages:
            with st.expander(f"Message for {msg['email']}"):
                st.write(msg['message'])
                if os.path.exists(msg['qr_path']):
                    st.image(msg['qr_path'], width=200)
                else:
                    st.warning("QR code not found")
    else:
        st.warning("No tickets generated yet")

# Single Send All button
if st.session_state.generated_messages:
    if st.button("🚀 Send All Messages", type="primary"):
        success_count = 0
        fail_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, msg in enumerate(st.session_state.generated_messages):
            status_text.text(f"Sending to {msg['email']}... ({i+1}/{len(st.session_state.generated_messages)})")
            progress_bar.progress((i+1)/len(st.session_state.generated_messages))
            
            if os.path.exists(msg['qr_path']):
                if send_email_with_qr(msg['email'], msg['message'], msg['qr_path']):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1
        
        status_text.empty()
        progress_bar.empty()
        st.success(f"✅ Sent {success_count} messages successfully!")
        if fail_count > 0:
            st.error(f"❌ Failed to send {fail_count} messages")



# Section: QR Code Validation
st.header("Validate Ticket with QR Code")

uploaded_qr = st.file_uploader("Upload a QR Code", type=["png", "jpg", "jpeg"])

if uploaded_qr:
    image = Image.open(uploaded_qr)
    st.image(image, caption="Uploaded QR Code", use_container_width=True)

    ticket_id = scan_qr_code(uploaded_qr)

    if ticket_id:
        try:
            # Load existing tickets
            if os.path.exists("tickets.csv") and os.path.getsize("tickets.csv") > 0:
                df_tickets = pd.read_csv("tickets.csv")
                df_tickets["Ticket ID"] = df_tickets["Ticket ID"].astype(str).str.strip()
                
                # Check if ticket exists
                if ticket_id in df_tickets["Ticket ID"].values:
                    email = df_tickets[df_tickets["Ticket ID"] == ticket_id]["Email"].values[0]
                    st.success(f"✅ Ticket is VALID!\n\nEmail: {email}\nTicket ID: {ticket_id}")
                else:
                    st.error("❌ Invalid Ticket - Not found in database")
            else:
                st.error("⚠️ No ticket data found. Please generate tickets first.")

        except Exception as e:
            st.error(f"Error processing ticket: {e}")
    else:
        st.warning("⚠️ No QR code detected. Please try again.")

# Section: Ticket Management
st.header("Ticket Management")

if st.button("Show All Tickets"):
    try:
        if os.path.exists("tickets.csv") and os.path.getsize("tickets.csv") > 0:
            df_tickets = pd.read_csv("tickets.csv")
            st.dataframe(df_tickets)
            
            # Add download button
            st.download_button(
                "Download All Tickets",
                data=df_tickets.to_csv(index=False),
                file_name="all_tickets.csv",
                mime="text/csv"
            )
        else:
            st.warning("No tickets found")
    except Exception as e:
        st.error(f"Error loading tickets: {e}")

if st.button("Clear All Tickets", type="primary"):
    if os.path.exists("tickets.csv"):
        os.remove("tickets.csv")
        pd.DataFrame(columns=['Email', 'Ticket ID']).to_csv("tickets.csv", index=False)
        st.success("All tickets cleared!")
    else:
        st.warning("No tickets to clear")