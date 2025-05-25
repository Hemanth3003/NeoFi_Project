from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Collaborative Event Management System",
    description="A RESTful API for an event scheduling application with collaborative editing features",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Collaborative Event Management System API",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)