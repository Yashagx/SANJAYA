import boto3
import json
import os
import re
import math
import pandas as pd
import io
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Use EC2 instance profile (sanjaya-ec2-role) for auth — no explicit keys needed
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_REGION', 'ap-south-2')
)
s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'ap-south-2'))

PRIMARY_MODEL  = "deepseek.v3.2"
FALLBACK_MODEL = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
S3_BUCKET      = "sanjaya-models-2026"

def call_bedrock(prompt: str, system: str, max_tokens: int = 2000) -> str:
    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        try:
            if "anthropic" in model:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}]
                })
            elif "deepseek" in model:
                # Native inference payload for DeepSeek models
                body = json.dumps({
                    "prompt": f"{system}\n\nUser: {prompt}\n\nAssistant:",
                    "max_tokens": max_tokens,
                    "temperature": 0.5
                })
            else:
                body = json.dumps({"prompt": prompt, "max_tokens": max_tokens})

            response = bedrock.invoke_model(
                modelId=model, body=body,
                contentType='application/json', accept='application/json'
            )
            result = json.loads(response['body'].read())
            
            # Parse based on model type
            if "anthropic" in model:
                return result['content'][0]['text']
            elif "deepseek" in model:
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['text']
                elif 'generation' in result:
                    return result['generation']
                else:
                    return str(result)
            return str(result)
        except Exception as e:
            print(f"[BRAHMA] {model} failed: {e}")
            continue
    return None

def clean_json(raw: str) -> dict:
    try:
        clean = raw.strip()
        if '```' in clean:
            clean = re.sub(r'```json?\n?', '', clean).replace('```', '')
        return json.loads(clean.strip())
    except Exception as e:
        print(f"[BRAHMA] JSON parse error: {e}")
        return {"error": str(e), "raw": raw[:500]}

# ─────────────────────────────────────
# LAYER 1: NL Intent Parser
# ─────────────────────────────────────
def parse_natural_language(user_input: str) -> dict:
    system = """You are SANJAYA's intent parser for a logistics risk system.
Extract shipment parameters from natural language input.
Return ONLY valid JSON, no explanation, no markdown.
Use these exact field names:
{
  "vessel_id": string,
  "origin": string,
  "destination": string,
  "transport_mode": "sea" or "road" or "air",
  "days_real": number (default 5),
  "days_scheduled": number (default 3),
  "departure_date": "YYYY-MM-DD",
  "quantity": number (default 1000),
  "hs_code": string (default "8471"),
  "category_id": number (default 73),
  "shipping_mode_encoded": 0,
  "benefit_per_order": number (default 50),
  "sales_per_customer": number (default 500),
  "discount_rate": 0.05,
  "profit_ratio": 0.1,
  "month": number (1-12),
  "confidence": number (0-1),
  "extracted_entities": list of strings
}
Today: """ + datetime.now().strftime("%Y-%m-%d") + """
Rules:
- "48 hours" → days_real=2, days_scheduled=1
- "urgent/expedited" → shipping_mode_encoded=2
- vessel/ship → sea, truck/highway → road, flight/cargo plane → air
- If Hormuz/Gulf/Iran mentioned → flag as critical geo zone"""

    result = call_bedrock(user_input, system, max_tokens=600)
    if not result:
        print("[BRAHMA] Using simulated NL fallback due to Bedrock failure")
        return {
            "vessel_id": "MV Chennai Star",
            "origin": "Khor Fakkan",
            "destination": "Rotterdam",
            "transport_mode": "sea",
            "days_real": 5,
            "days_scheduled": 3,
            "departure_date": datetime.now().strftime("%Y-%m-%d"),
            "quantity": 1000,
            "hs_code": "8471",
            "category_id": 73,
            "shipping_mode_encoded": 0,
            "benefit_per_order": 50,
            "sales_per_customer": 500,
            "discount_rate": 0.05,
            "profit_ratio": 0.1,
            "month": datetime.now().month,
            "confidence": 0.95,
            "extracted_entities": ["MV Chennai Star", "Khor Fakkan", "Rotterdam", "Hormuz transit"]
        }
    return clean_json(result)

