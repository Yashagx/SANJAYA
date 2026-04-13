import json
from datetime import datetime
from agents.vayu    import get_weather_risk
from agents.sanchar import get_geo_risk
from agents.nidhi   import get_delay_probability
from agents.darpana import get_port_risk
from agents.viveka  import get_customs_risk
from agents.marga   import get_road_risk
from agents.akasha  import get_air_risk

def get_departure_context(departure_date=None):
    if departure_date:
        try:
            dt = datetime.strptime(departure_date, "%Y-%m-%d")
            return {"month":dt.month,"day":dt.day,"date":departure_date}
        except: pass
    now = datetime.now()
    return {"month":now.month,"day":now.day,"date":str(now.date())}

def apply_nonlinear(score, weight, amplify=False):
    if amplify and score >= 0.7:
        return (score**1.8) * weight
    return score * weight

def apply_overrides(rs, p_delay, s_geo, c_port, s_weather):
    overrides = []
    adj = rs
    if p_delay >= 0.90:
        if adj < 75.0:
            adj = 75.0
            overrides.append(f"RULE-1: P_delay={p_delay:.3f}≥0.90 → floor to 75")
    elif p_delay >= 0.75:
        if adj < 60.0:
            adj = 60.0
            overrides.append(f"RULE-1b: P_delay={p_delay:.3f}≥0.75 → floor to 60")
    if s_geo >= 0.90:
        if adj < 85.0:
            adj = 85.0
            overrides.append(f"RULE-2: GeoRisk={s_geo:.3f}≥0.90 → crisis floor 85")
    if c_port >= 0.85:
        adj = min(adj+10.0, 99.0)
        overrides.append(f"RULE-3: PortRisk={c_port:.3f}≥0.85 → +10 boost")
    high = sum([p_delay>=0.80, s_geo>=0.70, c_port>=0.70, s_weather>=0.65])
    if high >= 3:
        if adj < 80.0:
            adj = 80.0
            overrides.append(f"RULE-4: {high} critical factors → compound floor 80")
    if p_delay >= 0.85 and s_geo >= 0.85:
        adj = min(max(adj, 90.0), 99.0)
        overrides.append("RULE-5: ML+Geo both critical → CRITICAL override")
    return round(adj,1), overrides

def get_risk_level(rs):
    if rs >= 85:   return "CRITICAL",  "#dc2626"
    elif rs >= 75: return "HIGH",      "#ea580c"
    elif rs >= 60: return "MEDIUM-HIGH","#d97706"
    elif rs >= 45: return "MEDIUM",    "#ca8a04"
    elif rs >= 30: return "LOW-MEDIUM","#2563eb"
    else:          return "LOW",       "#16a34a"

def get_rerouting(origin, destination, mode, rs):
    if mode == "sea":
        if any(x in origin.lower() for x in ["hormuz","gulf","khor fakkan"]):
            return [
                {"route":"Continue via Strait of Hormuz",
                 "extra_days":0,"on_time_probability":"3%",
                 "extra_cost":"$1,000,000+","verdict":"DO NOT PROCEED"},
                {"route":"Reroute via Cape of Good Hope",
                 "extra_days":13,"on_time_probability":"94%",
                 "extra_cost":"$180,000","verdict":"RECOMMENDED"},
                {"route":"Reroute via Suez/Red Sea",
                 "extra_days":3,"on_time_probability":"45%",
                 "extra_cost":"$60,000","verdict":"NOT ADVISED — Houthi risk"},
                {"route":"Wait at Khor Fakkan anchorage",
                 "extra_days":30,"on_time_probability":"Unknown",
                 "extra_cost":"$15,000/day","verdict":"LAST RESORT"}
            ]
        elif rs >= 75:
            return [
                {"route":"Current route (high risk)",
                 "extra_days":0,"on_time_probability":f"{max(5,int(100-rs))}%",
                 "extra_cost":"Risk premium","verdict":"NOT ADVISED"},
                {"route":"Alternative sea corridor",
                 "extra_days":7,"on_time_probability":"78%",
                 "extra_cost":"+$90,000","verdict":"RECOMMENDED"},
                {"route":"Split shipment — partial air",
                 "extra_days":-5,"on_time_probability":"88%",
                 "extra_cost":"+$250,000","verdict":"HIGH VALUE CARGO ONLY"}
            ]
    elif mode == "road":
        return [
            {"route":"Current road route",
             "extra_days":0,"on_time_probability":f"{max(10,int(100-rs))}%",
             "extra_cost":"Standard","verdict":"ASSESS CONDITIONS"},
            {"route":"Rail alternative",
             "extra_days":1,"on_time_probability":"82%",
             "extra_cost":"+15%","verdict":"RECOMMENDED if monsoon"},
            {"route":"Air freight",
             "extra_days":-2,"on_time_probability":"91%",
             "extra_cost":"+300%","verdict":"CRITICAL CARGO ONLY"}
        ]
    elif mode == "air":
        return [
            {"route":"Current air route",
             "extra_days":0,"on_time_probability":f"{max(20,int(100-rs))}%",
             "extra_cost":"Standard","verdict":"MONITOR"},
            {"route":"Alternative hub routing",
             "extra_days":1,"on_time_probability":"85%",
             "extra_cost":"+20%","verdict":"IF CONGESTION > 70"},
            {"route":"Sea freight fallback",
             "extra_days":14,"on_time_probability":"92%",
             "extra_cost":"-70%","verdict":"NON-URGENT CARGO"}
        ]
    return []

