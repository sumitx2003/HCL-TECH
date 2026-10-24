
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.chat import router as chat_router
from backend.routes.books import router as books_router
from backend.routes.users import router as users_router
from backend.routes.loans import router as loans_router

app = FastAPI(
    title="Smart Library Assistant API",
    description="Backend APIs for the Smart Library Management Assistant",
    version="1.0.0",
)

# Allow the React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(books_router)
app.include_router(chat_router)
app.include_router(users_router)
app.include_router(loans_router)


@app.get("/", tags=["Default"])
def home():
    return {
        "message": "Smart Library Assistant API is running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Default"])
def health():
    return {"status": "healthy"}
