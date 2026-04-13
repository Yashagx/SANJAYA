"""
KAVACH — Input Validation & Intelligence Guard Agent
Sanskrit: Kavach = Shield / Armor

Validates shipment parameters for coherence before risk assessment.
Uses rule-based intelligence engine with AWS Bedrock fallback when available.
"""

import os
import json
import re
from datetime import datetime

# ── VESSEL ID PREFIX → MODE MAPPING ──────────────────
VESSEL_MODE_MAP = {
    # Sea vessel prefixes
    "MV-": "sea", "MSC-": "sea", "EVER-": "sea", "MAERSK-": "sea",
    "CMA-": "sea", "COSCO-": "sea", "OOCL-": "sea", "ONE-": "sea",
    "ZIM-": "sea", "HMM-": "sea", "YML-": "sea", "PIL-": "sea",
    "SCI-": "sea", "MOL-": "sea", "NYK-": "sea", "APL-": "sea",
    "VESSEL-": "sea", "SHIP-": "sea", "SS-": "sea",
    # Road/truck prefixes
    "TRUCK-": "road", "TRK-": "road", "LORRY-": "road",
    "TRAILER-": "road", "CONTAINER-TRUCK-": "road",
    # Indian vehicle registration prefixes (state codes)
    "DL-": "road", "MH-": "road", "KA-": "road", "TN-": "road",
    "GJ-": "road", "RJ-": "road", "UP-": "road", "HR-": "road",
    "PB-": "road", "AP-": "road", "TS-": "road", "KL-": "road",
    "WB-": "road", "OR-": "road", "MP-": "road", "CG-": "road",
    "JH-": "road", "BR-": "road", "AS-": "road",
    # Air cargo prefixes
    "AI-": "air", "FDX-": "air", "UPS-": "air", "DHL-": "air",
    "CARGO-": "air", "AWB-": "air", "MAWB-": "air", "HAWB-": "air",
    "FLT-": "air", "FLIGHT-": "air", "AIR-": "air",
    "6E-": "air",  # IndiGo
    "SG-": "air",  # SpiceJet
    "EK-": "air",  # Emirates
    "QR-": "air",  # Qatar
    "EY-": "air",  # Etihad
}

# ── KNOWN CITIES FOR ROAD TRANSPORT ──────────────────
INDIAN_CITIES = {
    "delhi", "new delhi", "mumbai", "chennai", "kolkata", "bangalore",
    "bengaluru", "hyderabad", "pune", "ahmedabad", "surat", "jaipur",
    "lucknow", "kanpur", "nagpur", "indore", "thane", "bhopal",
    "visakhapatnam", "vizag", "patna", "vadodara", "ghaziabad",
    "ludhiana", "agra", "nashik", "faridabad", "meerut", "rajkot",
    "varanasi", "srinagar", "aurangabad", "dhanbad", "amritsar",
    "navi mumbai", "allahabad", "prayagraj", "ranchi", "howrah",
    "coimbatore", "jabalpur", "gwalior", "vijayawada", "jodhpur",
    "madurai", "raipur", "kota", "chandigarh", "guwahati", "solapur",
    "hubli", "mysore", "mysuru", "tiruchirappalli", "trichy",
    "bareilly", "moradabad", "gurgaon", "gurugram", "noida",
    "mangalore", "mangaluru", "udaipur", "jammu", "dehradun",
    "shimla", "gangtok", "imphal", "aizawl", "kohima", "itanagar",
    "panaji", "thiruvananthapuram", "trivandrum", "kochi", "cochin",
    "kozhikode", "calicut", "bhubaneswar", "cuttack",
    # Major logistics hubs
    "nhava sheva", "jawaharlal nehru", "mundra", "pipavav",
    "krishnapatnam", "ennore", "kamarajar", "tuticorin",
    "manesar", "bhiwandi", "taloja",
}

# ── GLOBAL PORT CITIES (for sea/air) ─────────────────
GLOBAL_PORT_CITIES = {
    "shanghai", "singapore", "rotterdam", "antwerp", "hamburg",
    "los angeles", "long beach", "dubai", "jebel ali", "hong kong",
    "busan", "ningbo", "shenzhen", "guangzhou", "tokyo", "osaka",
    "yokohama", "kaohsiung", "port klang", "colombo", "felixstowe",
    "valencia", "barcelona", "piraeus", "istanbul", "karachi",
    "london", "new york", "chicago", "atlanta", "dallas",
    "san francisco", "seattle", "miami", "doha", "muscat",
    "abu dhabi", "riyadh", "jeddah", "bangkok", "ho chi minh",
    "jakarta", "manila", "taipei", "kuala lumpur", "melbourne",
    "sydney", "auckland", "vancouver", "toronto", "montreal",
    "khor fakkan", "bandar abbas", "hormuz", "fujairah",
    "aden", "djibouti", "mombasa", "dar es salaam", "durban",
    "mumbai", "chennai", "kolkata", "kochi", "vizag",
    "nhava sheva", "mundra",
    # Airports
    "delhi", "heathrow", "frankfurt", "amsterdam", "paris",
    "beijing", "seoul", "cairo", "nairobi", "lagos",
}


