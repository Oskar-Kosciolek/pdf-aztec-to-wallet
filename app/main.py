from fastapi import FastAPI
from app.routers import tickets, wallet

app = FastAPI(
    title="Aztec Ticket Microservice",
    description="Decodes Aztec barcodes from PDF railway tickets (UIC 918.3)",
    version="0.1.0",
)

app.include_router(tickets.router)
app.include_router(wallet.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
