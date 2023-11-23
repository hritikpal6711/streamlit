import streamlit as st
import os
import fitz  # PyMuPDF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tempfile
import pandas as pd
import nltk
from nltk.corpus import stopwords
import re  # Import the 're' module for regular expressions
from docx import Document  # Import Document from python-docx

# Download stopwords
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Provided functions
def extract_phone_number(resume_text):
    phone_number = None
    pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    match = re.search(pattern, resume_text)
    if match:
        phone_number = match.group()
    return phone_number

def extract_email_from_resume(resume_text):
    email = None
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, resume_text)
    if match:
        email = match.group()
    return email

def count_sentences(text):
    sentences = re.split(r'[,.!?+]', text)
    return len(sentences)

def extract_info_from_pdf(pdf_path):
    text = ""
    word_count = 0
    page_count = 0
    #sentence_count = 0
    phone_number = None
    email = None
    with fitz.open(pdf_path) as doc:
        page_count = doc.page_count
        for page in doc:
            text += page.get_text()
            word_count += len(page.get_text("text").split())
            #sentence_count += count_sentences(page.get_text())
        # Extract phone number and email from the concatenated text
        phone_number = extract_phone_number(text)
        email = extract_email_from_resume(text)
    return text.lower(), word_count, page_count,  phone_number, email

def extract_info_from_docx(docx_path):
    text = ""
    word_count = 0
    #sentence_count = 0
    phone_number = None
    email = None
    doc = Document(docx_path)
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
        word_count += len(paragraph.text.split())
        #sentence_count += count_sentences(paragraph.text)
    # Extract phone number and email from the concatenated text
    phone_number = extract_phone_number(text)
    email = extract_email_from_resume(text)
    page_count=1
    docx_text=text.lower()
    return docx_text, word_count,page_count,  phone_number, email

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

st.title("RESUME RANKER")

# User input for skills
skills = st.text_input("Enter Skills (comma-separated):")

# User input for job description
job_description = st.text_area("Enter Job Description:")

# User input for uploading multiple resumes
resumes = st.file_uploader("Upload Resumes/CVs", type=["pdf", "docx"], accept_multiple_files=True)

if st.button("Rank Resumes"):
    if not resumes:
        st.warning("Please upload resumes.")
    else:
        skills = [skill.strip() for skill in skills.split(',')]
        job_description = job_description.lower()
        resume_data = []
        section_names = ["Professional Experience", "Summary", "Projects", "Skills", "Education", "Profile", "Career Objective", "Certificates"]
        desired=["Professional Experience", "Summary", "Projects","Profile", "Career Objective"]
        # Display the content of each section with the number of sentences in a tabular format
        data = []

        for resume in resumes:
            try:
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(resume.read())
                    temp_file_name = temp_file.name

                if resume.type == "application/pdf":
                    pdf_text, word_count, page_count,  phone_number, email = extract_info_from_pdf(temp_file_name)
                elif resume.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    docx_text, word_count, page_count, phone_number, email = extract_info_from_docx(temp_file_name)


                all_sections = extract_all_sections(temp_file_name)

                # Calculate the total sentence count for each resume
                total_sentence_count = sum(count_sentences(all_sections[section_name]) for section_name in desired if section_name in all_sections)

                data.append({"File Name": resume.name, "Prime Sections Sentences Count": total_sentence_count})


                os.remove(temp_file_name)

                
            

            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                continue

            resume_data.append((resume.name, pdf_text if resume.type == "application/pdf" else docx_text, word_count, page_count,  phone_number, email))

        if not resume_data:
            st.warning("No resumes found in the uploaded files.")
        else:
            resume_rankings = []

            for resume_name, resume_text, word_count, page_count,  phone_number, email in resume_data:
                matching_skills = [skill for skill in skills if skill.lower() in resume_text]
                similarity_score = len(matching_skills) / len(skills)
                missing_skills = [skill for skill in skills if skill.lower() not in resume_text]

                if job_description.strip():
                    job_description_filtered = ' '.join([word for word in job_description.split() if word.lower() not in stop_words])
                    resume_text_filtered = ' '.join([word for word in resume_text.split() if word.lower() not in stop_words])

                    tfidf_vectorizer = TfidfVectorizer()
                    job_description_matrix = tfidf_vectorizer.fit_transform([job_description_filtered])
                    resume_matrix = tfidf_vectorizer.transform([resume_text_filtered])
                    job_description_similarity = cosine_similarity(job_description_matrix, resume_matrix)
                    job_description_similarity = job_description_similarity[0][0]
                else:
                    job_description_similarity = 0

                similarity_score = round(similarity_score * 100, 2)
                job_description_similarity = round(job_description_similarity * 100, 2)

                resume_rankings.append((resume_name, f"{similarity_score}%", f"{job_description_similarity}%", missing_skills, word_count,page_count,  phone_number, email))

            resume_rankings.sort(key=lambda x: x[1], reverse=True)

            df = pd.DataFrame(resume_rankings, columns=["File Name", "Skills Match", "Job Description Match", "Missing Skills", "Word Count", "Page Count", "Phone Number", "Email"])

            if data:
               df1 = pd.DataFrame(data)
            
            merged_df = pd.merge(df, df1, on="File Name", how='inner')
            st.subheader("Ranked Resumes:")
            st.dataframe(merged_df)