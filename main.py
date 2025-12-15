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

# Use the stable Flash model
model = genai.GenerativeModel('gemini-flash-latest')

# Define input/output directories
OUTPUT_DIR = "outputs"
INPUT_DIR = "inputs"


# --- 2. Helper Functions ---

def read_pdf(file_path):
    """Extracts text from a PDF file."""
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
    """Reads a standard text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading text file ({file_path}): {e}")
        return None


def save_to_file(filename, content):
    """Saves content to a specific file inside the output directory."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created directory: {OUTPUT_DIR}")

    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Saved successfully: {filepath}")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")


def search_web(query, max_results=1):
    """Searches the web using DuckDuckGo."""
    print(f"🌐 Searching: '{query}'...")
    try:
        results = list(DDGS().text(query, max_results=max_results))
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []


def fetch_website_content(url):
    """Scrapes text content from a given URL."""
    print(f"🕷️ Scraping: {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(' ', strip=True)
            return text[:6000]  # Limit text length
        else:
            return None
    except Exception as e:
        print(f"Could not scrape {url}: {e}")
        return ""


# --- 3. Main Logic ---

def process_application(resume_text, job_description):
    """
    Orchestrates the process with Hybrid Questions, Expanded Sources, and Transparency.
    """

    print("\n--- 📉 Running BUDGET Mode (Simulated Agent) ---")

    # --- STEP 1: Analyze Profile ---
    print("\n--- Step 1: Analyzing Profile & Detecting Experience Level ---")

    prompt_batch = f"""
    Act as a Hiring Manager.
    Job Description: {job_description}
    Resume: {resume_text}

    TASK: Perform 4 actions.
    1. "feedback": Bullet points to improve resume.
    2. "cover_letter": A professional cover letter.
    3. "keywords": Extract top 3 technical skills.
    4. "experience_level": Choose one: "Entry-Level/Student", "Junior", "Mid-Level", "Senior".

    Output JSON format ONLY:
    {{
        "feedback": "string",
        "cover_letter": "string",
        "keywords": ["tech1", "tech2"],
        "experience_level": "Entry-Level/Student"
    }}
    """

    keywords = []
    experience_level = "Entry-Level/Student"

    try:
        response = model.generate_content(prompt_batch)
        cleaned_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned_json)

        save_to_file("resume_feedback.txt", data.get("feedback", ""))
        save_to_file("cover_letter.txt", data.get("cover_letter", ""))
        keywords = data.get("keywords", [])
        experience_level = data.get("experience_level", "Entry-Level/Student")

        print(f"🎓 Detected Experience Level: {experience_level}")
        print(f"🔍 Extracted Keywords: {keywords}")

    except Exception as e:
        print(f"❌ Critical Error in Step 1: {e}")
        return

    # --- STEP 2: Skip Search (Direct Knowledge) ---

    # --- STEP 3: Generate Hybrid Questions (Transparency & Quality Mode) ---
    print("\n--- Step 3: Generating Hybrid Interview Prep (Expanded Sources) ---")

    prompt_extraction = f"""
    You are a Technical Interview Coach.
    Target Audience: {experience_level}
    Topics: {keywords}

    TASK:
    Create a JSON list of interview materials.
    For each topic in {keywords}, generate exactly 2 items based on the topic type:

    --- LOGIC BRANCHING ---

    **CASE A: If the topic is a PROGRAMMING LANGUAGE** (Python, Java, SQL, etc.):
       1. **Item 1 (Theory):** A standard interview question found on **GeeksforGeeks, Javatpoint, or W3Schools**.
          - Focus on definitions, differences (e.g., "Interface vs Abstract Class"), and core concepts.
       2. **Item 2 (Practice):** - **PRIORITY:** Retrieve a **REAL LeetCode Problem** (Name, Description, Constraints).
          - **FALLBACK:** If no specific LeetCode problem exists, create a custom challenge but **SET 'is_real': false**.

    **CASE B: If the topic is a TOOL or CONCEPT** (Git, Agile, Docker, Linux, Networking):
       1. **Item 1 (Theory):** A classic conceptual question derived from **GeeksforGeeks or Javatpoint** (e.g., "Git Architecture", "Docker Layers").
       2. **Item 2 (Scenario):** - **PRIORITY:** Retrieve a famous/common scenario discussed on **StackOverflow** (e.g., "Detached HEAD", "Port already in use error").
          - **FALLBACK:** If you cannot find a specific famous scenario, create a realistic production incident but **SET 'is_real': false**.

    --- CRITICAL QUALITY RULES ---

    1. **DIFFICULTY CALIBRATION**:
       - Strictly match {experience_level}.
       - Student/Entry: Basic usage, definitions, simple flows.
       - Senior: Internals, complex conflicts, production incidents.

    2. **ANSWER QUALITY**:
       - **Coding/LeetCode**: Must include the `Starter Code`, `Explanation`, and the `Full Solution Code`.
       - **Theory/Scenario**: Clear, step-by-step professional answer.

    3. **TRANSPARENCY (The "Flagging" Rule)**:
       - If the question/scenario is based on a real external source (LeetCode/StackOverflow/GFG), set "is_real": true.
       - If you invented it, set "is_real": false.

    Output Format (JSON ONLY):
    [
        {{ 
            "topic": "Python", 
            "type": "LeetCode", 
            "is_real": true,
            "problem_name": "Two Sum", 
            "content": "Given an array...",
            "code_snippet": "def twoSum...",
            "solution": "Use a hash map..."
        }},
        {{
            "topic": "Git",
            "type": "Scenario",
            "is_real": true, 
            "problem_name": "Fixing Detached HEAD",
            "content": "You are in 'detached HEAD' state...",
            "code_snippet": "git checkout...",
            "solution": "1. Run git status..."
        }}
    ]
    """

    try:
        response_q = model.generate_content(prompt_extraction)
        cleaned_json_q = response_q.text.replace("```json", "").replace("```", "").strip()
        qa_list = json.loads(cleaned_json_q)

        q_file = f"--- INTERVIEW PREPARATION ({experience_level.upper()}) ---\n\n"
        sol_file = f"--- SOLUTIONS & EXPLANATIONS ---\n\n"

        for idx, item in enumerate(qa_list, 1):
            topic = item.get('topic', 'General')
            q_type = item.get('type', 'General')
            is_real = item.get('is_real', False)
            prob_name = item.get('problem_name', 'Question')
            content = item.get('content', '')
            code = item.get('code_snippet', '')
            solution = item.get('solution', '')

            # Dynamic Header
            if "LeetCode" in q_type:
                source_label = "[REAL LEETCODE]" if is_real else "[AI GENERATED CHALLENGE]"
                header = f"🧩 [{topic}] {source_label}: {prob_name}"
            elif "Scenario" in q_type:
                source_label = "[REAL SCENARIO - StackOverflow/GFG]" if is_real else "[AI GENERATED SCENARIO]"
                header = f"⚙️ [{topic}] {source_label}: {prob_name}"
            else:
                header = f"📚 [{topic}] [THEORY - GFG/Javatpoint]" if is_real else "[AI GENERATED SCENARIO]"

            # Write Question
            entry = f"{header}\n{'-' * 50}\n"
            entry += f"Description/Question:\n{content}\n"
            if code and code != "N/A":
                entry += f"\n💻 Starter Code:\n{code}\n"

            q_file += entry + f"\n\n"

            # Write Solution
            sol_file += f"Question {idx}: {header}\n"
            sol_file += f"Answer/Solution:\n{solution}\n"
            sol_file += f"{'=' * 50}\n\n"

        save_to_file("interview_questions.txt", q_file)
        save_to_file("interview_solutions.txt", sol_file)

    except Exception as e:
        print(f"❌ Error in Step 3: {e}")

# --- 4. Execution Entry Point ---

if __name__ == "__main__":
    print("--- Job Hunter Agent (Budget Edition) Started ---")

    resume_path = os.path.join(INPUT_DIR, "resume.pdf")
    job_desc_path = os.path.join(INPUT_DIR, "job_description.txt")

    if os.path.exists(resume_path) and os.path.exists(job_desc_path):
        my_resume_content = read_pdf(resume_path)
        job_desc_content = read_text_file(job_desc_path)

        if my_resume_content and job_desc_content:
            process_application(my_resume_content, job_desc_content)
            print("\n--- 🏁 Done! Created files in 'outputs' directory ---")
    else:
        print(f"❌ Error: Missing input files in '{INPUT_DIR}' directory.")