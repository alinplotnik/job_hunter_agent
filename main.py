import os
import time
import json
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup

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


def search_web(query, max_results=1):
    print(f"🌐 Searching: '{query}'...")
    try:
        results = list(DDGS().text(query, max_results=max_results))
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []


def fetch_website_content(url):
    print(f"🕷️ Scraping: {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(' ', strip=True)
            return text[:6000]  # Limit text to save context
        else:
            return None
    except Exception as e:
        print(f"Could not scrape {url}: {e}")
        return ""


# --- 3. Main Logic (Budget Version) ---

def process_application(resume_text, job_description):
    print("\n--- 📉 Running BUDGET Mode (2 API Calls Total) ---")

    # --- API CALL #1: Everything in one go (Resume + Cover Letter + Keywords) ---
    print("\n--- Step 1: Analyzing Profile & Generating Docs ---")

    prompt_batch = f"""
    Act as a Hiring Manager for a Student/Intern position.

    Job Description: {job_description}
    Resume: {resume_text}

    TASK: Perform 3 actions and output a single JSON object.
    1. "feedback": Bullet points to improve resume for this job.
    2. "cover_letter": A professional cover letter (Student level).
    3. "keywords": Extract top 3 technical skills (e.g. ["Python", "SQL", "AWS"]).

    Output JSON format ONLY:
    {{
        "feedback": "string",
        "cover_letter": "string",
        "keywords": ["tech1", "tech2", "tech3"]
    }}
    """

    keywords = []

    try:
        response = model.generate_content(prompt_batch)
        cleaned_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned_json)

        # Save Outputs
        save_to_file("resume_feedback.txt", data.get("feedback", "Error generating feedback"))
        save_to_file("cover_letter.txt", data.get("cover_letter", "Error generating cover letter"))
        keywords = data.get("keywords", [])

        print(f"🔍 Extracted Keywords for Search: {keywords}")

    except Exception as e:
        print(f"❌ Critical Error in Step 1: {e}")
        return  # Stop if step 1 fails

    # --- Step 2: Python-only Search (Free) ---
    print("\n--- Step 2: Gathering Interview Materials (No API Cost) ---")

    combined_scraped_text = ""

    for tech in keywords:
        # Strict search on good sites
        query = f"Top entry level {tech} interview questions freshers site:javatpoint.com OR site:geeksforgeeks.org OR site:interviewbit.com"
        results = search_web(query, max_results=1)

        for res in results:
            url = res['href']
            title = res['title']
            time.sleep(2)  # Be polite

            content = fetch_website_content(url)
            if content:
                combined_scraped_text += f"\n\n=== SOURCE: {title} (Topic: {tech}) ===\n{content}"

    # --- API CALL #2: Extract Questions from ALL text at once ---
    print("\n--- Step 3: Extracting Questions (Final API Call) ---")

    if not combined_scraped_text:
        print("❌ No content scraped. Check internet connection.")
        return

    prompt_extraction = f"""
    I have collected text from several interview websites.

    RAW TEXT:
    {combined_scraped_text[:25000]} 

    TASK:
    Go through the sources and extract the BEST interview questions for a **Student/Junior**.

    OUTPUT JSON List:
    [
        {{ "topic": "Python", "question": "...", "answer": "..." }},
        {{ "topic": "SQL", "question": "...", "answer": "..." }}
    ]

    RULES:
    1. Extract exactly 2 questions per topic found in the text.
    2. One Conceptual, One Coding (if applicable).
    3. Ignore senior-level questions.
    """

    try:
        response_q = model.generate_content(prompt_extraction)
        cleaned_json_q = response_q.text.replace("```json", "").replace("```", "").strip()
        qa_list = json.loads(cleaned_json_q)

        # Format the output files
        q_file = "--- INTERVIEW QUESTIONS ---\n\n"
        sol_file = "--- SOLUTIONS ---\n\n"

        for idx, item in enumerate(qa_list, 1):
            topic = item.get('topic', 'General')
            q = item.get('question')
            a = item.get('answer')

            q_file += f"[{topic}] Q{idx}: {q}\n\n"
            sol_file += f"[{topic}] Q{idx}: {q}\nAnswer: {a}\n{'-' * 30}\n"

        save_to_file("interview_questions.txt", q_file)
        save_to_file("interview_solutions.txt", sol_file)

    except Exception as e:
        print(f"❌ Error in Step 3: {e}")
        # Fallback: Save raw text if parsing fails
        save_to_file("debug_raw_scraped_content.txt", combined_scraped_text)


# --- 4. Execution ---

if __name__ == "__main__":
    print("--- Job Hunter Agent (Budget Edition) Started ---")

    resume_path = "resume.pdf"
    job_desc_path = "job_description.txt"

    if os.path.exists(resume_path) and os.path.exists(job_desc_path):
        my_resume_content = read_pdf(resume_path)
        job_desc_content = read_text_file(job_desc_path)

        if my_resume_content and job_desc_content:
            process_application(my_resume_content, job_desc_content)
            print("\n--- 🏁 Done! (Only used 2 API credits) ---")
    else:
        print("❌ Error: Missing input files.")