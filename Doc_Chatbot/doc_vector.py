import os
import tempfile 
from dotenv import load_dotenv, find_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import streamlit as st
from streamlit_chat import message

# Load API Key
load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Models
chat_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

# Initialize Streamlit UI
st.title("Docs QA Bot ")
st.header("Ask Anything")

# Initialize session state
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'qa_chain' not in st.session_state:
    st.session_state['qa_chain'] = None

# File Uploader
pdf_files = st.file_uploader('Upload Your documents', type=["pdf"], accept_multiple_files=True)

# Submit Button
extract_button = st.button("Submit")
documents = []

# Process Uploaded PDFs
if extract_button and pdf_files:
    with st.spinner("Processing PDFs..."):
        try:
            for pdf in pdf_files:
              
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_pdf.write(pdf.read())  
                    temp_pdf_path = temp_pdf.name  

                
                pypdf = PyPDFLoader(temp_pdf_path)
                documents.extend(pypdf.load())

               
                os.unlink(temp_pdf_path)

            # Text Splitting
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.split_documents(documents)

            # Create FAISS Vector Store
            db = FAISS.from_documents(docs, embeddings)

            # Create QA Chain and store in session state
            st.session_state['qa_chain'] = ConversationalRetrievalChain.from_llm(
                chat_model,
                db.as_retriever(search_kwargs={'k': 6}),
                return_source_documents=True,
                verbose=False
            )

            st.success("PDFs processed! You can start asking questions now.")

        except Exception as e:
            st.error(f"Error processing PDFs: {e}")

def get_query():
    return st.chat_input("Ask a question about a Document")


user_input = get_query()

if user_input:
    if st.session_state['qa_chain']:  # Ensure QA Chain is initialized
        result = st.session_state['qa_chain']({'question': user_input, 'chat_history': st.session_state['chat_history']})
        
        # Store chat history
        st.session_state['chat_history'].append((user_input, result['answer']))
        st.session_state.past.append(user_input)
        st.session_state.generated.append(result['answer'])

    else:
        st.error("Please upload and submit a document first.")

# Display Chat
if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])):
        message(st.session_state['generated'][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
