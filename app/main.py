from fastapi import FastAPI
from app.database import init_db

app = FastAPI(title = "AML / KYC")

@app.on_event("startup")
def onstartup():
    init_db()

@app.get("/health")
def health():
    return{"status" : "ok"}
