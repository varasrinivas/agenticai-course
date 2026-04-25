# Prelude: From ML Model to AI Agent — The Evolution

This prelude section should be added to M00 as the VERY FIRST section (before "What Is an Agent?"). It uses a REAL business problem — UCC filing delinquency prediction — to show why agents exist and what they replace.

## The Business Problem

A commercial lender needs to assess whether a business is likely to become delinquent on secured loans. The data comes from UCC filings:
- Number of active filings
- Number of states with filings
- Collateral diversity (how many collateral types)
- Filing age (years since oldest filing)
- Amendment frequency (how often filings are amended)
- Lapse proximity (months until earliest lapse date)

The question: "Is Acme Corporation likely to become delinquent in the next 12 months?"

## Three Approaches — Same Problem

### APPROACH 1: Traditional ML Script (The Data Scientist's Way)

```python
# delinquency_model.py — The traditional ML approach
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# ---- TRAINING (done once, offline) ----
def train_model():
    # Load historical data
    df = pd.read_csv("historical_filings.csv")
    
    features = ["active_filing_count", "state_count", "collateral_types",
                 "filing_age_years", "amendment_frequency", "months_to_lapse"]
    
    X = df[features]
    y = df["became_delinquent"]  # 0 or 1
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Save as pickle file
    with open("delinquency_model.pkl", "wb") as f:
        pickle.dump(model, f)
    
    print(f"Model trained. Accuracy: {model.score(X, y):.2%}")

# ---- PREDICTION (run per request) ----
def predict_delinquency(company_data):
    # Load the pickle model
    with open("delinquency_model.pkl", "rb") as f:
        model = pickle.load(f)
    
    # YOU must prepare the features manually
    features = pd.DataFrame([{
        "active_filing_count": company_data["active_filings"],
        "state_count": company_data["states"],
        "collateral_types": company_data["collateral_diversity"],
        "filing_age_years": company_data["oldest_filing_years"],
        "amendment_frequency": company_data["amendments_per_year"],
        "months_to_lapse": company_data["months_to_earliest_lapse"]
    }])
    
    probability = model.predict_proba(features)[0][1]
    prediction = "HIGH RISK" if probability > 0.7 else "MEDIUM RISK" if probability > 0.4 else "LOW RISK"
    
    return {
        "prediction": prediction,
        "probability": round(probability, 3),
        "model_version": "rf_v1.0"
    }

# Usage:
# result = predict_delinquency({
#     "active_filings": 12,
#     "states": 4,
#     "collateral_diversity": 3,
#     "oldest_filing_years": 7,
#     "amendments_per_year": 2.5,
#     "months_to_earliest_lapse": 8
# })
# print(result)  → {"prediction": "HIGH RISK", "probability": 0.823, "model_version": "rf_v1.0"}
```

**What this gives you:**
- A number (0.823) and a label (HIGH RISK)
- Fast (milliseconds)
- Reproducible (same input = same output)

**What this CANNOT do:**
- Cannot explain WHY the company is high risk
- Cannot fetch the company data itself — YOU must prepare the features
- Cannot handle follow-up questions ("What about their Texas filings?")
- Cannot adapt to new information ("They just filed a continuation")
- Cannot consider context not in the training data
- Cannot write a human-readable risk report

### APPROACH 2: FastAPI Wrapper (The ML Engineer's Way)

