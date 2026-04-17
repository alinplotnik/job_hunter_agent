# AI Job Hunter Agent

A Streamlit web app that analyzes a resume against a job description using Gemini and returns:
- ATS readability report
- resume feedback
- cover letter draft
- interview prep questions and solutions

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add:

```env
GEMINI_API_KEY=your_api_key_here
```

4. Start the app:

```bash
streamlit run app.py
```

5. Open the local URL shown by Streamlit.

## Host Online (Recommended: Streamlit Community Cloud)

This is the fastest way to make the app available from your phone.

1. Push this folder to GitHub.
2. Go to Streamlit Community Cloud and create a new app from your repo.
3. Set these app values:
- Main file path: `app.py`
- Python version: from `runtime.txt` (`python-3.11`)
4. In Streamlit app settings, add a secret:

```toml
GEMINI_API_KEY = "your_api_key_here"
```

5. Deploy.

After deploy, Streamlit gives you a public HTTPS URL. Open that URL on your phone.

## Why This Works in Cloud

`app.py` now loads `GEMINI_API_KEY` from Streamlit secrets before importing the core logic module, so the app starts correctly in hosted environments.

## Project Structure

```text
job_hunter_agent/
   app.py
   main.py
   requirements.txt
   runtime.txt
   .streamlit/
      config.toml
   inputs/
   outputs/
```

## Notes

- Keep `inputs/` and `outputs/` out of git if they contain private data.
- The generated reports are text files under `outputs/`.
- If deploy fails due to dependency build issues, try pinning Python to `3.10` in `runtime.txt`.
