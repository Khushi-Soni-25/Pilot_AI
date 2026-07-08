"""Recommendation logic for ProjectPilot AI."""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


PROFILE_COLUMNS = [
    "domain",
    "skill_level",
    "interests",
    "available_time",
    "preferred_language",
    "description",
    "required_skills",
    "required_libraries",
]


def build_user_profile(
    domain: str,
    skill_level: str,
    interests: str,
    available_time: str,
    preferred_language: str,
) -> str:
    """Convert user preferences into one searchable text profile."""
    return " ".join(
        [
            domain,
            skill_level,
            interests,
            available_time,
            preferred_language,
        ]
    ).lower()


def build_project_profiles(projects: pd.DataFrame) -> pd.Series:
    """Combine important project columns into one text profile per project."""
    return projects[PROFILE_COLUMNS].astype(str).agg(" ".join, axis=1).str.lower()


def recommend_projects(
    projects: pd.DataFrame,
    user_profile: str,
    top_n: int = 5,
) -> pd.DataFrame:
    """Return the top matching projects for a user profile.

    TF-IDF gives higher importance to useful words and lower importance to very
    common words. Cosine similarity then scores how close each project is to the
    user's preferences.
    """
    project_profiles = build_project_profiles(projects)
    search_corpus = pd.concat([pd.Series([user_profile]), project_profiles], ignore_index=True)

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(search_corpus)

    user_vector = tfidf_matrix[0]
    project_vectors = tfidf_matrix[1:]
    scores = cosine_similarity(user_vector, project_vectors).flatten()

    recommendations = projects.copy()
    recommendations["match_score"] = scores

    return (
        recommendations.sort_values("match_score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
