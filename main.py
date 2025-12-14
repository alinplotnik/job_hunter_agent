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
model = genai.GenerativeModel('gemini-flash-latest')


# --- 2. Helper Functions ---

def read_pdf(file_path):
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
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading text file ({file_path}): {e}")
        return None


def save_to_file(filename, content):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Saved successfully: {filename}")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")


# --- 3. Main Logic (The Agent) ---

def process_application(resume_text, job_description):
    # --- PHASE 1: Resume Critique (Not Rewrite) ---
    print("\n--- Phase 1: Team Lead Review (Critique) ---")

    prompt_resume = f"""
    Act as the Team Lead of the hiring team for this specific job description.
    You are reviewing my resume to decide if I should be interviewed.

    Job Description:
    {job_description}

    My Resume:
    {resume_text}

    TASK:
    Do NOT rewrite the resume.
    Instead, provide a specific feedback list (bullet points) on what I should change to pass your screening.
    Focus on:
    1. Missing keywords I should add.
    2. Irrelevant sections I should remove or shorten.
    3. Skills in the JD that are not emphasized enough in my resume.

    Output format: A clear list of actionable "Recommended Changes".
    """

    try:
        response_resume = model.generate_content(prompt_resume)
        save_to_file("resume_feedback.txt", response_resume.text)
    except Exception as e:
        print(f"Error generating feedback: {e}")

    # --- PHASE 2: Personalized Cover Letter ---
    print("\n--- Phase 2: Writing Personalized Cover Letter ---")

    prompt_cl = f"""
    Write a specific Cover Letter for this application.

    Source Material:
    - Job Description: {job_description}
    - My Resume: {resume_text}

    INSTRUCTIONS:
    1. EXTRACT my real name, phone, email, and LinkedIn from the resume text and place them at the top. DO NOT use placeholders like [Your Name].
    2. Analyze the writing style and tone of my resume, and write the cover letter in that same voice (professional, authentic).
    3. Adopt the company's culture tone found in the JD.
    4. Connect my specific past projects (from resume) to their requirements.

    Structure:
    - Header (My details)
    - Salutation (To "Hiring Team at [Company Name]")
    - Body Paragraphs
    - Sign-off
    """

    try:
        response_cl = model.generate_content(prompt_cl)
        save_to_file("cover_letter.txt", response_cl.text)
    except Exception as e:
        print(f"Error generating cover letter: {e}")

        # --- PHASE 3: Student/Junior Interview Questions ---
        print("\n--- Phase 3: Generating Student-Level Interview Questions ---")

        prompt_questions = f"""
        Act as a Technical Interviewer for a **Student/Junior Developer position (Internship)**.

        Based on the job description:
        {job_description}

        TASK:
        Generate 3 coding interview questions suitable for a candidate with **0 years of commercial experience**.

        Guidelines for the questions:
        1. **Question 1 (Algorithmic):** A standard LeetCode Easy/Medium problem focusing on Arrays, Strings, or Hash Maps (Python Lists/Dicts).
        2. **Question 2 (Practical Logic):** A small logic puzzle or data manipulation task (e.g., parsing a simple string or filtering a list).
        3. **Question 3 (Basic OOP):** A very simple Object-Oriented Design task. Example: "Design a 'ShoppingCart' class with methods to add/remove items and calculate total." (Do NOT ask for complex System Design or Cloud Architecture).

        For each question provide:
        1. Problem Name.
        2. Description.
        3. Example Input and Output.

        Do NOT provide the solution code.
        """

        try:
            response_q = model.generate_content(prompt_questions)
            save_to_file("interview_prep.txt", response_q.text)
        except Exception as e:
            print(f"Error generating questions: {e}")

# --- 4. Execution ---

if __name__ == "__main__":
    print("--- Job Hunter Agent Started ---")

    resume_path = "resume.pdf"
    job_desc_path = "job_description.txt"

    if os.path.exists(resume_path) and os.path.exists(job_desc_path):
        print("Files loaded. Sending to Gemini...")
        my_resume_content = read_pdf(resume_path)
        job_desc_content = read_text_file(job_desc_path)

        if my_resume_content and job_desc_content:
            process_application(my_resume_content, job_desc_content)
            print("\n--- 🏁 Done! Check 'resume_feedback.txt', 'cover_letter.txt', and 'interview_prep.txt' ---")
    else:
        print("❌ Error: Missing resume.pdf or job_description.txt")