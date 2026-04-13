# SANJAYA AppSheet Setup

> Complete configuration guide for connecting Google Sheets + Apps Script to the SANJAYA Shipment Risk Intelligence API.

---

## Base API URL

```
https://nxvg8lbkrh.execute-api.ap-south-2.amazonaws.com/prod
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | `POST` | Assess shipment risk for a single shipment |
| `/health` | `GET` | Health check |

---

## Step 1 — Create the Input Google Sheet

Create a Google Sheet called **`SANJAYA_Inputs`** with the following columns:

| Column | Header | Description |
|--------|--------|-------------|
| A | `vessel_id` | Unique vessel identifier |
| B | `origin` | Origin port name |
| C | `destination` | Destination port name |
| D | `days_real` | Actual transit days |
| E | `days_scheduled` | Scheduled transit days |
| F | `benefit_per_order` | Benefit per order (USD) |
| G | `sales_per_customer` | Sales per customer (USD) |
| H | `discount_rate` | Discount rate (decimal) |
| I | `profit_ratio` | Profit ratio (decimal) |
| J | `quantity` | Shipment quantity |
| K | `category_id` | Product category ID |
| L | `shipping_mode_encoded` | Encoded shipping mode |
| M | `month` | Month of shipment (1–12) |
| N | `hs_code` | HS tariff code |

### Sample Data Row

| vessel_id | origin | destination | days_real | days_scheduled | benefit_per_order | sales_per_customer | discount_rate | profit_ratio | quantity | category_id | shipping_mode_encoded | month | hs_code |
|-----------|--------|-------------|-----------|----------------|-------------------|--------------------|---------------|--------------|----------|-------------|-----------------------|-------|---------|
| MV-CHENNAI-STAR | Khor Fakkan | Rotterdam | 8 | 3 | -50 | 500 | 0.05 | -0.1 | 8400 | 73 | 0 | 2 | 8471 |

---

## Step 2 — Create the Output Google Sheet

Create a Google Sheet called **`SANJAYA_Results`** with the following columns:

| Column | Header | Description |
|--------|--------|-------------|
| A | `timestamp` | When the assessment was run |
| B | `vessel_id` | Vessel identifier (from API response) |
| C | `route` | Route string (origin → destination) |
| D | `risk_score` | Overall risk score (0–100) |
| E | `risk_level` | Risk classification (`LOW` / `MEDIUM` / `CRITICAL`) |
| F | `recommendation` | AI-generated recommendation |
| G | `p_delay` | Delay prediction score |
| H | `s_weather` | Weather severity score |
| I | `s_geo` | Geopolitical risk score |
| J | `c_port` | Port congestion score |
| K | `customs_risk` | Customs/tariff risk score |

---

## Step 3 — Add the Google Apps Script

> **How to open the script editor:**  
> In your Google Sheet, go to **Extensions → Apps Script**, then replace the default code with the script below.

```javascript
function assessShipmentRisk() {
  var inputSheet = SpreadsheetApp.getActiveSpreadsheet()
    .getSheetByName("SANJAYA_Inputs");
  var outputSheet = SpreadsheetApp.getActiveSpreadsheet()
    .getSheetByName("SANJAYA_Results");
  
  var lastRow = inputSheet.getLastRow();
  var data = inputSheet.getRange(2, 1, lastRow - 1, 14).getValues();
  
  var apiUrl = "https://nxvg8lbkrh.execute-api.ap-south-2.amazonaws.com/prod/predict";
  
  // Clear previous results (keep header)
  if (outputSheet.getLastRow() > 1) {
    outputSheet.getRange(2, 1, outputSheet.getLastRow() - 1, 11).clearContent();
  }
  
  for (var i = 0; i < data.length; i++) {
    var row = data[i];
    if (!row[0]) continue; // skip empty rows
    
    var payload = {
      vessel_id: row[0],
      origin: row[1],
      destination: row[2],
      days_real: Number(row[3]),
      days_scheduled: Number(row[4]),
      benefit_per_order: Number(row[5]),
      sales_per_customer: Number(row[6]),
      discount_rate: Number(row[7]),
      profit_ratio: Number(row[8]),
      quantity: Number(row[9]),
      category_id: Number(row[10]),
      shipping_mode_encoded: Number(row[11]),
      month: Number(row[12]),
      hs_code: String(row[13])
    };
    
    var options = {
      method: "POST",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
    
    try {
      var response = UrlFetchApp.fetch(apiUrl, options);
      var result = JSON.parse(response.getContentText());
      
      // Color code based on risk
      var riskColor = "#00ff00"; // green
      if (result.risk_level === "CRITICAL") riskColor = "#ff0000";
      else if (result.risk_level === "MEDIUM") riskColor = "#ff9900";
      
      var outputRow = [
        new Date(),
        result.vessel_id,
        result.route,
        result.risk_score,
        result.risk_level,
        result.recommendation,
        result.breakdown.p_delay,
        result.breakdown.s_weather,
        result.breakdown.s_geo,
        result.breakdown.c_port,
        result.breakdown.customs_risk
      ];
      
      var targetRow = outputSheet.getLastRow() + 1;
      outputSheet.getRange(targetRow, 1, 1, 11).setValues([outputRow]);
      
      // Color the risk score cell
      outputSheet.getRange(targetRow, 4).setBackground(riskColor)
        .setFontColor("#ffffff").setFontWeight("bold");
      outputSheet.getRange(targetRow, 5).setBackground(riskColor)
        .setFontColor("#ffffff").setFontWeight("bold");
        
    } catch(e) {
      Logger.log("Error for row " + i + ": " + e.toString());
    }
    
    Utilities.sleep(500); // avoid rate limiting
  }
  
  Logger.log("SANJAYA assessment complete. " + data.length + " shipments processed.");
}

// Auto-trigger when sheet is edited
function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  if (sheet.getName() === "SANJAYA_Inputs") {
    assessShipmentRisk();
  }
}
```

---

## Step 4 — Setup Instructions

### 4.1 Create Both Sheets in the Same Spreadsheet

1. Open [Google Sheets](https://sheets.google.com) and create a new spreadsheet.
2. Rename the first tab to **`SANJAYA_Inputs`** and add the header row (columns A–N as listed above).
3. Create a second tab named **`SANJAYA_Results`** and add the header row (columns A–K as listed above).
4. Paste the sample data row into `SANJAYA_Inputs` row 2.

### 4.2 Add the Apps Script

1. Go to **Extensions → Apps Script**.
2. Delete any existing code in `Code.gs`.
3. Paste the full script from Step 3 above.
4. Click **💾 Save** (or `Ctrl+S`).
5. Click **▶ Run** and select `assessShipmentRisk`.
6. On first run, authorize the script when prompted (it needs permission to access the sheet and make external HTTP requests).

### 4.3 Verify the Auto-Trigger

The `onEdit(e)` function triggers automatically when you edit the `SANJAYA_Inputs` sheet. To test:

1. Add a new row of data to `SANJAYA_Inputs`.
2. Switch to the `SANJAYA_Results` tab — results should appear within a few seconds.
3. Risk scores will be **color-coded**:
   - 🟢 **Green** — Low risk
   - 🟠 **Orange** — Medium risk
   - 🔴 **Red** — Critical risk

> [!IMPORTANT]
> The `onEdit` simple trigger cannot make external `UrlFetchApp` calls in some configurations. If the auto-trigger doesn't fire the API call, set up an **installable trigger** instead:
> 1. In Apps Script, go to **Triggers** (clock icon in left sidebar).
> 2. Click **+ Add Trigger**.
> 3. Set: Function = `assessShipmentRisk`, Event source = `From spreadsheet`, Event type = `On change`.
> 4. Save and authorize.

---

## Step 5 — Connect to AppSheet (Optional Dashboard)

If you want a no-code mobile/web dashboard on top of the data:

1. Go to [AppSheet](https://www.appsheet.com/) and sign in with your Google account.
2. Click **Create → App → Start with existing data**.
3. Select the `SANJAYA_Results` Google Sheet as the data source.
4. AppSheet will auto-generate a basic app with views.
5. Customize:
   - Add a **Detail View** for each shipment risk result.
   - Add a **Dashboard View** combining a table + chart of risk scores.
   - Add **Color Rules**: format `risk_level` column with conditional colors.
   - Add a **Form View** connected to `SANJAYA_Inputs` to submit new assessments from mobile.

---

## API Reference

### POST `/predict`

**Request Body:**

```json
{
  "vessel_id": "MV-CHENNAI-STAR",
  "origin": "Khor Fakkan",
  "destination": "Rotterdam",
  "days_real": 8,
  "days_scheduled": 3,
  "benefit_per_order": -50,
  "sales_per_customer": 500,
  "discount_rate": 0.05,
  "profit_ratio": -0.1,
  "quantity": 8400,
  "category_id": 73,
  "shipping_mode_encoded": 0,
  "month": 2,
  "hs_code": "8471"
}
```

**Response:**

```json
{
  "vessel_id": "MV-CHENNAI-STAR",
  "route": "Khor Fakkan → Rotterdam",
  "risk_score": 72.5,
  "risk_level": "CRITICAL",
  "recommendation": "...",
  "breakdown": {
    "p_delay": 0.85,
    "s_weather": 0.6,
    "s_geo": 0.4,
    "c_port": 0.3,
    "customs_risk": 0.7
  }
}
```

---

> [!NOTE]
> This configuration connects your Google Sheets environment to the SANJAYA production API deployed on AWS (ap-south-2). Ensure the API endpoint is reachable and the Lambda function is deployed before testing.
