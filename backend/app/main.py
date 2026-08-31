from fastapi import FastAPI

app = FastAPI(title="stock_insight backend")


@app.get("/health")
def health():
    return {"status": "ok"}
