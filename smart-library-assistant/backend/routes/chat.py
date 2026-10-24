
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.routes.users import get_current_user

# Change this import if you place rag_pipeline.py elsewhere.
from backend.rag_pipeline import ask_library

router = APIRouter(prefix="/chat", tags=["Research Assistant"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@router.post("")
def chat(
    data: ChatRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    question = data.question.strip()

    if not question:
        raise HTTPException(status_code=422, detail="Question is required")

    try:
        result = ask_library(question)
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
        }
    except Exception as exc:
        # Log the actual exception in the backend terminal.
        print(f"Research assistant error: {exc}")
        raise HTTPException(
            status_code=503,
            detail="The research assistant is unavailable. Check the RAG, ChromaDB and Ollama setup.",
        ) from exc
