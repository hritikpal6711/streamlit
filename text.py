import streamlit as st
import fitz  # PyMuPDF
import re
import pandas as pd
import tempfile
import os

def extract_all_sections(pdf_path):
    sections = {}

    current_section = None
    current_text = ""

    with fitz.open(pdf_path) as pdf_doc:
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc[page_num]
            page_text = page.get_text()

            for line in page_text.split('\n'):
                # Check if a line contains a section heading
                for section_name in section_names:
                    if section_name.lower() in line.lower():
                        # Save the current section
                        if current_section:
                            sections[current_section] = sections.get(current_section, "") + current_text.strip()

                        # Start a new section with bold text
                        current_section = section_name
                        current_text = f"{line}\n"
                        break
                else:
                    # Add the line to the current section with regular formatting
                    current_text += line + '\n'

    # Save the last section
    if current_section:
        sections[current_section] = sections.get(current_section, "") + current_text.strip()

    return sections

def count_sentences(text):
    sentences = re.split(r'[.!?]', text)
    return len(sentences)

# Streamlit app
st.title("Resume Section Extractor")

# User input for uploading multiple PDF resumes
resumes = st.file_uploader("Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if resumes:
    st.write("Analyzing...")

    # Define section names based on patterns
    section_names = ["Professional Experience", "Summary", "Projects", "Skills", "Education", "Profile", "Career Objective", "Certificates"]
    desired=["Professional Experience", "Summary", "Projects","Profile", "Career Objective"]
    # Display the content of each section with the number of sentences in a tabular format
    data = []

    for resume in resumes:
        # Save the uploaded PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(resume.read())
            temp_pdf_path = temp_pdf.name

        # Extract all sections from the resume
        all_sections = extract_all_sections(temp_pdf_path)

        # Calculate the total sentence count for each resume
        #total_sentence_count = sum(count_sentences(all_sections[section_name]) for section_name in desired if section_name in all_sections)

        for section_name in section_names:
            if section_name in all_sections:
                if section_name in desired:
                    total_sentence_count = (count_sentences(all_sections[section_name]))
                    data.append({"Resume": resume.name,"section":section_name ,"all section":all_sections[section_name],"Prime Sections Sentences Count": total_sentence_count})

        # Remove the temporary PDF file
        os.remove(temp_pdf_path)

    if data:
        df = pd.DataFrame(data)
        st.subheader("Total Sentence Counts for Each Resume:")
        st.table(df)
    else:
        st.warning("No content found for the specified sections.")
