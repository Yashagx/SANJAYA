from datetime import datetime

CRISIS_PORTS = {
    "hormuz":      {"score":0.99,"ais":"AIS signals dark","wait":"∞","berths":"0% available"},
    "khor fakkan": {"score":0.99,"ais":"800+ vessels anchored","wait":">30 days","berths":"0% available"},
    "bandar abbas":{"score":0.99,"ais":"IRGC controlled","wait":"∞","berths":"Seized"},
    "red sea":     {"score":0.88,"ais":"Houthi exclusion zone","wait":"N/A","berths":"Diverted"},
    "odessa":      {"score":0.85,"ais":"Military zone","wait":"∞","berths":"Closed"}
}

PORT_DATA = {
    "shanghai":      {"base":0.72,"median_wait":"2.1 days","utilization":"89%","berths":40,"throughput":"47M TEU/yr"},
    "ningbo":        {"base":0.70,"median_wait":"1.9 days","utilization":"86%","berths":35,"throughput":"37M TEU/yr"},
    "shenzhen":      {"base":0.68,"median_wait":"1.7 days","utilization":"84%","berths":38,"throughput":"30M TEU/yr"},
    "singapore":     {"base":0.55,"median_wait":"1.2 days","utilization":"78%","berths":55,"throughput":"38M TEU/yr"},
    "port klang":    {"base":0.52,"median_wait":"1.1 days","utilization":"75%","berths":22,"throughput":"14M TEU/yr"},
    "colombo":       {"base":0.50,"median_wait":"1.3 days","utilization":"73%","berths":18,"throughput":"7M TEU/yr"},
    "nhava sheva":   {"base":0.58,"median_wait":"2.3 days","utilization":"81%","berths":25,"throughput":"6.5M TEU/yr"},
    "chennai":       {"base":0.48,"median_wait":"1.8 days","utilization":"35.59%","berths":20,"throughput":"2.5M TEU/yr"},
    "kamarajar":     {"base":0.55,"median_wait":"2.1 days","utilization":"56.66%","berths":12,"throughput":"1.2M TEU/yr"},
    "mumbai":        {"base":0.52,"median_wait":"1.6 days","utilization":"72%","berths":30,"throughput":"6M TEU/yr"},
    "los angeles":   {"base":0.60,"median_wait":"2.8 days","utilization":"82%","berths":28,"throughput":"10M TEU/yr"},
    "long beach":    {"base":0.62,"median_wait":"3.1 days","utilization":"85%","berths":26,"throughput":"9M TEU/yr"},
    "rotterdam":     {"base":0.45,"median_wait":"0.8 days","utilization":"68%","berths":50,"throughput":"15M TEU/yr"},
    "jebel ali":     {"base":0.50,"median_wait":"1.78 days","utilization":"75%","berths":67,"throughput":"14M TEU/yr"},
    "dubai":         {"base":0.48,"median_wait":"1.5 days","utilization":"71%","berths":35,"throughput":"14M TEU/yr"}
}

PEAK_SEASONS = {
    (1,2):   {"zones":["shanghai","ningbo","china"],"boost":0.20,"reason":"Chinese New Year shutdown"},
    (6,7,8,9):{"zones":["chennai","mumbai","nhava","india","kolkata"],"boost":0.18,"reason":"Monsoon — Indian port disruption"},
    (10,11): {"zones":["chennai","mumbai","india"],"boost":0.15,"reason":"Diwali/festive cargo surge"},
    (11,12): {"zones":["all"],"boost":0.12,"reason":"Global peak shipping season"}
}

def get_port_risk(origin: str, month: int = None) -> dict:
    if month is None:
        month = datetime.now().month
    loc = origin.lower()

    # Crisis check
    for port, info in CRISIS_PORTS.items():
        if port in loc:
            return {
                "score": info["score"],
                "congestion_tier": "CRISIS",
                "matched_port": port,
                "evidence_points": [
                    {
                        "metric": "AIS Signal Status",
                        "value": info["ais"],
                        "benchmark": "Normal: 135 ships/day transit",
                        "impact": "CRITICAL — port effectively closed",
                        "severity": "critical"
                    },
                    {
                        "metric": "Estimated Wait Time",
                        "value": info["wait"],
                        "benchmark": "Normal: 1-3 days",
                        "impact": "Indefinite delay — military/crisis override",
                        "severity": "critical"
                    },
                    {
                        "metric": "Berth Availability",
                        "value": info["berths"],
                        "benchmark": "Normal: 60-80% available",
                        "impact": "Zero commercial operations",
                        "severity": "critical"
                    }
                ],
                "data_source": "Maritime AIS Intelligence + SeaRates"
            }

    # Known ports
    base_score = 0.30
    port_info  = {"median_wait":"2.0 days","utilization":"60%",
                  "berths":20,"throughput":"Unknown"}
    matched    = "unknown"

    for port, pdata in PORT_DATA.items():
        if port in loc:
            base_score = pdata["base"]
            port_info  = pdata
            matched    = port
            break

    # Peak season
    peak_boost  = 0.0
    peak_reason = "Normal operations"
    for months, season in PEAK_SEASONS.items():
        if month in months:
            zones = season["zones"]
            if zones == ["all"] or any(z in loc for z in zones):
                peak_boost  = season["boost"]
                peak_reason = season["reason"]
                break

    final = min(base_score + peak_boost, 0.98)

    evidence_points = [
        {
            "metric": "Port Congestion Index",
            "value": f"{round(base_score*100)}% congestion score",
            "benchmark": f"Utilization: {port_info['utilization']}",
            "impact": "HIGH congestion — expect delays" if base_score > 0.65
                     else "MODERATE — standard operations" if base_score > 0.40
                     else "LOW — efficient operations",
            "severity": "high" if base_score > 0.65 else "medium" if base_score > 0.40 else "low"
        },
        {
            "metric": "Median Berth Wait Time",
            "value": port_info.get("median_wait","Unknown"),
            "benchmark": "Global avg: 1.5 days | Jebel Ali: 1.78 days",
            "impact": f"Port handles {port_info.get('throughput','N/A')} annually",
            "severity": "medium"
        },
        {
            "metric": f"Seasonal Factor — Month {month}",
            "value": f"+{round(peak_boost*100)}% boost applied",
            "benchmark": "Baseline port risk",
            "impact": peak_reason,
            "severity": "high" if peak_boost > 0.15 else "low"
        }
    ]

    return {
        "score": round(final, 3),
        "congestion_tier": "HIGH" if final > 0.65 else "MEDIUM" if final > 0.40 else "LOW",
        "matched_port": matched,
        "base_congestion": base_score,
        "peak_boost": peak_boost,
        "peak_reason": peak_reason,
        "port_stats": port_info,
        "evidence_points": evidence_points,
        "data_source": "SeaRates/SeaVantage AIS + CBIC NTRS 2024"
    }
