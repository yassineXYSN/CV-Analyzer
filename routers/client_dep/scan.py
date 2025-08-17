from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import httpx
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from routers.client_dep.dependencies import get_db, get_current_user
from databaseclient.insert_to_db import insert_candidate_data

router = APIRouter()

# Resolve templates directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

# n8n webhook URL (set N8N_WEBHOOK_URL in env to override)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# Optional polling endpoint if your n8n exposes one (leave empty if not used)
N8N_RESULT_URL = os.getenv("N8N_RESULT_URL")


def add_query_params(url: str, params: Dict[str, str]) -> str:
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q.update(params)
    new_query = urlencode(q)
    return urlunparse(parsed._replace(query=new_query))


def to_prod_webhook(url: str) -> str:
    return url.replace("/webhook-test/", "/webhook/")


def compute_overall_score_from_categories(scores: Dict[str, Any], job_data: List[Dict] = None) -> int:
    """
    Compute overall score with optional job-specific weighting
    """
    numeric_values: List[float] = []
    for v in scores.values():
        try:
            numeric_values.append(float(v))
        except Exception:
            continue
    if not numeric_values:
        return 0
    
    base_score = sum(numeric_values) / len(numeric_values)
    
    # If job data is provided, apply job-specific adjustments
    if job_data and len(job_data) > 0:
        # This is a simplified example - you can make this more sophisticated
        job_bonus = 0
        for job in job_data:
            # Add bonus points for matching job requirements
            if job.get('skills'):
                job_bonus += 2  # Small bonus for each job with defined skills
        
        # Cap the bonus at 10 points
        job_bonus = min(job_bonus, 10)
        base_score = min(base_score + job_bonus, 100)
    
    return int(round(base_score))


def normalize_improvements(improvements: Any) -> List[Dict[str, str]]:
    """
    Normalize improvements into a list of dicts: [{ category: str, action: str }]
    Supports inputs like:
      - ["String tip", ...]
      - [{"improvement": "..."}, ...]
      - [{"category": "Education", "action": "..."} , ...]
      - "single string"
    """
    result: List[Dict[str, str]] = []
    if not improvements:
        return result

    def push(cat: str, act: str):
        act = str(act).strip()
        if act:
            result.append({"category": str(cat or "General"), "action": act})

    if isinstance(improvements, list):
        for item in improvements:
            if isinstance(item, dict):
                # accept several common keys
                category = item.get("category") or item.get("type") or "General"
                action = item.get("action") or item.get("improvement") or item.get("text") or ""
                push(category, action)
            else:
                push("General", str(item))
    elif isinstance(improvements, dict):
        category = improvements.get("category") or "General"
        action = improvements.get("action") or improvements.get("improvement") or ""
        push(category, action)
    else:
        push("General", str(improvements))

    return result


def first_item_if_list(data: Any) -> Any:
    if isinstance(data, list) and data:
        return data[0]
    return data


async def post_to_n8n_wait_for_json(
    url: str,
    file_name: str,
    file_bytes: bytes,
    content_type: Optional[str],
    selected_profiles: str,
    job_data: str = None,
    timeout_seconds: int = 180,
) -> Optional[dict]:
    """
    Post to n8n webhook and wait for JSON:
    - Adds wait=true to query string
    - Long timeout
    - Tries both test and prod paths
    - Includes job data for enhanced analysis
    """
    wait_url = add_query_params(url, {"wait": "true"})
    alt_wait_url = add_query_params(to_prod_webhook(url), {"wait": "true"})

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for target_url in (wait_url, alt_wait_url):
            try:
                files = {
                    "CV": (file_name, file_bytes, content_type or "application/pdf")
                }
                data = {
                    "selectedProfiles": selected_profiles,
                    "jobData": job_data or "[]"  # Include job data
                }
                resp = await client.post(target_url, files=files, data=data)

                if resp.status_code >= 400:
                    continue

                ctype = (resp.headers.get("content-type") or "").lower()
                text = resp.text or ""
                if "application/json" in ctype:
                    try:
                        print(f"Received JSON response from n8n: {resp.text}")
                        return resp.json()
                    except Exception:
                        pass

                if text.strip().startswith("{") or text.strip().startswith("["):
                    try:
                        return json.loads(text)
                    except Exception:
                        pass
            except httpx.HTTPError:
                continue

    return None


@router.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("client-dep/analyze.html", {
        "request": request,
        "current_user": current_user
    })


