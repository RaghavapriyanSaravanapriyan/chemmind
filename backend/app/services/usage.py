from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.usage import UsageRecord
from app.schemas.usage import QuotaLimits, WorkspaceUsageSummary


class UsageService:
    async def record_usage(
        self,
        db: AsyncSession,
        workspace_id: str,
        user_id: str,
        metric_type: str,
        amount: int = 1,
    ) -> UsageRecord:
        result = await db.execute(
            select(UsageRecord).where(
                UsageRecord.workspace_id == workspace_id,
                UsageRecord.metric_type == metric_type,
            )
        )
        record = result.scalar_one_or_none()

        if record:
            record.count += amount
        else:
            record = UsageRecord(
                workspace_id=workspace_id,
                user_id=user_id,
                metric_type=metric_type,
                count=amount,
            )
            db.add(record)

        await db.commit()
        await db.refresh(record)
        return record

    async def get_workspace_usage_summary(
        self, db: AsyncSession, workspace_id: str
    ) -> WorkspaceUsageSummary:
        result = await db.execute(
            select(UsageRecord).where(UsageRecord.workspace_id == workspace_id)
        )
        records = result.scalars().all()

        usage_map = {r.metric_type: r.count for r in records}

        docs_count = usage_map.get("documents_uploaded", 0)
        storage_bytes = usage_map.get("storage_bytes", 0)
        ai_requests_count = usage_map.get("ai_requests", 0)

        storage_mb = round(storage_bytes / (1024 * 1024), 2)

        limits = QuotaLimits(
            max_documents=settings.DEFAULT_WORKSPACE_DOC_LIMIT,
            max_storage_mb=settings.DEFAULT_WORKSPACE_STORAGE_MB,
            max_ai_requests=settings.DEFAULT_WORKSPACE_AI_REQUEST_LIMIT,
        )

        return WorkspaceUsageSummary(
            workspace_id=workspace_id,
            documents_count=docs_count,
            storage_bytes=storage_bytes,
            storage_mb=storage_mb,
            ai_requests_count=ai_requests_count,
            limits=limits,
        )

    async def check_quota_available(
        self,
        db: AsyncSession,
        workspace_id: str,
        metric_type: str,
        incoming_amount: int = 1,
    ) -> None:
        summary = await self.get_workspace_usage_summary(db, workspace_id)

        if metric_type == "documents_uploaded":
            if summary.documents_count + incoming_amount > summary.limits.max_documents:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Workspace document quota limit ({summary.limits.max_documents}) exceeded.",
                )
        elif metric_type == "storage_bytes":
            incoming_mb = incoming_amount / (1024 * 1024)
            if summary.storage_mb + incoming_mb > summary.limits.max_storage_mb:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Workspace storage quota limit ({summary.limits.max_storage_mb}MB) exceeded.",
                )
        elif metric_type == "ai_requests":
            if summary.ai_requests_count + incoming_amount > summary.limits.max_ai_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Workspace AI request quota limit ({summary.limits.max_ai_requests}) exceeded.",
                )


usage_service = UsageService()
