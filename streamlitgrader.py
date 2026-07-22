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
    st.subheader("Resources")
    question = st.text_area("Paste the FRQ here:", height=150)
    rubric_file = st.file_uploader("Upload the Rubric (PDF)", type=["pdf"])

with col2:
    st.subheader("Response")
    student_text = st.text_area(
        "Type/Paste the response to be graded:", height=250)

if st.button("Grade This Response", type="primary"):
    if not question or not rubric_file or not student_text:
        st.warning(
            "Please fill out all fields in this form")
    else:
        with st.spinner("Grading Response..."):
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
                st.download_button(
                    label="📄 Download Official PDF Report",
                    data=pdf_data,
                    file_name=f"Grading_Report_{report.submission_id}.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(
                    f"An error occurred while running the evaluation: {e}")

if "report" in st.session_state and "pdf_bytes" in st.session_state:
    report = st.session_state["report"]
    pdf_data = st.session_state["pdf_bytes"]

    st.divider()

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
    st.download_button(
        label="📄 Download Official PDF Report",
        data=pdf_data,
        file_name=f"Grading_Report_{report.submission_id}.pdf",
        mime="application/pdf"
    )
