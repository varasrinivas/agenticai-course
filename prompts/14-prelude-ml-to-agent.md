# Prelude: From ML Model to AI Agent

Same business problem (UCC delinquency prediction) solved 3 ways:

## Approach 1: ML Script + Pickle
Train RandomForest, save pickle, predict(manual_features) -> "HIGH RISK, 82.3%"
Problem: YOU prepare features, no explanation, no follow-ups, misses name variations

## Approach 2: FastAPI Wrapper
POST /predict {"company_name": "Acme"} -> auto-fetch from DB -> JSON response
Problem: hardcoded SQL, misses "ACME CORP" and DBAs, still no explanation

## Approach 3: Claude Agent with ML Tool
Agent searches "Acme Corporation" -> "ACME CORP" -> "ACME CORP DBA ROADRUNNER SUPPLIES"
Runs ML model as ONE tool -> checks riskiest filings -> writes narrative report
Key: ML model doesn't go away, agent USES it as a tool

## Hands-On Lab (30 min, 5 steps)
Step 1: mock_data.py + train pickle (12 filings, 3 entities)
Step 2: approach1_script.py -> get a number
Step 3: approach2_api.py + curl -> get JSON, misses 6 filings  
Step 4: approach3_agent.py -> finds all 9 filings, writes report
Step 5: follow-up question -> only agent handles it

## Animated Diagram
Three lanes: gray rigid script | blue FastAPI | colorful dynamic agent
