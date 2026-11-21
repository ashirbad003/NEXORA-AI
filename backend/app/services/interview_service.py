import re
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models.interview import MockInterviewSession, MockInterviewTurn
from backend.app.schemas.interview import (
    MockInterviewStartSchema, MockInterviewRespondSchema
)
from ai_engine.providers.factory import get_ai_provider

class InterviewService:
    # Seed Question Catalog (FEAT-119: Behavioral & Technical Question Bank)
    QUESTION_BANK = {
        "Technical": [
            ("Explain the difference between optimistic and pessimistic locking in relational databases.", "Database Systems"),
            ("How would you design a distributed cache like Redis to handle high-concurrency read replicas?", "System Design"),
            ("Walk me through the time and space complexity of Quicksort versus Mergesort in worst-case scenarios.", "Data Structures & Algorithms"),
            ("What are Goroutines or Python asyncio tasks under the hood, and how do they avoid OS thread context-switching overhead?", "Concurrency"),
            ("How does HTTPS establish a secure session between client and server? Describe the TLS 1.3 handshake.", "Networking & Security")
        ],
        "HR & Behavioral": [
            ("Tell me about a time when you faced a severe project deadline conflict with conflicting requirements from stakeholders. How did you resolve it?", "Conflict Resolution"),
            ("Describe a technical failure or bug you introduced into production. What was the impact and what safeguards did you put in place afterward?", "Accountability"),
            ("Give an example of a time you disagreed with a senior team member's architectural decision. How did you approach the conversation?", "Leadership & Influence"),
            ("Walk me through a project where you had to learn an unfamiliar technology stack in under a week. How did you organize your learning?", "Agility & Adaptability")
        ],
        "System Design": [
            ("Design a globally distributed URL shortening service like TinyURL handling 100M active writes per day.", "Distributed Systems"),
            ("Design a real-time notification service supporting web push, SMS, and email with strict deduplication.", "Event-Driven Architecture"),
            ("How would you architect a live collaborative code editor with conflict-free replicated data types (CRDTs)?", "Real-Time Collaboration")
        ]
    }

    COMPANY_PERSONA_PROMPTS = {
        "Google": "You are a Senior Principal Engineer at Google. You value clean algorithmic reasoning, time-space trade-offs, scalability, and precise communication.",
        "Amazon": "You are an Amazon Bar Raiser. You rigorously probe for Amazon Leadership Principles (Customer Obsession, Ownership, Bias for Action, Deliver Results).",
        "TCS": "You are a Technical Lead at TCS Digital. You evaluate fundamental CS concepts, OOP design principles, SQL queries, and solid engineering discipline.",
        "Microsoft": "You are a Principal Software Architect at Microsoft. You value design patterns, maintainability, robust cloud integration, and defensive coding."
    }

    @staticmethod
    async def start_session(
        db: AsyncSession, student_id: str, data: MockInterviewStartSchema
    ) -> Dict[str, Any]:
        # Create session (FEAT-103)
        session = MockInterviewSession(
            student_id=student_id,
            role_target=data.role_target,
            interview_type=data.interview_type,
            company_persona=data.company_persona,
            status="in_progress",
            total_turns=1
        )
        db.add(session)
        await db.flush()

        # Pick initial question based on category
        questions = InterviewService.QUESTION_BANK.get(data.interview_type, InterviewService.QUESTION_BANK["Technical"])
        first_q_text, category = questions[0]

        turn = MockInterviewTurn(
            session_id=session.id,
            turn_index=1,
            question_text=first_q_text,
            question_category=category,
            is_followup=False
        )
        db.add(turn)
        await db.commit()
        await db.refresh(session)
        await db.refresh(turn)

        return {
            "session_id": session.id,
            "role_target": session.role_target,
            "interview_type": session.interview_type,
            "company_persona": session.company_persona,
            "status": session.status,
            "current_turn": {
                "turn_index": turn.turn_index,
                "question_text": turn.question_text,
                "question_category": turn.question_category,
                "is_followup": turn.is_followup
            }
        }

    @staticmethod
    async def process_response(
        db: AsyncSession, session_id: str, student_id: str, data: MockInterviewRespondSchema
    ) -> Dict[str, Any]:
        stmt = select(MockInterviewSession).where(
            and_(MockInterviewSession.id == session_id, MockInterviewSession.student_id == student_id)
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
        if session.status != "in_progress":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interview session is already completed")

        # Fetch latest turn
        turn_stmt = select(MockInterviewTurn).where(
            MockInterviewTurn.session_id == session.id
        ).order_by(MockInterviewTurn.turn_index.desc())
        turn_res = await db.execute(turn_stmt)
        current_turn = turn_res.scalars().first()
        if not current_turn:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active turn found")

        # Store response and whiteboard if provided (FEAT-120)
        current_turn.student_response_text = data.response_text
        current_turn.audio_duration_seconds = data.audio_duration_seconds
        if data.whiteboard_snapshot:
            session.whiteboard_state = data.whiteboard_snapshot

        # FEAT-118: Timer & Pacing Coach
        words = len(data.response_text.split())
        if words < 15:
            current_turn.pacing_verdict = "Too Brief"
        elif words > 250:
            current_turn.pacing_verdict = "Rambling"
        else:
            current_turn.pacing_verdict = "Optimal"

        # AI Evaluation for turn
        provider = get_ai_provider()
        prompt = (
            f"Interviewer Persona: {session.company_persona}\n"
            f"Question: {current_turn.question_text}\n"
            f"Candidate Response: {data.response_text}\n"
            "Evaluate this candidate response concisely. If there are missing details, note them. Provide a 2-sentence feedback."
        )
        ai_resp = await provider.generate_response(prompt=prompt)
        current_turn.interviewer_feedback = ai_resp.content

        # Decide whether to ask dynamic follow-up (FEAT-110) or next question
        session.total_turns += 1
        is_final_turn = session.total_turns >= 4  # 4 turns per session

        if is_final_turn:
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            await db.commit()
            return await InterviewService.evaluate_and_conclude_session(db, session_id, student_id)

        # Generate follow-up or next question
        catalog = InterviewService.QUESTION_BANK.get(session.interview_type, InterviewService.QUESTION_BANK["Technical"])
        if session.total_turns % 2 == 0:
            # FEAT-110: Dynamic Contextual Follow-up Question
            followup_prompt = (
                f"Candidate answered: '{data.response_text}' to '{current_turn.question_text}'.\n"
                "As an interviewer, ask one intelligent follow-up question digging deeper into their response."
            )
            followup_resp = await provider.generate_response(prompt=followup_prompt)
            next_q_text = followup_resp.content.strip()
            is_followup = True
            cat = current_turn.question_category
        else:
            q_idx = min(session.total_turns // 2, len(catalog) - 1)
            next_q_text, cat = catalog[q_idx]
            is_followup = False

        next_turn = MockInterviewTurn(
            session_id=session.id,
            turn_index=session.total_turns,
            question_text=next_q_text,
            question_category=cat,
            is_followup=is_followup
        )
        db.add(next_turn)
        await db.commit()

        return {
            "session_id": session.id,
            "status": "in_progress",
            "previous_feedback": current_turn.interviewer_feedback,
            "pacing_verdict": current_turn.pacing_verdict,
            "next_turn": {
                "turn_index": next_turn.turn_index,
                "question_text": next_turn.question_text,
                "question_category": next_turn.question_category,
                "is_followup": next_turn.is_followup
            }
        }

    @staticmethod
    async def evaluate_and_conclude_session(
        db: AsyncSession, session_id: str, student_id: str
    ) -> Dict[str, Any]:
        stmt = select(MockInterviewSession).where(
            and_(MockInterviewSession.id == session_id, MockInterviewSession.student_id == student_id)
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")

        # Fetch all turns
        t_stmt = select(MockInterviewTurn).where(
            MockInterviewTurn.session_id == session.id
        ).order_by(MockInterviewTurn.turn_index.asc())
        t_res = await db.execute(t_stmt)
        turns = t_res.scalars().all()

        # Transcript compilation (FEAT-114: Mock Interview History & Playback)
        transcript = []
        full_text = ""
        for t in turns:
            resp_text = t.student_response_text or "(No response)"
            transcript.append({
                "turn": t.turn_index,
                "question": t.question_text,
                "response": resp_text,
                "pacing": t.pacing_verdict,
                "feedback": t.interviewer_feedback or "Good overview provided."
            })
            full_text += f" Q: {t.question_text} A: {resp_text}"

        # FEAT-112: Communication Tone & Clarity Analyzer + Filler Word Detector
        filler_patterns = [r"\bum\b", r"\buh\b", r"\blike\b", r"\byou know\b", r"\bactually\b", r"\bbasically\b"]
        total_fillers = 0
        for pat in filler_patterns:
            total_fillers += len(re.findall(pat, full_text.lower()))

        tone_clarity = max(40.0, min(95.0, 95.0 - (total_fillers * 2.5)))
        session.filler_word_count = total_fillers
        session.tone_clarity_score = round(tone_clarity, 1)

        # FEAT-111: STAR Methodology Scorer (Situation, Task, Action, Result)
        has_situation = any(w in full_text.lower() for w in ["when", "project", "situation", "company", "client", "problem"])
        has_task = any(w in full_text.lower() for w in ["task", "goal", "responsibility", "needed", "requirement", "target"])
        has_action = any(w in full_text.lower() for w in ["implemented", "designed", "created", "built", "optimized", "refactored"])
        has_result = any(w in full_text.lower() for w in ["result", "reduced", "increased", "latency", "percent", "outcome", "delivered"])

        session.star_situation_score = 4.2 if has_situation else 2.5
        session.star_task_score = 4.0 if has_task else 2.0
        session.star_action_score = 4.5 if has_action else 3.0
        session.star_result_score = 4.1 if has_result else 2.2

        # FEAT-113: Technical Accuracy Score
        tech_words = ["complexity", "cache", "database", "distributed", "concurrency", "thread", "async", "lock", "scale", "memory"]
        tech_count = sum(1 for w in tech_words if w in full_text.lower())
        tech_score = max(50.0, min(98.0, 60.0 + (tech_count * 4.0)))
        session.technical_accuracy_score = round(tech_score, 1)

        # FEAT-117: Holistic Interview Readiness Scorecard (0-100)
        overall = (session.technical_accuracy_score * 0.45) + (session.tone_clarity_score * 0.30) + (
            ((session.star_situation_score + session.star_task_score + session.star_action_score + session.star_result_score) / 20.0 * 100) * 0.25
        )
        session.overall_score = round(overall, 1)

        # FEAT-115: Mistake & Blunder Analysis Card
        blunders = []
        if total_fillers > 5:
            blunders.append(f"High filler-word frequency detected ({total_fillers} instances). Practice speaking in deliberate pauses.")
        if not has_result:
            blunders.append("Omitted quantifiable metrics in answer outcomes (STAR 'Result' was unmeasured).")
        if tech_count < 3:
            blunders.append("Technical explanations lacked depth on underlying systems trade-offs and complexity.")

        # FEAT-116: Actionable Improvement Plan Generator
        improvement_plan = {
            "focus_areas": [
                "Practice quantifying project impact with percentages and latencies.",
                "Reinforce behavioral stories using the STAR structural template.",
                "Deepen distributed systems trade-offs (consistency vs availability)."
            ],
            "recommended_drills": [
                "Complete 2 System Design Whiteboard mock scenarios.",
                "Review Operating Systems Concurrency flashcards in Module H.",
                "Record 1 timed 3-minute STAR story without verbal crutches."
            ]
        }
        session.improvement_plan = improvement_plan
        await db.commit()

        return {
            "session_id": session.id,
            "role_target": session.role_target,
            "overall_readiness_score": session.overall_score,
            "star_scores": {
                "situation": session.star_situation_score,
                "task": session.star_task_score,
                "action": session.star_action_score,
                "result": session.star_result_score
            },
            "tone_clarity_score": session.tone_clarity_score,
            "filler_word_count": session.filler_word_count,
            "technical_accuracy_score": session.technical_accuracy_score,
            "pacing_verdict": turns[-1].pacing_verdict if turns else "Optimal",
            "mistakes_and_blunders": blunders,
            "improvement_plan": improvement_plan,
            "transcript": transcript
        }