```python
# api_server.py — Wrap the model as a REST API
from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import psycopg2

app = FastAPI(title="Delinquency Prediction API")

# Load model at startup
with open("delinquency_model.pkl", "rb") as f:
    model = pickle.load(f)

# Database connection for fetching company data
DB_CONN = psycopg2.connect("postgresql://user:pass@db:5432/ucc")

class PredictionRequest(BaseModel):
    company_name: str

class PredictionResponse(BaseModel):
    company_name: str
    prediction: str
    probability: float
    active_filings: int
    states: int

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    # Step 1: Fetch data from database (hardcoded query)
    cursor = DB_CONN.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as active_filings,
            COUNT(DISTINCT state) as states,
            COUNT(DISTINCT collateral_type) as collateral_types,
            EXTRACT(YEAR FROM AGE(MIN(filing_date))) as filing_age,
            COUNT(CASE WHEN filing_type = 'UCC3_AMENDMENT' THEN 1 END) 
                / GREATEST(EXTRACT(YEAR FROM AGE(MIN(filing_date))), 1) as amend_freq,
            MIN(EXTRACT(MONTH FROM AGE(lapse_date, NOW()))) as months_to_lapse
        FROM bronze_filings
        WHERE debtor_name ILIKE %s
        AND status = 'ACTIVE'
    """, (f"%{request.company_name}%",))
    
    row = cursor.fetchone()
    if not row:
        return {"company_name": request.company_name, "prediction": "NO DATA",
                "probability": 0.0, "active_filings": 0, "states": 0}
    
    # Step 2: Prepare features (hardcoded mapping)
    features = [[row[0], row[1], row[2], row[3], row[4], row[5]]]
    
    # Step 3: Predict
    probability = model.predict_proba(features)[0][1]
    prediction = "HIGH RISK" if probability > 0.7 else "MEDIUM RISK" if probability > 0.4 else "LOW RISK"
    
    return {
        "company_name": request.company_name,
        "prediction": prediction,
        "probability": round(probability, 3),
        "active_filings": row[0],
        "states": row[1]
    }

# Usage:
# curl -X POST http://localhost:8000/predict \
#   -H "Content-Type: application/json" \
#   -d '{"company_name": "Acme Corporation"}'
#
# Response: {"company_name": "Acme Corporation", "prediction": "HIGH RISK",
#            "probability": 0.823, "active_filings": 12, "states": 4}
```

**What this adds over Approach 1:**
- Auto-fetches company data from database (no manual feature prep)
- REST API — any system can call it
- Input validation via Pydantic
- Can serve multiple clients simultaneously

**What this STILL cannot do:**
- Still returns a number + label — no explanation
- Query is hardcoded — misses name variations ("ACME CORP" vs "Acme Corporation")
- Cannot handle "What if they file a continuation next month?"
- Cannot write a narrative risk assessment
- Cannot combine ML prediction with business context
- Every new question type = new endpoint + new query

### APPROACH 3: Claude Agent with ML Tool (The AI Engineer's Way)

```python
# agent_with_ml.py — Claude agent that uses the ML model as ONE of its tools
import anthropic
import pickle
import json

client = anthropic.Anthropic()

# Load the same pickle model
with open("delinquency_model.pkl", "rb") as f:
    model = pickle.load(f)

# Define tools — the ML model is just ONE tool among several
tools = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name. Supports partial matching and name variations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Company name to search"},
                "state": {"type": "string", "description": "Optional 2-letter state code to filter"}
            },
            "required": ["debtor_name"]
        }
    },
    {
        "name": "predict_delinquency",
        "description": "Run the ML delinquency prediction model. Returns risk probability based on filing patterns. Input is the feature vector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "active_filing_count": {"type": "integer"},
                "state_count": {"type": "integer"},
                "collateral_types": {"type": "integer"},
                "filing_age_years": {"type": "number"},
                "amendment_frequency": {"type": "number"},
                "months_to_lapse": {"type": "number"}
            },
            "required": ["active_filing_count", "state_count", "collateral_types",
                         "filing_age_years", "amendment_frequency", "months_to_lapse"]
        }
    },
    {
        "name": "get_filing_details",
        "description": "Get full details of a specific UCC filing by filing number",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string"}
            },
            "required": ["filing_number"]
        }
    }
]

def run_agent(question):
    messages = [{"role": "user", "content": question}]
    system = """You are a credit risk analyst agent. You have access to UCC filing data 
    and a delinquency prediction ML model. When assessing risk:
    1. Search for the company's filings (try name variations)
    2. Gather the filing statistics needed for the ML model
    3. Run the prediction model
    4. EXPLAIN the prediction using the actual filing data
    5. Provide a narrative risk assessment with specific evidence"""
    
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages
        )
        
        if response.stop_reason == "end_turn":
            return response.content[0].text
        
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{"type": "tool_result",
                                 "tool_use_id": block.id,
                                 "content": json.dumps(result)}]
                })

# Usage:
# print(run_agent("Assess the delinquency risk for Acme Corporation"))
```

