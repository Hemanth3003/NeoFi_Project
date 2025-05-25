from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .models.user import User
from .models.event import Event
from .models.permission import Permission
from .models.version import EventVersion
from .routers import auth_router, events_router, collaboration_router, versions_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Collaborative Event Management System",
    description="A RESTful API for an event scheduling application with collaborative editing features",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(collaboration_router)
app.include_router(versions_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Collaborative Event Management System API",
        "documentation": "/docs"
    }