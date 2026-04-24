"""权限验证工具函数。

提供统一的数据隔离验证逻辑，确保用户只能访问自己的数据。
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job


async def verify_job_ownership(
    session: AsyncSession, 
    job_id: str, 
    owner_id: int
) -> Job:
    """验证职位归属，如果不是当前用户的则抛出 403。
    
    Args:
        session: 数据库会话
        job_id: 职位 ID
        owner_id: 当前用户 ID
        
    Returns:
        Job: 职位对象
        
    Raises:
        HTTPException: 404 (职位不存在) 或 403 (无权访问)
    """
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="职位不存在",
        )
    if job.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该职位",
        )
    return job


async def verify_candidate_ownership(
    session: AsyncSession,
    candidate_id: str,
    owner_id: int,
) -> tuple:
    """验证候选人归属（通过关联的 Job 验证）。
    
    Args:
        session: 数据库会话
        candidate_id: 候选人 ID
        owner_id: 当前用户 ID
        
    Returns:
        tuple: (candidate, job) 对象
        
    Raises:
        HTTPException: 404 或 403
    """
    from app.models.candidate import Candidate
    
    candidate = await session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="候选人不存在",
        )
    
    # 通过 job_id 验证归属
    job = await session.get(Job, candidate.job_id)
    if not job or job.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该候选人",
        )
    
    return candidate, job


async def verify_task_ownership(
    session: AsyncSession,
    task_id: str,
    owner_id: int,
) -> tuple:
    """验证分拣任务归属（通过关联的 Job 验证）。
    
    Args:
        session: 数据库会话
        task_id: 任务 ID
        owner_id: 当前用户 ID
        
    Returns:
        tuple: (task, job) 对象
        
    Raises:
        HTTPException: 404 或 403
    """
    from app.models.task import SortingTask
    
    task = await session.get(SortingTask, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    
    # 通过 job_id 验证归属
    job = await session.get(Job, task.job_id)
    if not job or job.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该任务",
        )
    
    return task, job


async def verify_file_ownership(
    session: AsyncSession,
    file_id: str,
    owner_id: int,
) -> tuple:
    """验证文件归属（通过关联的 Job 验证）。
    
    Args:
        session: 数据库会话
        file_id: 文件 ID
        owner_id: 当前用户 ID
        
    Returns:
        tuple: (file, job) 对象
        
    Raises:
        HTTPException: 404 或 403
    """
    from app.models.file import ResumeFile
    
    file_record = await session.get(ResumeFile, file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )
    
    # 通过 job_id 验证归属
    job = await session.get(Job, file_record.job_id)
    if not job or job.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该文件",
        )
    
    return file_record, job
