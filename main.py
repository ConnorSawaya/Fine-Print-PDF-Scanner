''' Uses Streamlit for the ui pypdf to read pdfs selected by the user from tkinter to use openai chatgpt api to see i nthe text if theres anything hiding it in like sus terms and condiotions or whatever and then displays the results in the ui using st. also it has pre analyzed sample pdfs for testing purposes and for deploy purposes so ppl dont steal my api key 😒. '''
# imports 
import os # for env variables and file paths
import sys # for file paths
import time # for sleeping
from pypdf import PdfReader # the pdf reader to convert pdf to text for the chatgpt api to later look at
from openai import OpenAI # chatgpt api wrapper
from dotenv import load_dotenv # env viariable loader
import streamlit as st # for running the ui
import json # for running sample files so no one steals my api key
import re


load_dotenv() # loads env variavble for api key!!
anaylsis_text = "" # variable to store chatgpt response

def get_client():
    api_key = os.getenv("OPENAI_API_KEY") 
    
    if not api_key:
        st.error("API KEY NOT FOUND. Sample PDFS still work tho :)")
        return None
        
    # You MUST return the client here if the key exists!
    return OpenAI(api_key=api_key)


BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # base directory for the project (for file paths)

SAMPLE_JSON = os.path.join(BASE_DIR, "sample_files.json") # file path for sample files(responses)


def select_pdf(): # selection for pdf
    return st.file_uploader("Choose a PDF file", type="pdf")  # file uploader for the streamlit (NOT DEMO)



def pre_select_pdf(): # selection for pdf samples function
    options = ["Discord TOS", "APPLE PURCHASE AGREEMENT", "None"]
    choice = st.selectbox("Or select a sample PDF", options)

    if choice == "Discord TOS" and st.button("Scan Discord TOS"): # checks dropdown for click on it and it loads the sample reponse
        with open(SAMPLE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f) # loads the json file from the sample.


        st.write(data["Discord_TOS"])

    elif choice == "APPLE PURCHASE AGREEMENT" and st.button("Scan APPLE PURCHASE AGREEMENT"): # checks dropdown for click on it and it loads the sample reponse
        with open(SAMPLE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)


        st.write(data["Apple_Purchase_Agreement"]) # Apples purchase agrement for sampleing !!
    
    else:
        return None



def scan_fine_print(uploaded_file): # scans the pdf (main thing)  
    if not uploaded_file:
        st.warning("Upload a PDF first, or try a sample PDF below (works offline).")
        return ""
    
    client = get_client()
    
    # Check if client exists before proceeding
    if client is None:
        st.warning("Live scan needs OPENAI_API_KEY. Sample PDFs below work without a key.")
        return ""
        
    #---------------------------------------------------- PDF reader to convert pdf to text ----------------------------------------------------#  
    try:
        reader = PdfReader(uploaded_file) # reads the pdf file
        full_text = "".join([(page.extract_text() or "") for page in reader.pages]) # extracts text into one string
    except Exception as e:
        st.error(f"Could not read that PDF: {e}")
        return ""
    if not full_text.strip():
        st.warning("No readable text found in that PDF. Try a sample PDF below.")
        return ""
    #---------------------------------------------------- PDF reader to convert pdf to text ----------------------------------------------------#  
        
    
     #---------------------------------------------------- chatgpt api stuff ----------------------------------------------------#  
    with st.spinner("Analyzing for fine print..."):
        response = client.chat.completions.create(
             model="gpt-4o-mini", # model selection (gpt4.0 mini is hella cheap so) can be changed later for maybe something cheaper or more powerful
            messages=[
                {"role": "system", "content": "You are a helpful assistant that identifies fine print in documents."},
                {"role": "user", "content": f"Identify any fine print that could concern most people, stuff that most people would overlook at the end of the response please include a score out of 100 with 100 being the most concerning and 0 being the safest THE LAST FEW WORDS MUST BE THIS IN THIS FORMAT MAKE IT IN THIS FORMAT \"Score: <number> /100 \" \n\n{full_text}" }
                ]
            ) 
    
        anaylsis_text = response.choices[0].message.content 
        match = re.search(r"Score:\s*(\d+)", anaylsis_text) # looks for the score using the format i gave it before
        if match: # 
            score_val = max(0, min(100, int(match.group(1))))
            st.progress(score_val / 100, text="Fine Print Score — HIGHER = MORE CONCERNING") # score bar
        else:
            st.warning("No Score Found :(")
        st.write(anaylsis_text)
        return anaylsis_text
st.title("PDF fine print scanner")
if not os.getenv("OPENAI_API_KEY"):
    st.info("MOCK MODE: no OPENAI_API_KEY found. Sample PDFs below work offline with pre-analyzed results. Add OPENAI_API_KEY in .env for live scans.")
pdf_file = select_pdf() # calls the function to select the pdf file for the scanning to happen

pre_select_pdf() # sample pdf viewer (works offline, no key needed)
if pdf_file:
    if st.button("Scan PDF"): # button to scan the uploaded pdf file
        try:
            result = scan_fine_print(pdf_file) # runs scan fine print on uploaded pdf file
            st.download_button("Download Simplified PDF", data=result or "", file_name=pdf_file.name.replace(".pdf", "_simplified.txt"), mime="text/plain")
        except Exception as e:
            st.error(f"Scan failed: {e}. Try a sample PDF below (works offline).")




