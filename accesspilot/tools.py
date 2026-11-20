"""Function tools exposed to the ADK agents.

ADK reads each function's name, type hints and docstring to build the tool
schema, so the docstrings are written for the model.
"""
from functools import lru_cache

from .db import make_repository
from .service import AccessService
from .servicenow import make_client


@lru_cache(maxsize=1)
def get_service() -> AccessService:
    return AccessService(make_repository(), make_client())


# --- inventory agent tools ---------------------------------------------------
def search_catalog(query: str) -> dict:
    """Find catalog items (hardware, software or access) matching what the user asked for.

    Args:
        query: The user's request in plain words, e.g. "laptop for coding" or "finance system access".
    """
    return get_service().search_catalog(query)


def get_my_assets(employee_id: str) -> dict:
    """List the hardware, software and access already assigned to an employee.

    Args:
        employee_id: Employee id such as "E100".
    """
    return get_service().my_assets(employee_id)


def submit_request(employee_id: str, item_id: str, justification: str) -> dict:
    """Submit a request for one catalog item. Company policy decides the outcome:
    auto-approved, sent to the manager, or escalated to ServiceNow.

    Args:
        employee_id: Employee id of the requester, such as "E100".
        item_id: Catalog item id returned by search_catalog, such as "HW-MON-27".
        justification: Short business reason given by the user.
    """
    return get_service().request_item(employee_id, item_id, justification)


def get_request_status(request_id: int) -> dict:
    """Get the current status of a request.

    Args:
        request_id: The numeric request id.
    """
    return get_service().request_status(request_id)


# --- approval agent tools ----------------------------------------------------
def list_pending_approvals(manager_id: str) -> dict:
    """List requests from a manager's team that are waiting for their approval.

    Args:
        manager_id: Manager's employee id, such as "M200".
    """
    return get_service().pending_approvals(manager_id)


def decide_request(request_id: int, manager_id: str, approve: bool, comment: str = "") -> dict:
    """Approve or reject a pending request. Only the requester's own manager can decide.

    Args:
        request_id: The numeric request id.
        manager_id: Employee id of the manager making the decision.
        approve: True to approve, False to reject.
        comment: Optional note explaining the decision.
    """
    return get_service().decide(request_id, manager_id, approve, comment)
