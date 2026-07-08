"""Utilities for loading and validating ProjectPilot AI datasets."""

import json
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "project_id",
    "title",
    "domain",
    "skill_level",
    "interests",
    "available_time",
    "preferred_language",
    "description",
    "learning_roadmap",
    "required_skills",
    "required_libraries",
    "free_datasets",
    "free_apis",
    "learning_resources",
    "future_scope",
}


def load_projects(csv_path: str | Path) -> pd.DataFrame:
    """Load the project dataset and check that all required columns exist."""
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"Project dataset not found: {path}")

    if path.suffix.lower() == ".json":
        projects = _load_json_projects(path)
    else:
        projects = pd.read_csv(path)

    return normalize_project_dataframe(projects).fillna("")


def normalize_project_dataframe(projects: pd.DataFrame) -> pd.DataFrame:
    """Normalize and validate a project dataframe from any supported source."""
    normalized_projects = _normalize_project_columns(projects)
    missing_columns = REQUIRED_COLUMNS.difference(normalized_projects.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset is missing required columns: {missing}")

    return normalized_projects


def _load_json_projects(path: Path) -> pd.DataFrame:
    """Load ProjectPilot's rich JSON dataset."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        records = data.get("projects", [])
    else:
        records = data

    return pd.DataFrame(records)


def _join_items(value) -> str:
    """Convert JSON list fields into the pipe-separated format used by the UI."""
    if isinstance(value, list):
        return "|".join(str(item).strip() for item in value if str(item).strip())
    return str(value) if value is not None else ""


def _normalize_project_columns(projects: pd.DataFrame) -> pd.DataFrame:
    """Map the richer JSON schema into the recommender's compact schema."""
    projects = projects.copy()

    column_map = {
        "project_name": "title",
        "difficulty_level": "skill_level",
        "estimated_completion_time": "available_time",
        "programming_languages": "preferred_language",
        "short_description": "description",
    }

    for source, target in column_map.items():
        if target not in projects.columns and source in projects.columns:
            projects[target] = projects[source]

    if "interests" not in projects.columns:
        interest_parts = []
        for column in ["interest_category", "subdomain", "tags"]:
            if column in projects.columns:
                interest_parts.append(projects[column].map(_join_items))

        if interest_parts:
            interests = interest_parts[0]
            for part in interest_parts[1:]:
                interests = interests + "|" + part
            projects["interests"] = interests

    if "free_datasets" not in projects.columns and "dataset_name" in projects.columns:
        dataset_links = projects.get("dataset_link", "Not applicable")
        projects["free_datasets"] = projects["dataset_name"].astype(str) + " - " + dataset_links.astype(str)

    if "free_apis" not in projects.columns and "api_name" in projects.columns:
        api_links = projects.get("api_link", "Not applicable")
        projects["free_apis"] = projects["api_name"].astype(str) + " - " + api_links.astype(str)

    if "learning_resources" not in projects.columns:
        projects["learning_resources"] = (
            "Official documentation|GitHub examples|freeCodeCamp tutorials|Kaggle Learn"
        )

    for column in [
        "learning_roadmap",
        "required_skills",
        "required_libraries",
        "free_datasets",
        "free_apis",
        "learning_resources",
        "future_scope",
        "preferred_language",
    ]:
        if column in projects.columns:
            projects[column] = projects[column].map(_join_items)

    return projects
