import pandas as pd
import numpy as np
import json
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

# Load data
df = pd.read_csv("data/DataCoSupplyChainDataset.csv", encoding="latin-1")
print(f"Loaded: {df.shape}")

# Feature engineering
df["Shipping_Mode_Encoded"] = df["Shipping Mode"].map({
    "Standard Class": 0,
    "Second Class": 1,
    "First Class": 2,
    "Same Day": 3
}).fillna(0)

df["order_date_parsed"] = pd.to_datetime(
    df["order date (DateOrders)"], errors="coerce"
)
df["Order_Month"] = df["order_date_parsed"].dt.month.fillna(0).astype(int)

FEATURES = [
    "Days for shipping (real)",
    "Days for shipment (scheduled)",
    "Benefit per order",
    "Sales per customer",
    "Order Item Discount Rate",
    "Order Item Profit Ratio",
    "Order Item Quantity",
    "Category Id",
    "Shipping_Mode_Encoded",
    "Order_Month"
]
TARGET = "Late_delivery_risk"

df_clean = df[FEATURES + [TARGET]].dropna()
print(f"After dropna: {df_clean.shape}")

X = df_clean[FEATURES]
y = df_clean[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    eval_metric="logloss",
    random_state=42
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=50
)

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

acc = round(accuracy_score(y_test, y_pred) * 100, 2)
auc = round(roc_auc_score(y_test, y_prob), 4)

print(f"\n[OK] ACCURACY: {acc}%")
print(f"[OK] AUC-ROC:  {auc}")
print("\n", classification_report(y_test, y_pred))

# Save model and features
joblib.dump(model, "model/sanjaya_model.pkl")
with open("model/features.json", "w") as f:
    json.dump(FEATURES, f)

print("\n[OK] model/sanjaya_model.pkl saved")
print("[OK] model/features.json saved")
