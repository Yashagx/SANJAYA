"""
SANJAYA — Multi-Agent Shipment Risk Intelligence System
FastAPI backend serving risk assessments.
"""

import os
import io
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, text

from agents.arjuna import orchestrate
from agents.kavach import validate_shipment
from agents.brahma import (
    parse_natural_language,
    generate_deep_analysis,
    generate_narrative,
    analyze_company_history,
    enrich_agent_outputs
)
from database import save_assessment

app = FastAPI(
    title="SANJAYA",
    description="Multi-Agent Shipment Risk Intelligence System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request schema ──────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    origin: str
    destination: str
    vessel_id: Optional[str] = "N/A"
    transport_mode: Optional[str] = "sea"
    departure_date: Optional[str] = None
    days_real: Optional[int] = 5
    days_scheduled: Optional[int] = 4
    month: Optional[int] = 1
    category_id: Optional[int] = 1
    hs_code: Optional[str] = "0000"
    benefit_per_order: Optional[float] = 50.0
    sales_per_customer: Optional[float] = 200.0
    quantity: Optional[int] = 2
    discount_rate: Optional[float] = 0.05
    profit_ratio: Optional[float] = 0.1
    shipping_mode_encoded: Optional[int] = 0


# ── Helpers ─────────────────────────────────────────────────────────────
def get_history_for_bedrock(limit=10):
    try:
        engine_local = create_engine(
            os.getenv("DATABASE_URL",
            "postgresql://sanjaya_user:Sanjaya2026!@localhost:5432/sanjaya_db")
        )
        with engine_local.connect() as conn:
            result = conn.execute(text("""
                SELECT vessel_id, origin, destination, risk_score,
                       risk_level, transport_mode, timestamp
                FROM risk_assessments
                ORDER BY timestamp DESC LIMIT :limit
            """), {"limit": limit})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"[HISTORY] Error: {e}")
        return []


# Store company history in memory (session)
_company_history_cache = {}


# ── Endpoints ───────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """Health-check endpoint."""
    return {"status": "ok", "system": "SANJAYA", "version": "2.0.0", "brahma": True}


@app.post("/validate")
def validate(req: PredictRequest):
    """Pre-flight validation — checks inputs before assessment."""
    payload = req.model_dump()
    validation = validate_shipment(payload)
    return validation


@app.post("/predict")
def predict(req: PredictRequest):
    """Run the full SANJAYA risk assessment pipeline."""
    payload = req.model_dump()

    # ── KAVACH VALIDATION GATE ──────────────────────
    validation = validate_shipment(payload)
    if not validation["valid"]:
        return JSONResponse(
            status_code=422,
            content={
                "blocked": True,
                "validation_agent": "KAVACH",
                "errors": validation["errors"],
                "warnings": validation.get("warnings", []),
                "suggestions": validation.get("suggestions", []),
                "mode_detection": validation.get("mode_detection", {}),
                "validation_engine": validation.get("validation_engine", "kavach")
            }
        )

    # ── PROCEED WITH ASSESSMENT ─────────────────────
    result = orchestrate(payload)

    # Attach any validation warnings to the result
    if validation.get("warnings"):
        result["validation_warnings"] = validation["warnings"]
    result["validation_engine"] = validation.get("validation_engine", "kavach")

    # Save to PostgreSQL
    save_assessment(result, payload)
    return result


# ── ENDPOINT: NL Predict (BRAHMA) ──────────────────
@app.post("/nlpredict")
async def nl_predict(request: dict):
    user_text = request.get("text", "")
    if not user_text:
        return {"error": "Please provide text input"}

    print(f"[NLPREDICT] {user_text}")
    parsed = parse_natural_language(user_text)
    if not parsed:
        return {"error": "Could not parse input", "input": user_text}

    agent_results = orchestrate(parsed)
    historical = get_history_for_bedrock(10)
    company_hist = _company_history_cache.get("latest")
    deep_analysis = generate_deep_analysis(
        agent_results, parsed, historical, company_hist
    )
    narrative = generate_narrative(agent_results, deep_analysis)
    agent_enrichment = enrich_agent_outputs(agent_results, parsed)
    save_assessment(agent_results, parsed)

    return {
        **agent_results,
        "input_text": user_text,
        "parsed_payload": parsed,
        "bedrock_analysis": deep_analysis,
        "executive_narrative": narrative,
        "agent_enrichment": agent_enrichment,
        "company_history_loaded": company_hist is not None,
        "brahma_powered": True
    }


# ── ENDPOINT: Enhanced Predict (BRAHMA) ────────────
@app.post("/predict/enhanced")
async def predict_enhanced(payload: dict):
    agent_results = orchestrate(payload)
    historical = get_history_for_bedrock(10)
    company_hist = _company_history_cache.get("latest")
    deep_analysis = generate_deep_analysis(
        agent_results, payload, historical, company_hist
    )
    narrative = generate_narrative(agent_results, deep_analysis)
    agent_enrichment = enrich_agent_outputs(agent_results, payload)
    save_assessment(agent_results, payload)

    return {
        **agent_results,
        "bedrock_analysis": deep_analysis,
        "executive_narrative": narrative,
        "agent_enrichment": agent_enrichment,
        "company_history_loaded": company_hist is not None,
        "brahma_powered": True
    }


