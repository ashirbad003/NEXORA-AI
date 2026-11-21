import re
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from backend.app.models.phase8_intelligence import ResumeDocument
from backend.app.schemas.phase8_intelligence import (
    ResumeCreateRequest, ResumeUpdateRequest, ATSAnalysisResponse,
    BulletOptimizationResponse
)

STRONG_ACTION_VERBS = [
    "architected", "developed", "spearheaded", "engineered", "implemented",
    "optimized", "automated", "designed", "accelerated", "deployed",
    "refactored", "orchestrated", "reduced", "increased", "maximized"
]

COMMON_TECH_KEYWORDS = [
    "python", "fastapi", "react", "next.js", "typescript", "javascript",
    "postgresql", "docker", "redis", "rest", "api", "git", "ci/cd",
    "sql", "tailwind", "aws", "microservices", "unit testing", "system design"
]

class ResumeIntelligenceService:

    @staticmethod
    def calculate_completeness_and_ats(
        structured_data: Dict[str, Any],
        raw_content: str = ""
    ) -> Tuple[float, float, List[str], List[str], List[str], List[str], str, str]:
        """
        Evaluates completeness (FEAT-197) and ATS readiness score (FEAT-182).
        Returns:
            completeness_score, ats_score, matches, missing, formatting_issues, suggestions, metric_feedback, verdict
        """
        completeness_points = 0.0
        formatting_issues = []
        action_suggestions = []

        # Check sections
        has_contact = bool(structured_data.get("contact") or structured_data.get("email") or "@" in raw_content)
        has_education = bool(structured_data.get("education"))
        has_skills = bool(structured_data.get("skills"))
        has_experience = bool(structured_data.get("experience") or structured_data.get("projects"))

        if has_contact:
            completeness_points += 25.0
        else:
            formatting_issues.append("Missing or incomplete contact details (email, phone, LinkedIn/GitHub).")

        if has_education:
            completeness_points += 25.0
        else:
            formatting_issues.append("Missing education section or degree information.")

        if has_skills:
            completeness_points += 25.0
        else:
            formatting_issues.append("Missing categorized technical skills section.")

        if has_experience:
            completeness_points += 25.0
        else:
            formatting_issues.append("Missing projects or professional experience details.")

        completeness_score = min(100.0, completeness_points)

        # Keyword and text analysis for ATS Score
        full_text = (raw_content + " " + str(structured_data)).lower()
        matched_keywords = []
        missing_keywords = []

        for kw in COMMON_TECH_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", full_text):
                matched_keywords.append(kw)
            else:
                missing_keywords.append(kw)

        keyword_score = (len(matched_keywords) / max(1, len(COMMON_TECH_KEYWORDS))) * 60.0

        # Action verbs check
        verb_count = sum(1 for verb in STRONG_ACTION_VERBS if re.search(rf"\b{verb}\b", full_text))
        action_verb_score = min(20.0, verb_count * 5.0)
        if verb_count < 3:
            action_suggestions.append("Incorporate more active impact verbs such as 'architected', 'spearheaded', or 'automated'.")

        # Metrics & numbers check (FEAT-184)
        has_metrics = bool(re.search(r"(\b\d+(\.\d+)?(%|x|k|ms|s|users|rps)?\b|\b\d+\b)", full_text))
        metric_score = 20.0 if has_metrics else 5.0
        metric_feedback = (
            "Great job quantifying achievements with metrics (%, latency, users)."
            if has_metrics
            else "Quantify your achievements using specific numerical metrics (e.g., 'reduced latency by 40%', 'served 10k users')."
        )

        ats_score = round(keyword_score + action_verb_score + metric_score, 1)
        ats_score = min(100.0, max(10.0, ats_score))

        if ats_score >= 80:
            verdict = "Excellent ATS Match. High probability of clearing automated parsing systems."
        elif ats_score >= 60:
            verdict = "Moderate ATS Match. Strong foundation; improve keyword density and action metrics."
        else:
            verdict = "Needs Optimization. Add industry keywords, active verbs, and quantifiable metrics."

        return (
            completeness_score, ats_score, matched_keywords, missing_keywords[:8],
            formatting_issues, action_suggestions, metric_feedback, verdict
        )

    @staticmethod
    async def create_resume(session: AsyncSession, student_id: str, payload: ResumeCreateRequest) -> ResumeDocument:
        completeness, ats, _, _, _, _, _, _ = ResumeIntelligenceService.calculate_completeness_and_ats(
            payload.structured_data, payload.raw_content or ""
        )
        # If set as primary, unset existing primary resumes
        if payload.is_primary:
            stmt = select(ResumeDocument).where(ResumeDocument.student_id == student_id, ResumeDocument.is_primary == True)
            res = await session.execute(stmt)
            for r in res.scalars().all():
                r.is_primary = False

        resume = ResumeDocument(
            student_id=student_id,
            title=payload.title,
            template_type=payload.template_type,
            raw_content=payload.raw_content,
            structured_data=payload.structured_data,
            ats_score=ats,
            completeness_score=completeness,
            is_primary=payload.is_primary
        )
        session.add(resume)
        await session.commit()
        await session.refresh(resume)
        return resume

    @staticmethod
    async def get_resumes_for_student(session: AsyncSession, student_id: str) -> List[ResumeDocument]:
        stmt = select(ResumeDocument).where(ResumeDocument.student_id == student_id).order_by(ResumeDocument.created_at.desc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_resume_by_id(session: AsyncSession, resume_id: str, student_id: str) -> ResumeDocument:
        stmt = select(ResumeDocument).where(ResumeDocument.id == resume_id, ResumeDocument.student_id == student_id)
        res = await session.execute(stmt)
        resume = res.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found or unauthorized access.")
        return resume

    @staticmethod
    async def update_resume(
        session: AsyncSession, resume_id: str, student_id: str, payload: ResumeUpdateRequest
    ) -> ResumeDocument:
        resume = await ResumeIntelligenceService.get_resume_by_id(session, resume_id, student_id)
        
        if payload.title is not None:
            resume.title = payload.title
        if payload.template_type is not None:
            resume.template_type = payload.template_type
        if payload.raw_content is not None:
            resume.raw_content = payload.raw_content
        if payload.structured_data is not None:
            resume.structured_data = payload.structured_data
        if payload.is_primary is not None and payload.is_primary:
            stmt = select(ResumeDocument).where(ResumeDocument.student_id == student_id, ResumeDocument.is_primary == True)
            res = await session.execute(stmt)
            for r in res.scalars().all():
                r.is_primary = False
            resume.is_primary = True

        completeness, ats, _, _, _, _, _, _ = ResumeIntelligenceService.calculate_completeness_and_ats(
            resume.structured_data, resume.raw_content or ""
        )
        resume.completeness_score = completeness
        resume.ats_score = ats

        await session.commit()
        await session.refresh(resume)
        return resume

    @staticmethod
    async def analyze_resume_ats(session: AsyncSession, resume_id: str, student_id: str) -> ATSAnalysisResponse:
        resume = await ResumeIntelligenceService.get_resume_by_id(session, resume_id, student_id)
        completeness, ats, matches, missing, issues, suggestions, metric_fb, verdict = (
            ResumeIntelligenceService.calculate_completeness_and_ats(resume.structured_data, resume.raw_content or "")
        )
        return ATSAnalysisResponse(
            resume_id=resume.id,
            ats_score=ats,
            completeness_score=completeness,
            keyword_matches=matches,
            missing_critical_keywords=missing,
            formatting_issues=issues,
            action_verb_suggestions=suggestions,
            quantitative_metric_feedback=metric_fb,
            summary_verdict=verdict
        )

    @staticmethod
    def optimize_bullet_point(bullet: str, role_target: str = "Software Engineer") -> BulletOptimizationResponse:
        """
        Enhances weak bullet points using STAR methodology and impact verbs (FEAT-183).
        """
        cleaned = bullet.strip().rstrip(".")
        first_word = cleaned.split()[0].lower() if cleaned else ""

        if first_word in ["worked", "did", "helped", "made", "used", "created", "was"]:
            optimized = f"Architected and deployed {cleaned[len(first_word):].strip()}, improving operational throughput by 35% and enhancing system reliability."
            verb_used = "Architected"
            metric_added = True
            explanation = "Replaced generic passive verb with high-impact action verb 'Architected' and added quantifiable throughput metrics."
        else:
            optimized = f"Spearheaded {cleaned}, boosting delivery velocity by 25% and ensuring full production grade test coverage."
            verb_used = "Spearheaded"
            metric_added = True
            explanation = "Elevated ownership tone with 'Spearheaded' and framed output with engineering quality metrics."

        return BulletOptimizationResponse(
            original=bullet,
            optimized=optimized,
            action_verb_used=verb_used,
            metric_added=metric_added,
            explanation=explanation
        )

    @staticmethod
    def generate_latex_resume(resume: ResumeDocument) -> str:
        """
        Generates standard Overleaf/LaTeX compileable ATS-optimized resume format (FEAT-186).
        """
        data = resume.structured_data or {}
        contact = data.get("contact", {})
        skills = data.get("skills", ["Python", "FastAPI", "React", "PostgreSQL", "Docker"])
        
        name = contact.get("name", "NEXORA Candidate")
        email = contact.get("email", "candidate@nexora.ai")
        phone = contact.get("phone", "+91 9876543210")
        github = contact.get("github", "github.com/nexora-engineer")

        skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)

        latex_template = f"""\\documentclass[letterpaper,10pt]{{article}}
\\usepackage[margin=0.75in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{titlesec}}
\\titleformat{{\\section}}{{\\large\\bfseries\\uppercase}}{{}}{{0em}}{{}}[\\titlerule]

\\begin{{document}}

\\begin{{center}}
    \\textbf{{\\Huge {name}}} \\\\ \\vspace{{4pt}}
    \\small {phone} $|$ \\href{{mailto:{email}}}{{{email}}} $|$ \\href{{https://{github}}}{{{github}}}
\\end{{center}}

\\section{{Technical Skills}}
\\textbf{{Languages \\& Technologies:}} {skills_str}

\\section{{Experience \\& Engineering Projects}}
\\textbf{{{resume.title}}} \\hfill \\textit{{Production Deployment}} \\\\
\\begin{{itemize}}
    \\item Designed and implemented scalable asynchronous microservices adhering to strict security requirements.
    \\item Reduced latency by 42\\% through query indexing and strategic caching layers.
    \\item Authored full test coverage ensuring robust CI/CD automated validation.
\\end{{itemize}}

\\section{{Education}}
\\textbf{{Bachelor of Technology in Computer Science}} \\hfill \\textit{{Graduated First Class}} \\\\
Core Coursework: Data Structures, Algorithms, Distributed Systems, Database Management.

\\end{{document}}
"""
        return latex_template
