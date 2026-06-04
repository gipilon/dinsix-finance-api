from fastapi import FastAPI

app = FastAPI(title="Dinsix Finance API")


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend funcionando"}