# ─────────────────────────────────────
# LAYER 2: CSV/Excel Historical Analyzer
# ─────────────────────────────────────
def analyze_company_history(file_bytes: bytes, filename: str) -> dict:
    """
    Analyze company's uploaded shipment CSV/Excel.
    Returns insights + risk calibration data.
    """
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin-1')
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            return {"error": "Unsupported file type. Use CSV or Excel."}

        # Basic stats
        row_count = len(df)
        col_count = len(df.columns)
        columns   = df.columns.tolist()

        # Upload to S3 for reference
        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=f"company-data/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}",
                Body=file_bytes
            )
        except Exception as e:
            print(f"[BRAHMA] S3 upload skipped: {e}")

        # Sample data for Bedrock
        sample = df.head(10).to_string()
        stats  = df.describe().to_string() if df.select_dtypes(
            include='number').shape[1] > 0 else "No numeric columns"

        system = """You are BRAHMA, a logistics intelligence analyst.
Analyze company shipment data and return ONLY valid JSON:
{
  "dataset_summary": "2-3 sentence overview of the data",
  "total_records": number,
  "key_columns_detected": list of strings,
  "avg_delay_days": number or null,
  "delay_rate_percent": number or null,
  "top_risk_routes": [
    {"route": string, "avg_delay": number, "frequency": number}
  ],
  "seasonal_patterns": [
    {"period": string, "observation": string}
  ],
  "carrier_performance": [
    {"carrier": string, "on_time_rate": number}
  ],
  "risk_calibration": {
    "company_baseline_delay": number (0-1),
    "historical_adjustment": number (-0.1 to 0.1),
    "calibration_confidence": "HIGH" or "MEDIUM" or "LOW",
    "recommendation": string
  },
  "key_insights": [
    {"insight": string, "impact": "HIGH" or "MEDIUM" or "LOW", "action": string}
  ],
  "data_quality_score": number (0-100),
  "brahma_assessment": "One sentence overall finding"
}"""

        prompt = f"""
Company Shipment Data Analysis:
File: {filename}
Rows: {row_count} | Columns: {col_count}
Column Names: {columns}

Sample Data (first 10 rows):
{sample}

Statistical Summary:
{stats}

Analyze this company's historical shipment performance.
Identify delay patterns, risk routes, seasonal trends.
Provide risk calibration to improve SANJAYA predictions."""

        result = call_bedrock(prompt, system, max_tokens=1500)
        if not result:
            return {
                "error": "Bedrock analysis unavailable",
                "dataset_summary": f"Loaded {row_count} records from {filename}",
                "total_records": row_count,
                "key_columns_detected": columns[:10]
            }

        analysis = clean_json(result)
        analysis["raw_stats"] = {
            "rows": row_count,
            "columns": col_count,
            "column_names": columns
        }
        return analysis

    except Exception as e:
        return {"error": f"File processing failed: {str(e)}"}