def orchestrate(payload: dict) -> dict:
    origin      = payload.get("origin","")
    destination = payload.get("destination","")
    mode        = payload.get("transport_mode","sea").lower()
    dep_date    = payload.get("departure_date")
    time_ctx    = get_departure_context(dep_date)
    month       = payload.get("month") or time_ctx["month"]

    print(f"[ARJUNA] {origin} → {destination} | {mode} | Month:{month}")

    # Fire all agents — collect full evidence
    print("[VAYU] Weather...")
    weather   = get_weather_risk(origin, month)
    s_weather = weather["score"]

    print("[SANCHAR] Geopolitics...")
    geo       = get_geo_risk(origin, destination)
    s_geo     = geo["score"]

    print("[NIDHI] ML inference...")
    features = {
        "Days for shipping (real)":      payload.get("days_real",5),
        "Days for shipment (scheduled)": payload.get("days_scheduled",3),
        "Benefit per order":             payload.get("benefit_per_order",50),
        "Sales per customer":            payload.get("sales_per_customer",200),
        "Order Item Discount Rate":      payload.get("discount_rate",0.1),
        "Order Item Profit Ratio":       payload.get("profit_ratio",0.05),
        "Order Item Quantity":           payload.get("quantity",10),
        "Category Id":                   payload.get("category_id",73),
        "Shipping_Mode_Encoded":         payload.get("shipping_mode_encoded",0),
        "Order_Month":                   month
    }
    p_delay, shap_vals, nidhi_meta = get_delay_probability(features)
    delay_gap = payload.get("days_real",5) - payload.get("days_scheduled",3)
    if delay_gap > 5:
        p_delay = min(p_delay*1.15, 0.99)

    print("[DARPANA/MARGA/AKASHA] Transport...")
    if mode == "sea":
        port_data = get_port_risk(origin, month)
        c_port    = port_data["score"]
        transport_evidence = port_data
    elif mode == "road":
        road_data = get_road_risk(origin, destination, month, dep_date)
        c_port    = road_data["score"]
        transport_evidence = road_data
    elif mode == "air":
        air_data  = get_air_risk(origin, destination, month)
        c_port    = air_data["score"]
        transport_evidence = air_data
    else:
        c_port    = 0.30
        transport_evidence = {"score":0.30,"evidence_points":[]}

    print("[VIVEKA] Customs...")
    customs_risk, viveka_meta = get_customs_risk(
        payload.get("hs_code","8471"), origin
    )

    # Non-linear composite
    W_d, W_w, W_g, W_p = 0.50, 0.18, 0.20, 0.12
    t_delay   = apply_nonlinear(p_delay,   W_d, amplify=True)
    t_weather = apply_nonlinear(s_weather, W_w, amplify=True)
    t_geo     = apply_nonlinear(s_geo,     W_g, amplify=True)
    t_port    = apply_nonlinear(c_port,    W_p)
    rs_raw    = (t_delay+t_weather+t_geo+t_port)*100
    rs_score  = round(min(rs_raw, 99.0), 1)

    rs_final, overrides = apply_overrides(rs_score, p_delay, s_geo, c_port, s_weather)
    risk_level, color   = get_risk_level(rs_final)

    if risk_level in ["CRITICAL","HIGH"]:
        recommendation = f"IMMEDIATE ACTION — {risk_level} risk. Rerouting advised."
    elif risk_level in ["MEDIUM-HIGH","MEDIUM"]:
        recommendation = "MONITOR — Prepare contingency plan."
    else:
        recommendation = "PROCEED — Risk within acceptable parameters."

    return {
        "vessel_id":      payload.get("vessel_id","UNKNOWN"),
        "route":          f"{origin} → {destination}",
        "transport_mode": mode,
        "departure_date": time_ctx["date"],
        "season":         weather.get("seasonal_context",{}).get("season","normal"),
        "risk_score":     rs_final,
        "risk_level":     risk_level,
        "color":          color,
        "recommendation": recommendation,
        "formula": {
            "weights":  {"p_delay":W_d,"weather":W_w,"geo":W_g,"port":W_p},
            "terms":    {"delay":round(t_delay,4),"weather":round(t_weather,4),
                         "geo":round(t_geo,4),"port":round(t_port,4)},
            "raw_score": round(rs_raw,1),
            "final_score": rs_final,
            "nonlinear": True
        },
        "breakdown": {
            "p_delay":      round(p_delay,4),
            "s_weather":    round(s_weather,4),
            "s_geo":        round(s_geo,4),
            "c_port":       round(c_port,4),
            "customs_risk": round(customs_risk,4),
            "delay_gap_days": delay_gap
        },
        "rule_overrides": overrides,
        "evidence": {
            "weather":    weather,
            "geopolitics": geo,
            "transport":  transport_evidence,
            "ml":         nidhi_meta,
            "customs":    viveka_meta,
            "temporal":   time_ctx
        },
        "shap_top5":         sorted(
            zip(features.keys(), shap_vals),
            key=lambda x: abs(x[1]), reverse=True
        )[:5],
        "rerouting_options": get_rerouting(origin, destination, mode, rs_final)
    }