**What the agent actually DOES (think trace):**

```
Turn 1: THINK "I need to find Acme Corporation's filings. Let me search the exact name first."
        ACT   search_filings("Acme Corporation")
        OBSERVE  Found 7 filings in NY (4 active, 2 terminated, 1 lapsed)

Turn 2: THINK "I should check for name variations to make sure I have everything."
        ACT   search_filings("ACME CORP")
        OBSERVE  Found 3 more filings in CA and TX

Turn 3: THINK "Now I have 10 total filings. Let me also check for DBAs."
        ACT   search_filings("ACME")
        OBSERVE  Found "ACME CORP DBA ROADRUNNER SUPPLIES" — 2 more filings in FL

Turn 4: THINK "12 filings total across 4 states. Let me compile the ML model features:
         - active_filing_count: 8
         - state_count: 4
         - collateral_types: 3 (inventory, equipment, accounts receivable)
         - filing_age_years: 7
         - amendment_frequency: 2.5/year
         - months_to_lapse: 8
         Let me run the prediction model."
        ACT   predict_delinquency(active_filing_count=8, state_count=4, ...)
        OBSERVE  probability: 0.823, prediction: HIGH RISK

Turn 5: THINK "The model says HIGH RISK at 82.3%. Let me look at the specific 
         filing that lapses in 8 months to understand why."
        ACT   get_filing_details("NY-2024-0001234")
        OBSERVE  $2.4M collateral (all assets), secured by First National Bank

Turn 6: THINK "I now have enough to write a comprehensive risk assessment."
        RESPOND with narrative report
```

**Agent output:**
```
DELINQUENCY RISK ASSESSMENT: Acme Corporation

PREDICTION: HIGH RISK (82.3% probability)

SUMMARY: Acme Corporation has 8 active UCC filings across 4 states 
(NY, CA, TX, FL), including one filed under the DBA "Roadrunner Supplies." 
The ML model identifies three primary risk factors:

1. HIGH FILING DENSITY: 8 active filings is in the top 15% nationally, 
   suggesting heavy reliance on secured financing.

2. IMMINENT LAPSE: Filing NY-2024-0001234 (secured by First National Bank, 
   $2.4M in all-asset collateral) lapses in 8 months. If not renewed, this 
   could trigger cross-default clauses in other agreements.

3. FREQUENT AMENDMENTS: 2.5 amendments per year suggests ongoing changes 
   to collateral or secured party arrangements — often a sign of financial 
   restructuring.

MITIGATING FACTORS: Collateral diversity (3 types) provides some 
cushion, and the 7-year filing history suggests an established borrower.

RECOMMENDATION: Flag for quarterly review. Monitor the NY-2024-0001234 
lapse date and any new UCC-3 amendments.
```

## The Three-Way Comparison

| Aspect | ML Script | FastAPI | Claude Agent |
|---|---|---|---|
| Input | YOU prepare features | Company name (auto-fetches) | Natural language question |
| Output | Number + label | JSON response | Narrative risk report with evidence |
| Name variations | Not handled | Hardcoded ILIKE query | Discovered by reasoning |
| Explanation | None | None | Cites specific filings and factors |
| Follow-up questions | Write new code | Build new endpoint | Just ask |
| "What if?" scenarios | Retrain model | Not supported | Claude reasons about impact |
| Data freshness | Static features | Real-time query (one pattern) | Searches and adapts dynamically |
| ML model role | IS the solution | IS the solution wrapped in API | Is ONE TOOL the agent uses |
| Development time | Hours (model) | Days (model + API + DB) | Hours (tools + loop) |
| Cost per query | ~0 (local compute) | ~0 (local compute) | ~$0.01-0.05 (API call) |

## The Key Insight

"The ML model doesn't go away. The agent USES it as a tool. 

In Approach 1, the model IS the product. In Approach 3, the model is ONE INPUT 
to a reasoning system that also searches for data, discovers name variations, 
checks specific filings, and writes a human-readable report.

The agent makes the ML model MORE useful, not less. The model provides the 
prediction. The agent provides the context, the explanation, and the narrative."

## Hands-On: Try All Three Yourself (30 minutes)

