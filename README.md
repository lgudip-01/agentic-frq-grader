🎓 Project Documentation: Agentic FRQ & Essay Grader
📁 Repository Structure
Plaintext
agentic-frq-grader/
│
├── .gitignore
├── .env # (Keep private! Do NOT commit to GitHub)
├── config.toml # Streamlit Theme Config (inside .streamlit/)
├── requirements.txt # Dependency Manifest
├── README.md # Project Overview & Setup Guide
├── schemas.py # Pydantic Data Models
└── grader.py # Main Streamlit Application & PDF Engine

1. Environment & Config Files
   .gitignore
   Code snippet
   .env
   venv/
   **pycache**/
   \*.pyc
   .DS_Store
   .env (Example structure — insert your actual key)
   Code snippet
   OPENAI_API_KEY=your_openai_api_key_here
   .streamlit/config.toml
   Ini, TOML
   [theme]
   primaryColor = "#4F46E5"
   backgroundColor = "#F9FAFB"
   secondaryBackgroundColor = "#FFFFFF"
   textColor = "#111827"
   requirements.txt
   Plaintext
   openai>=1.0.0
   pydantic>=2.0.0
   pypdf>=3.0.0
   python-dotenv>=1.0.0
   reportlab>=4.0.0
   streamlit>=1.30.0
2. Python Source Code
   schemas.py
   Python
   from pydantic import BaseModel, Field
   from typing import List

class CriterionEvaluation(BaseModel):
criterion_name: str = Field(description="Name of the rubric criterion evaluated.")
points_awarded: float = Field(description="Points granted to the student for this criterion.")
max_points: float = Field(description="Maximum points possible for this criterion.")
rationale: str = Field(description="Detailed explanation justifying the awarded score based on the rubric.")

class GradingReport(BaseModel):
submission_id: str = Field(description="A unique identification string for this submission.")
total_score: float = Field(description="Sum of all points awarded across all criteria.")
max_score: float = Field(description="Sum of maximum possible points across all criteria.")
evaluations: List[CriterionEvaluation] = Field(description="Criterion-by-criterion breakdown of the grading.")
summary_feedback: str = Field(description="Overall diagnostic assessment highlighting strengths and areas for improvement.")
grader.py
Python
import io
import os
from dotenv import load_dotenv
from openai import OpenAI
from schemas import GradingReport
from pypdf import PdfReader
import streamlit as st

# ReportLab imports for generating PDF reports

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Load API key from local .env file

load_dotenv()

client = OpenAI()

def read_pdf(file_path):
"""Parses text from an uploaded PDF file."""
reader = PdfReader(file_path)
return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def grade_frq(question: str, rubric: str, student_submission: str) -> GradingReport:
"""
Evaluates a student's response against a rubric using structured Pydantic outputs.
"""
system_prompt = (
"You are an expert academic evaluator. Your task is to objectively grade "
"a student's response based strictly on the provided rubric. Evaluate each "
"criterion independently and provide clear, constructive feedback."
)

    user_prompt = f"""
    --- QUESTION ---
    {question}

    --- RUBRIC ---
    {rubric}

    --- STUDENT SUBMISSION ---
    {student_submission}
    """

    # Call OpenAI with structured Pydantic format
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=GradingReport
    )

    return response.choices[0].message.parsed

def generate_pdf_report(report: GradingReport) -> bytes:
"""Generates a downloadable PDF summary report of the grading results."""
buffer = io.BytesIO()
doc = SimpleDocTemplate(
buffer,
pagesize=letter,
rightMargin=36,
leftMargin=36,
topMargin=36,
bottomMargin=36
)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#111827'))
    heading_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#4F46E5'), spaceBefore=10)
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#1F2937'))

    story = []

    # Title & Overall Score Block
    story.append(Paragraph("🎓 Official AI FRQ Evaluation Report", title_style))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(f"<b>Submission ID:</b> {report.submission_id}", body_style))
    story.append(
        Paragraph(f"<b>Final Score:</b> {report.total_score} / {report.max_score}", body_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor('#E5E7EB'), spaceAfter=15))

    # Detailed Criteria Section
    story.append(Paragraph("Criteria Breakdown", heading_style))
    for item in report.evaluations:
        criterion_header = f"• <b>{item.criterion_name}</b> ({item.points_awarded}/{item.max_points} pts)"
        story.append(Paragraph(criterion_header, body_style))
        story.append(
            Paragraph(f"<i>Rationale:</i> {item.rationale}", body_style))
        story.append(Spacer(1, 8))

    story.append(HRFlowable(width="100%", thickness=0.5,
                 color=colors.HexColor('#F3F4F6'), spaceBefore=10, spaceAfter=15))

    # Diagnostic Summary Feedback
    story.append(Paragraph("Summary Feedback", heading_style))
    story.append(Paragraph(report.summary_feedback, body_style))

    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- STREAMLIT USER INTERFACE ---

