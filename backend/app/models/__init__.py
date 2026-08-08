"""Database models module"""
from app.models.user import User, UserRole, UserType
from app.models.task import Task, TaskAssignment, AssignedGroup
from app.models.submission import TaskSubmission, SubmissionFile, SubmissionStatus, FileScanStatus
from app.models.points_and_audit import (
    PointsTransaction, TransactionType, DeadlinePenaltyApplied,
    AuditLog, AuditActionType
)
from app.models.leaderboard_schedule_announcement import (
    LeaderboardCache, Schedule, Announcement, TargetGroup
)
from app.models.metajungle import (
    Quest, QuestCompletion, NFTHolding, P2POrder, Stake,
    Partner, Campaign, CampaignParticipation, CampaignTask, CampaignTaskCompletion,
    Course, CourseCompletion, Redemption,
    CAMPAIGN_STATUSES, CAMPAIGN_COMPLETION_STATUSES,
)

__all__ = [
    "User",
    "UserRole",
    "UserType",
    "Task",
    "TaskAssignment",
    "AssignedGroup",
    "TaskSubmission",
    "SubmissionFile",
    "SubmissionStatus",
    "FileScanStatus",
    "PointsTransaction",
    "TransactionType",
    "DeadlinePenaltyApplied",
    "AuditLog",
    "AuditActionType",
    "LeaderboardCache",
    "Schedule",
    "Announcement",
    "TargetGroup",
    "Quest",
    "QuestCompletion",
    "NFTHolding",
    "P2POrder",
    "Stake",
    "Partner",
    "Campaign",
    "CampaignParticipation",
    "CampaignTask",
    "CampaignTaskCompletion",
    "CAMPAIGN_STATUSES",
    "CAMPAIGN_COMPLETION_STATUSES",
    "Course",
    "CourseCompletion",
    "Redemption",
]
