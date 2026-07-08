"""FastAPI backend for ProjectPilot AI."""

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    FilterOptions,
    HealthResponse,
    ProjectDetail,
    ProjectSummary,
    RecommendationRequest,
    RecommendationResponse,
)
from database import (
    get_database_status,
    initialize_database,
    load_projects_from_mongodb,
)
from src.data_loader import load_projects
from src.project_details import split_items
from src.recommender import build_user_profile, recommend_projects


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "projects.json"

app = FastAPI(
    title="ProjectPilot AI Backend",
    description="Backend API for intelligent student project recommendations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    """Initialize MongoDB when it is available."""
    initialize_database(DATA_PATH)


def get_projects() -> pd.DataFrame:
    """Load projects from MongoDB, falling back to the local JSON dataset.

    MongoDB is the preferred project store. The JSON fallback keeps local
    development usable before pymongo or a MongoDB server is configured.
    """
    try:
        mongo_projects = load_projects_from_mongodb()
        if not mongo_projects.empty:
            return mongo_projects
    except Exception:
        pass

    return load_projects(DATA_PATH)


def normalize_any(value: str) -> str:
    """Treat empty strings and 'Any' as no filter."""
    cleaned_value = value.strip()
    return "" if cleaned_value.lower() == "any" else cleaned_value


def project_to_detail(project: pd.Series) -> ProjectDetail:
    """Convert one project row into a detailed API response."""
    return ProjectDetail(
        project_id=project["project_id"],
        title=project["title"],
        domain=project["domain"],
        skill_level=project["skill_level"],
        interests=split_items(str(project["interests"]).replace(" ", "|")),
        available_time=project["available_time"],
        preferred_language=project["preferred_language"],
        description=project["description"],
        learning_roadmap=split_items(project["learning_roadmap"]),
        required_skills=split_items(project["required_skills"]),
        required_libraries=split_items(project["required_libraries"]),
        free_datasets=split_items(project["free_datasets"]),
        free_apis=split_items(project["free_apis"]),
        learning_resources=split_items(project["learning_resources"]),
        future_scope=split_items(project["future_scope"]),
    )


def project_to_summary(project: pd.Series) -> ProjectSummary:
    """Convert one recommended project row into a compact API response."""
    match_score = float(project["match_score"])

    return ProjectSummary(
        project_id=project["project_id"],
        title=project["title"],
        domain=project["domain"],
        skill_level=project["skill_level"],
        available_time=project["available_time"],
        preferred_language=project["preferred_language"],
        description=project["description"],
        match_score=round(match_score, 4),
        match_percentage=round(match_score * 100, 2),
    )


@app.get("/", response_model=dict[str, str])
def root() -> dict[str, str]:
    """Default route with a short API message."""
    return {
        "message": "ProjectPilot AI backend is running.",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Check whether the backend can load project data."""
    projects = get_projects()

    return HealthResponse(
        status="ok",
        app_name="ProjectPilot AI Backend",
        total_projects=len(projects),
    )


@app.get("/database", response_model=dict)
def database_status() -> dict:
    """Check MongoDB connection and project_data database status."""
    return get_database_status(DATA_PATH)


@app.get("/options", response_model=FilterOptions)
def get_filter_options() -> FilterOptions:
    """Return filter values for frontend dropdowns."""
    projects = get_projects()

    return FilterOptions(
        domains=sorted(projects["domain"].unique().tolist()),
        skill_levels=sorted(projects["skill_level"].unique().tolist()),
        available_times=sorted(projects["available_time"].unique().tolist()),
        preferred_languages=sorted(projects["preferred_language"].unique().tolist()),
    )


@app.get("/projects", response_model=list[ProjectDetail])
def list_projects() -> list[ProjectDetail]:
    """Return all projects with full details."""
    projects = get_projects()

    return [project_to_detail(project) for _, project in projects.iterrows()]


@app.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str) -> ProjectDetail:
    """Return full details for one selected project."""
    projects = get_projects()
    matched_projects = projects[projects["project_id"].str.lower() == project_id.lower()]

    if matched_projects.empty:
        raise HTTPException(status_code=404, detail="Project not found")

    return project_to_detail(matched_projects.iloc[0])


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """Recommend projects from user preferences."""
    projects = get_projects()
    user_profile = build_user_profile(
        domain=normalize_any(request.domain),
        skill_level=normalize_any(request.skill_level),
        interests=request.interests.strip(),
        available_time=normalize_any(request.available_time),
        preferred_language=normalize_any(request.preferred_language),
    )

    recommendations = recommend_projects(projects, user_profile, top_n=request.top_n)

    return RecommendationResponse(
        user_profile=user_profile,
        total_projects=len(projects),
        recommendations=[
            project_to_summary(project) for _, project in recommendations.iterrows()
        ],
    )
