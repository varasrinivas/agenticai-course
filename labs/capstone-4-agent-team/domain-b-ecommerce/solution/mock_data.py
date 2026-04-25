"""
Mock data for B2B Ecommerce Order Pipeline — Multi-Agent Capstone.

Contains realistic purchase orders, inventory, warehouse data, carrier info,
SLA rules, and pricing contracts. 16 records with edge cases.
"""

from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Purchase Orders (16 records with edge cases)
# ---------------------------------------------------------------------------
ORDERS = {
    "PO-2024-5001": {
        "order_id": "PO-2024-5001",
        "customer_id": "CUST-100",
        "customer_name": "Apex Manufacturing Corp",
        "items": [
            {"sku": "WDG-4420", "description": "Industrial Widget A", "qty": 500, "unit_price": 12.50},
            {"sku": "BLT-7780", "description": "Steel Bolt M10x50", "qty": 2000, "unit_price": 0.85},
        ],
        "shipping_address": {"city": "Detroit", "state": "MI", "zip": "48201"},
        "requested_delivery": "2024-12-01",
        "sla_tier": "standard",  # 5 business days
        "po_status": "received",
        "submitted_date": "2024-11-20",
    },
    "PO-2024-5002": {
        "order_id": "PO-2024-5002",
        "customer_id": "CUST-101",
        "customer_name": "Sterling Automotive",
        "items": [
            {"sku": "WDG-4420", "description": "Industrial Widget A", "qty": 10000, "unit_price": 11.25},
        ],
        "shipping_address": {"city": "Nashville", "state": "TN", "zip": "37201"},
        "requested_delivery": "2024-11-25",
        "sla_tier": "expedited",  # 2 business days
        "po_status": "received",
        "submitted_date": "2024-11-20",
    },
    "PO-2024-5003": {
        "order_id": "PO-2024-5003",
        "customer_id": "CUST-102",
        "customer_name": "Pacific Coast Builders",
        "items": [
            {"sku": "PNL-2210", "description": "Composite Panel 4x8", "qty": 200, "unit_price": 45.00},
            {"sku": "FST-1100", "description": "Panel Fastener Kit", "qty": 200, "unit_price": 8.75},
        ],
        "shipping_address": {"city": "Portland", "state": "OR", "zip": "97201"},
        "requested_delivery": "2024-12-10",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-11-21",
    },
    "PO-2024-5004": {
        "order_id": "PO-2024-5004",
        "customer_id": "CUST-103",
        "customer_name": "Heartland Equipment Co",
        "items": [
            {"sku": "MTR-9900", "description": "Electric Motor 5HP", "qty": 50, "unit_price": 320.00},
        ],
        "shipping_address": {"city": "Omaha", "state": "NE", "zip": "68101"},
        "requested_delivery": "2024-12-05",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-11-22",
    },
    "PO-2024-5005": {
        "order_id": "PO-2024-5005",
        "customer_id": "CUST-100",
        "customer_name": "Apex Manufacturing Corp",
        "items": [
            {"sku": "WDG-4420", "description": "Industrial Widget A", "qty": 300, "unit_price": 12.50},
            {"sku": "GKT-5500", "description": "Silicone Gasket Ring", "qty": 1000, "unit_price": 2.15},
        ],
        "shipping_address": {"city": "Detroit", "state": "MI", "zip": "48201"},
        "requested_delivery": "2024-12-15",
        "sla_tier": "economy",  # 10 business days
        "po_status": "received",
        "submitted_date": "2024-11-23",
    },
    # --- Edge case: SKU not in inventory ---
    "PO-2024-5006": {
        "order_id": "PO-2024-5006",
        "customer_id": "CUST-104",
        "customer_name": "Delta Industrial Supply",
        "items": [
            {"sku": "INVALID-SKU", "description": "Unknown Product", "qty": 100, "unit_price": 50.00},
        ],
        "shipping_address": {"city": "Atlanta", "state": "GA", "zip": "30301"},
        "requested_delivery": "2024-12-01",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-11-24",
    },
    # --- Edge case: quantity exceeds all warehouse stock (split shipment) ---
    "PO-2024-5007": {
        "order_id": "PO-2024-5007",
        "customer_id": "CUST-105",
        "customer_name": "National Assembly Inc",
        "items": [
            {"sku": "WDG-4420", "description": "Industrial Widget A", "qty": 25000, "unit_price": 10.75},
        ],
        "shipping_address": {"city": "Chicago", "state": "IL", "zip": "60601"},
        "requested_delivery": "2024-12-08",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-11-25",
    },
    # --- Edge case: wrong pricing (contract price mismatch) ---
    "PO-2024-5008": {
        "order_id": "PO-2024-5008",
        "customer_id": "CUST-100",
        "customer_name": "Apex Manufacturing Corp",
        "items": [
            {"sku": "WDG-4420", "description": "Industrial Widget A", "qty": 500, "unit_price": 15.00},
        ],
        "shipping_address": {"city": "Detroit", "state": "MI", "zip": "48201"},
        "requested_delivery": "2024-12-01",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-11-26",
    },
    # --- Edge case: past-due delivery date ---
    "PO-2024-5009": {
        "order_id": "PO-2024-5009",
        "customer_id": "CUST-106",
        "customer_name": "QuickBuild Contractors",
        "items": [
            {"sku": "PNL-2210", "description": "Composite Panel 4x8", "qty": 50, "unit_price": 45.00},
        ],
        "shipping_address": {"city": "Dallas", "state": "TX", "zip": "75201"},
        "requested_delivery": "2024-11-19",
        "sla_tier": "expedited",
        "po_status": "received",
        "submitted_date": "2024-11-20",
    },
    "PO-2024-5010": {
        "order_id": "PO-2024-5010",
        "customer_id": "CUST-107",
        "customer_name": "Precision Parts LLC",
        "items": [
            {"sku": "BLT-7780", "description": "Steel Bolt M10x50", "qty": 5000, "unit_price": 0.85},
            {"sku": "GKT-5500", "description": "Silicone Gasket Ring", "qty": 3000, "unit_price": 2.15},
        ],
        "shipping_address": {"city": "Cleveland", "state": "OH", "zip": "44101"},
        "requested_delivery": "2024-12-12",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-11-27",
    },
    "PO-2024-5011": {
        "order_id": "PO-2024-5011",
        "customer_id": "CUST-108",
        "customer_name": "Southeast Fabrication",
        "items": [
            {"sku": "MTR-9900", "description": "Electric Motor 5HP", "qty": 10, "unit_price": 320.00},
        ],
        "shipping_address": {"city": "Charlotte", "state": "NC", "zip": "28201"},
        "requested_delivery": "2024-12-03",
        "sla_tier": "expedited",
        "po_status": "received",
        "submitted_date": "2024-11-28",
    },
    # --- Edge case: duplicate order ---
    "PO-2024-5012": {
        "order_id": "PO-2024-5012",
        "customer_id": "CUST-100",
        "customer_name": "Apex Manufacturing Corp",
        "items": [
            {"sku": "WDG-4420", "description": "Industrial Widget A", "qty": 500, "unit_price": 12.50},
            {"sku": "BLT-7780", "description": "Steel Bolt M10x50", "qty": 2000, "unit_price": 0.85},
        ],
        "shipping_address": {"city": "Detroit", "state": "MI", "zip": "48201"},
        "requested_delivery": "2024-12-01",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-11-29",
    },
    # --- Edge case: zero quantity ---
    "PO-2024-5013": {
        "order_id": "PO-2024-5013",
        "customer_id": "CUST-109",
        "customer_name": "Null Industries",
        "items": [
            {"sku": "WDG-4420", "description": "Industrial Widget A", "qty": 0, "unit_price": 12.50},
        ],
        "shipping_address": {"city": "Phoenix", "state": "AZ", "zip": "85001"},
        "requested_delivery": "2024-12-05",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-11-30",
    },
    "PO-2024-5014": {
        "order_id": "PO-2024-5014",
        "customer_id": "CUST-110",
        "customer_name": "Great Lakes Mfg",
        "items": [
            {"sku": "WDG-4420", "description": "Industrial Widget A", "qty": 800, "unit_price": 12.50},
        ],
        "shipping_address": {"city": "Milwaukee", "state": "WI", "zip": "53201"},
        "requested_delivery": "2024-12-04",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-12-01",
    },
    "PO-2024-5015": {
        "order_id": "PO-2024-5015",
        "customer_id": "CUST-111",
        "customer_name": "Summit Engineering",
        "items": [
            {"sku": "PNL-2210", "description": "Composite Panel 4x8", "qty": 100, "unit_price": 45.00},
            {"sku": "MTR-9900", "description": "Electric Motor 5HP", "qty": 5, "unit_price": 320.00},
        ],
        "shipping_address": {"city": "Denver", "state": "CO", "zip": "80201"},
        "requested_delivery": "2024-12-20",
        "sla_tier": "economy",
        "po_status": "received",
        "submitted_date": "2024-12-02",
    },
    "PO-2024-5016": {
        "order_id": "PO-2024-5016",
        "customer_id": "CUST-112",
        "customer_name": "Valley Contractors Group",
        "items": [
            {"sku": "FST-1100", "description": "Panel Fastener Kit", "qty": 500, "unit_price": 8.75},
        ],
        "shipping_address": {"city": "Sacramento", "state": "CA", "zip": "95814"},
        "requested_delivery": "2024-12-06",
        "sla_tier": "standard",
        "po_status": "received",
        "submitted_date": "2024-12-03",
    },
}


