import pdfplumber
import os


def check_pdf_layout_safety(file_path):
    print(f"\n--- 🕵️ Testing Layout Safety for: {file_path} ---")

    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for i, page in enumerate(pdf.pages):
            print(f"\n--- PAGE {i + 1} ---")
            # layout=True מנסה לחקות את המיקום הפיזי של הטקסט
            text = page.extract_text(layout=True)
            if text:
                full_text += text
                print(text)
            else:
                print("[No text found on this page]")
            print("-" * 40)

    print("\n--- 🏁 DIAGNOSIS ---")
    # בדיקה: האם אנחנו מצליחים למצוא את המילה Summary כשהיא לבד?
    if "SUMMARY" in full_text.upper() or "PROFILE" in full_text.upper():
        print("✅ The word 'SUMMARY'/'PROFILE' was found.")
    else:
        print("❌ CRITICAL: The 'Summary' section header was NOT detected clearly.")


# כאן אנחנו קוראים לפונקציה כדי שהיא תרוץ
# תוודאי שהקובץ resume.pdf באמת נמצא בתיקיית inputs!
check_pdf_layout_safety("inputs/resume.pdf")