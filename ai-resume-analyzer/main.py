import streamlit as st

from dotenv import load_dotenv

import json
import os
from datetime import datetime
from pathlib import Path

from parse import read_resume_pdf
from analyzer import (
    extract_resume_profile, extract_jd_profile, analyse_keyword_match,
    analyse_bullets, analyse_jargon, analyse_structure,
    analyse_degree_alignment, summarise_overall, compute_overall_score,
)
from report import render_markdown

load_dotenv()
VALID_DEGREES = ["RTIS", "IMGD", "UXGD", "BFA"]

st.set_page_config(page_title="Resume Analyzer", layout="wide")
st.title("📄 AI Resume Analyzer")

resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste Job Description", height=250)
degree = st.selectbox("Select Degree", VALID_DEGREES)
run = st.button("Analyze Resume")

if run:
    if not resume_file or not jd_text:
        st.error("Please upload resume and paste job description.")
        st.stop()

    model = os.getenv("MODEL", "openai/gpt-4o-mini")
    st.caption(f"Using model: {model}")

    try:
        with st.spinner("[1/7] Parsing résumé..."):
            resume_text = read_resume_pdf(resume_file)

        with st.spinner("[2/7] Extracting résumé profile (LLM)..."):
            resume_profile = extract_resume_profile(resume_text)

        with st.spinner("[3/7] Extracting JD profile (LLM)..."):
            jd_profile = extract_jd_profile(jd_text)

        with st.spinner("[4/7] Keyword match (LLM)..."):
            keyword_match = analyse_keyword_match(resume_profile, jd_profile)

        with st.spinner("[5/7] Bullet audit (LLM)..."):
            bullets = analyse_bullets(resume_profile)

        with st.spinner("[6/7] Jargon, structure, degree alignment (LLM x3)..."):
            jargon = analyse_jargon(resume_profile, jd_profile)
            structure = analyse_structure(resume_text)
            degree_alignment = analyse_degree_alignment(resume_profile, jd_profile, degree)

    except ValueError as exc:
        st.error(f"ERROR: {exc}")
        st.stop()
    except RuntimeError as exc:
        st.error(f"ERROR: {exc}")
        st.stop()

    report = {
        "meta": {
            "resume_path": resume_file.name,
            "job_path": "pasted_job_description.txt",
            "model": model,
            "degree": degree,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "resume_profile":    resume_profile,
        "jd_profile":        jd_profile,
        "keyword_match":     keyword_match,
        "bullets":           bullets,
        "jargon":            jargon,
        "structure":         structure,
        "degree_alignment":  degree_alignment,
    }
    report["overall_score"]        = compute_overall_score(report)
    report["passes_ats_threshold"] = report["overall_score"] >= 60

    try:
        with st.spinner("[7/7] Final summary (LLM)..."):
            report["summary"] = summarise_overall(report)
    except RuntimeError as exc:
        st.error(f"ERROR: {exc}")
        st.stop()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("outputs").mkdir(exist_ok=True)
    json_path = f"outputs/match_report_{ts}.json"
    md_path   = f"outputs/match_report_{ts}.md"

    Path(json_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    render_markdown(report, out_path=md_path)

    verdict = "PASS" if report["passes_ats_threshold"] else "FAIL"
    col1, col2 = st.columns(2)
    col1.metric("Overall Score", f"{report['overall_score']}/100")
    col2.metric("ATS 60% Threshold", verdict)

    st.subheader("Summary")
    st.write(report["summary"])

    with st.expander("Full report (JSON)"):
        st.json(report)

    dl_col1, dl_col2 = st.columns(2)
    dl_col1.download_button(
        "Download report (Markdown)",
        data=Path(md_path).read_bytes(),
        file_name=Path(md_path).name,
        mime="text/markdown",
    )
    dl_col2.download_button(
        "Download report (JSON)",
        data=Path(json_path).read_bytes(),
        file_name=Path(json_path).name,
        mime="application/json",
    )