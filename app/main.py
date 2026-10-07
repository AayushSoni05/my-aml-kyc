from fastapi import FastAPI
from app.database import init_db
from app.routers import( 
    customer,
    individuals,
    sole_proprietors,
    companies, 
    kyc,
    screening
)

app = FastAPI(title = "AML / KYC")

app.include_router(customer.router)
app.include_router(individuals.router)
app.include_router(sole_proprietors.router)
app.include_router(companies.router)
app.include_router(kyc.router)
app.include_router(screening.router)

@app.on_event("startup")
def onstartup():
    init_db()

@app.get("/health")
def health():
    return{"status" : "ok"}
