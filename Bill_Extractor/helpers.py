
import os
import tempfile
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
import pandas as pd

# Set Tesseract OCR path (Windows users only)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update this path if needed

def get_pdf_text(pdf_file):
    text = ""
    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_file.read())
            tmp_file_path = tmp_file.name

        # Try extracting text using pypdf
        pdf_reader = PdfReader(tmp_file_path)
        for page in pdf_reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"

        # If no text was found, use OCR as fallback
        if not text.strip() or text.strip() == "CamScanner":
            print("No text found with pypdf. Using OCR...")
            text = ocr_extract_text(tmp_file_path)

    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

    return text

def ocr_extract_text(pdf_path):
    images = convert_from_path(pdf_path)  # Convert PDF to images
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"  # OCR on each page
    return text
import ast  # For safely evaluating the LLM response

import ast
import re

def extracted_data(pages_data):
    template = """
    Extract the following values from the provided bill:
    - Company Name (Rent, Gas, or Electric), Issue Date, Due Date, and Amount.

    Instructions:
    1. Identify the type of bill (Rent, Gas, or Electric) based on the text.
    2. Extract the Issue Date if available. If not, leave it blank.
    3. Extract the Due Date if available. If not, leave it blank.
    4. Extract the Amount (total amount due or current bill amount).

    Bill Text: {pages}

    Expected output format:
    {{
        'Company Name': 'Rent',  # or 'Gas' or 'Electric'
        'Issue Date': '05/09/2024',  # Leave blank if not available
        'Due Date': '05/09/2024',  # Leave blank if not available
        'Amount': '25,600'
    }}

    Return ONLY the dictionary in the expected format. Do not include any additional text or explanations.
    """
    prompt_template = PromptTemplate(input_variables=["pages"], template=template)
    llm = GoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)
    
    # Use .invoke() instead of __call__
    full_response = llm.invoke(prompt_template.format(pages=pages_data))
    
    # Debug: Print the raw LLM response
    print("Raw LLM Response:", full_response)
    
    # Clean the response
    try:
        # Remove the ```json wrapper if present
        if full_response.strip().startswith("```json"):
            full_response = re.sub(r"```json|```", "", full_response).strip()
        
        # Replace "null" with empty string
        full_response = full_response.replace("null", '""')
        
        # Parse the response into a dictionary
        structured_data = ast.literal_eval(full_response)
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing LLM response: {e}")
        structured_data = {
            'Company Name': '',
            'Issue Date': '',
            'Due Date': '',
            'Amount': ''
        }
    
    return structured_data
def create_docs(pdf_files):
    # Initialize an empty DataFrame
    df = pd.DataFrame(columns=["Company Name", "Issue Date", "Due Date", "Amount"],)
    
    # Process each uploaded file
    for pdf_file in pdf_files:
        # Extract text from the PDF
        extracted_text = get_pdf_text(pdf_file)
        
        # Extract structured data from the text
        structured_data = extracted_data(extracted_text)
        
        # Convert structured_data to a DataFrame
        structured_df = pd.DataFrame([structured_data])
        
        # Append the data to the main DataFrame
        df = pd.concat([df, structured_df], ignore_index=True)
    
    return df