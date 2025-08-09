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


def compute_overall_score_from_categories(scores: Dict[str, Any]) -> int:
    numeric_values: List[float] = []
    for v in scores.values():
        try:
            numeric_values.append(float(v))
        except Exception:
            continue
    if not numeric_values:
        return 0
    return int(round(sum(numeric_values) / len(numeric_values)))


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
    timeout_seconds: int = 180,
) -> Optional[dict]:
    """
    Post to n8n webhook and wait for JSON:
    - Adds wait=true to query string
    - Long timeout
    - Tries both test and prod paths
    """
    wait_url = add_query_params(url, {"wait": "true"})
    alt_wait_url = add_query_params(to_prod_webhook(url), {"wait": "true"})

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for target_url in (wait_url, alt_wait_url):
            try:
                files = {
                    "CV": (file_name, file_bytes, content_type or "application/pdf")
                }
                data = {"selectedProfiles": selected_profiles}
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
    db: Session = Depends(get_db)
):
    """
    Unified route:
    - Forwards the CV to n8n and waits for JSON
    - Builds all data (including detailed analysis) server-side
    - Renders result page with detailed analysis already populated
    """
    current_user = get_current_user(request, db)

    # Save uploaded file
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{filetoscan.filename}"
    file_bytes = await filetoscan.read()
    with open(file_location, "wb") as f:
        f.write(file_bytes)

    # 1) Wait for n8n JSON
    n8n_data = [{"name":"Zied Ameur","title":"Développeur Intégrateur WordPress","yearsOfExperience":"4","contact":{"email":"ziedameur02@gmail.com","phone":"+216 26 925 917","linkedin":"","address":"1145 mhamdia ben arous Tunisie, Rue ibn elmokafaa cité enazeha"},"profile":"","education":[{"institution":"ISI KEF","degree":"Master Professionnel en administration et sécurité des réseaux informatiques","years":"2015-2019"},{"institution":"ISET JENDOUBA","degree":"Licence Appliqué en Développement des Systèmes d’informations","years":"2012-2014"},{"institution":"CIFOP","degree":"Formation PHP7/Symfony4","years":"2020"},{"institution":"CIFOP","degree":"Formation Développement web","years":"2019"}],"languages":["Arabe","Français","Anglais"],"certificates":["Apprenez à créer votre site web avec OpenClassrooms","Introduction à jQuery - OpenClassrooms","Écrivez du JavaScript pour le web – OpenClassrooms","Programmez-en Orienté Objet - OpenClassrooms","HTML5 et CSS3 – OpenClassrooms"],"skills":["HTML5","CSS3","JavaScript","jQuery","Bootstrap","PHP","WordPress","Elementor","Prestashop","Symfony4","MySQL","PostgreSQL","UML","SEO","WordPress plugins configuration","Website optimization","Content management system configuration","Responsive web design","Technical support","User training","ERP MS setup","Problem-solving","Website maintenance"],"strong_points":[],"weak_points":["Lack of hands-on experience with modern frameworks beyond Symfony4","No mention of certifications or formal education in web development","Limited experience with popular content management systems aside from WordPress","No specialization in specific industry applications or roles","Outdated skills in some areas such as basic PHP and frontend technologies","Lack of information on collaborative or team projects","Insufficient details on any leadership or management roles","Missing current and relevant programming methodologies or practices","Absence of soft skills or interpersonal skills highlighted","No evidence of staying updated with recent trends in web development"],"scores":{"Work Experience":80,"Skills & Technical Expertise":90,"Education":70,"Certifications & Training":75,"Soft Skills & Leadership":65,"Overall Structure & Presentation":60},"key_improvements":["Gain hands-on experience with modern frameworks like React.js, Vue.js, or Angular and include them in the CV.","Pursue and obtain relevant certifications in web development or related technologies and add them to the CV to enhance credibility.","Broaden experience by working with a wider range of content management systems like Drupal or Joomla, and list this experience on the CV.","Identify a specific industry or niche such as e-commerce, education, or healthcare, and prepare projects that demonstrate expertise in this area.","Update knowledge on basic PHP and frontend technologies by taking current courses or tutorials, and reflect these in an updated skills list.","Participate in group projects or team collaborations and include specific roles and contributions to demonstrate teamwork skills.","Seek leadership opportunities within projects or organizations and highlight these experiences to showcase management capabilities.","Incorporate current programming methodologies such as Agile, Scrum, or DevOps practices in the CV to show familiarity with modern development processes.","Highlight soft skills such as communication, teamwork, and problem-solving abilities to create a more balanced skill set.","Engage with web development communities or continuous learning platforms to stay updated with the latest trends and technologies, and add recent workshops or webinars attended to the CV."],"summary":"The candidate has a foundational understanding of web development technologies, particularly in HTML, CSS, JavaScript, and Symfony4, which are their strongest points. However, they lack practical experience with modern frameworks and have outdated skills in areas like basic PHP and frontend technologies. There is no formal education or certifications in web development, which raises concerns about their professional credibility. The absence of hands-on experience with various content management systems aside from WordPress and a lack of specialization limit their employability in niche roles. Furthermore, the CV fails to highlight collaborative projects, leadership experience, or soft skills, suggesting a gap in interpersonal capabilities and current industry practices. Overall, while the candidate has the basics, they are not equipped to meet the demands of a rapidly evolving web development landscape."}]
    n8n_data = await post_to_n8n_wait_for_json(
        N8N_WEBHOOK_URL,
        filetoscan.filename,
        file_bytes,
        filetoscan.content_type,
        selectedProfiles,
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
            }
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
    overall_score = compute_overall_score_from_categories(scores_map)

    skills_list: List[str] = user_info.get("skills", []) or []
    cleaned_skills = [(s.split(":")[0] if isinstance(s, str) else str(s)) for s in skills_list]
    skills_titles_str = ", ".join(cleaned_skills)

    # Persist candidate (link to user if present)
    candidate_id = insert_candidate_data(user_info, summary, current_user.id if current_user else None)

    # Build the detailed analysis payload for direct rendering
    detailed_analysis = {
        "success": True,
        "categorie_scores": scores_map,
        "good_points": user_info.get("strong_points", []),
        "weak_points": user_info.get("weak_points", []),
        "improvements": normalize_improvements(user_info.get("key_improvements", [])),
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
        "detailed_analysis": detailed_analysis
    })