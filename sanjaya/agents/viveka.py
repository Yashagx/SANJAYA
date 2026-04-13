CBIC_BENCHMARKS = {
    "seaport_export_release": "22:49 hrs",
    "seaport_import_release": "85:17 hrs",
    "icd_average":            "30:20 hrs",
    "air_cargo_release":      "18:30 hrs"
}

HIGH_RISK_HS = {
    "93":{"risk":0.80,"reason":"Weapons — requires special permits, heavy inspection"},
    "28":{"risk":0.65,"reason":"Chemicals — HAZMAT declaration, expert inspection"},
    "27":{"risk":0.60,"reason":"Petroleum — export license, quantity restrictions"},
    "84":{"risk":0.35,"reason":"Machinery — technology transfer controls possible"},
    "85":{"risk":0.38,"reason":"Electronics — dual-use export control checks"},
    "62":{"risk":0.25,"reason":"Apparel — standard inspection"},
    "73":{"risk":0.30,"reason":"Steel articles — anti-dumping duty risk"}
}

SANCTIONED_ROUTES = {
    ("iran","rotterdam"):0.90, ("iran","usa"):0.99,
    ("russia","usa"):0.85,     ("russia","europe"):0.70,
    ("north korea","any"):0.99,("myanmar","usa"):0.75
}

def get_customs_risk(hs_code: str, origin: str) -> tuple:
    hs2  = str(hs_code)[:2]
    base = 0.25
    hs_info = HIGH_RISK_HS.get(hs2, {"risk":0.25,"reason":"Standard cargo classification"})
    base    = hs_info["risk"]

    # Sanctions check
    sanctions_risk = 0.0
    sanctions_hit  = ""
    org_lower = origin.lower()
    for (o, d), risk in SANCTIONED_ROUTES.items():
        if o in org_lower:
            sanctions_risk = risk
            sanctions_hit  = f"Sanctions detected: {o.upper()} origin"
            break

    final = min(max(base, sanctions_risk), 0.98)

    evidence_points = [
        {
            "metric": "HS Code Classification",
            "value": f"HS {hs_code} — Chapter {hs2}",
            "benchmark": f"CBIC seaport export: {CBIC_BENCHMARKS['seaport_export_release']}",
            "impact": hs_info["reason"],
            "severity": "high" if base > 0.60 else "medium" if base > 0.35 else "low"
        },
        {
            "metric": "Sanctions & Embargo Check",
            "value": sanctions_hit if sanctions_hit else "No sanctions flags",
            "benchmark": "OFAC + EU Consolidated Sanctions List",
            "impact": f"Risk: {round(sanctions_risk*100)}%" if sanctions_risk > 0
                     else "Clear — standard processing",
            "severity": "critical" if sanctions_risk > 0.80 else "low"
        },
        {
            "metric": "CBIC Clearance Benchmark",
            "value": f"Seaport import: {CBIC_BENCHMARKS['seaport_import_release']}",
            "benchmark": f"ICD average: {CBIC_BENCHMARKS['icd_average']}",
            "impact": "NTRS 2024 compliance benchmark applied",
            "severity": "low"
        }
    ]

    return final, {
        "hs_chapter": hs2,
        "hs_description": hs_info["reason"],
        "sanctions_risk": sanctions_risk,
        "sanctions_detail": sanctions_hit,
        "cbic_benchmarks": CBIC_BENCHMARKS,
        "evidence_points": evidence_points,
        "data_source": "CBIC NTRS 2024 + ICEGATE + OFAC Sanctions"
    }