# ─────────────────────────────────────
# LAYER 3: Deep Intelligence Analysis
# ─────────────────────────────────────
def generate_deep_analysis(
    agent_results: dict,
    payload: dict,
    historical_data: list = None,
    company_history: dict = None
) -> dict:
    breakdown = agent_results.get('breakdown', {})
    evidence  = agent_results.get('evidence', {})
    b = breakdown

    # Build computation steps
    p  = b.get('p_delay', 0)
    w  = b.get('s_weather', 0)
    g  = b.get('s_geo', 0)
    cp = b.get('c_port', 0)

    term_delay   = round(0.50 * (p ** 1.8) * 100, 2)
    term_weather = round(0.18 * w * 100, 2)
    term_geo     = round(0.20 * (g ** 1.8) * 100, 2)
    term_port    = round(0.12 * cp * 100, 2)
    rs_computed  = round(term_delay + term_weather + term_geo + term_port, 1)

    # Historical DB context
    hist_ctx = ""
    if historical_data:
        hist_ctx = f"INTERNAL DB ({len(historical_data)} past assessments):\n"
        hist_ctx += "\n".join([
            f"- {h.get('origin','?')} \u2192 {h.get('destination','?')}: "
            f"RS={h.get('risk_score','?')} {h.get('risk_level','?')} "
            f"[{str(h.get('timestamp','?'))[:10]}]"
            for h in historical_data[:5]
        ])

    # Company history context
    company_ctx = ""
    if company_history and not company_history.get('error'):
        rc = company_history.get('risk_calibration', {})
        company_ctx = f"""
COMPANY HISTORICAL DATA (uploaded CSV/Excel):
Dataset: {company_history.get('dataset_summary', 'N/A')}
Records: {company_history.get('total_records', 0)}
Baseline Delay Rate: {rc.get('company_baseline_delay', 'N/A')}
Historical Adjustment: {rc.get('historical_adjustment', 0)}
Key Insights: {[i.get('insight','') for i in company_history.get('key_insights',[])[:3]]}"""

    system = """You are BRAHMA \u2014 SANJAYA's supreme intelligence layer.
Analyze multi-agent outputs with mathematical rigor.
Return ONLY valid JSON, no markdown:
{
  "executive_summary": "2-3 sentence assessment",
  "confidence_score": number (0-100),
  "brahma_confidence": "HIGH" or "MEDIUM" or "LOW",
  "computation_steps": [
    {
      "step": number,
      "agent": "AGENT NAME",
      "sanskrit": "Sanskrit meaning",
      "input": "what data was used",
      "output": number,
      "formula": "exact formula used",
      "result": number,
      "interpretation": "what this means in plain English"
    }
  ],
  "mathematical_validation": {
    "formula_breakdown": "step by step shown",
    "nonlinear_amplification": "squaring effect explanation",
    "dominant_factor": "which factor dominates",
    "sensitivity_analysis": "what changes score most"
  },
  "alternative_scenarios": [
    {
      "name": "Optimistic Scenario",
      "assumption": string,
      "p_delay_adj": number,
      "s_geo_adj": number,
      "s_weather_adj": number,
      "c_port_adj": number,
      "calculated_rs": number,
      "risk_level": string,
      "formula_shown": string,
      "probability": string
    },
    {
      "name": "Base Case Scenario",
      "assumption": string,
      "p_delay_adj": number,
      "s_geo_adj": number,
      "s_weather_adj": number,
      "c_port_adj": number,
      "calculated_rs": number,
      "risk_level": string,
      "formula_shown": string,
      "probability": string
    },
    {
      "name": "Pessimistic Scenario",
      "assumption": string,
      "p_delay_adj": number,
      "s_geo_adj": number,
      "s_weather_adj": number,
      "c_port_adj": number,
      "calculated_rs": number,
      "risk_level": string,
      "formula_shown": string,
      "probability": string
    }
  ],
  "agent_insights": [
    {
      "agent": string,
      "finding": string,
      "severity": "CRITICAL" or "HIGH" or "MEDIUM" or "LOW",
      "evidence": string,
      "recommendation": string
    }
  ],
  "company_history_impact": {
    "used": true or false,
    "adjustment_applied": number,
    "explanation": string
  },
  "historical_pattern_match": {
    "similar_incidents": string,
    "pattern_risk_adjustment": number,
    "precedent_cases": list of strings
  },
  "domain_intelligence": {
    "geopolitical_assessment": string,
    "weather_pattern_analysis": string,
    "supply_chain_cascade": string,
    "financial_impact_estimate": string
  },
  "recommended_actions": [
    {"priority": "IMMEDIATE", "action": string, "rationale": string},
    {"priority": "24H", "action": string, "rationale": string},
    {"priority": "72H", "action": string, "rationale": string}
  ],
  "brahma_verdict": "One powerful sentence",
  "adjusted_risk_score": number
}"""

    prompt = f"""
SHIPMENT: {payload.get('origin')} \u2192 {payload.get('destination')}
Vessel: {payload.get('vessel_id')} | Mode: {payload.get('transport_mode','sea').upper()}
Departure: {payload.get('departure_date')} | Season: {agent_results.get('season')}

AGENT SCORES:
- NIDHI  (ML XGBoost, P_delay):   {p:.4f}
- VAYU   (Weather, S_weather):    {w:.4f} \u2014 {evidence.get('weather',{}).get('condition','unknown')}
- SANCHAR(Geopolitics, S_geo):    {g:.4f} \u2014 {evidence.get('geopolitics',{}).get('top_headline','N/A')[:80]}
- DARPANA(Port/Transport, C_port):{cp:.4f}
- VIVEKA (Customs):               {b.get('customs_risk',0):.4f}
- Delay Gap: {b.get('delay_gap_days',0)} days over schedule

COMPUTATION (show step by step):
Step 1 NIDHI:   0.50 \u00d7 {p}^1.8 \u00d7 100 = {term_delay}
Step 2 VAYU:    0.18 \u00d7 {w} \u00d7 100 = {term_weather}
Step 3 SANCHAR: 0.20 \u00d7 {g}^1.8 \u00d7 100 = {term_geo}
Step 4 DARPANA: 0.12 \u00d7 {cp} \u00d7 100 = {term_port}
TOTAL RS = {term_delay} + {term_weather} + {term_geo} + {term_port} = {rs_computed}

RULE OVERRIDES: {agent_results.get('rule_overrides',[])}
FINAL RS (after overrides): {agent_results.get('risk_score')}
RISK LEVEL: {agent_results.get('risk_level')}

{hist_ctx}
{company_ctx}

Generate rigorous analysis with all 6 computation steps,
3 alternative scenarios with actual RS calculations,
per-agent insights, and company history impact assessment."""

    result = call_bedrock(prompt, system, max_tokens=2500)
    if not result:
        return {
            "error": "Bedrock unavailable",
            "executive_summary": "Analysis unavailable \u2014 Bedrock connection failed",
            "computation_steps": [],
            "alternative_scenarios": [],
            "agent_insights": []
        }
    return clean_json(result)

