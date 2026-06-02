from fastapi import APIRouter, Depends, File, UploadFile
from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.documents import DocumentSearchRequest, DocumentSearchResponse
from app.services.rag import rag_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), user: User = Depends(get_current_user)) -> dict[str, int | str]:
    content = await file.read()
    chunks = rag_service.add_document(file.filename or "upload.txt", content, uploaded_by=user.id)
    return {"filename": file.filename or "upload.txt", "chunks_indexed": chunks}


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(payload: DocumentSearchRequest, user: User = Depends(get_current_user)) -> DocumentSearchResponse:
    answer, chunks = await rag_service.answer(payload.query)
    return DocumentSearchResponse(answer=answer, chunks=chunks)