# ── ENDPOINT: Upload Company CSV/Excel ─────────────
@app.post("/upload/history")
async def upload_company_history(file: UploadFile = File(...)):
    """
    Upload company's historical shipment CSV or Excel.
    Brahma analyzes it and caches insights for future predictions.
    """
    allowed = ['.csv', '.xlsx', '.xls']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        return JSONResponse(
            status_code=400,
            content={"error": f"File type {ext} not supported. Use: {allowed}"}
        )

    file_bytes = await file.read()
    print(f"[UPLOAD] Analyzing {file.filename} ({len(file_bytes)} bytes)")

    analysis = analyze_company_history(file_bytes, file.filename)
    _company_history_cache["latest"] = analysis
    _company_history_cache["filename"] = file.filename
    _company_history_cache["uploaded_at"] = datetime.now().isoformat()

    return {
        "status": "success",
        "filename": file.filename,
        "analysis": analysis,
        "message": "Company history loaded. BRAHMA will now use this data to improve predictions.",
        "cached": True
    }


# ── ENDPOINT: Get cached company history ───────────
@app.get("/company/history")
async def get_company_history():
    if not _company_history_cache.get("latest"):
        return {"loaded": False, "message": "No company history uploaded yet"}
    return {
        "loaded": True,
        "filename": _company_history_cache.get("filename"),
        "uploaded_at": _company_history_cache.get("uploaded_at"),
        "analysis": _company_history_cache.get("latest")
    }


# ── ENDPOINT: Chat (BRAHMA) ───────────────────────
@app.post("/chat")
async def chat(request: dict):
    from agents.brahma import call_bedrock
    message = request.get("message", "")
    history = get_history_for_bedrock(5)
    company = _company_history_cache.get("latest", {})

    hist_str = "\n".join([
        f"- {h.get('origin')} \u2192 {h.get('destination')}: RS={h.get('risk_score')} {h.get('risk_level')}"
        for h in history
    ]) if history else "No assessments yet"

    company_str = ""
    if company and not company.get('error'):
        company_str = f"\nCompany Data Loaded: {company.get('dataset_summary', 'N/A')}"

    system = f"""You are SANJAYA-BRAHMA, an expert AI logistics risk advisor.
You power 7 specialized agents: NIDHI(ML), VAYU(weather), SANCHAR(geopolitics),
DARPANA(ports), VIVEKA(customs), MARGA(roads), AKASHA(air).
Recent DB assessments: {hist_str}
{company_str}
Answer logistics questions expertly and concisely.
Today: {datetime.now().strftime('%Y-%m-%d')}"""

    response = call_bedrock(message, system, max_tokens=400)
    return {
        "response": response or "Connection issue. Please retry.",
        "brahma_powered": True
    }


# ── ENDPOINT: History ──────────────────────────────
@app.get("/history")
def get_history():
    """Return the last 50 risk assessments from PostgreSQL."""
    try:
        engine_local = create_engine(
            os.getenv("DATABASE_URL",
            "postgresql://sanjaya_user:Sanjaya2026!@localhost:5432/sanjaya_db")
        )
        with engine_local.connect() as conn:
            result = conn.execute(text("""
                SELECT id, timestamp, vessel_id, origin, destination,
                       risk_score, risk_level, recommendation,
                       p_delay, s_weather, s_geo, c_port, transport_mode
                FROM risk_assessments
                ORDER BY timestamp DESC
                LIMIT 50
            """))
            rows = []
            for row in result:
                rows.append({
                    "id": row[0],
                    "timestamp": str(row[1]),
                    "vessel_id": row[2],
                    "origin": row[3],
                    "destination": row[4],
                    "risk_score": float(row[5]) if row[5] else 0,
                    "risk_level": row[6],
                    "recommendation": row[7],
                    "p_delay": float(row[8]) if row[8] else 0,
                    "s_weather": float(row[9]) if row[9] else 0,
                    "s_geo": float(row[10]) if row[10] else 0,
                    "c_port": float(row[11]) if row[11] else 0,
                    "transport_mode": row[12] if len(row) > 12 and row[12] else "sea"
                })
            return {"assessments": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e), "assessments": []}


@app.get("/stats")
def get_stats():
    """Return aggregate statistics from PostgreSQL."""
    try:
        engine_local = create_engine(
            os.getenv("DATABASE_URL",
            "postgresql://sanjaya_user:Sanjaya2026!@localhost:5432/sanjaya_db")
        )
        with engine_local.connect() as conn:
            stats = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    AVG(risk_score) as avg_score,
                    COUNT(CASE WHEN risk_level='CRITICAL' THEN 1 END) as critical,
                    COUNT(CASE WHEN risk_level='HIGH' THEN 1 END) as high,
                    COUNT(CASE WHEN risk_level IN ('MEDIUM','MEDIUM-HIGH') THEN 1 END) as medium,
                    COUNT(CASE WHEN risk_level IN ('LOW','LOW-MEDIUM') THEN 1 END) as low
                FROM risk_assessments
            """)).fetchone()
            return {
                "total_assessments": int(stats[0]),
                "avg_risk_score": round(float(stats[1]), 1) if stats[1] else 0,
                "critical_count": int(stats[2]),
                "high_count": int(stats[3]),
                "medium_count": int(stats[4]),
                "low_count": int(stats[5])
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Serve the SANJAYA live web dashboard."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(dashboard_path, "r") as f:
        return f.read()


# ── Entrypoint ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
