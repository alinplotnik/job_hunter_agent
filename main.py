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
            text = soup.get_text(separator=' ', strip=True)
            return text[:7000]
        else:
            return None
    except Exception as e:
        print(f"Could not scrape {url}: {e}")
        return None


# --- 3. Main Logic ---

def process_application(resume_text, job_description):
    # --- PHASE 1: Resume Feedback ---
    print("\n--- Phase 1: Team Lead Review ---")
    prompt_resume = f"""
    Act as a Hiring Manager for a Student/Intern position.
    Job Desc: {job_description}. Resume: {resume_text}.
    Provide bullet points to improve my resume. Focus on missing keywords suitable for a Junior.
    """
    try:
        response_resume = model.generate_content(prompt_resume)
        save_to_file("resume_feedback.txt", response_resume.text)
    except Exception as e:
        print(f"Error Phase 1: {e}")

    # --- PHASE 2: Cover Letter ---
    print("\n--- Phase 2: Writing Cover Letter ---")
    prompt_cl = f"""
    Write a Cover Letter for a Student/Intern position.
    JD: {job_description}. Resume: {resume_text}.
    Extract my details. Write in a professional, authentic voice.
    """
    try:
        response_cl = model.generate_content(prompt_cl)
        save_to_file("cover_letter.txt", response_cl.text)
    except Exception as e:
        print(f"Error Phase 2: {e}")

    # --- PHASE 3: Smart Search (Junior Level) ---
    print("\n--- Phase 3: Searching for Student/Junior Interview Questions ---")

    # Step A: Identify Topics
    prompt_topics = f"""
    Analyze this Job Description: {job_description}.
    Identify the top 3 technical skills. 
    Output ONLY a comma-separated list. Example: Python, SQL, REST API
    """
    topics_text = model.generate_content(prompt_topics).text.strip()
    topics_list = [t.strip() for t in topics_text.split(',')]
    print(f"🔍 Key Topics: {topics_list}")

    questions_file_content = f"--- INTERVIEW QUESTIONS (STUDENT LEVEL) ---\nTopics: {topics_list}\n\n"
    solutions_file_content = f"--- SOLUTIONS & ANSWERS ---\nTopics: {topics_list}\n\n"

    # Step B: Loop topics
    for topic in topics_list:
        query = f"Entry level student interview questions for {topic} GeeksforGeeks Medium"
        search_results = search_web(query, max_results=1)

        for result in search_results:
            url = result['href']
            title = result['title']
            time.sleep(2)

            raw_content = fetch_website_content(url)

            if raw_content:
                print(f"🧠 Extracting {topic} Q&A...")

                # --- The Logic Update is HERE ---
                analysis_prompt = f"""
                Source text: {raw_content}
                Current Topic: {topic}

                TASK:
                Extract the 2 BEST technical interview questions for a **Student/Junior** (0 experience).

                CRITICAL SELECTION RULES:
                1. IF the topic is a Programming Language (e.g., Python, Java, C++, JavaScript):
                   - Question 1 MUST be **Conceptual/Theoretical** (e.g., "Difference between list and tuple").
                   - Question 2 MUST be a **Coding Challenge** (e.g., "Write a function to...").

                2. IF the topic is a Tool/Platform/Concept (e.g., AWS, Git, SQL, AI):
                   - Focus on core concepts, commands, or definitions.

                Output must be a valid JSON list of objects:
                [
                    {{"question": "The question text", "answer": "The answer summary"}}
                ]
                Do not add markdown formatting. Just the raw JSON string.
                """
                try:
                    json_response = model.generate_content(analysis_prompt).text
                    json_response = json_response.replace("```json", "").replace("```", "").strip()

                    qa_list = json.loads(json_response)

                    questions_file_content += f"### TOPIC: {topic}\n(Source: {title})\n"
                    solutions_file_content += f"### TOPIC: {topic}\n(Source: {title})\n"

                    for i, item in enumerate(qa_list, 1):
                        q = item.get('question', 'N/A')
                        a = item.get('answer', 'N/A')

                        questions_file_content += f"Q{i}: {q}\n\n"
                        solutions_file_content += f"Q{i}: {q}\n\nA{i}: {a}\n{'-' * 30}\n"

                    questions_file_content += f"{'=' * 30}\n\n"
                    solutions_file_content += f"{'=' * 30}\n\n"

                except json.JSONDecodeError:
                    print(f"⚠️ Could not parse JSON for {topic}. Saving raw text.")
                    solutions_file_content += f"RAW ERROR FOR {topic}: {json_response}\n\n"
                except Exception as e:
                    print(f"Error analyzing {topic}: {e}")

    save_to_file("interview_questions.txt", questions_file_content)
    save_to_file("interview_solutions.txt", solutions_file_content)


# --- 4. Execution ---

if __name__ == "__main__":
    print("--- Job Hunter Agent Started ---")

    resume_path = "resume.pdf"
    job_desc_path = "job_description.txt"

    if os.path.exists(resume_path) and os.path.exists(job_desc_path):
        my_resume_content = read_pdf(resume_path)
        job_desc_content = read_text_file(job_desc_path)

        if my_resume_content and job_desc_content:
            process_application(my_resume_content, job_desc_content)
            print("\n--- 🏁 Done! Created 'interview_questions.txt' and 'interview_solutions.txt' ---")
    else:
        print("❌ Error: Missing input files.")