def detect_mode_from_vessel_id(vessel_id: str) -> dict:
    """Detect the expected transport mode from vessel ID prefix."""
    upper = vessel_id.upper().strip()
    for prefix, mode in VESSEL_MODE_MAP.items():
        if upper.startswith(prefix):
            return {"detected_mode": mode, "prefix": prefix, "confidence": "high"}
    return {"detected_mode": None, "prefix": None, "confidence": "unknown"}


def validate_road_cities(origin: str, destination: str) -> dict:
    """Validate that origin and destination are specific Indian cities for road transport."""
    issues = []
    suggestions = []
    o = origin.lower().strip()
    d = destination.lower().strip()

    o_valid = o in INDIAN_CITIES
    d_valid = d in INDIAN_CITIES

    if not o_valid:
        issues.append(f"Origin '{origin}' is not a recognized Indian city for road transport")
        # Fuzzy suggest
        matches = [c.title() for c in INDIAN_CITIES if o[:3] in c][:5]
        if matches:
            suggestions.append(f"Did you mean: {', '.join(matches)}?")
        else:
            suggestions.append("Enter a specific Indian city (e.g., Delhi, Mumbai, Chennai, Bangalore)")

    if not d_valid:
        issues.append(f"Destination '{destination}' is not a recognized Indian city for road transport")
        matches = [c.title() for c in INDIAN_CITIES if d[:3] in c][:5]
        if matches:
            suggestions.append(f"Did you mean: {', '.join(matches)}?")
        else:
            suggestions.append("Enter a specific Indian city (e.g., Delhi, Mumbai, Chennai, Bangalore)")

    return {
        "origin_valid": o_valid,
        "destination_valid": d_valid,
        "issues": issues,
        "suggestions": suggestions,
        "valid": o_valid and d_valid
    }


def validate_sea_locations(origin: str, destination: str) -> dict:
    """Validate that locations make sense for sea freight."""
    o = origin.lower().strip()
    d = destination.lower().strip()
    issues = []

    # Check if both are landlocked locations (not near coast/port)
    LANDLOCKED = {"delhi", "lucknow", "jaipur", "bhopal", "nagpur", "indore",
                  "chandigarh", "patna", "ranchi", "raipur", "gwalior"}
    if o in LANDLOCKED:
        issues.append(f"Origin '{origin}' is a landlocked city — not a sea port")
    if d in LANDLOCKED:
        issues.append(f"Destination '{destination}' is a landlocked city — not a sea port")

    return {"issues": issues, "valid": len(issues) == 0}


def validate_air_locations(origin: str, destination: str) -> dict:
    """Basic air freight validation."""
    issues = []
    # Air is flexible — most cities have airports, so minimal validation
    o = origin.lower().strip()
    d = destination.lower().strip()
    if o == d:
        issues.append("Origin and destination cannot be the same for air freight")
    return {"issues": issues, "valid": len(issues) == 0}


def try_bedrock_validation(payload: dict) -> dict:
    """
    Try to use AWS Bedrock for AI-powered validation.
    Falls back to rule-based engine if Bedrock is unavailable.
    """
    try:
        import boto3
        region = os.getenv("AWS_BEDROCK_REGION", "us-east-1")
        client = boto3.client("bedrock-runtime", region_name=region)

        prompt = f"""You are a logistics validation AI. Analyze this shipment for coherence issues:
- Vessel ID: {payload.get('vessel_id')}
- Transport Mode: {payload.get('transport_mode')}
- Origin: {payload.get('origin')}
- Destination: {payload.get('destination')}
- Departure: {payload.get('departure_date')}
- Quantity: {payload.get('quantity')}

Check for:
1. Does the vessel ID match the transport mode?
2. Are origin/destination realistic for this transport mode?
3. Are there any date/quantity anomalies?

Respond in JSON: {{"valid": true/false, "issues": [...], "suggestions": [...], "ai_confidence": 0.0-1.0}}"""

        response = client.invoke_model(
            modelId="amazon.titan-text-express-v1",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 300,
                    "temperature": 0.2,
                    "topP": 0.9
                }
            })
        )
        result = json.loads(response["body"].read())
        text = result.get("results", [{}])[0].get("outputText", "")

        # Try parsing JSON from response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            ai_result = json.loads(json_match.group())
            ai_result["engine"] = "aws-bedrock-titan"
            return ai_result

    except Exception as e:
        pass  # Fall through to rule-based engine

    return None  # Bedrock unavailable


