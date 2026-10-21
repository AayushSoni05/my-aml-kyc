from fastapi import FastAPI
from app.database import init_db, engine
from app.routers import( 
    customer,
    individuals,
    sole_proprietors,
    companies, 
    kyc,
    screening,
    kyc_config
)
from sqlmodel import Session
from app.idp.store import seed_kyc_config


app = FastAPI(title = "AML / KYC")

app.include_router(customer.router)
app.include_router(individuals.router)
app.include_router(sole_proprietors.router)
app.include_router(companies.router)
app.include_router(kyc.router)
app.include_router(screening.router)
app.include_router(kyc_config.router)

@app.on_event("startup")
def onstartup():
    init_db()
    with Session(engine) as s:
        seed_kyc_config(s)

@app.get("/health")
def health():
    return{"status" : "ok"}
