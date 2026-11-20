"""ADK multi-agent setup: one coordinator that routes to two specialist sub-agents.

Run locally with `adk web` from the repository root, or deploy with
`adk deploy agent_engine` (see deploy/README.md).
"""
from google.adk.agents import Agent

from . import config
from .tools import (
    decide_request,
    get_my_assets,
    get_request_status,
    list_pending_approvals,
    search_catalog,
    submit_request,
)

inventory_agent = Agent(
    name="inventory_agent",
    model=config.MODEL,
    description="Handles employee requests for laptops, monitors, software licences and system access, "
                "and checks request status or what the employee already has.",
    instruction=(
        "You help employees get IT equipment, software and access.\n"
        "1. If you do not know the employee id, ask for it (format E100).\n"
        "2. Use search_catalog to find the right item. If several items match, show the top options "
        "with cost and stock and ask the user to pick one. Never guess the item.\n"
        "3. Ask for a one-line business justification if the user has not given one.\n"
        "4. Call submit_request. Then tell the user the decision, the reason, the request id, "
        "any ServiceNow ticket number and the next step, in plain language.\n"
        "You never approve anything yourself: the policy in submit_request decides."
    ),
    tools=[search_catalog, get_my_assets, submit_request, get_request_status],
)

approval_agent = Agent(
    name="approval_agent",
    model=config.MODEL,
    description="Helps managers review and approve or reject pending requests from their team.",
    instruction=(
        "You help managers handle approvals.\n"
        "1. Ask for the manager id if you do not know it (format M200).\n"
        "2. Use list_pending_approvals and summarise each request: who, what, why.\n"
        "3. Only call decide_request after the manager clearly says approve or reject for a "
        "specific request id. Confirm the outcome afterwards."
    ),
    tools=[list_pending_approvals, decide_request, get_request_status],
)

root_agent = Agent(
    name="accesspilot",
    model=config.MODEL,
    description="IT asset and access request assistant.",
    instruction=(
        "You are AccessPilot, the IT asset and access desk.\n"
        "- Employees asking for hardware, software or access, or asking about their requests or "
        "assets -> transfer to inventory_agent.\n"
        "- Managers reviewing, approving or rejecting requests -> transfer to approval_agent.\n"
        "- If the intent is unclear, ask one short question. Keep replies brief."
    ),
    sub_agents=[inventory_agent, approval_agent],
)
