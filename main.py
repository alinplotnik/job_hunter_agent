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
    Orchestrates the process with professionally translated prompts and dynamic date.
    Fixed indentation and variable scoping.
    """
    from datetime import datetime  # For dynamic date injection

    print("\n--- 📉 Running BUDGET Mode (Simulated Agent) ---")

    # =========================================================================
    # STEP 0: Advanced ATS Technical Check
    # =========================================================================
    print("\n--- Step 0: Performing Deep ATS Technical Analysis ---")

    # We ask Gemini to simulate a strict parser
    prompt_ats = f"""
    Act as a strict ATS (Applicant Tracking System) Parser algorithm.

    Here is the RAW TEXT extracted from a candidate's PDF resume:
    ---------------------
    {resume_text[:3000]} ... (truncated)
    ---------------------
    TASK: Perform a deep technical audit on readability.
    Check for these specific fatal errors:
    1. **Parsing Logic / Layout:** - Are sentences broken or mixed due to multi-column layout?
       - Can you clearly verify the Email and Phone number? (If they were in the Header/Footer of the PDF, they might be missing here).

    2. **Section Headers:** - Does the resume use standard headers (e.g., "Experience", "Education", "Skills")?
       - If it uses creative names like "My Journey" or "Tech Life", flag it as an error.
    3. **Name Formatting:** - Is the name written normally (e.g., "Alin Plotnikov") or spaced out ("A l i n")?
    4. **Graphics/Bars:** - Does the text imply the use of "skill bars" or "graphs" (e.g., disconnected numbers like "80%", "4/5")? ATS cannot read these.

    Output a JSON report:
    {{
        "is_readable": true/false,
        "score_1_to_10": 8,
        "extracted_name": "Name Found in Text",
        "recommended_filename": "FirstName_LastName_Position.pdf",
        "critical_issues": ["Issue 1", "Issue 2"],
        "deduction_reasoning": "Score reduced by 2 points because contact info is missing (likely in header) and Section Headers are non-standard."
    }}
    """

    try:
        response_ats = model.generate_content(prompt_ats)
        raw_text = response_ats.text
        cleaned_json_ats = raw_text.replace("```json", "").replace("```", "").strip()

        try:
            ats_data = json.loads(cleaned_json_ats)
        except json.JSONDecodeError:
            print(f"⚠️ Warning: Model returned non-JSON. Raw: '{raw_text[:100]}...'")
            ats_data = {
                "score_1_to_10": 0,
                "recommended_filename": "Error_Check_Logs.pdf",
                "extracted_name": "Unknown",
                "critical_issues": ["API Error: Could not parse response (Safety Filter or Empty)"],
                "deduction_reasoning": "The AI model returned an invalid response. This often happens if the resume contains sensitive info that triggers safety filters."
            }
        score = ats_data.get('score_1_to_10', 0)

        print(f"\n🤖 ATS Readability Score: {score}/10")

        readable_report = f"--- 🤖 ATS READABILITY REPORT ---\n"
        readable_report += f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        readable_report += f"==========================================\n\n"

        readable_report += f"📊 SCORE: {score}/10\n"
        readable_report += f"📂 RECOMMENDED FILENAME: {ats_data.get('recommended_filename', 'N/A')}\n"
        readable_report += f"👤 NAME DETECTED: {ats_data.get('extracted_name', 'Not Found')}\n\n"

        readable_report += f"--- ⚠️ CRITICAL ISSUES FOUND ---\n"
        if ats_data.get('critical_issues'):
            for issue in ats_data.get('critical_issues', []):
                readable_report += f"[X] {issue}\n"
        else:
            readable_report += "✅ No critical issues found. Great job!\n"

        readable_report += f"\n--- 📉 DETAILED REASONING ---\n"
        readable_report += f"{ats_data.get('deduction_reasoning', 'N/A')}\n"

        readable_report += f"\n==========================================\n"
        readable_report += f"NOTE: If the score is below 8, please fix the layout issues in Canva/Word."

        save_to_file("ats_readability_report.txt", readable_report)

    except Exception as e:
        print(f"⚠️ Could not perform ATS check: {e}")

    # =========================================================================
    # STEP 1: Analyze Profile & Detect Experience Level
    # =========================================================================
    print("\n--- Step 1: Analyzing Profile & Detecting Experience Level ---")

    # Get current date for the cover letter
    current_date = datetime.now().strftime("%B %d, %Y")

    prompt_batch = f"""
    Act as a Hiring Manager and Technical Recruiter.
    Job Description: {job_description}
    Resume: {resume_text}

    TASK: Perform 4 actions and output a JSON.

    1. "feedback": Provide bullet points to improve the resume SPECIFICALLY for this job.
       - **PERSPECTIVE:** Analyze as both an **HR Recruiter** (scanning for clarity/keywords) and a **Tech Team Lead** (looking for technical depth).
       - **RULE:** Do NOT encourage inventing skills or experiences the candidate does not have. Focus exclusively on how to better frame and highlight the *existing* truth.

    2. "cover_letter": Write a professional, concise, and sincere cover letter.
       - **FORMATTING RULES (Strict):**
             1. **TOP HEADER:** Place Candidate Name, Email, and Phone at the very top. Use contact details from the resume only (if missing, leave blank, do not invent).
             2. **DATE:** Place the date "{current_date}" BELOW the contact info.
             3. **RECIPIENT:** Place "Hiring Team" or Company Name below the date.
       - **TONE:** Authentic, direct, and conversational. Avoid overly formal words, "fluff", or "AI-sounding" language. Keep it brief.
       - **CONTENT:** Do NOT summarize the resume (the recruiter already has it). Focus on **"Why THIS company and THIS team?"**.
       - **THE HOOK:** Identify a specific project, hobby, or technical interest from the resume (e.g., an AI/Computer Vision project) and factually connect it to the company's product/domain. Show genuine passion through facts, not flattery.

    3. "keywords": Extract the top 3 most critical technical skills **FROM THE JOB DESCRIPTION**.
       - Select the 3 topics that are **most likely to appear in a technical interview** for this specific role.

    4. "experience_level": Determine the target experience level based **STRICTLY ON THE JOB DESCRIPTION REQUIREMENTS**.
       - Do NOT infer from the resume (candidate might have irrelevant history).
       - Choose one: "Entry-Level/Student", "Junior", "Mid-Level", "Senior".

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

        # --- FIX: Handle List vs String for Feedback ---
        feedback_data = data.get("feedback", "")
        if isinstance(feedback_data, list):
            feedback_data = "\n- ".join(feedback_data)  # Convert list to string

        save_to_file("resume_feedback.txt", feedback_data)
        save_to_file("cover_letter.txt", data.get("cover_letter", ""))
        keywords = data.get("keywords", [])
        experience_level = data.get("experience_level", "Entry-Level/Student")

        print(f"🎓 Detected Experience Level: {experience_level}")
        print(f"🔍 Extracted Keywords (Based on JD): {keywords}")

    except Exception as e:
        print(f"❌ Critical Error in Step 1: {e}")
        return

    # =========================================================================
    # STEP 2: Generate Hybrid Questions (Verified & Linked)
    # =========================================================================
    print("\n--- Step 2: Generating Hybrid Interview Prep (With Verification Links) ---")

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
       2. **Item 2 (Practice):** Retrieve a **REAL LeetCode Problem**.
          - You MUST provide the direct URL.

    **CASE B: If the topic is a TOOL, CONCEPT, or AMBIGUOUS** (Git, Agile, Docker, Linux, REST API, System Design):
       1. **Item 1 (Theory):** A classic conceptual question derived from **GeeksforGeeks or Javatpoint**.
       2. **Item 2 (Scenario):** A common scenario discussed on **StackOverflow**.
          - Provide a link to a relevant StackOverflow discussion.

    **⚠️ FALLBACK RULE:**
    If you are unsure whether a topic is a Language or a Concept, **TREAT IT AS CASE B** (Concept/Tool).

    --- CRITICAL QUALITY RULES ---

    1. **DIFFICULTY CALIBRATION**:
       - Strictly match {experience_level}.
       - Student/Entry: Basic Algorithms (Easy/Medium).
       - Senior: System Design, Internals (Medium/Hard).

    2. **SOLUTION RELIABILITY & VERIFICATION**:
       - **Coding Questions**: MUST include `Starter Code`, `Full Solution`, `Complexity`, and `verification_link`.
       - **Links**: You MUST provide a `verification_link`. If not available, set to "N/A".

    3. **TRANSPARENCY**:
       - If the question is real/verified -> "is_real": true.
       - If generated/invented -> "is_real": false.

    Output Format (JSON ONLY):
    [
        {{ 
            "topic": "Python", 
            "type": "LeetCode", 
            "is_real": true,
            "problem_name": "Two Sum", 
            "verification_link": "https://leetcode.com/problems/two-sum/",
            "content": "Given an array...",
            "code_snippet": "def twoSum...",
            "solution": "Use a hash map...",
            "complexity": "Time: O(n), Space: O(n)"
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
            link = item.get('verification_link', 'N/A')
            content = item.get('content', '')
            code = item.get('code_snippet', '')
            solution = item.get('solution', '')
            complexity = item.get('complexity', 'N/A')

            # --- Dynamic Header Logic ---
            if "LeetCode" in q_type:
                source_label = "[REAL LEETCODE]" if is_real else "[AI CHALLENGE]"
                header = f"🧩 [{topic}] {source_label}: {prob_name}"
            elif "Scenario" in q_type:
                source_label = "[REAL SCENARIO]" if is_real else "[AI SCENARIO]"
                header = f"⚙️ [{topic}] {source_label}: {prob_name}"
            else:
                source_label = "[REAL THEORY]" if is_real else "[AI THEORY]"
                header = f"📚 [{topic}] {source_label}: {prob_name}"

            # --- Write Question File ---
            entry = f"{header}\n{'-' * 50}\n"
            if link and link != "N/A":
                entry += f"🔗 Verify Here: {link}\n"
            entry += f"{'-' * 50}\n"
            entry += f"Description/Question:\n{content}\n"
            if code and code != "N/A":
                entry += f"\n💻 Starter Code:\n{code}\n"
            q_file += entry + f"\n\n"

            # --- Write Solution File ---
            sol_file += f"Question {idx}: {header}\n"
            if link and link != "N/A":
                sol_file += f"🔗 Source/Verify: {link}\n"
            sol_file += f"Answer/Solution:\n{solution}\n"
            if complexity and complexity != "N/A":
                sol_file += f"\n📊 Complexity Analysis: {complexity}\n"
            sol_file += f"{'=' * 50}\n\n"

        save_to_file("interview_questions.txt", q_file)
        save_to_file("interview_solutions.txt", sol_file)

    except Exception as e:
        print(f"❌ Error in Step 2: {e}")

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