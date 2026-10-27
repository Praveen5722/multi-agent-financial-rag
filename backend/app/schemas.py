from pydantic import BaseModel, Field
from typing import Literal

class Evidence(BaseModel):
    source_id: str
    filename: str
    page: int | None = None
    text: str
    score: float | None = None

class Metric(BaseModel):
    company: str = "Unknown"
    period: str = "Unknown"
    metric: str
    value: float
    unit: str = ""
    source_id: str = "user_input"
    confidence: float = 1.0

class AnalyzeRequest(BaseModel):
    question: str = Field(min_length=5, max_length=4000)
    company: str = ""
    metrics: list[Metric] = []

class AgentStatus(BaseModel):
    name: str
    status: Literal['completed','warning','skipped','failed']
    summary: str

class AnalyzeResponse(BaseModel):
    report_id: str
    title: str
    executive_summary: str
    findings: list[str]
    calculations: list[dict]
    risks: list[dict]
    evidence: list[Evidence]
    validation: dict
    agents: list[AgentStatus]
    limitations: list[str]