st.set_page_config(page_title="FRQ Grader", page_icon="🎓", layout="wide")

st.title("🎓 Agentic FRQ Grader")
st.write("Upload a rubric PDF and enter the question and student response below to generate an automated evaluation.")

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
st.warning(
"Please fill in the question, upload a rubric PDF, and enter the student response.")
else:
with st.spinner("Running FRQ Grader..."):
try:
rubric_content = read_pdf(rubric_file)
report = grade_frq(question, rubric_content, student_text)

                st.divider()
                st.success("Grading Complete!")

                # Overview Metrics
                score_col1, score_col2 = st.columns(2)
                score_col1.metric("Submission ID", report.submission_id)
                score_col2.metric(
                    "Final Score", f"{report.total_score} / {report.max_score}")

                # Detailed Breakdown
                st.subheader("Breakdown by Section")
                for item in report.evaluations:
                    with st.expander(f"• {item.criterion_name} ({item.points_awarded}/{item.max_points} pts)"):
                        st.write(f"**Rationale:** {item.rationale}")

                # Summary Feedback
                st.subheader("Summary Feedback")
                st.info(report.summary_feedback)

                # PDF Export Action Button
                st.divider()
                pdf_data = generate_pdf_report(report)
                st.download_button(
                    label="📄 Download Official PDF Report",
                    data=pdf_data,
                    file_name=f"Grading_Report_{report.submission_id}.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"An error occurred while running the evaluation: {e}")

3. GitHub Readme
   README.md
   Markdown

# 🎓 Agentic FRQ & Essay Grader

An automated evaluation system built with **Python**, **Streamlit**, and **OpenAI Structured Outputs**. The platform ingests unstructured PDF rubrics and free-response questions (FRQs), performs deterministic criteria-by-criteria scoring, and generates exportable evaluation reports.

---

## ✨ Features

- **PDF Rubric Extraction:** Extracts and parses rubric criteria directly from uploaded PDF documents using `pypdf`.
- **Deterministic Structured Evaluation:** Uses OpenAI's `beta.chat.completions.parse` backed by **Pydantic** schemas to ensure reliable, structured output without hallucinations.
- **Interactive Streamlit Dashboard:** Clean UI for uploading rubrics, entering prompts, reading detailed feedback, and analyzing score breakdowns.
- **Dynamic Theme:** Fully customized visual presentation built using `.streamlit/config.toml`.
- **PDF Report Generation:** Programmatically compiles and exports official evaluation summaries into downloadable PDF reports powered by `ReportLab`.

---

## 🛠️ Tech Stack

- **Frontend / Framework:** [Streamlit](https://streamlit.io/)
- **AI / Language Model:** [OpenAI API (GPT-4o / GPT-4o-mini)](https://platform.openai.com/)
- **Schema Validation:** [Pydantic](https://docs.pydantic.dev/)
- **PDF Processing & Generation:** `PyPDF`, `ReportLab`
- **Environment Management:** `python-dotenv`

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher installed
- An OpenAI API Key

### 1. Clone the Repository

git clone [https://github.com/lgudip-01/agentic-frq-grader.git](https://github.com/lgudip-01/agentic-frq-grader.git)
cd agentic-frq-grader 2. Create a Virtual Environment
Bash
python -m venv venv

# On Windows:

venv\Scripts\activate

# On macOS/Linux:

source venv/bin/activate 3. Install Dependencies
Bash
pip install -r requirements.txt 4. Configure Environment Variables
Create a .env file in the root directory and add your OpenAI API key:

OPENAI_API_KEY=your_actual_openai_api_key_here 5. Run the Application
Bash
streamlit run grader.py --server.port 8502
Navigate to http://localhost:8502 in your browser to test the app!

📄 License
This project is open-source and available under the MIT License.
