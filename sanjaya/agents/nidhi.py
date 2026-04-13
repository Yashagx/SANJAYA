import joblib, json, shap
import numpy as np
import pandas as pd
import os

MODEL_PATH    = os.path.join(os.path.dirname(__file__), '..', 'model', 'sanjaya_model.pkl')
FEATURES_PATH = os.path.join(os.path.dirname(__file__), '..', 'model', 'features.json')

_model    = None
_explainer= None
_features = None

def load_model():
    global _model, _explainer, _features
    if _model is None:
        _model    = joblib.load(MODEL_PATH)
        _features = json.load(open(FEATURES_PATH))
        _explainer= shap.TreeExplainer(_model)
    return _model, _explainer, _features

def get_delay_probability(features: dict) -> tuple:
    model, explainer, feature_names = load_model()

    row = pd.DataFrame([[features.get(f, 0) for f in feature_names]],
                       columns=feature_names)
    p_delay     = float(model.predict_proba(row)[0][1])
    shap_vals   = explainer.shap_values(row)[0].tolist()

    # Build evidence points from feature contributions
    shap_pairs  = sorted(zip(feature_names, shap_vals),
                         key=lambda x: abs(x[1]), reverse=True)

    # Feature explanations
    FEATURE_EXPLAIN = {
        "Days for shipping (real)": "Actual transit days recorded",
        "Days for shipment (scheduled)": "Originally planned transit days",
        "Benefit per order": "Profit margin per order ($)",
        "Sales per customer": "Customer revenue value ($)",
        "Order Item Discount Rate": "Discount rate applied to order",
        "Order Item Profit Ratio": "Profit ratio for this shipment",
        "Order Item Quantity": "Number of units/TEUs in shipment",
        "Category Id": "Product category classification",
        "Shipping_Mode_Encoded": "Transport class (0=Standard, 3=Same Day)",
        "Order_Month": "Month of departure (seasonality)"
    }

    evidence_points = []
    for feat, shap_val in shap_pairs[:4]:
        feat_val  = features.get(feat, 0)
        direction = "INCREASES delay risk" if shap_val > 0 else "DECREASES delay risk"
        impact    = "HIGH" if abs(shap_val) > 0.3 else "MEDIUM" if abs(shap_val) > 0.1 else "LOW"
        evidence_points.append({
            "feature": feat,
            "value": feat_val,
            "shap_contribution": round(shap_val, 4),
            "direction": direction,
            "impact": impact,
            "explanation": FEATURE_EXPLAIN.get(feat, feat),
            "interpretation": (
                f"Gap of {feat_val - features.get('Days for shipment (scheduled)',3):.0f} days "
                f"over schedule — major delay signal"
                if "real" in feat.lower() else
                f"Value {feat_val} {'pushes risk up' if shap_val > 0 else 'reduces risk'} "
                f"by {abs(shap_val):.3f} SHAP units"
            )
        })

    # Delay gap analysis
    days_real  = features.get("Days for shipping (real)", 5)
    days_sched = features.get("Days for shipment (scheduled)", 3)
    delay_gap  = days_real - days_sched

    return p_delay, shap_vals, {
        "evidence_points": evidence_points,
        "delay_gap_days": delay_gap,
        "delay_gap_severity": "CRITICAL" if delay_gap > 5 else "HIGH" if delay_gap > 2 else "MEDIUM" if delay_gap > 0 else "LOW",
        "model_type": "XGBoost (n_estimators=200, max_depth=6)",
        "training_records": 180519,
        "model_accuracy": "97.44%",
        "auc_roc": "0.9731",
        "data_source": "Trained on DataCo Supply Chain Dataset (180,519 records)"
    }
