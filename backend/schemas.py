"""Request and response models for the ProjectPilot AI backend."""

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """User preferences sent by the frontend."""

    domain: str = Field(default="", examples=["Machine Learning"])
    skill_level: str = Field(default="", examples=["Beginner"])
    interests: str = Field(default="", examples=["recommendation dashboard NLP"])
    available_time: str = Field(default="", examples=["2-3 weeks"])
    preferred_language: str = Field(default="", examples=["Python"])
    top_n: int = Field(default=5, ge=1, le=10)


class ProjectSummary(BaseModel):
    """Small project card returned in recommendation results."""

    project_id: str
    title: str
    domain: str
    skill_level: str
    available_time: str
    preferred_language: str
    description: str
    match_score: float
    match_percentage: float


class ProjectDetail(BaseModel):
    """Complete project information shown after a project is selected."""

    project_id: str
    title: str
    domain: str
    skill_level: str
    interests: list[str]
    available_time: str
    preferred_language: str
    description: str
    learning_roadmap: list[str]
    required_skills: list[str]
    required_libraries: list[str]
    free_datasets: list[str]
    free_apis: list[str]
    learning_resources: list[str]
    future_scope: list[str]


class RecommendationResponse(BaseModel):
    """Response returned by the recommendation endpoint."""

    user_profile: str
    total_projects: int
    recommendations: list[ProjectSummary]


class FilterOptions(BaseModel):
    """Dropdown options used by the frontend."""

    domains: list[str]
    skill_levels: list[str]
    available_times: list[str]
    preferred_languages: list[str]


class HealthResponse(BaseModel):
    """Simple health-check response."""

    status: str
    app_name: str
    total_projects: int
