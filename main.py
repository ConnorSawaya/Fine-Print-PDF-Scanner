"""Streamlit interface for the fine-print PDF scanner."""

import json
import os
import re

from dotenv import load_dotenv
import streamlit as st

from scanner import (
    MAX_PDF_PAGES,
    PdfLimitError,
    analyze_text,
    extract_pdf_text,
    get_client,
    reserve_scan,
)


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_JSON = os.path.join(BASE_DIR, "sample_files.json")


def select_pdf():
    return st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help=f"Maximum 10 MB and {MAX_PDF_PAGES} pages. Password-protected files are not supported.",
    )


def pre_select_pdf():
    options = ["Discord TOS", "APPLE PURCHASE AGREEMENT", "None"]
    choice = st.selectbox("Or select a sample PDF", options)
    sample_keys = {
        "Discord TOS": ("Scan Discord TOS", "Discord_TOS"),
        "APPLE PURCHASE AGREEMENT": (
            "Scan APPLE PURCHASE AGREEMENT",
            "Apple_Purchase_Agreement",
        ),
    }
    if choice in sample_keys:
        button_label, data_key = sample_keys[choice]
        if st.button(button_label):
            try:
                with open(SAMPLE_JSON, "r", encoding="utf-8") as sample_file:
                    st.write(json.load(sample_file)[data_key])
            except (OSError, ValueError, KeyError):
                st.error("The sample analysis is temporarily unavailable.")


def scan_fine_print(uploaded_file, consent_to_share=False):
    if uploaded_file is None:
        st.warning("Upload a PDF first, or try a sample PDF below (works offline).")
        return ""

    client = get_client()
    if client is None:
        st.warning("Live scans are not configured. Sample PDFs work without an API key.")
        return ""
    if not consent_to_share:
        st.warning("Confirm that you want to send this document's extracted text to OpenAI.")
        return ""

    try:
        full_text = extract_pdf_text(uploaded_file)
    except (PdfLimitError, ValueError) as exc:
        st.warning(str(exc))
        return ""

    if not reserve_scan(st.session_state):
        st.warning(
            "The scan limit has been reached. Try again later. "
            "The public demo allows up to 3 scans per session and 12 per server per hour."
        )
        return ""

    try:
        with st.spinner("Analyzing for fine print..."):
            analysis = analyze_text(client, full_text)
    except Exception:
        st.error("The analysis service is unavailable. Please try again later.")
        return ""

    match = re.search(r"Score:\s*(\d+)", analysis, re.IGNORECASE)
    if match:
        score_value = max(0, min(100, int(match.group(1))))
        st.progress(score_value / 100, text="Fine Print Score — HIGHER = MORE CONCERNING")
    else:
        st.warning("No score was returned. Review the analysis text below.")
    st.write(analysis)
    return analysis


st.title("PDF fine print scanner")
if not os.getenv("OPENAI_API_KEY"):
    st.info(
        "Sample mode is active. Pre-analyzed samples work offline; live scans are "
        "disabled until the operator configures an API key."
    )
else:
    st.caption(
        "Live analysis sends extracted PDF text to OpenAI. Files are not saved by this app."
    )

pdf_file = select_pdf()
pre_select_pdf()

if pdf_file:
    consent_to_share = False
    if os.getenv("OPENAI_API_KEY"):
        consent_to_share = st.checkbox(
            "I agree to send this PDF's extracted text to OpenAI for analysis."
        )
    if st.button("Scan PDF"):
        result = scan_fine_print(pdf_file, consent_to_share=consent_to_share)
        if result:
            base_name = os.path.basename(pdf_file.name)
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name)
            if safe_name.lower().endswith(".pdf"):
                safe_name = safe_name[:-4]
            st.download_button(
                "Download analysis",
                data=result,
                file_name=f"{safe_name or 'analysis'}_analysis.txt",
                mime="text/plain",
            )
