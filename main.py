import os
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2

# 1. Configuration Setup
# ----------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)


# 2. Helper Functions
# -------------------
def extract_text_from_pdf(pdf_path):
    """
    Reads a PDF file and converts it to plain text.
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            # Loop through each page and extract text
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except FileNotFoundError:
        return None


def analyze_resume(resume_text):
    """
    Sends the resume text to Gemini for initial analysis.
    """
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = f"""
    You are an expert career coach. 
    Here is a resume text:
    {resume_text}

    Please list the top 3 main skills of this candidate.
    Output only the skills list.
    """

    response = model.generate_content(prompt)
    return response.text


# 3. Main Execution
# -----------------
if __name__ == "__main__":
    print("--- Job Hunter Agent Started ---")

    # Path to your resume file
    resume_path = "resume.pdf"

    print(f"Reading resume from: {resume_path}...")
    resume_content = extract_text_from_pdf(resume_path)

    if resume_content:
        print("Resume read successfully! Sending to Gemini...")
        analysis = analyze_resume(resume_content)

        print("\n--- Gemini Analysis ---")
        print(analysis)
    else:
        print("Error: 'resume.pdf' not found. Please add your PDF file to the project folder.")