from fastapi import FastAPI
from app.database import init_db
from app.routers import( 
    customer,
    individuals,
    sole_proprietors
)

app = FastAPI(title = "AML / KYC")

app.include_router(customer.router)
app.include_router(individuals.router)
app.include_router(sole_proprietors.router)

@app.on_event("startup")
def onstartup():
    init_db()

@app.get("/health")
def health():
    return{"status" : "ok"}
