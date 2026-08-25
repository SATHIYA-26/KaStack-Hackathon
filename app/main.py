from fastapi import FastAPI

app = FastAPI(title="Semantic Communication System")

@app.get("/")
def read_root():
    return {
        "status": "running",
        "service": "semantic-communication"
    }
