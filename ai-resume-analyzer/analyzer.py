"""
analyzer.py

Core analysis pipeline for the résumé × JD Analyzer.

Every extraction/analysis step delegates its reasoning to the LLM via
`ask_json`, each using the dedicated prompt constant defined in prompts.py.
`summarise_overall` is the one text-returning step and uses `ask_text`.
`compute_overall_score` is pure arithmetic — no LLM call.
"""

import json

from llm import ask_json, ask_text
from prompts import (
    RESUME_PROFILE_PROMPT,
    JD_PROFILE_PROMPT,
    KEYWORD_MATCH_PROMPT,
    BULLET_QUALITY_PROMPT,
    JARGON_AUDIT_PROMPT,
    STRUCTURE_AUDIT_PROMPT,
    BACKGROUND_FIT_PROMPT,
    DEGREE_ALIGNMENT_PROMPT,
    OVERALL_SUMMARY_PROMPT,
)


def extract_resume_profile(resume_text: str) -> dict:
    """
    Parse raw résumé text into the structured résumé-profile schema
    (contact info, education, projects, experience, skills).
    """
    return ask_json(RESUME_PROFILE_PROMPT, resume_text, max_tokens=2000)


def extract_jd_profile(jd_text: str) -> dict:
    """
    Parse raw job-description text into the structured JD-profile schema
    (required_skills / preferred_skills, each broken out by category).
    """
    return ask_json(JD_PROFILE_PROMPT, jd_text, max_tokens=1500)


def analyse_keyword_match(resume_profile: dict, jd_profile: dict) -> dict:
    """
    Compare résumé profile against JD profile to find present/missing
    keywords and compute keyword_match_score (0-100, based on required
    keyword coverage).
    """
    user_message = json.dumps(
        {"resume_profile": resume_profile, "jd_profile": jd_profile}
    )
    return ask_json(KEYWORD_MATCH_PROMPT, user_message, max_tokens=2000)


def analyse_bullets(resume_profile: dict) -> dict:
    """
    Score each résumé bullet on the Action -> Technology -> Impact rubric
    and return per-bullet detail plus aggregate bullet_quality_avg (0-1).
    """
    user_message = json.dumps({"resume_profile": resume_profile})
    return ask_json(BULLET_QUALITY_PROMPT, user_message, max_tokens=2500)


def analyse_jargon(resume_profile: dict, jd_profile: dict) -> dict:
    """
    Flag JD/résumé terminology pairs that likely refer to the same
    underlying skill but are worded differently, and compute jargon_score
    (0-100).
    """
    user_message = json.dumps(
        {"resume_profile": resume_profile, "jd_profile": jd_profile}
    )
    return ask_json(JARGON_AUDIT_PROMPT, user_message, max_tokens=2500)


def analyse_structure(resume_text: str) -> dict:
    """
    Audit ATS parseability of the résumé (layout, headers, ordering,
    length, contact placement, images) and compute structure_score (0-100).
    """
    return ask_json(STRUCTURE_AUDIT_PROMPT, resume_text, max_tokens=1200)


def analyse_background_fit(resume_profile: dict, jd_profile: dict) -> dict:
    """
    Compare candidate education/experience against JD requirements across
    fixed dimensions (degree level, field of study, years of experience,
    industry background, role-type continuity) and compute
    background_fit_score (0-100).
    """
    user_message = json.dumps(
        {"resume_profile": resume_profile, "jd_profile": jd_profile}
    )
    return ask_json(BACKGROUND_FIT_PROMPT, user_message, max_tokens=1200)


def analyse_degree_alignment(resume_profile: dict, jd_profile: dict, degree: str) -> dict:
    """
    Compare the candidate's selected program/degree (one of VALID_DEGREES:
    RTIS, IMGD, UXGD, BFA) against the JD's requirements, flagging how well
    the coursework/skills typically associated with that degree line up
    with what the role expects, and compute degree_alignment_score (0-100).
    """
    user_message = json.dumps(
        {"resume_profile": resume_profile, "jd_profile": jd_profile, "degree": degree}
    )
    return ask_json(DEGREE_ALIGNMENT_PROMPT, user_message, max_tokens=1200)


def summarise_overall(report: dict) -> str:
    """
    Synthesize the five audit outputs plus overall score into a 3-bullet
    plain-text executive summary.
    """
    user_message = json.dumps(report)
    return ask_text(OVERALL_SUMMARY_PROMPT, user_message, max_tokens=400)


def compute_overall_score(report: dict) -> int:
    """
    Compute the final weighted overall score (0-100):

        keyword_match_score    weight 0.40
        bullet_quality_avg     weight 0.25
        structure_score        weight 0.15
        jargon_score           weight 0.10
        degree_alignment_score weight 0.10  (or background_fit_score, whichever the
                                              report contains — main.py's pipeline
                                              still produces "background_fit")

    Note: per BULLET_QUALITY_PROMPT's schema, bullet_quality_avg is a float
    on a 0-1 scale (unlike the other four scores, which are 0-100). This
    function reads and weights the values exactly as they appear in the
    report, per spec.
    """
    keyword_match_score = report["keyword_match"]["keyword_match_score"]
    bullet_quality_avg = report["bullets"]["bullet_quality_avg"]
    structure_score = report["structure"]["structure_score"]
    jargon_score = report["jargon"]["jargon_score"]

    if "degree_alignment" in report:
        fit_score = report["degree_alignment"]["degree_alignment_score"]
    else:
        fit_score = report["background_fit"]["background_fit_score"]

    total = (
        keyword_match_score * 0.40
        + bullet_quality_avg * 0.25
        + structure_score * 0.15
        + jargon_score * 0.10
        + fit_score * 0.10
    )

    return int(round(total))