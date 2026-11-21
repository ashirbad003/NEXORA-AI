import math
from typing import Dict, Any, List, Set, Tuple

# Standard Industry Role Competency Models (FEAT-012, FEAT-024, FEAT-025)
ROLE_REQUIRED_SKILLS: Dict[str, Dict[str, float]] = {
    "software_engineer": {
        "python": 0.8, "java": 0.8, "c++": 0.7, "dsa": 0.9, "algorithms": 0.9,
        "operating_systems": 0.8, "dbms": 0.8, "sql": 0.8, "git": 0.8,
        "system_design": 0.7, "networks": 0.7
    },
    "fullstack_developer": {
        "javascript": 0.9, "typescript": 0.9, "react": 0.9, "next.js": 0.8,
        "node.js": 0.8, "python": 0.7, "sql": 0.8, "html_css": 0.9,
        "rest_api": 0.9, "git": 0.8, "docker": 0.6
    },
    "data_engineer": {
        "python": 0.9, "sql": 0.9, "dbms": 0.9, "spark": 0.8, "hadoop": 0.7,
        "data_warehousing": 0.8, "etl": 0.9, "git": 0.7, "docker": 0.7
    },
    "devops_engineer": {
        "linux": 0.9, "docker": 0.9, "kubernetes": 0.8, "ci_cd": 0.9,
        "git": 0.8, "python": 0.7, "bash": 0.8, "cloud_aws": 0.8, "terraform": 0.7
    }
}

# CS Knowledge Graph Core Nodes (FEAT-020)
KNOWLEDGE_GRAPH = {
    "arrays": {"category": "data_structures", "difficulty": "Easy", "next_nodes": ["two_pointers", "sliding_window", "hash_tables"]},
    "two_pointers": {"category": "algorithms", "difficulty": "Medium", "next_nodes": ["binary_search", "sorting"]},
    "linked_lists": {"category": "data_structures", "difficulty": "Medium", "next_nodes": ["stacks", "queues", "fast_slow_pointers"]},
    "trees": {"category": "data_structures", "difficulty": "Medium", "next_nodes": ["binary_search_trees", "heap", "trie"]},
    "graphs": {"category": "data_structures", "difficulty": "Hard", "next_nodes": ["bfs", "dfs", "dijkstra", "topological_sort"]},
    "dynamic_programming": {"category": "algorithms", "difficulty": "Hard", "next_nodes": ["memoization", "tabulation", "bitmask_dp"]},
    "operating_systems": {"category": "systems", "difficulty": "Medium", "next_nodes": ["concurrency", "deadlocks", "virtual_memory"]},
    "databases": {"category": "systems", "difficulty": "Medium", "next_nodes": ["indexing", "acid_transactions", "normalization"]}
}