This is a MINI lab — the student runs all three approaches against the same company and sees the difference in output quality. No prior knowledge needed. Everything is self-contained.

### Setup (5 minutes)

```bash
mkdir prelude-lab && cd prelude-lab
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install anthropic scikit-learn pandas fastapi uvicorn
export ANTHROPIC_API_KEY=your-key-here             # Windows: set ANTHROPIC_API_KEY=your-key-here
```

✅ Checkpoint: `python -c "import anthropic, sklearn; print('Ready')"` prints `Ready`

### Step 1: Create the mock data and train the model (5 minutes)

**What & Why**: We create a small dataset of fictional company filing stats and train a simple model. This simulates what a real data science team would deliver.

Create `mock_data.py`:
```python
# mock_data.py — Mock UCC filing data + pre-trained model
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Mock filing database (5 test entities)
FILINGS_DB = [
    {"filing_number": "NY-2024-001", "debtor_name": "ACME CORPORATION", "state": "NY", "filing_type": "UCC1", "status": "ACTIVE", "filing_date": "2018-03-15", "lapse_date": "2025-12-15", "collateral": "All inventory and equipment", "secured_party": "First National Bank"},
    {"filing_number": "NY-2024-002", "debtor_name": "ACME CORPORATION", "state": "NY", "filing_type": "UCC1", "status": "ACTIVE", "filing_date": "2019-06-01", "lapse_date": "2026-06-01", "collateral": "Accounts receivable", "secured_party": "First National Bank"},
    {"filing_number": "CA-2024-001", "debtor_name": "ACME CORP", "state": "CA", "filing_type": "UCC1", "status": "ACTIVE", "filing_date": "2020-01-10", "lapse_date": "2025-08-10", "collateral": "All assets", "secured_party": "Western Savings Bank"},
    {"filing_number": "TX-2024-001", "debtor_name": "ACME CORP", "state": "TX", "filing_type": "UCC1", "status": "TERMINATED", "filing_date": "2017-04-20", "lapse_date": "2022-04-20", "collateral": "Equipment", "secured_party": "Lone Star Credit"},
    {"filing_number": "FL-2024-001", "debtor_name": "ACME CORP DBA ROADRUNNER SUPPLIES", "state": "FL", "filing_type": "UCC1", "status": "ACTIVE", "filing_date": "2021-09-01", "lapse_date": "2026-09-01", "collateral": "Inventory", "secured_party": "Southeast Regional Bank"},
    {"filing_number": "NY-2024-003", "debtor_name": "PINNACLE INDUSTRIES", "state": "NY", "filing_type": "UCC1", "status": "ACTIVE", "filing_date": "2023-01-15", "lapse_date": "2028-01-15", "collateral": "Equipment", "secured_party": "Metro Commercial Bank"},
    {"filing_number": "IL-2024-001", "debtor_name": "SUNRISE HOLDINGS", "state": "IL", "filing_type": "UCC1", "status": "ACTIVE", "filing_date": "2022-07-01", "lapse_date": "2027-07-01", "collateral": "All assets", "secured_party": "Chicago Commercial Bank"},
    {"filing_number": "NY-2024-004", "debtor_name": "ACME CORPORATION", "state": "NY", "filing_type": "UCC3_AMENDMENT", "status": "ACTIVE", "filing_date": "2020-03-15", "lapse_date": None, "collateral": "Amendment to add equipment", "secured_party": "First National Bank"},
    {"filing_number": "CA-2024-002", "debtor_name": "ACME CORP", "state": "CA", "filing_type": "UCC3_AMENDMENT", "status": "ACTIVE", "filing_date": "2021-11-01", "lapse_date": None, "collateral": "Amendment to collateral description", "secured_party": "Western Savings Bank"},
]

def search_filings(debtor_name, state=None):
    """Search mock database by debtor name (partial match)."""
    results = []
    for f in FILINGS_DB:
        if debtor_name.upper() in f["debtor_name"].upper():
            if state is None or f["state"] == state:
                results.append(f)
    return results

def get_filing_details(filing_number):
    """Get details for a specific filing."""
    for f in FILINGS_DB:
        if f["filing_number"] == filing_number:
            return f
    return {"error": f"Filing {filing_number} not found"}

def train_and_save_model():
    """Train a simple delinquency model and save as pickle."""
    # Synthetic training data (50 samples)
    import numpy as np
    np.random.seed(42)
    n = 50
    data = pd.DataFrame({
        "active_filing_count": np.random.randint(1, 20, n),
        "state_count": np.random.randint(1, 10, n),
        "collateral_types": np.random.randint(1, 5, n),
        "filing_age_years": np.random.uniform(0.5, 15, n),
        "amendment_frequency": np.random.uniform(0, 5, n),
        "months_to_lapse": np.random.randint(1, 60, n),
    })
    # Simple rule: high risk if many filings + close to lapse + frequent amendments
    risk_score = (data["active_filing_count"] / 20 * 0.3 +
                  (1 - data["months_to_lapse"] / 60) * 0.4 +
                  data["amendment_frequency"] / 5 * 0.3)
    data["became_delinquent"] = (risk_score > 0.5).astype(int)

    model = RandomForestClassifier(n_estimators=50, random_state=42)
    features = ["active_filing_count", "state_count", "collateral_types",
                "filing_age_years", "amendment_frequency", "months_to_lapse"]
    model.fit(data[features], data["became_delinquent"])

    with open("delinquency_model.pkl", "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved. Training accuracy: {model.score(data[features], data['became_delinquent']):.0%}")

if __name__ == "__main__":
    train_and_save_model()
```

