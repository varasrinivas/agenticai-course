"""
M15B — Configuration (Complete — do not modify)
================================================
Shared constants and state registry for the UCC Filing Research System.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Model to use for all agents
MODEL = "claude-sonnet-4-20250514"

# Maximum turns for ReAct loops
MAX_AGENT_TURNS = 10
MAX_SUBAGENT_TURNS = 6

# Conversation history window (for coordinator memory)
MAX_HISTORY_TURNS = 5

# US state codes and names for validation
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"
}

# Risk score thresholds
RISK_THRESHOLDS = {
    "HIGH": 0.7,
    "MEDIUM": 0.4,
    "LOW": 0.0,
}
