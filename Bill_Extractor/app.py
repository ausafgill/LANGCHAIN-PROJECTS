import streamlit as st
from helpers import *
import pandas as pd

def main():
    st.set_page_config(page_title="Bill Extractor")
    st.title("Bill Extractor AI Agent")
    
    # Initialize session state variables
    if "data_frame" not in st.session_state:
        st.session_state.data_frame = None
    if "extract_button_clicked" not in st.session_state:
        st.session_state.extract_button_clicked = False
    
    # Upload bills
    pdf_files = st.file_uploader("Upload your bills in PDF format only.", type=["pdf"], accept_multiple_files=True)
    
    # Extract button
    extract_button = st.button("Extract bill data")
    
    if extract_button and pdf_files:
        with st.spinner("Extracting...it takes time"):
            # Process the uploaded files and create a DataFrame
            st.session_state.data_frame = create_docs(pdf_files)
            st.session_state.extract_button_clicked = True
        
        st.success("Extraction completed successfully!")
    
    # Display the DataFrame if extraction is done
    if st.session_state.extract_button_clicked and st.session_state.data_frame is not None:
        st.write(st.session_state.data_frame.head())
        
        # Divide the amount among roommates
        room_mates = st.text_input("How many people do you want to divide the amount among?")
        cal = st.button("Calculate")
        
        if room_mates and cal:
            try:
                # Remove commas and convert "Amount" column to float
                st.session_state.data_frame["Amount"] = st.session_state.data_frame["Amount"].str.replace(",", "").astype(float)
                
                total_amount = st.session_state.data_frame["Amount"].sum()
                
                # Convert room_mates to integer
                room_mates = int(room_mates)
                
                # Calculate per-head amount
                per_head_amount = total_amount / room_mates
                
                # Display the total amount and per-head amount
                st.write(f"Total amount from all bills: {total_amount}")
                st.write(f"Dividing among {room_mates} people gives: {per_head_amount} per head")
            except ValueError as e:
                st.error(f"Invalid input: {e}. Please enter a valid number.")
        
        # Convert DataFrame to CSV
        csv_data = st.session_state.data_frame.to_csv(index=False).encode("utf-8")
        
        # Download button for CSV
        st.download_button(
            "Download data as CSV",
            csv_data,
            "CSV_BILLS.csv",
            "text/csv",
            key="download-csv"
        )

if __name__ == "__main__":
    main()