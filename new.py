import streamlit as st
import fitz  # PyMuPDF
import re
import pandas as pd

def extract_all_sections(pdf_doc):
    sections = {}

    current_section = None
    current_text = ""

    for page_num in range(pdf_doc.page_count):
        page = pdf_doc[page_num]
        page_text = page.get_text()

        for line in page_text.split('\n'):
            # Check if a line contains a section heading
            for section_name in section_names:
                if section_name.lower() in line.lower():
                    # Save the current section
                    if current_section:
                        sections[current_section] = current_text.strip()

                    # Start a new section with bold text
                    current_section = section_name
                    current_text = f"{line}\n"
                    break
            else:
                # Add the line to the current section with regular formatting
                current_text += line + '\n'

    # Save the last section
    if current_section:
        sections[current_section] = current_text.strip()

    return sections

def count_sentences(text):
    sentences = re.split(r'[,.!?+]', text)
    return len(sentences)

# Streamlit app
st.title("Resume Section Extractor")

# User input for uploading a PDF resume
pdf_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

if pdf_resume:
    st.write("Analyzing...")

    # Define section names based on patterns
    section_names = ["Professional Experience", "Summary", "Projects", "Skills", "Education", "Profile", "Career Objective", "Certificates"]

    # Open PDF document using PyMuPDF
    pdf_doc = fitz.open(pdf_resume)

    # Extract all sections from the resume
    all_sections = extract_all_sections(pdf_doc)

    # Display the content of each section with the number of sentences in a tabular format
    data = []
    for section_name in section_names:
        if section_name in all_sections:
            sentences_count = count_sentences(all_sections[section_name])
            data.append({"Section": section_name, "Content": all_sections[section_name], "Sentences Count": sentences_count})

    if data:
        df = pd.DataFrame(data)
        st.subheader("Content and Number of Sentences in Each Section:")
        st.table(df)
    else:
        st.warning("No content found for the specified sections.")

    # Close the PDF document
    pdf_doc.close()
