"""Offline walkthrough of the request flows (no LLM, no cloud). Run: python scripts/demo.py"""
import json

from accesspilot.db.repository import SqliteRepository
from accesspilot.service import AccessService
from accesspilot.servicenow import MockServiceNow

svc = AccessService(SqliteRepository(":memory:"), MockServiceNow())


def show(title, result):
    print(f"\n=== {title}")
    print(json.dumps(result, indent=2, default=str))


show("Employee searches: 'monitor for a second screen'", svc.search_catalog("monitor for a second screen"))
show("E100 requests a monitor (standard -> auto-approved)",
     svc.request_item("E100", "HW-MON-27", "Need a second screen"))
sap = svc.request_item("E101", "AC-FIN-SAP", "Month-end close")
show("E101 requests SAP Finance access (sensitive -> manager)", sap)
show("Manager M201 sees pending approvals", svc.pending_approvals("M201"))
show("M201 approves", svc.decide(sap["request_id"], "M201", approve=True, comment="Approved for close"))
show("E100 requests production DB admin (privileged -> ServiceNow security review)",
     svc.request_item("E100", "AC-PROD-DB", "Debug incident"))
show("E100 requests a developer laptop (out of stock -> ServiceNow procurement)",
     svc.request_item("E100", "HW-LAP-DEV", "Local builds"))
