"""SQLModel 数据库模型汇总 —— 在此导入以触发表元数据注册。"""
from app.models.candidate import Candidate
from app.models.file import FileType, ParseStatus, ResumeFile
from app.models.job import Job, JobStatus
from app.models.task import SortingTask, TaskStatus
from app.models.user import User

__all__ = [
    "User",
    "Candidate",
    "FileType",
    "ParseStatus",
    "ResumeFile",
    "Job",
    "JobStatus",
    "SortingTask",
    "TaskStatus",
]