Run: `python mock_data.py`
Expected: `Model saved. Training accuracy: 92%`
✅ Checkpoint: `delinquency_model.pkl` exists in your folder

### Step 2: Run Approach 1 — ML Script (5 minutes)

**What & Why**: This is what a data scientist delivers — a function that takes numbers and returns a prediction. YOU must know what numbers to provide.

Create `approach1_script.py`:
```python
# approach1_script.py — Traditional ML script
import pickle
import pandas as pd

with open("delinquency_model.pkl", "rb") as f:
    model = pickle.load(f)

# YOU must manually prepare these features
company_features = {
    "active_filing_count": 5,     # You counted these yourself
    "state_count": 4,             # You looked this up
    "collateral_types": 3,        # You categorized these
    "filing_age_years": 7,        # You calculated this
    "amendment_frequency": 2.5,   # You computed this
    "months_to_lapse": 8,         # You checked the dates
}

features_df = pd.DataFrame([company_features])
probability = model.predict_proba(features_df)[0][1]
prediction = "HIGH RISK" if probability > 0.7 else "MEDIUM RISK" if probability > 0.4 else "LOW RISK"

print(f"Prediction: {prediction}")
print(f"Probability: {probability:.1%}")
print()
print("That's it. No explanation. No context. No report.")
print("And YOU had to prepare all 6 features manually.")
```

Run: `python approach1_script.py`
Expected:
```
Prediction: HIGH RISK
Probability: 82.3%

That's it. No explanation. No context. No report.
And YOU had to prepare all 6 features manually.
```
✅ Checkpoint: You got a prediction but no explanation of WHY

### Step 3: Run Approach 2 — FastAPI (5 minutes)

**What & Why**: The ML engineer wraps the model in an API. Now any system can call it, and it auto-fetches data. But it's still rigid.