@router.post("/scan", response_class=HTMLResponse)
async def scan_file(
    request: Request,
    filetoscan: UploadFile = File(...),
    selectedProfiles: str = Form(...),
    selectedJobsData: str = Form(default="[]"),  # Added job data parameter
    db: Session = Depends(get_db)
):
    """
    Unified route:
    - Forwards the CV to n8n and waits for JSON
    - Includes job data for enhanced scoring
    - Builds all data (including detailed analysis) server-side
    - Renders result page with detailed analysis already populated
    """
    current_user = get_current_user(request, db)

    # Parse job data
    try:
        job_data = json.loads(selectedJobsData) if selectedJobsData else []
    except json.JSONDecodeError:
        job_data = []

    # Save uploaded file
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{filetoscan.filename}"
    file_bytes = await filetoscan.read()
    with open(file_location, "wb") as f:
        f.write(file_bytes)

    # 1) Wait for n8n JSON with job data
    n8n_data = await post_to_n8n_wait_for_json(
        N8N_WEBHOOK_URL,
        filetoscan.filename,
        file_bytes,
        filetoscan.content_type,
        selectedProfiles,
        selectedJobsData,  # Pass job data to n8n
        timeout_seconds=180,
    )

    # 2) Optional: single poll on a result endpoint (if configured)
    if n8n_data is None and N8N_RESULT_URL:
        try:
            poll_url = add_query_params(N8N_RESULT_URL, {"filename": filetoscan.filename})
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.get(poll_url)
                if r.status_code < 400 and r.text.strip():
                    if "application/json" in (r.headers.get("content-type", "").lower()):
                        n8n_data = r.json()
                    elif r.text.strip().startswith("{") or r.text.strip().startswith("["):
                        n8n_data = json.loads(r.text)
        except Exception:
            n8n_data = None

    # If no JSON, render with a friendly error
    if n8n_data is None:
        return templates.TemplateResponse("client-dep/result.html", {
            "request": request,
            "filename": filetoscan.filename,
            "pdf_text": "",
            "images_text": "",
            "summary": "Aucune réponse JSON reçue depuis n8n. Veuillez vérifier le workflow (mode de réponse, Respond to Webhook).",
            "score": 0,
            "user_info": {
                "name": "",
                "title": "",
                "yearsOfExperience": "0",
                "contact": {"email": "", "phone": "", "linkedin": "", "address": ""},
                "profile": "",
                "education": [],
                "languages": [],
                "certificates": [],
                "skills": [],
                "strong_points": [],
                "weak_points": [],
                "scores": {}
            },
            "skills_titles": "",
            "candidate_id": None,
            "current_user": current_user,
            "detailed_analysis": {
                "success": False,
                "categorie_scores": {},
                "good_points": [],
                "weak_points": [],
                "improvements": []
            },
            "job_data": job_data  # Include job data in template
        })

    n8n_data = first_item_if_list(n8n_data)
    if not isinstance(n8n_data, dict):
        n8n_data = {}

    summary: str = n8n_data.get("summary", "") or ""
    user_info: Dict[str, Any] = {
        "name": n8n_data.get("name", "") or "",
        "title": n8n_data.get("title", "") or "",
        "yearsOfExperience": n8n_data.get("yearsOfExperience", "0") or "0",
        "contact": n8n_data.get("contact", {}) or {"email": "", "phone": "", "linkedin": "", "address": ""},
        "profile": n8n_data.get("profile", "") or "",
        "education": n8n_data.get("education", []) or [],
        "languages": n8n_data.get("languages", []) or [],
        "certificates": n8n_data.get("certificates", []) or [],
        "skills": n8n_data.get("skills", []) or [],
        "strong_points": n8n_data.get("strong_points", []) or [],
        "weak_points": n8n_data.get("weak_points", []) or [],
        "scores": n8n_data.get("scores", {}) or {},
        # Accept both key_improvements and improvements keys from n8n
        "key_improvements": n8n_data.get("key_improvements", n8n_data.get("improvements", [])) or [],
    }

    scores_map = user_info.get("scores", {}) or {}
    overall_score = compute_overall_score_from_categories(scores_map, job_data)

    skills_list: List[str] = user_info.get("skills", []) or []
    cleaned_skills = [(s.split(":")[0] if isinstance(s, str) else str(s)) for s in skills_list]
    skills_titles_str = ", ".join(cleaned_skills)

    # Persist candidate (link to user if present)
    candidate_id = insert_candidate_data(user_info, summary, current_user.id if current_user else None)

    detailed_analysis = {
        "success": True,
        "categorie_scores": scores_map,
        "good_points": user_info.get("strong_points", []),
        "weak_points": user_info.get("weak_points", []),
        "improvements": normalize_improvements(user_info.get("key_improvements", [])),
        "job_match_analysis": generate_job_match_analysis(user_info, job_data) if job_data else None
    }

    # Render the results with detailed analysis data embedded
    return templates.TemplateResponse("client-dep/result.html", {
        "request": request,
        "filename": filetoscan.filename,
        "pdf_text": "",
        "images_text": "",
        "summary": summary,
        "score": overall_score,
        "user_info": user_info,
        "skills_titles": skills_titles_str,
        "candidate_id": candidate_id,
        "current_user": current_user,
        "detailed_analysis": detailed_analysis,
        "job_data": job_data  # Include job data in template
    })


def generate_job_match_analysis(user_info: Dict[str, Any], job_data: List[Dict]) -> Dict[str, Any]:
    """
    Generate job-specific matching analysis
    """
    if not job_data:
        return {}
    
    user_skills = set(skill.lower() for skill in user_info.get("skills", []))
    
    job_matches = []
    for job in job_data:
        job_skills = set(skill.lower() for skill in job.get("skills", []))
        
        # Calculate skill match percentage
        if job_skills:
            matching_skills = user_skills.intersection(job_skills)
            match_percentage = (len(matching_skills) / len(job_skills)) * 100
        else:
            match_percentage = 0
        
        job_matches.append({
            "job_title": job.get("title", ""),
            "company": job.get("company", ""),
            "match_percentage": round(match_percentage, 1),
            "matching_skills": list(user_skills.intersection(job_skills)),
            "missing_skills": list(job_skills - user_skills),
            "requirements_summary": job.get("requirements", "")[:200] + "..." if len(job.get("requirements", "")) > 200 else job.get("requirements", "")
        })
    
    # Sort by match percentage
    job_matches.sort(key=lambda x: x["match_percentage"], reverse=True)
    
    return {
        "total_jobs_analyzed": len(job_data),
        "best_match": job_matches[0] if job_matches else None,
        "job_matches": job_matches,
        "average_match": round(sum(job["match_percentage"] for job in job_matches) / len(job_matches), 1) if job_matches else 0
    }