# ---------------------------------------------------------------------------
# Inventory by Warehouse
# ---------------------------------------------------------------------------
INVENTORY = {
    "WH-EAST": {
        "warehouse_id": "WH-EAST",
        "name": "Eastern Distribution Center",
        "city": "Pittsburgh",
        "state": "PA",
        "stock": {
            "WDG-4420": 8000,
            "BLT-7780": 50000,
            "GKT-5500": 20000,
            "PNL-2210": 150,
            "FST-1100": 800,
            "MTR-9900": 25,
        },
    },
    "WH-CENTRAL": {
        "warehouse_id": "WH-CENTRAL",
        "name": "Central Fulfillment Hub",
        "city": "Indianapolis",
        "state": "IN",
        "stock": {
            "WDG-4420": 12000,
            "BLT-7780": 30000,
            "GKT-5500": 15000,
            "PNL-2210": 300,
            "FST-1100": 500,
            "MTR-9900": 40,
        },
    },
    "WH-WEST": {
        "warehouse_id": "WH-WEST",
        "name": "Western Logistics Center",
        "city": "Reno",
        "state": "NV",
        "stock": {
            "WDG-4420": 5000,
            "BLT-7780": 20000,
            "GKT-5500": 10000,
            "PNL-2210": 200,
            "FST-1100": 600,
            "MTR-9900": 15,
        },
    },
}


