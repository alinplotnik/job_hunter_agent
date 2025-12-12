import os
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2

# --- 1. Configuration & Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API Key not found! Check your .env file.")

genai.configure(api_key=api_key)

# Using 'gemini-flash-latest' as it proved to be stable and generous with quotas
model = genai.GenerativeModel('gemini-flash-latest')


# --- 2. Helper Functions ---

def read_pdf(file_path):
    """
    Extracts text from a PDF file.
    """
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
    except Exception as e:
        print(f"Error reading PDF ({file_path}): {e}")
        return None


def read_text_file(file_path):
    """
    Reads the content of a standard text file (used for job description).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading text file ({file_path}): {e}")
        return None


def save_to_file(filename, content):
    """
    Saves the AI-generated content to a local file.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Saved successfully: {filename}")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")


# --- 3. Main Logic (The Agent) ---

def process_application(resume_text, job_description):
    print("\n--- Phase 1: Tailoring Resume ---")

    # Prompt for Resume Adaptation
    prompt_resume = f"""
    Act as an expert technical career coach.

    Current Resume:
    {resume_text}

    Target Job Description:
    {job_description}

    TASK:
    1. Rewrite the resume content to better match the keywords and skills required in the job description.
    2. Maintain a professional tone.
    3. At the very end, provide a section titled "Changes Made" explaining why you made specific edits.

    Output the full tailored resume followed by the changes section.
    """

    try:
        response_resume = model.generate_content(prompt_resume)
        save_to_file("tailored_resume.txt", response_resume.text)
    except Exception as e:
        print(f"Error generating resume: {e}")

    print("\n--- Phase 2: Writing Cover Letter ---")

    # Prompt for Cover Letter
    prompt_cl = f"""
    Write a professional Cover Letter for this job application.

    My Resume: {resume_text}
    Job Description: {job_description}

    Guidelines:
    - Match the tone of the company (based on the job description).
    - Highlight my key achievements that are relevant to this specific role.
    - Keep it concise and engaging.
    """

    try:
        response_cl = model.generate_content(prompt_cl)
        save_to_file("cover_letter.txt", response_cl.text)
    except Exception as e:
        print(f"Error generating cover letter: {e}")

    print("\n--- Phase 3: Generating Interview Questions ---")

    # Prompt for Interview Prep
    prompt_questions = f"""
    Based strictly on this job description:
    {job_description}

    Generate 3 LeetCode-style coding interview questions (or technical system design questions) relevant to this role.
    For each question provide:
    1. Problem Description
    2. Example Input/Output

    DO NOT provide the solution code yet.
    """

    try:
        response_q = model.generate_content(prompt_questions)
        save_to_file("interview_prep.txt", response_q.text)
    except Exception as e:
        print(f"Error generating questions: {e}")


# --- 4. Execution Entry Point ---

if __name__ == "__main__":
    print("--- Job Hunter Agent Started ---")

    # Define file paths
    resume_path = "resume.pdf"
    job_desc_path = "job_description.txt"

    # Check if files exist before running
    if not os.path.exists(resume_path):
        print(f"❌ Error: '{resume_path}' not found. Please add your PDF resume.")
    elif not os.path.exists(job_desc_path):
        print(f"❌ Error: '{job_desc_path}' not found. Please create this file with the job description.")
    else:
        # Load data
        print(f"Reading {resume_path}...")
        my_resume_content = read_pdf(resume_path)

        print(f"Reading {job_desc_path}...")
        job_desc_content = read_text_file(job_desc_path)

        if my_resume_content and job_desc_content:
            print("Files loaded. Sending to Gemini...")
            process_application(my_resume_content, job_desc_content)
            print("\n--- 🏁 All tasks completed! Check your folder for the new files. ---")