# ─────────────────────────────────────
# LAYER 4: Narrative Generator
# ─────────────────────────────────────
def generate_narrative(agent_results: dict, deep_analysis: dict) -> str:
    system = """You are BRAHMA, SANJAYA's intelligence narrator.
Write a 4-5 sentence executive briefing for a logistics CEO.
Direct, authoritative, specific. No bullets. Max 120 words."""

    prompt = f"""
Risk Score: {agent_results.get('risk_score')} / {agent_results.get('risk_level')}
Route: {agent_results.get('route')}
P_delay: {agent_results.get('breakdown',{}).get('p_delay',0):.3f}
Geo Risk: {agent_results.get('breakdown',{}).get('s_geo',0):.3f}
Recommendation: {agent_results.get('recommendation')}
Brahma Verdict: {deep_analysis.get('brahma_verdict','N/A')}
Write executive briefing:"""

    result = call_bedrock(prompt, system, max_tokens=200)
    return result if result else agent_results.get('recommendation','')

# ─────────────────────────────────────
# LAYER 5: Per-Agent Narrative Enrichment
# ─────────────────────────────────────
def enrich_agent_outputs(agent_results: dict, payload: dict) -> dict:
    """
    Bedrock reads each agent's raw evidence and generates
    a human-readable narrative explanation for each.
    """
    evidence  = agent_results.get("evidence", {})
    breakdown = agent_results.get("breakdown", {})
    enriched  = {}

    agents_to_enrich = [
        {
            "name": "VAYU",
            "data": evidence.get("weather", {}),
            "score": breakdown.get("s_weather", 0),
            "prompt_extra": "Focus on specific weather parameters and maritime safety implications."
        },
        {
            "name": "SANCHAR",
            "data": evidence.get("geopolitics", {}),
            "score": breakdown.get("s_geo", 0),
            "prompt_extra": "Focus on geopolitical events, trade routes, and diplomatic context."
        },
        {
            "name": "NIDHI",
            "data": evidence.get("ml", {}),
            "score": breakdown.get("p_delay", 0),
            "prompt_extra": "Explain ML model decision in plain English. Reference SHAP values."
        },
        {
            "name": "DARPANA",
            "data": evidence.get("transport", {}),
            "score": breakdown.get("c_port", 0),
            "prompt_extra": "Explain port congestion and maritime traffic context."
        },
        {
            "name": "VIVEKA",
            "data": evidence.get("customs", {}),
            "score": breakdown.get("customs_risk", 0),
            "prompt_extra": "Explain customs risk, HS code implications and clearance times."
        }
    ]

    system = """You are BRAHMA enriching individual agent reports.
Write 2-3 sentences explaining WHY this agent gave this score.
Be specific \u2014 reference actual data values from the evidence.
Be concise, expert, and use logistics domain language.
Return plain text only, no JSON, no bullets."""

    for agent in agents_to_enrich:
        evidence_str = json.dumps(agent["data"], indent=2)[:800]
        prompt = f"""
Agent: {agent['name']}
Score: {agent['score']:.4f} ({round(agent['score']*100)}% risk)
Evidence Data: {evidence_str}
{agent['prompt_extra']}
Explain in 2-3 sentences why this score is correct given this data:"""

        narrative = call_bedrock(prompt, system, max_tokens=150)
        enriched[agent["name"]] = {
            "score": agent["score"],
            "narrative": narrative or f"{agent['name']} scored {round(agent['score']*100)}% based on available data.",
            "evidence_points": agent["data"].get("evidence_points", [])
        }

    return enriched
