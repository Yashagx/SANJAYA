"""
SANJAYA — Multi-Agent Shipment Risk Intelligence System
FastAPI backend serving risk assessments + authentication + centralized logging.
"""

import os
import io
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
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
from auth import (
    UserLogin, UserRegister, Token,
    hash_password, verify_password, create_access_token,
    get_user_by_email, create_user, update_last_login,
    validate_password_strength, validate_email_format,
    get_current_user, get_admin_user
)
from logger_module import (
    log_info, log_warning, log_error, log_debug, log_exception,
    get_recent_logs, log_startup, log_shutdown
)

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

# Log startup
log_startup()


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


class ChatRequest(BaseModel):
    message: str


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

# ── AUTHENTICATION ENDPOINTS ────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def login_page():
    """Serve the login page."""
    log_info("Login page accessed")
    login_path = os.path.join(os.path.dirname(__file__), "login.html")
    with open(login_path, "r") as f:
        return f.read()


@app.post("/auth/register", response_model=Token)
def register(user: UserRegister):
    """Register a new user with email and password."""
    log_info(f"Registration attempt for email: {user.email}")
    
    # Validate email format
    valid_email, msg = validate_email_format(user.email)
    if not valid_email:
        log_error(f"Invalid email format: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Validate password strength
    valid_pwd, msg = validate_password_strength(user.password)
    if not valid_pwd:
        log_error(f"Weak password for {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Check if user exists
    existing_user = get_user_by_email(user.email)
    if existing_user:
        log_error(f"User already exists: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Hash password and create user
    hashed_pwd = hash_password(user.password)
    if not create_user(user.email, hashed_pwd):
        log_error(f"Failed to create user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    log_info(f"User registered successfully: {user.email}")
    
    # Generate token
    access_token = create_access_token(
        data={"sub": user.email, "is_admin": False}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_email=user.email,
        is_admin=False
    )


@app.post("/auth/login", response_model=Token)
def login(user: UserLogin):
    """Login user with email and password."""
    log_info(f"Login attempt for email: {user.email}")
    
    # Get user from database
    db_user = get_user_by_email(user.email)
    if not db_user:
        log_error(f"User not found: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(user.password, db_user["hashed_password"]):
        log_error(f"Invalid password for: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Update last login
    update_last_login(user.email)
    log_info(f"User logged in successfully: {user.email}")
    
    # Generate token
    access_token = create_access_token(
        data={"sub": user.email, "is_admin": db_user.get("is_admin", False)}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_email=user.email,
        is_admin=db_user.get("is_admin", False)
    )


@app.get("/auth/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    log_debug(f"User info accessed: {current_user['email']}")
    return {
        "email": current_user["email"],
        "is_admin": current_user.get("is_admin", False),
        "created_at": "N/A"  # Could add to database
    }


@app.get("/logs")
def get_logs(limit: int = 100, current_user: dict = Depends(get_admin_user)):
    """
    Get recent application logs.
    Admin access required.
    """
    log_debug(f"Logs accessed by: {current_user['email']}")
    try:
        logs = get_recent_logs(limit)
        return {
            "logs": logs,
            "count": len(logs),
            "accessed_by": current_user["email"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log_exception("Error retrieving logs", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving logs"
        )


# ── CORE ENDPOINTS (EXISTING) ────────────────────────────────────────────
@app.get("/health")
def health_check():
    """Health-check endpoint."""
    log_debug("Health check")
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
    try:
        log_info(f"Prediction request: {req.origin} → {req.destination}")
        payload = req.model_dump()

        # ── KAVACH VALIDATION GATE ──────────────────────
        validation = validate_shipment(payload)
        if not validation["valid"]:
            log_warning(f"Validation failed for {req.origin} → {req.destination}")
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
        log_info(f"Prediction completed: {req.origin} → {req.destination}, Risk: {result.get('risk_level')}")

        # Attach any validation warnings to the result
        if validation.get("warnings"):
            result["validation_warnings"] = validation["warnings"]
        result["validation_engine"] = validation.get("validation_engine", "kavach")

        # Save to PostgreSQL
        save_assessment(result, payload)
        return result
    except Exception as e:
        log_exception(f"Prediction error for {req.origin} → {req.destination}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed"
        )


# ── ENDPOINT: NL Predict (BRAHMA) ──────────────────
@app.post("/nlpredict")
async def nl_predict(request: dict):
    try:
        user_text = request.get("text", "")
        if not user_text:
            log_warning("NL predict called with empty text")
            return {"error": "Please provide text input"}

        log_info(f"NL Predict: {user_text[:50]}...")
        parsed = parse_natural_language(user_text)
        if not parsed:
            log_error(f"Failed to parse: {user_text[:50]}")
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
        
        log_info("NL predict completed successfully")

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
    except Exception as e:
        log_exception("NL predict error", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="NL predict failed"
        )


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
    try:
        allowed = ['.csv', '.xlsx', '.xls']
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            log_error(f"Invalid file type: {ext} for {file.filename}")
            return JSONResponse(
                status_code=400,
                content={"error": f"File type {ext} not supported. Use: {allowed}"}
            )

        file_bytes = await file.read()
        log_info(f"Uploading company history: {file.filename} ({len(file_bytes)} bytes)")

        analysis = analyze_company_history(file_bytes, file.filename)
        _company_history_cache["latest"] = analysis
        _company_history_cache["filename"] = file.filename
        _company_history_cache["uploaded_at"] = datetime.now().isoformat()

        log_info(f"Company history analyzed: {file.filename}")

        return {
            "status": "success",
            "filename": file.filename,
            "analysis": analysis,
            "message": "Company history loaded. BRAHMA will now use this data to improve predictions.",
            "cached": True
        }
    except Exception as e:
        log_exception(f"Error uploading {file.filename}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed"
        )


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
async def chat(request: ChatRequest):
    try:
        from agents.brahma import call_groq
        message = request.message
        if not message:
            log_warning("Chat called with empty message")
            return {"response": "", "brahma_powered": False}
        
        log_info(f"Chat message: {message[:50]}...")
        history = get_history_for_bedrock(5)
        company = _company_history_cache.get("latest", {})

        hist_str = "\n".join([
            f"- {h.get('origin')} → {h.get('destination')}: RS={h.get('risk_score')} {h.get('risk_level')}"
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
Style rules:
- Be short, crisp, and professional.
- Infer user intent first (risk check, ETA, mitigation, compliance, route advice) and answer that intent directly.
- Keep response to 3-5 lines, plain language, no filler.
- Include only actionable facts or clear next steps.
Today: {datetime.now().strftime('%Y-%m-%d')}"""

        response = call_groq(message, system, max_tokens=220)
        log_info("Chat response generated")
        return {
            "response": response or "Unable to complete request right now. Please retry shortly.",
            "brahma_powered": True
        }
    except Exception as e:
        log_exception("Chat error", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat failed"
        )
# ── ENDPOINT: History ──────────────────────────────
@app.get("/history")
def get_history():
    """Return the last 50 risk assessments from PostgreSQL."""
    try:
        log_info("History endpoint accessed")
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
            log_info(f"History retrieved: {len(rows)} assessments")
            return {"assessments": rows, "count": len(rows)}
    except Exception as e:
        log_exception("History endpoint error", e)
        return {"error": str(e), "assessments": []}


@app.get("/stats")
def get_stats():
    """Return aggregate statistics from PostgreSQL."""
    try:
        log_info("Stats endpoint accessed")
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
            result = {
                "total_assessments": int(stats[0]),
                "avg_risk_score": round(float(stats[1]), 1) if stats[1] else 0,
                "critical_count": int(stats[2]),
                "high_count": int(stats[3]),
                "medium_count": int(stats[4]),
                "low_count": int(stats[5])
            }
            log_info(f"Stats retrieved: {result['total_assessments']} total assessments")
            return result
    except Exception as e:
        log_exception("Stats endpoint error", e)
        return {"error": str(e)}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Serve the SANJAYA live web dashboard."""
    log_info("Dashboard accessed")
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(dashboard_path, "r") as f:
        return f.read()


# ── Entrypoint ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
