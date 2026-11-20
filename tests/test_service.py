import pytest

from accesspilot.db.repository import SqliteRepository
from accesspilot.policy import Decision
from accesspilot.service import AccessService
from accesspilot.servicenow import MockServiceNow


@pytest.fixture
def svc():
    return AccessService(SqliteRepository(":memory:"), MockServiceNow())


def test_search_finds_monitor(svc):
    res = svc.search_catalog("I need a second screen monitor")
    assert res["items"][0]["id"] == "HW-MON-27"


def test_standard_item_is_auto_approved_and_assigned(svc):
    res = svc.request_item("E100", "HW-MON-27", "Need a second screen")
    assert res["decision"] == Decision.AUTO_APPROVED
    assert svc.repo.get_request(res["request_id"])["status"] == "FULFILLED"
    assert any(a["id"] == "HW-MON-27" for a in svc.my_assets("E100")["assets"])
    assert svc.repo.stock("HW-MON-27") == 29


def test_sensitive_access_goes_to_manager_then_approved(svc):
    res = svc.request_item("E101", "AC-FIN-SAP", "Month-end close")
    assert res["decision"] == Decision.PENDING_MANAGER
    pending = svc.pending_approvals("M201")["pending"]
    assert [p["id"] for p in pending] == [res["request_id"]]
    out = svc.decide(res["request_id"], "M201", approve=True, comment="ok")
    assert out["result"] == "FULFILLED"
    assert svc.repo.has_asset("E101", "AC-FIN-SAP")


def test_wrong_manager_cannot_approve(svc):
    res = svc.request_item("E101", "AC-FIN-SAP", "Month-end close")
    out = svc.decide(res["request_id"], "M200", approve=True)
    assert out["status"] == "error"
    assert svc.repo.get_request(res["request_id"])["status"] == "PENDING_MANAGER"


def test_high_cost_needs_manager(svc):
    res = svc.request_item("E102", "SW-TABLEAU", "Dashboards")
    assert res["decision"] == Decision.PENDING_MANAGER


def test_privileged_access_escalates_to_servicenow(svc):
    res = svc.request_item("E100", "AC-PROD-DB", "Fix incident")
    assert res["decision"] == Decision.ESCALATED_SECURITY
    assert res["servicenow_ticket"].startswith("INC")
    assert len(svc.snow.tickets) == 1
    assert not svc.repo.has_asset("E100", "AC-PROD-DB")


def test_out_of_stock_hardware_escalates_to_procurement(svc):
    res = svc.request_item("E100", "HW-LAP-DEV", "Local builds")
    assert res["decision"] == Decision.ESCALATED_PROCUREMENT
    assert res["servicenow_ticket"]


def test_duplicate_request_rejected(svc):
    res = svc.request_item("E100", "AC-GITHUB", "Code access")
    assert res["decision"] == Decision.REJECTED


def test_unknown_ids(svc):
    assert svc.request_item("E999", "HW-MON-27", "x")["status"] == "error"
    assert svc.request_item("E100", "NOPE", "x")["status"] == "error"
