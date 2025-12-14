import streamlit as st
import time

# Page configuration and layout setup
st.set_page_config(page_title="Job Hunter AI Agent", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Job Hunter AI Agent")
st.markdown("### The system that prepares you for your next interview")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Enter your API key...")
    st.info("System is currently in 'Design Mode' - Results are for demonstration only.")

# --- Input Area ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Resume (PDF)")
    uploaded_file = st.file_uploader("Drag and drop your file here", type="pdf")

with col2:
    st.subheader("2. Job Description")
    job_description = st.text_area("Paste the Job Description here...", height=150)

# --- Action Button ---
run_btn = st.button("🚀 Run Agent", type="primary")

# --- Logic (Event handling) ---
if run_btn:
    if not uploaded_file or not job_description:
        st.error("Missing data! Please upload a resume and provide a job description.")
    else:
        # Tomorrow, this section will be replaced by the real call to main.py
        # Today, we are mocking the process to build the UI structure

        with st.status("Agent is working...", expanded=True) as status:
            st.write("📄 Reading resume...")
            time.sleep(1)  # Artificial delay for visual effect

            st.write("🤖 Analyzing job description...")
            time.sleep(1)

            st.write("🌐 Searching for interview questions (GeeksForGeeks)...")
            time.sleep(2)

            status.update(label="Process Complete!", state="complete", expanded=False)

        # --- Display Results (Mock Data) ---
        st.success("Analysis finished successfully!")

        # Results Tabs
        tab1, tab2, tab3 = st.tabs(["📝 Resume Feedback", "✉️ Cover Letter", "❓ Interview Questions"])

        with tab1:
            st.subheader("Improvement Suggestions")
            st.info("This is a preview of what you will see tomorrow:")
            st.markdown("""
            * Missing details about your final Python project.
            * Consider adding **'Git'** to your skills section.
            * Add a link to your LinkedIn profile.
            """)

        with tab2:
            st.subheader("Cover Letter Draft")
            st.text_area("Copy from here:", value="Dear Hiring Manager,\n\nI am excited to apply for...", height=200)

        with tab3:
            st.subheader("Prep Questions (Personalized)")
            with st.expander("Python Questions"):
                st.write("**Q: What is the difference between list and tuple?**")
                st.write("A: Lists are mutable, tuples are immutable.")

            with st.expander("Git Questions"):
                st.write("**Q: Explain git rebase vs merge.**")