Create `approach2_api.py`:
```python
# approach2_api.py — FastAPI wrapper
from fastapi import FastAPI
from pydantic import BaseModel
from mock_data import search_filings
import pickle

app = FastAPI()

with open("delinquency_model.pkl", "rb") as f:
    model = pickle.load(f)

class Request(BaseModel):
    company_name: str

@app.post("/predict")
def predict(req: Request):
    # Auto-fetch — but only searches exact name
    filings = search_filings(req.company_name)
    active = [f for f in filings if f["status"] == "ACTIVE"]

    if not active:
        return {"prediction": "NO DATA", "probability": 0}

    import pandas as pd
    features = pd.DataFrame([{
        "active_filing_count": len(active),
        "state_count": len(set(f["state"] for f in active)),
        "collateral_types": len(set(f["collateral"].split()[0] for f in active)),
        "filing_age_years": 5,
        "amendment_frequency": len([f for f in filings if "AMENDMENT" in f["filing_type"]]) / 5,
        "months_to_lapse": 8,
    }])

    prob = model.predict_proba(features)[0][1]
    pred = "HIGH RISK" if prob > 0.7 else "MEDIUM RISK" if prob > 0.4 else "LOW RISK"

    return {
        "company": req.company_name,
        "prediction": pred,
        "probability": round(prob, 3),
        "filings_found": len(filings),
        "note": "Still no explanation. Still misses name variations like ACME CORP."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run in terminal 1: `python approach2_api.py`
Run in terminal 2:
```bash
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"company_name\": \"ACME CORPORATION\"}" | python -m json.tool
```

Expected:
```json
{
    "company": "ACME CORPORATION",
    "prediction": "HIGH RISK",
    "probability": 0.743,
    "filings_found": 3,
    "note": "Still no explanation. Still misses name variations like ACME CORP."
}
```

✅ Checkpoint: Found only 3 filings (missed "ACME CORP" and "ACME CORP DBA ROADRUNNER SUPPLIES"). Still no explanation.
Stop the server (Ctrl+C in terminal 1).

### Step 4: Run Approach 3 — Claude Agent (10 minutes)

**What & Why**: Now the ML model is ONE TOOL among several. Claude REASONS about what to search, discovers name variations, runs the model, checks specific filings, and writes a report.

Create `approach3_agent.py`:
```python
# approach3_agent.py — Claude agent with ML model as a tool
import anthropic
import pickle
import json
import pandas as pd
from mock_data import search_filings, get_filing_details

client = anthropic.Anthropic()

with open("delinquency_model.pkl", "rb") as f:
    model = pickle.load(f)

tools = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name. Supports partial matching. Always try name variations like abbreviations and DBAs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Company name to search for"},
                "state": {"type": "string", "description": "Optional 2-letter state code"}
            },
            "required": ["debtor_name"]
        }
    },
    {
        "name": "predict_delinquency",
        "description": "Run the ML delinquency model. Returns probability of delinquency in next 12 months.",
        "input_schema": {
            "type": "object",
            "properties": {
                "active_filing_count": {"type": "integer"},
                "state_count": {"type": "integer"},
                "collateral_types": {"type": "integer"},
                "filing_age_years": {"type": "number"},
                "amendment_frequency": {"type": "number"},
                "months_to_lapse": {"type": "number"}
            },
            "required": ["active_filing_count", "state_count", "collateral_types",
                         "filing_age_years", "amendment_frequency", "months_to_lapse"]
        }
    },
    {
        "name": "get_filing_details",
        "description": "Get full details of a specific UCC filing by filing number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string"}
            },
            "required": ["filing_number"]
        }
    }
]

def execute_tool(name, inputs):
    if name == "search_filings":
        return search_filings(inputs["debtor_name"], inputs.get("state"))
    elif name == "get_filing_details":
        return get_filing_details(inputs["filing_number"])
    elif name == "predict_delinquency":
        features = pd.DataFrame([inputs])
        prob = model.predict_proba(features)[0][1]
        return {"probability": round(prob, 3), "prediction": "HIGH RISK" if prob > 0.7 else "MEDIUM RISK" if prob > 0.4 else "LOW RISK"}

def run_agent(question):
    messages = [{"role": "user", "content": question}]
    system = """You are a credit risk analyst. When assessing delinquency risk:
1. Search for the company (try exact name AND common abbreviations AND DBAs)
2. Count active filings and gather statistics
3. Run the ML prediction model with the filing statistics
4. Look at the riskiest specific filings for context
5. Write a narrative risk report explaining WHY with evidence from actual filings"""

    print(f"\nQuestion: {question}\n")
    print("Agent working...\n")

    turn = 0
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            final = next((b.text for b in response.content if hasattr(b, "text")), "")
            print("=== AGENT RESPONSE ===\n")
            print(final)
            return final

        for block in response.content:
            if block.type == "tool_use":
                turn += 1
                print(f"  Turn {turn}: {block.name}({json.dumps(block.input)[:80]}...)")
                result = execute_tool(block.name, block.input)
                print(f"           → {json.dumps(result)[:100]}...")
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}]
                })

if __name__ == "__main__":
    run_agent("Assess the delinquency risk for Acme Corporation. Be thorough.")
