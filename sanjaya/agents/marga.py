def get_road_risk(origin: str, destination: str,
                  month: int = None, departure_date: str = None) -> dict:
    from datetime import datetime
    if month is None:
        month = datetime.now().month

    origin_l = origin.lower()
    dest_l   = destination.lower()
    combined = f"{origin_l} {dest_l}"

    base_score = 0.25  # Road always has base risk

    # High-risk road corridors in India
    HIGH_RISK_CORRIDORS = {
        "western ghats":  {"score": 0.55, "reason": "Ghat roads — steep, fog, landslides"},
        "nh44":           {"score": 0.50, "reason": "NH-44 — highest accident density India"},
        "assam":          {"score": 0.60, "reason": "Assam — flood-prone, poor road quality"},
        "manipur":        {"score": 0.65, "reason": "Manipur — insurgency + poor connectivity"},
        "j&k":            {"score": 0.70, "reason": "J&K — weather + security disruptions"},
        "kashmir":        {"score": 0.70, "reason": "Kashmir — seasonal road closures"},
        "uttarakhand":    {"score": 0.55, "reason": "Uttarakhand — landslide prone"},
        "himachal":       {"score": 0.52, "reason": "Himachal — mountain roads, snow risk"}
    }

    # LEADS 2024 state risk weights (lower = better logistics)
    LEADS_RISK = {
        "gujarat": 0.15, "haryana": 0.18, "punjab": 0.20,
        "maharashtra": 0.22, "karnataka": 0.25, "tamil nadu": 0.25,
        "telangana": 0.28, "andhra": 0.28, "rajasthan": 0.32,
        "uttar pradesh": 0.40, "bihar": 0.45, "west bengal": 0.35,
        "odisha": 0.38, "jharkhand": 0.42, "chhattisgarh": 0.45,
        "madhya pradesh": 0.38, "assam": 0.50, "manipur": 0.60,
        "nagaland": 0.58, "meghalaya": 0.52
    }

    # Check high-risk corridors
    corridor_risk = 0.0
    corridor_reason = ""
    for corridor, info in HIGH_RISK_CORRIDORS.items():
        if corridor in combined:
            corridor_risk = info["score"]
            corridor_reason = info["reason"]
            break

    # LEADS state risk
    leads_risk = 0.25
    for state, risk in LEADS_RISK.items():
        if state in combined:
            leads_risk = risk
            break

    # Seasonal road risk
    seasonal_boost = 0.0
    seasonal_reason = ""

    # Monsoon — road flooding (June-Sept)
    if month in [6,7,8,9]:
        indian_cities = ["mumbai","chennai","kolkata","hyderabad","bangalore",
                        "pune","nagpur","surat","ahmedabad","kochi","india",
                        "delhi"]
        if any(c in combined for c in indian_cities):
            seasonal_boost = 0.30
            seasonal_reason = "Monsoon — road flooding, landslides, highway closures"

    # Winter fog — North India (Dec-Feb)
    elif month in [12,1,2]:
        fog_cities = ["delhi","lucknow","kanpur","varanasi","agra",
                     "patna","chandigarh","amritsar","ludhiana"]
        if any(c in combined for c in fog_cities):
            seasonal_boost = 0.25
            seasonal_reason = "Dense winter fog — NH visibility < 50m, convoy delays"

    # FASTag congestion hotspots
    FASTAG_HOTSPOTS = ["delhi","mumbai","pune","bangalore","hyderabad","surat"]
    fastag_boost = 0.10 if any(c in combined for c in FASTAG_HOTSPOTS) else 0.0

    final_score = min(
        base_score + corridor_risk + (leads_risk * 0.3) + seasonal_boost + fastag_boost,
        0.95
    )

    return {
        "score": round(final_score, 3),
        "corridor_risk": corridor_risk,
        "corridor_reason": corridor_reason if corridor_reason else "Standard highway",
        "leads_risk_weight": leads_risk,
        "seasonal_boost": seasonal_boost,
        "seasonal_reason": seasonal_reason if seasonal_reason else "Normal season",
        "fastag_hotspot": fastag_boost > 0,
        "transport_mode": "road"
    }
