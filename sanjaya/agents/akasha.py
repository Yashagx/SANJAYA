def get_air_risk(origin: str, destination: str,
                 month: int = None) -> dict:
    from datetime import datetime
    if month is None:
        month = datetime.now().month

    combined = f"{origin} {destination}".lower()

    # Major air cargo hubs congestion
    CONGESTED_AIRPORTS = {
        "dubai": 0.55, "dxb": 0.55,
        "hong kong": 0.58, "hkg": 0.58,
        "shanghai": 0.52, "pvg": 0.52,
        "singapore": 0.45, "sin": 0.45,
        "frankfurt": 0.48, "fra": 0.48,
        "london heathrow": 0.50, "lhr": 0.50,
        "new york": 0.52, "jfk": 0.52,
        "los angeles": 0.50, "lax": 0.50,
        "delhi": 0.45, "mumbai": 0.42,
        "chennai": 0.38, "bangalore": 0.40,
        "doha": 0.48, "abu dhabi": 0.45
    }

    # Conflict zone airspace closures
    CLOSED_AIRSPACE = {
        "iran": 0.95, "hormuz": 0.90,
        "ukraine": 0.92, "russia": 0.85,
        "belarus": 0.80, "iraq": 0.75,
        "syria": 0.90, "yemen": 0.92,
        "libya": 0.85, "somalia": 0.80
    }

    # Check closed airspace
    for zone, score in CLOSED_AIRSPACE.items():
        if zone in combined:
            return {
                "score": score,
                "reason": f"Airspace closed/restricted: {zone}",
                "congestion_tier": "CRISIS",
                "transport_mode": "air"
            }

    # Base airport congestion
    base_score = 0.25
    matched = "standard"
    for airport, score in CONGESTED_AIRPORTS.items():
        if airport in combined:
            base_score = max(base_score, score)
            matched = airport

    # Seasonal boosts
    seasonal_boost = 0.0
    seasonal_reason = "Normal operations"

    # Peak cargo season Nov-Dec
    if month in [11, 12]:
        seasonal_boost = 0.20
        seasonal_reason = "Peak air cargo season — severe backlogs"

    # Chinese New Year Jan-Feb
    elif month in [1, 2] and any(c in combined for c in ["china","shanghai","hong kong","beijing"]):
        seasonal_boost = 0.18
        seasonal_reason = "Chinese New Year — Asia air cargo surge"

    # Summer fog/storm — Indian subcontinent June-Sept
    elif month in [6,7,8,9] and any(c in combined for c in ["india","delhi","mumbai","chennai"]):
        seasonal_boost = 0.15
        seasonal_reason = "Monsoon weather disruptions — flight delays"

    # Winter fog — North India/Pakistan Dec-Feb
    elif month in [12,1,2] and any(c in combined for c in ["delhi","lahore","karachi"]):
        seasonal_boost = 0.22
        seasonal_reason = "Dense fog — airport closures and diversions"

    final_score = min(base_score + seasonal_boost, 0.95)

    return {
        "score": round(final_score, 3),
        "matched_hub": matched,
        "base_congestion": base_score,
        "seasonal_boost": seasonal_boost,
        "seasonal_reason": seasonal_reason,
        "transport_mode": "air"
    }
