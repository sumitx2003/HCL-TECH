from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import ask_library

app = FastAPI(title="Smart Library Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local testing only
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {"message": "Smart Library Assistant API is running"}

@app.post("/api/research/ask")
def ask_research(request: ResearchRequest):
    return ask_library(request.question)
