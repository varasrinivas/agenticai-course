"""
Tests for B2B Ecommerce Order Exception Resolution Agent tools.

Run from the domain-b-ecommerce directory:
    python -m pytest tests/

These tests exercise the tool functions directly using mock data.
No API key or network access is required.
"""

import sys
import os
import json

# Add the solution directory to the path so we can import tools and mock_data
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solution"))

from tools import (
    get_order_details,
    query_warehouse_inventory,
    track_shipment,
    get_contract_pricing,
    check_quality_hold_status,
    draft_customer_notification,
    execute_tool,
)
from mock_data import ORDERS, WAREHOUSE_INVENTORY, CARRIER_TRACKING, CONTRACT_PRICING, QUALITY_HOLDS


# -----------------------------------------------------------------------
# get_order_details
# -----------------------------------------------------------------------

class TestGetOrderDetails:
    def test_known_order(self):
        """ORD-2024-1847 should return full order details."""
        result = get_order_details("ORD-2024-1847")
        assert "error" not in result
        assert result["order_id"] == "ORD-2024-1847"
        assert result["customer_name"] == "Meridian Industrial Supply"
        assert result["status"] == "exception"
        assert result["exception_type"] == "delayed_shipment"
        assert result["priority"] == "high"
        assert result["total_value"] == 14750.00
        assert len(result["lines"]) == 3
        assert result["sla_penalty_clause"] is True
        assert result["sla_penalty_rate"] == 0.02

    def test_quality_hold_order(self):
        """ORD-2024-1873 should be a quality_hold exception."""
        result = get_order_details("ORD-2024-1873")
        assert result["exception_type"] == "quality_hold"
        assert result["lines"][0]["sku"] == "BEAR-LIN-25MM"

    def test_pricing_discrepancy_order(self):
        """ORD-2024-1860 should be a pricing_discrepancy exception."""
        result = get_order_details("ORD-2024-1860")
        assert result["exception_type"] == "pricing_discrepancy"
        assert result["customer_name"] == "Greenfield Energy Solutions"

    def test_partial_delivery_order(self):
        """ORD-2024-1852 should be a partial_delivery exception."""
        result = get_order_details("ORD-2024-1852")
        assert result["exception_type"] == "partial_delivery"
        # Line 2 short-shipped: 30 of 50
        line2 = result["lines"][1]
        assert line2["sku"] == "PCB-CTRL-V4"
        assert line2["qty_ordered"] == 50
        assert line2["qty_shipped"] == 30

    def test_unknown_order_returns_error(self):
        """Unknown order ID should return an error."""
        result = get_order_details("ORD-0000-0000")
        assert "error" in result


# -----------------------------------------------------------------------
# query_warehouse_inventory
# -----------------------------------------------------------------------

class TestQueryWarehouseInventory:
    def test_known_sku_at_known_warehouse(self):
        """HYD-PUMP-3200 at WH-EAST should return inventory details."""
        result = query_warehouse_inventory("WH-EAST", "HYD-PUMP-3200")
        assert "error" not in result
        assert result["sku"] == "HYD-PUMP-3200"
        assert result["warehouse_id"] == "WH-EAST"
        assert result["warehouse_name"] == "Eastern Distribution Center"
        assert result["qty_available"] == 12
        assert result["qty_reserved"] == 5
        assert result["qty_on_hold"] == 20

    def test_discontinued_sku(self):
        """FSTNR-TI-M6 at WH-EAST should show DISCONTINUED status."""
        result = query_warehouse_inventory("WH-EAST", "FSTNR-TI-M6")
        assert result["status"] == "DISCONTINUED"
        assert result["qty_available"] == 0
        assert result["replacement_sku"] == "FSTNR-TI-M6-V2"

    def test_sku_on_quality_hold(self):
        """BEAR-LIN-25MM at WH-EAST should show units on hold."""
        result = query_warehouse_inventory("WH-EAST", "BEAR-LIN-25MM")
        assert result["qty_on_hold"] == 40
        assert result["qty_available"] == 0
        assert "hold_reason" in result

    def test_unknown_warehouse_returns_error(self):
        """Unknown warehouse should return an error."""
        result = query_warehouse_inventory("WH-NOWHERE", "HYD-PUMP-3200")
        assert "error" in result

    def test_unknown_sku_returns_error(self):
        """Unknown SKU at a valid warehouse should return an error."""
        result = query_warehouse_inventory("WH-EAST", "UNKNOWN-SKU")
        assert "error" in result
        assert result["warehouse_name"] == "Eastern Distribution Center"


# -----------------------------------------------------------------------
# track_shipment
# -----------------------------------------------------------------------

class TestTrackShipment:
    def test_known_tracking_number_pickup_missed(self):
        """FFL-9928374650 should show pickup_missed status."""
        result = track_shipment("FFL-9928374650")
        assert "error" not in result
        assert result["tracking_number"] == "FFL-9928374650"
        assert result["carrier"] == "FastFreight Logistics"
        assert result["status"] == "pickup_missed"
        assert result["estimated_delivery"] is None
        assert len(result["events"]) == 3

    def test_delivered_shipment(self):
        """FFL-9930128456 should show delivered status."""
        result = track_shipment("FFL-9930128456")
        assert result["status"] == "delivered"
        assert "actual_delivery" in result

    def test_delayed_with_service_disruption(self):
        """NFS-5503847291 should show delayed status with service disruption."""
        result = track_shipment("NFS-5503847291")
        assert result["status"] == "delayed"
        assert result["service_disruption"] is True
        assert "disruption_reason" in result

    def test_in_transit_partial(self):
        """NFS-5501928374 should show in_transit for a partial shipment."""
        result = track_shipment("NFS-5501928374")
        assert result["status"] == "in_transit"
        assert "partial" in result["status_detail"].lower()

    def test_unknown_tracking_returns_error(self):
        """Unknown tracking number should return an error."""
        result = track_shipment("FAKE-0000000000")
        assert "error" in result


