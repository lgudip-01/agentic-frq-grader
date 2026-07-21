from pydantic import BaseModel, Field
from typing import List


class CriterionEvaluation(BaseModel):
    criterion_name: str = Field(
        description="The name or specific requirement from the rubric.")
    max_points: int = Field(
        description="Maximum points possible for this criterion.")
    points_awarded: int = Field(
        description="Points awarded based on the student's submission.")
    rationale: str = Field(
        description="Detailed explanation justifying the points awarded.")


class GradingReport(BaseModel):
    submission_id: str = Field(
        description="Identifier or student submission label.")
    total_score: int = Field(
        description="Sum of all awarded points across criteria.")
    max_score: int = Field(description="Maximum total points available.")
    evaluations: List[CriterionEvaluation] = Field(
        description="List of criterion-by-criterion breakdowns.")
    summary_feedback: str = Field(
        description="Overall diagnostic feedback and suggestions for improvement.")
