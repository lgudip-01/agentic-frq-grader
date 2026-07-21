import os
from dotenv import load_dotenv
from openai import OpenAI
from schemas import GradingReport
from pypdf import PdfReader
import streamlit as st

# Load environment variables & client
load_dotenv()
client = OpenAI()


def read_pdf(file_path):
    reader = PdfReader(file_path)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])


def grade_frq(question: str, rubric: str, student_submission: str) -> GradingReport:
    system_prompt = (
        "You are an expert academic evaluator. Your task is to objectively grade "
        "a student's response based strictly on the provided rubric."
    )
    user_prompt = f"""
    --- QUESTION ---
    {question}

    --- RUBRIC ---
    {rubric}

    --- STUDENT SUBMISSION ---
    {student_submission}
    """
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=GradingReport
    )
    return response.choices[0].message.parsed


# --- STREAMLIT UI (TOP-TO-BOTTOM) ---
st.set_page_config(page_title="FRQ Grader", page_icon="🎓", layout="wide")
st.title("🎓 Agentic FRQ Grader")
st.write("Upload a rubric PDF and enter the question and student response below.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Setup")
    question = st.text_area("Paste the Question here:", height=150)
    rubric_file = st.file_uploader("Upload the Rubric (PDF)", type=["pdf"])

with col2:
    st.subheader("2. Submission")
    student_text = st.text_area(
        "Type/Paste the response to be graded:", height=250)

if st.button("Run FRQ Grader", type="primary"):
    if not question or not rubric_file or not student_text:
        st.warning("Please fill in all fields and upload the PDF!")
    else:
        with st.spinner("Running FRQ Grader..."):
            try:
                rubric_content = read_pdf(rubric_file)
                report = grade_frq(question, rubric_content, student_text)

                st.divider()
                st.success("Grading Complete!")

                score_col1, score_col2 = st.columns(2)
                score_col1.metric("Submission ID", report.submission_id)
                score_col2.metric(
                    "Final Score", f"{report.total_score} / {report.max_score}")

                st.subheader("Breakdown by Section")
                for item in report.evaluations:
                    with st.expander(f"• {item.criterion_name} ({item.points_awarded}/{item.max_points} pts)"):
                        st.write(f"**Rationale:** {item.rationale}")

                st.subheader("Summary Feedback")
                st.info(report.summary_feedback)

            except Exception as e:
                st.error(f"Error: {e}")
