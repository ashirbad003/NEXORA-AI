from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.phase8_intelligence import GitHubProfileCache
from backend.app.schemas.phase8_intelligence import (
    GitHubProfileResponse, RepositoryHealth
)

class GitHubIntelligenceService:

    @staticmethod
    async def scan_and_cache_profile(
        session: AsyncSession, student_id: str, github_username: str
    ) -> GitHubProfileCache:
        """
        Scans and analyzes GitHub profile metrics (FEAT-201 to FEAT-216).
        Simulates deterministic offline scan without paid third-party dependencies.
        """
        # Normalize username
        username = github_username.strip().lstrip("@")
        
        # Calculate simulated repositories and metrics based on username hash
        seed = sum(ord(c) for c in username)
        repo_count = (seed % 15) + 3  # 3 to 18 repos

        mock_repos: List[Dict[str, Any]] = [
            {
                "name": f"{username}-distributed-systems",
                "description": "High performance async microservice pipeline with PostgreSQL and Docker.",
                "primary_language": "Python",
                "has_readme": True,
                "has_license": True,
                "stars_count": (seed % 20) + 2,
                "forks_count": (seed % 5),
                "open_issues_count": 1,
                "health_score": 92.0,
                "recommendations": ["Great README documentation.", "Include architecture diagram."]
            },
            {
                "name": f"nextjs-interactive-portfolio",
                "description": "Full-stack modern developer portfolio built with React, Next.js, and Tailwind CSS.",
                "primary_language": "TypeScript",
                "has_readme": True,
                "has_license": True,
                "stars_count": (seed % 10) + 1,
                "forks_count": 0,
                "open_issues_count": 0,
                "health_score": 88.0,
                "recommendations": ["Add Lighthouse CI test workflow."]
            },
            {
                "name": f"algo-arena-solutions",
                "description": "Competitive programming algorithms in C++ and Python.",
                "primary_language": "C++",
                "has_readme": False,
                "has_license": False,
                "stars_count": 1,
                "forks_count": 0,
                "open_issues_count": 0,
                "health_score": 60.0,
                "recommendations": ["Missing README.md description.", "Add MIT or Apache-2.0 License."]
            }
        ]

        languages_dist = {
            "Python": 45.0,
            "TypeScript": 35.0,
            "C++": 15.0,
            "Shell": 5.0
        }

        # Calculate portfolio score (FEAT-212)
        avg_health = sum(r["health_score"] for r in mock_repos) / len(mock_repos)
        readme_bonus = 10.0 if all(r["has_readme"] for r in mock_repos[:2]) else 0.0
        portfolio_score = round(min(100.0, (avg_health * 0.9) + readme_bonus), 1)

        recommendations = [
            "Pin your top two full-stack repositories on your GitHub profile overview.",
            "Ensure all repositories contain a standard open-source LICENSE and descriptive README.",
            "Maintain an active commit cadence across your core backend projects."
        ]

        # Check existing cache
        stmt = select(GitHubProfileCache).where(GitHubProfileCache.student_id == student_id)
        res = await session.execute(stmt)
        cache = res.scalar_one_or_none()

        if cache:
            cache.github_username = username
            cache.portfolio_score = portfolio_score
            cache.public_repos_count = repo_count
            cache.languages_distribution = languages_dist
            cache.repository_health_metrics = mock_repos
            cache.recommendations = recommendations
            cache.last_scanned_at = datetime.utcnow()
        else:
            cache = GitHubProfileCache(
                student_id=student_id,
                github_username=username,
                portfolio_score=portfolio_score,
                public_repos_count=repo_count,
                languages_distribution=languages_dist,
                repository_health_metrics=mock_repos,
                recommendations=recommendations,
                last_scanned_at=datetime.utcnow()
            )
            session.add(cache)

        await session.commit()
        await session.refresh(cache)
        return cache

    @staticmethod
    async def get_cached_profile(session: AsyncSession, student_id: str) -> GitHubProfileCache:
        stmt = select(GitHubProfileCache).where(GitHubProfileCache.student_id == student_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()