```

Run: `python approach3_agent.py`

Expected output (will vary but follows this pattern):
```
Question: Assess the delinquency risk for Acme Corporation. Be thorough.

Agent working...

  Turn 1: search_filings({"debtor_name": "Acme Corporation"})...
           → [{"filing_number": "NY-2024-001", "debtor_name": "ACME CORPORATION"...
  Turn 2: search_filings({"debtor_name": "ACME CORP"})...
           → [{"filing_number": "CA-2024-001", "debtor_name": "ACME CORP"...
  Turn 3: search_filings({"debtor_name": "ACME"})...
           → [includes "ACME CORP DBA ROADRUNNER SUPPLIES"...
  Turn 4: predict_delinquency({"active_filing_count": 5, "state_count": 4, ...})...
           → {"probability": 0.823, "prediction": "HIGH RISK"}...
  Turn 5: get_filing_details({"filing_number": "CA-2024-001"})...
           → {"collateral": "All assets", "lapse_date": "2025-08-10"...

=== AGENT RESPONSE ===

DELINQUENCY RISK ASSESSMENT: Acme Corporation

PREDICTION: HIGH RISK (82.3% probability)
...
[Full narrative report with specific filing citations and reasoning]
```

✅ Checkpoint: Compare the three outputs side by side:
- Approach 1: `HIGH RISK, 82.3%` — a number, nothing else
- Approach 2: `HIGH RISK, 0.743, 3 filings found` — a number + count, missed 6 filings
- Approach 3: Full narrative report citing specific filings across 4 states, explaining WHY

### Step 5: Ask a Follow-Up (2 minutes)

Modify the last line of `approach3_agent.py`:
```python
    run_agent("What happens to the risk if they file a UCC-3 continuation on the CA filing?")
```

Run: `python approach3_agent.py`

The agent reasons about the hypothetical scenario. Try this with Approach 1 or 2 — impossible without writing new code.

✅ Final Checkpoint: You've seen the same problem solved three ways. The agent found more data, explained its reasoning, and handles follow-ups — all using the SAME ML model that the script used.

### What You Just Built (Summary Card)

| What | Approach 1 | Approach 2 | Approach 3 |
|---|---|---|---|
| Files created | 1 script | 1 API server | 1 agent script |
| Lines of code | ~30 | ~50 | ~60 |
| Filings found | 0 (you provide numbers) | 3 (exact name only) | 9 (found variations + DBAs) |
| Output | Number | JSON | Narrative report |
| Follow-up | Write new code | Build new endpoint | Just ask |
| ML model | IS the solution | IS the solution in an API | Is ONE tool the agent uses |

"Now you've seen it with your own hands. The rest of this course teaches you how to build Approach 3 from scratch."

## Where to Add This

### M00 (Course Overview) — Full Prelude
Add as the VERY FIRST section before "What Is an Agent?". Title: "Prelude: From ML Model to AI Agent"

Show all three approaches with the code. This is the "before and after" that motivates the entire course. The student should think: "I build ML models and APIs. Now I see what agents add on top."

### M05 (Function Calling) — Reference Back
When teaching tool definitions, reference the predict_delinquency tool from the prelude:
"Remember the ML model from the Prelude? Here's how you expose it as a tool that Claude can call."

### M15B (Build Complete Agent) — Stretch Goal
Optional extension: "Add a predict_delinquency tool that wraps a scikit-learn pickle model to your agent."

### Lab Repository
Add `labs/prelude/` with:
- `mock_data.py` (complete — provided)
- `approach1_script.py` (complete — provided)
- `approach2_api.py` (complete — provided)
- `approach3_agent.py` (complete — provided)
- `README.md` with these step-by-step instructions

### Animated Diagram
Three-lane animation:
- Lane 1 (LEFT): ML Script — gray boxes, rigid flow, ends at a number
- Lane 2 (CENTER): FastAPI — adds a database query box before the model, ends at JSON
- Lane 3 (RIGHT): Agent — colorful, think bubbles, multiple searches, calls ML model as one step, ends at a narrative report

The animation should show the SAME data flowing through all three, but the agent path is longer, richer, and produces a qualitatively different output.
