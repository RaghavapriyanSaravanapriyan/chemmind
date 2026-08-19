import os
from typing import Any, List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.workspaces import get_workspace_with_user_role
from app.core.config import settings
from app.models.document import Document, DocumentMetadata
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.storage import storage_service
from app.services.usage import usage_service

router = APIRouter()


@router.post(
    "/{workspace_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Workspace Document",
)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Verify workspace membership & permissions
    workspace, role = await get_workspace_with_user_role(workspace_id, current_user.id, db)
    if role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or editors can upload documents",
        )

    # Check workspace document limit quota
    await usage_service.check_quota_available(db, workspace_id, "documents_uploaded", 1)

    # Validate file extension
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Save file to object storage
    storage_path, checksum, file_size = await storage_service.save_upload_file(workspace_id, file)

    # Check file size limit & storage quota
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        storage_service.delete_file(storage_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    try:
        await usage_service.check_quota_available(db, workspace_id, "storage_bytes", file_size)
    except HTTPException:
        storage_service.delete_file(storage_path)
        raise

    # Create Document record
    document = Document(
        workspace_id=workspace.id,
        uploaded_by_id=current_user.id,
        filename=file.filename or "document.pdf",
        file_size=file_size,
        mime_type="application/pdf",
        storage_path=storage_path,
        status="UPLOADED",
    )
    db.add(document)
    await db.flush()

    # Create DocumentMetadata record
    doc_meta = DocumentMetadata(
        document_id=document.id,
        checksum=checksum,
        title=file.filename,
    )
    db.add(doc_meta)

    # Record usage metrics
    await usage_service.record_usage(db, workspace_id, current_user.id, "documents_uploaded", 1)
    await usage_service.record_usage(db, workspace_id, current_user.id, "storage_bytes", file_size)

    await db.commit()
    await db.refresh(document)
    return document


@router.get(
    "/{workspace_id}/documents",
    response_model=List[DocumentRead],
    summary="List Workspace Documents",
)
async def list_documents(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await get_workspace_with_user_role(workspace_id, current_user.id, db)

    result = await db.execute(
        select(Document).where(Document.workspace_id == workspace_id)
    )
    documents = result.scalars().all()
    return documents


@router.get(
    "/{workspace_id}/documents/{document_id}",
    response_model=DocumentRead,
    summary="Get Document Details",
)
async def get_document(
    workspace_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await get_workspace_with_user_role(workspace_id, current_user.id, db)

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.delete(
    "/{workspace_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
)
async def delete_document(
    workspace_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _, role = await get_workspace_with_user_role(workspace_id, current_user.id, db)
    if role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or editors can delete documents",
        )

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete storage file
    storage_service.delete_file(document.storage_path)

    # Delete DB record
    await db.delete(document)
    await db.commit()
    return None