# ---------------------------------------------------------------------------
# Contract Pricing
# ---------------------------------------------------------------------------
CONTRACT_PRICING = {
    "CUST-100": {
        "customer_id": "CUST-100",
        "customer_name": "Apex Manufacturing Corp",
        "pricing_tier": "gold",
        "contract_prices": {
            "WDG-4420": 12.50,
            "BLT-7780": 0.80,
            "GKT-5500": 2.00,
        },
        "discount_pct": 0.05,
    },
    "CUST-101": {
        "customer_id": "CUST-101",
        "customer_name": "Sterling Automotive",
        "pricing_tier": "platinum",
        "contract_prices": {
            "WDG-4420": 11.25,
        },
        "discount_pct": 0.10,
    },
}


# ---------------------------------------------------------------------------
# SLA Rules
# ---------------------------------------------------------------------------
SLA_RULES = {
    "economy": {"max_days": 10, "carrier_tier": "ground", "penalty_pct": 0.02},
    "standard": {"max_days": 5, "carrier_tier": "ground_express", "penalty_pct": 0.05},
    "expedited": {"max_days": 2, "carrier_tier": "air", "penalty_pct": 0.10},
}


# ---------------------------------------------------------------------------
# Carrier Data
# ---------------------------------------------------------------------------
CARRIERS = {
    "CARRIER-FRT": {"id": "CARRIER-FRT", "name": "FreightMax Ground", "tier": "ground", "avg_days": 7, "cost_per_lb": 0.45},
    "CARRIER-EXP": {"id": "CARRIER-EXP", "name": "ExpressLine Logistics", "tier": "ground_express", "avg_days": 4, "cost_per_lb": 0.85},
    "CARRIER-AIR": {"id": "CARRIER-AIR", "name": "SkyFreight Premium", "tier": "air", "avg_days": 1, "cost_per_lb": 2.50},
}


# ---------------------------------------------------------------------------
# SLA Violation Tracker (for circuit breaker testing)
# ---------------------------------------------------------------------------
SLA_VIOLATIONS_LOG = [
    {"order_id": "PO-2024-4990", "violation_type": "late_delivery", "days_late": 2, "timestamp": "2024-11-18T14:00:00"},
    {"order_id": "PO-2024-4991", "violation_type": "late_delivery", "days_late": 1, "timestamp": "2024-11-19T09:00:00"},
    {"order_id": "PO-2024-4992", "violation_type": "wrong_item", "timestamp": "2024-11-19T11:30:00"},
]
