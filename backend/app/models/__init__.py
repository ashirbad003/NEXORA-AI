from backend.app.models.auth import (
    Base, User, Role, user_roles, StudentProfile, AdminProfile, PlacementCellProfile, RefreshToken, AuditLog
)
from backend.app.models.learning import (
    LearningModule, StudentTopicProgress, StudentTopicNote, TopicFeedback
)
from backend.app.models.coding import (
    CodingProblem, ProblemTestCase, CodeSubmission, StudentCodingStats
)
from backend.app.models.copilot import (
    CopilotCareerPath, CopilotRoadmap, CopilotSprintTask, CopilotConversation, CopilotMessage
)
from backend.app.models.assessment import (
    AssessmentTest, AssessmentQuestion, AssessmentAttempt, AssessmentAnswer
)
from backend.app.models.interview import (
    MockInterviewSession, MockInterviewTurn
)
from backend.app.models.phase8_intelligence import (
    ResumeDocument, GitHubProfileCache, JobOpportunity, JobApplication
)
from backend.app.models.phase9_portals import (
    PlacementDrive, PlacementDriveRegistration, PlacementOffer, StudentPlacementProfile,
    SystemFeatureFlag, SystemMetricSnapshot
)

__all__ = [
    "Base", "User", "Role", "user_roles", "StudentProfile", "AdminProfile",
    "PlacementCellProfile", "RefreshToken", "AuditLog",
    "LearningModule", "StudentTopicProgress", "StudentTopicNote", "TopicFeedback",
    "CodingProblem", "ProblemTestCase", "CodeSubmission", "StudentCodingStats",
    "CopilotCareerPath", "CopilotRoadmap", "CopilotSprintTask", "CopilotConversation", "CopilotMessage",
    "AssessmentTest", "AssessmentQuestion", "AssessmentAttempt", "AssessmentAnswer",
    "MockInterviewSession", "MockInterviewTurn",
    "ResumeDocument", "GitHubProfileCache", "JobOpportunity", "JobApplication",
    "PlacementDrive", "PlacementDriveRegistration", "PlacementOffer", "StudentPlacementProfile",
    "SystemFeatureFlag", "SystemMetricSnapshot"
]
