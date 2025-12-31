import streamlit as st
import os
import tempfile
import main  # Imports your logic

# --- Page Config ---
st.set_page_config(
    page_title="Job Hunter AI Agent",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Better UI ---
# This fixes the font sizes, link colors, and direction issues
st.markdown("""
    <style>
    /* Global font settings */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* Make the Interview Prep links smaller and grey */
    a {
        color: #0066cc;
        text-decoration: none;
        font-size: 0.9em;
    }
    a:hover {
        text-decoration: underline;
    }

    /* Style the output containers */
    .stTextArea textarea {
        background-color: #f0f2f6;
        color: #31333F;
    }

    /* Warnings and Info boxes */
    .stAlert {
        border-radius: 8px;
    }

    /* Headers alignment */
    h1, h2, h3 {
        padding-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if 'results' not in st.session_state:
    st.session_state['results'] = None

# --- Main Header ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("# 🕵️‍♂️")
with col_title:
    st.title("Job Hunter AI Agent")
    st.caption("Optimize your Resume & Prep for Interviews using Gemini AI")

# --- Sidebar ---
with st.sidebar:
    st.header("ℹ️ About the Agent")
    st.markdown("""
    This intelligent agent helps you land your next job by:

    1. **Parsing** your PDF Resume.
    2. **Comparing** it against a specific Job Description.
    3. **Generating** tailored interview questions.
    """)

    st.divider()

    st.info(
        "🔒 **Privacy Note:**\nYour data is processed via Google Gemini API and is not stored permanently on this server.")

    st.write("---")
    st.caption("v1.0.0 | Budget Mode")

# --- Input Area ---
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Resume")
    uploaded_file = st.file_uploader("Upload your PDF Resume", type="pdf", help="Must be a readable PDF file")

with col2:
    st.subheader("2. Job Description")
    job_description = st.text_area("Paste the JD here...", height=150,
                                   placeholder="e.g. 'We are looking for a Senior Python Developer...'")

# --- Run Button ---
run_pressed = st.button("🚀 Analyze Application", type="primary", use_container_width=True)

if run_pressed:
    if not uploaded_file or not job_description:
        st.error("⚠️ Please provide both a Resume (PDF) and a Job Description.")
    else:
        # Create a status container
        status_box = st.status("Agent is working...", expanded=True)

        try:
            # 1. Save temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            # 2. Extract Text
            status_box.write("📄 Reading PDF content...")
            resume_text = main.read_pdf(tmp_path)

            if not resume_text:
                status_box.update(label="Error: Unreadable PDF", state="error")
                st.error("Could not extract text. The PDF might be an image scan.")
            else:
                # 3. Main Logic
                status_box.write("🧠 Analyzing fit, checking visuals, and generating prep...")

                # CALL MAIN LOGIC
                st.session_state['results'] = main.process_application(tmp_path, resume_text, job_description)

                status_box.update(label="Analysis Complete!", state="complete", expanded=False)

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

# --- Results Display ---
if st.session_state['results']:
    results = st.session_state['results']
    if results.get("fatal_error"):
        st.error("🚨 Operation Stopped")
        st.warning(results.get("fatal_error"))
        st.stop()
    st.success("Analysis Ready! See detailed breakdown below. 👇")

    # Visual Warning (Collapsible to keep UI clean)
    if results.get("visual_warning"):
        with st.expander("🚨 Visual Layout Warning Detected", expanded=True):
            st.error(f"Issue: {results['visual_warning'].get('issue_detected')}")
            st.info(f"💡 Advice: {results['visual_warning'].get('advice')}")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 ATS Score", "📝 Feedback", "✉️ Cover Letter", "❓ Interview Prep"])

    # Tab 1: ATS
    with tab1:
        st.subheader("ATS Compatibility Check")
        score = results.get("ats_score", 0)

        c1, c2 = st.columns([1, 3])
        with c1:
            st.metric("Readability Score", f"{score}/10")
            if score >= 8:
                st.balloons()
        with c2:
            st.text_area("Detailed Report", results.get("ats_report", ""), height=200)
            st.download_button("📥 Download Report", results.get("ats_report", ""), "ats_report.txt")

    # Tab 2: Feedback
    with tab2:
        st.subheader("Resume Improvement Tips")
        st.markdown(results.get("feedback", "No feedback available."))
        st.download_button("📥 Download Feedback", results.get("feedback", ""), "resume_feedback.txt")

    # Tab 3: Cover Letter
    with tab3:
        st.subheader("Draft Cover Letter")
        st.text_area("Copy content:", results.get("cover_letter", ""), height=400)
        st.download_button("📥 Download .txt", results.get("cover_letter", ""), "cover_letter.txt")

    # Tab 4: Interview Prep
    with tab4:
        st.subheader("Tailored Interview Questions")

        # Here we display the markdown.
        # The CSS at the top of the file will help format the links.
        st.markdown(results.get("interview_prep", "No questions generated."))

        st.download_button("📥 Download Prep Sheet", results.get("interview_prep", ""), "interview_prep.txt")

    # Reset Button
    if st.button("Start New Analysis"):
        st.session_state['results'] = None
        st.rerun()