# -----------------------------------------------------------------------
# get_contract_pricing
# -----------------------------------------------------------------------

class TestGetContractPricing:
    def test_active_contract(self):
        """CTR-2024-0091 should be active with pricing tiers."""
        result = get_contract_pricing("CTR-2024-0091")
        assert "error" not in result
        assert result["contract_id"] == "CTR-2024-0091"
        assert result["customer_name"] == "Meridian Industrial Supply"
        assert result["status"] == "active"
        assert "HYD-PUMP-3200" in result["pricing_tiers"]
        tier = result["pricing_tiers"]["HYD-PUMP-3200"]
        assert tier["contract_price"] == 1750.00
        assert tier["list_price"] == 1850.00

    def test_expired_contract(self):
        """CTR-2023-0200 should show expired status."""
        result = get_contract_pricing("CTR-2023-0200")
        assert result["status"] == "expired"
        assert result["customer_name"] == "Cascade Water Systems"
        assert result["renewal_status"] == "pending_review"

    def test_contract_with_volume_rebate(self):
        """CTR-2024-0091 should have volume rebate details."""
        result = get_contract_pricing("CTR-2024-0091")
        assert result["volume_rebate"] is not None
        assert result["volume_rebate"]["threshold"] == 100000
        assert result["volume_rebate"]["ytd_spend"] == 87500

    def test_contract_without_volume_rebate(self):
        """CTR-2024-0078 should have no volume rebate."""
        result = get_contract_pricing("CTR-2024-0078")
        assert result["volume_rebate"] is None

    def test_unknown_contract_returns_error(self):
        """Unknown contract should return an error."""
        result = get_contract_pricing("CTR-0000-0000")
        assert "error" in result


# -----------------------------------------------------------------------
# check_quality_hold_status
# -----------------------------------------------------------------------

class TestCheckQualityHoldStatus:
    def test_sku_with_quality_hold(self):
        """BEAR-LIN-25MM should have an active quality hold."""
        result = check_quality_hold_status("BEAR-LIN-25MM")
        assert result["status"] == "holds_found"
        assert result["hold_count"] >= 1
        hold = result["holds"][0]
        assert hold["sku"] == "BEAR-LIN-25MM"
        assert hold["severity"] == "critical"
        assert hold["inspection_status"] == "pending"

    def test_sku_with_investigation_hold(self):
        """HYD-PUMP-3200 should have a hold with investigation in progress."""
        result = check_quality_hold_status("HYD-PUMP-3200")
        assert result["status"] == "holds_found"
        hold = result["holds"][0]
        assert hold["inspection_status"] == "investigation_in_progress"
        assert "seal leak" in hold["hold_reason"].lower()

    def test_sku_with_no_holds(self):
        """FLT-KIT-STD should have no quality holds."""
        result = check_quality_hold_status("FLT-KIT-STD")
        assert result["status"] == "no_active_holds"
        assert result["holds"] == []

    def test_nonexistent_sku_no_holds(self):
        """A completely unknown SKU should also return no holds."""
        result = check_quality_hold_status("FAKE-SKU-000")
        assert result["status"] == "no_active_holds"


# -----------------------------------------------------------------------
# draft_customer_notification
# -----------------------------------------------------------------------

class TestDraftCustomerNotification:
    def test_basic_notification(self):
        """Should produce a draft email with all required fields."""
        result = draft_customer_notification(
            order_id="ORD-2024-1847",
            customer_name="Meridian Industrial Supply",
            contact_name="Janet Kowalski",
            contact_email="procurement@meridian-industrial.com",
            exception_summary="Your order was delayed.",
            root_cause="Carrier routing error.",
            resolution="Emergency pickup rescheduled.",
            sla_impact="SLA credit of $295 applied if late.",
        )
        assert result["status"] == "draft_ready"
        assert result["to"] == "procurement@meridian-industrial.com"
        assert result["order_id"] == "ORD-2024-1847"
        assert result["customer_name"] == "Meridian Industrial Supply"
        assert "ORD-2024-1847" in result["subject"]
        assert "Janet Kowalski" in result["body"]
        assert "Carrier routing error" in result["body"]
        assert "Emergency pickup rescheduled" in result["body"]

    def test_notification_body_sections(self):
        """The body should contain all four sections."""
        result = draft_customer_notification(
            order_id="ORD-TEST",
            customer_name="Test Co",
            contact_name="Jane Doe",
            contact_email="jane@test.com",
            exception_summary="Test summary.",
            root_cause="Test cause.",
            resolution="Test resolution.",
            sla_impact="No SLA impact.",
        )
        body = result["body"]
        assert "ISSUE SUMMARY" in body
        assert "ROOT CAUSE" in body
        assert "RESOLUTION & NEXT STEPS" in body
        assert "SLA & CREDIT INFORMATION" in body


# -----------------------------------------------------------------------
# execute_tool dispatcher
# -----------------------------------------------------------------------

class TestExecuteTool:
    def test_dispatch_get_order_details(self):
        """execute_tool should dispatch to get_order_details."""
        raw = execute_tool("get_order_details", {"order_id": "ORD-2024-1847"})
        result = json.loads(raw)
        assert result["order_id"] == "ORD-2024-1847"

    def test_dispatch_unknown_tool(self):
        """execute_tool should return an error for unknown tool names."""
        raw = execute_tool("nonexistent_tool", {})
        result = json.loads(raw)
        assert "error" in result
        assert "Unknown tool" in result["error"]
