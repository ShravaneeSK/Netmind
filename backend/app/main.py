from fastapi import FastAPI

app = FastAPI(title="NetMind")


@app.get("/health")
def health():
    return {"status": "ok"}