def validate_shipment(payload: dict) -> dict:
    """
    Master validation function — validates all shipment parameters.
    Tries Bedrock first, falls back to rule-based intelligence.
    """
    vessel_id = payload.get("vessel_id", "").strip()
    transport_mode = payload.get("transport_mode", "sea").lower()
    origin = payload.get("origin", "").strip()
    destination = payload.get("destination", "").strip()
    departure_date = payload.get("departure_date", "")
    quantity = payload.get("quantity", 0)

    errors = []      # Hard blockers — PREVENT assessment
    warnings = []    # Soft warnings — allow but flag
    suggestions = [] # Helpful suggestions

    # ── 1. REQUIRED FIELDS ─────────────────────────
    if not origin:
        errors.append("Origin is required")
    if not destination:
        errors.append("Destination is required")
    if origin.lower().strip() == destination.lower().strip():
        errors.append("Origin and destination cannot be the same")

    # ── 2. VESSEL ID ↔ TRANSPORT MODE CHECK ────────
    mode_check = detect_mode_from_vessel_id(vessel_id)
    detected = mode_check["detected_mode"]

    if detected and detected != transport_mode:
        mode_labels = {"sea": "Sea Freight 🚢", "road": "Road Transport 🚚", "air": "Air Freight ✈️"}
        errors.append(
            f"TRANSPORT MODE MISMATCH: Vessel '{vessel_id}' (prefix '{mode_check['prefix']}') "
            f"is registered as {mode_labels.get(detected, detected)}, "
            f"but you selected {mode_labels.get(transport_mode, transport_mode)}. "
            f"This will produce dangerously inaccurate results."
        )
        suggestions.append(
            f"Change transport mode to '{detected}' or use a valid {transport_mode} vessel ID"
        )

    # ── 3. MODE-SPECIFIC LOCATION VALIDATION ───────
    if transport_mode == "road" and origin and destination:
        road_check = validate_road_cities(origin, destination)
        if not road_check["valid"]:
            errors.extend(road_check["issues"])
            suggestions.extend(road_check["suggestions"])
            suggestions.append(
                "Road transport in SANJAYA requires specific Indian city names "
                "(e.g., Delhi, Mumbai, Chennai, Bangalore, Hyderabad, Pune, Kolkata)"
            )

    elif transport_mode == "sea" and origin and destination:
        sea_check = validate_sea_locations(origin, destination)
        if not sea_check["valid"]:
            for issue in sea_check["issues"]:
                warnings.append(issue)
            suggestions.append("For sea freight, use coastal port cities")

    elif transport_mode == "air" and origin and destination:
        air_check = validate_air_locations(origin, destination)
        if not air_check["valid"]:
            errors.extend(air_check["issues"])

    # ── 4. DATE VALIDATION ─────────────────────────
    if departure_date:
        try:
            dt = datetime.strptime(departure_date, "%Y-%m-%d")
            if dt.date() < datetime.now().date():
                warnings.append(
                    f"Departure date {departure_date} is in the past — "
                    f"assessment will use historical weather conditions"
                )
        except ValueError:
            warnings.append(f"Invalid date format: {departure_date}. Expected YYYY-MM-DD")

    # ── 5. QUANTITY SANITY CHECK ───────────────────
    if quantity:
        qty = int(quantity) if quantity else 0
        if transport_mode == "air" and qty > 5000:
            warnings.append(
                f"Quantity {qty} is unusually high for air freight — "
                f"consider sea or road transport for bulk shipments"
            )
        if transport_mode == "road" and qty > 50000:
            warnings.append(
                f"Quantity {qty} exceeds typical road transport capacity — "
                f"consider multiple trucks or rail transport"
            )

    # ── 6. TRY AWS BEDROCK AI VALIDATION ───────────
    ai_validation = None
    bedrock_result = try_bedrock_validation(payload)
    if bedrock_result:
        ai_validation = bedrock_result
        # Merge any AI-discovered issues
        if not bedrock_result.get("valid", True):
            for issue in bedrock_result.get("issues", []):
                if issue not in warnings:
                    warnings.append(f"[AI] {issue}")
            for sug in bedrock_result.get("suggestions", []):
                if sug not in suggestions:
                    suggestions.append(f"[AI] {sug}")

    # ── BUILD RESPONSE ─────────────────────────────
    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "blocked": not is_valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "validation_engine": ai_validation["engine"] if ai_validation else "kavach-rule-engine",
        "mode_detection": mode_check,
        "transport_mode_requested": transport_mode,
        "checks_performed": [
            "vessel_id_mode_match",
            "location_validity",
            "date_sanity",
            "quantity_sanity",
            "ai_coherence" if ai_validation else "rule_coherence"
        ]
    }
