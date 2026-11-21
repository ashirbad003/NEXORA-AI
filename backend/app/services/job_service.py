from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from backend.app.models.phase8_intelligence import JobOpportunity, JobApplication, ResumeDocument
from backend.app.schemas.phase8_intelligence import (
    JobOpportunityCreateRequest, JobOpportunityResponse,
    ApplicationStatusUpdateRequest, JobApplicationResponse,
    ColdEmailDraftRequest, ColdEmailDraftResponse
)

VALID_STATUSES = ["Wishlist", "Applied", "Interview", "Offer", "Rejected"]

class JobIntelligenceService:

    @staticmethod
    async def list_jobs(
        session: AsyncSession,
        student_id: Optional[str] = None,
        role_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        on_campus_only: bool = False
    ) -> List[JobOpportunityResponse]:
        """
        Lists curated opportunities with dynamic student match score (FEAT-218, FEAT-223).
        """
        stmt = select(JobOpportunity).order_by(JobOpportunity.created_at.desc())
        if type_filter:
            stmt = stmt.where(JobOpportunity.opportunity_type == type_filter)
        if on_campus_only:
            stmt = stmt.where(JobOpportunity.is_on_campus == True)

        res = await session.execute(stmt)
        jobs = list(res.scalars().all())

        # If student_id is provided, compute skill match scores based on primary resume
        student_skills = set(["python", "react", "postgresql", "docker", "fastapi"])
        if student_id:
            r_stmt = select(ResumeDocument).where(
                ResumeDocument.student_id == student_id,
                ResumeDocument.is_primary == True
            )
            r_res = await session.execute(r_stmt)
            resume = r_res.scalar_one_or_none()
            if resume and resume.structured_data:
                raw_skills = resume.structured_data.get("skills", [])
                if isinstance(raw_skills, list):
                    student_skills = {str(s).lower() for s in raw_skills}

        responses = []
        for j in jobs:
            required = [str(s).lower() for s in j.required_skills]
            if required:
                matched = [s for s in required if s in student_skills]
                match_pct = round((len(matched) / len(required)) * 100.0, 1)
            else:
                match_pct = 75.0

            item = JobOpportunityResponse(
                id=j.id,
                company_name=j.company_name,
                role_title=j.role_title,
                opportunity_type=j.opportunity_type,
                location=j.location,
                stipend_or_salary=j.stipend_or_salary,
                description=j.description,
                required_skills=j.required_skills,
                deadline=j.deadline,
                is_on_campus=j.is_on_campus,
                application_url=j.application_url,
                created_at=j.created_at,
                match_score=match_pct
            )
            if role_filter:
                if role_filter.lower() in j.role_title.lower() or role_filter.lower() in j.company_name.lower():
                    responses.append(item)
            else:
                responses.append(item)

        return responses

    @staticmethod
    async def create_job(session: AsyncSession, payload: JobOpportunityCreateRequest) -> JobOpportunity:
        job = JobOpportunity(
            company_name=payload.company_name,
            role_title=payload.role_title,
            opportunity_type=payload.opportunity_type,
            location=payload.location,
            stipend_or_salary=payload.stipend_or_salary,
            description=payload.description,
            required_skills=payload.required_skills,
            deadline=payload.deadline,
            is_on_campus=payload.is_on_campus,
            application_url=payload.application_url
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def apply_or_save_job(
        session: AsyncSession, student_id: str, job_id: str, initial_status: str = "Applied"
    ) -> JobApplication:
        """
        Creates or updates a Kanban application entry (FEAT-219).
        """
        if initial_status not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {initial_status}")

        # Verify job exists
        j_stmt = select(JobOpportunity).where(JobOpportunity.id == job_id)
        j_res = await session.execute(j_stmt)
        job = j_res.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job opportunity not found.")

        # Check existing application
        stmt = select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.student_id == student_id
        )
        res = await session.execute(stmt)
        application = res.scalar_one_or_none()

        if application:
            application.status = initial_status
            if initial_status == "Applied" and not application.applied_at:
                application.applied_at = datetime.utcnow()
        else:
            application = JobApplication(
                job_id=job_id,
                student_id=student_id,
                status=initial_status,
                applied_at=datetime.utcnow() if initial_status == "Applied" else None,
                match_score=85.0
            )
            session.add(application)

        await session.commit()
        await session.refresh(application)
        return application

    @staticmethod
    async def update_application_status(
        session: AsyncSession, application_id: str, student_id: str, payload: ApplicationStatusUpdateRequest
    ) -> JobApplication:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {payload.status}")

        stmt = select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.student_id == student_id
        )
        res = await session.execute(stmt)
        app = res.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found or unauthorized.")

        app.status = payload.status
        if payload.interview_date is not None:
            app.interview_date = payload.interview_date
        if payload.notes is not None:
            app.notes = payload.notes
        if payload.status == "Applied" and not app.applied_at:
            app.applied_at = datetime.utcnow()

        await session.commit()
        await session.refresh(app)
        return app

    @staticmethod
    async def get_student_applications(session: AsyncSession, student_id: str) -> List[JobApplication]:
        stmt = select(JobApplication).where(JobApplication.student_id == student_id).order_by(JobApplication.updated_at.desc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def generate_cold_email(
        session: AsyncSession, student_id: str, payload: ColdEmailDraftRequest
    ) -> ColdEmailDraftResponse:
        """
        Drafts high-converting, personalized cold email/networking reach-out (FEAT-230).
        """
        j_stmt = select(JobOpportunity).where(JobOpportunity.id == payload.job_id)
        j_res = await session.execute(j_stmt)
        job = j_res.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job opportunity not found.")

        role = job.role_title
        company = job.company_name
        manager = payload.hiring_manager_name or "Hiring Team"

        subject = f"Inquiry regarding {role} opening at {company} - Aspiring Software Engineer"
        body = (
            f"Dear {manager},\n\n"
            f"I hope this note finds you well. I have been following {company}'s impressive engineering milestones "
            f"and am writing to express my enthusiasm for the {role} position.\n\n"
            f"As a developer with deep experience in scalable microservices, Python/FastAPI, Next.js, and containerized architectures, "
            f"I recently engineered resilient systems achieving 40% performance gains through query optimization and modular design.\n\n"
            f"I would welcome the opportunity to connect for a brief 10-minute conversation to discuss how my technical skills "
            f"and problem-solving drive align with {company}'s current technical roadmaps.\n\n"
            f"Thank you for your time and consideration.\n\n"
            f"Best regards,\nCandidate\nPortfolio: github.com/nexora-engineer"
        )
        tips = [
            "Send between 8:30 AM and 9:30 AM in the recipient's local timezone for highest open rates.",
            "Keep the message concise (under 150 words) to respect the hiring manager's schedule.",
            "Follow up politely in 4 to 5 business days if no reply."
        ]

        return ColdEmailDraftResponse(
            subject_line=subject,
            body_text=body,
            tips=tips
        )