class SkillAnalyticsEngine:
    """
    Computes skill gap vectors (FEAT-012), readiness index (FEAT-016),
    knowledge graph linking (FEAT-020), confidence estimation (FEAT-014),
    and explainability rationales (FEAT-006).
    """

    @staticmethod
    def calculate_skill_gap(user_skills: List[str], target_role: str) -> Dict[str, Any]:
        """
        Calculates semantic gap between user mastered skills and role requirements (FEAT-012).
        """
        role_key = target_role.lower().replace(" ", "_")
        target_skills = ROLE_REQUIRED_SKILLS.get(role_key, ROLE_REQUIRED_SKILLS["software_engineer"])

        user_skill_set = {s.lower().strip() for s in user_skills if s}
        matched_skills = []
        missing_skills = []

        total_weight = sum(target_skills.values())
        achieved_weight = 0.0

        for skill, weight in target_skills.items():
            if skill in user_skill_set:
                matched_skills.append(skill)
                achieved_weight += weight
            else:
                missing_skills.append({"skill": skill, "priority": "High" if weight >= 0.8 else "Medium"})

        match_score_pct = round((achieved_weight / total_weight) * 100, 1) if total_weight > 0 else 0.0
        gap_score_pct = round(100.0 - match_score_pct, 1)

        return {
            "target_role": target_role,
            "match_score_pct": match_score_pct,
            "gap_score_pct": gap_score_pct,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "recommendation_count": len(missing_skills)
        }

    @staticmethod
    def calculate_career_readiness_index(
        cgpa: float,
        topics_completed: int,
        total_topics: int,
        problems_solved: int,
        easy_solved: int,
        medium_solved: int,
        hard_solved: int,
        quiz_accuracy_pct: float
    ) -> Dict[str, Any]:
        """
        Computes holistic Career Readiness Index (0-100) (FEAT-016).
        Weights:
        - Curriculum Coverage (30%): topics_completed / total_topics
        - Coding Proficiency (40%): weighted problem solving (Easy: 1, Med: 3, Hard: 5)
        - Academic & Quiz Consistency (30%): CGPA (15%) + Quiz Accuracy (15%)
        """
        # Curriculum coverage score (max 30)
        curriculum_ratio = (topics_completed / max(total_topics, 1))
        score_curriculum = min(curriculum_ratio * 30.0, 30.0)

        # Coding proficiency score (max 40)
        # Baseline target: 50 weighted points = 40 max points
        weighted_coding = (easy_solved * 1.0) + (medium_solved * 3.0) + (hard_solved * 5.0)
        score_coding = min((weighted_coding / 50.0) * 40.0, 40.0)

        # Consistency score (max 30)
        cgpa_score = min((cgpa / 10.0) * 15.0, 15.0) if cgpa else 9.0
        quiz_score = (quiz_accuracy_pct / 100.0) * 15.0
        score_consistency = cgpa_score + quiz_score

        total_readiness = round(score_curriculum + score_coding + score_consistency, 1)
        tier = "Ready for Placement" if total_readiness >= 75 else ("Accelerating" if total_readiness >= 50 else "Foundation Building")

        return {
            "readiness_index": total_readiness,
            "readiness_tier": tier,
            "breakdown": {
                "curriculum_score": round(score_curriculum, 1),
                "coding_score": round(score_coding, 1),
                "consistency_score": round(score_consistency, 1)
            },
            "recommendation": (
                "Target tier-1 interviews and timed mock drills." if total_readiness >= 75
                else "Increase medium problem practice and complete system design modules."
            )
        }

    @staticmethod
    def link_concept_to_knowledge_graph(query_or_topic: str) -> List[Dict[str, Any]]:
        """
        Maps user questions/topics to CS knowledge graph nodes (FEAT-020).
        """
        query_lower = query_or_topic.lower()
        linked = []
        for node_id, data in KNOWLEDGE_GRAPH.items():
            if node_id in query_lower or any(n in query_lower for n in data["next_nodes"]):
                linked.append({
                    "concept_id": node_id,
                    "category": data["category"],
                    "difficulty": data["difficulty"],
                    "next_recommended_nodes": data["next_nodes"]
                })
        return linked

    @staticmethod
    def estimate_confidence(matched_context_count: int, is_fallback: bool) -> float:
        """
        Estimates output confidence score (0.0 to 1.0) (FEAT-014).
        """
        if is_fallback:
            return 0.88  # Deterministic rules have high verified confidence
        confidence = 0.70 + min(matched_context_count * 0.05, 0.25)
        return round(confidence, 2)

    @staticmethod
    def generate_explainability_rationale(action_title: str, user_weak_tags: List[str]) -> str:
        """
        Provides rationale metrics for why an action/recommendation was suggested (FEAT-006).
        """
        matching_tags = [t for t in user_weak_tags if t.lower() in action_title.lower()]
        if matching_tags:
            return f"Recommended because you recently struggled with '{', '.join(matching_tags)}' in coding submissions."
        return "Recommended based on standard Tier-1 placement frequency patterns and role requirements."
