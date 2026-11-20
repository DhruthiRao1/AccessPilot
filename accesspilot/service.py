"""Business logic behind the agent tools. Plain Python, fully testable offline."""
from .policy import Decision, evaluate


class AccessService:
    def __init__(self, repo, servicenow):
        self.repo = repo
        self.snow = servicenow

    # --- inventory agent -------------------------------------------------
    def search_catalog(self, query: str) -> dict:
        items = self.repo.search_catalog(query)
        if not items:
            return {"status": "not_found", "message": f"No catalog item matches '{query}'."}
        return {"status": "ok", "items": [_public_item(i, self.repo.stock(i["id"])) for i in items]}

    def my_assets(self, employee_id: str) -> dict:
        if not self.repo.get_employee(employee_id):
            return {"status": "error", "message": f"Unknown employee id {employee_id}."}
        return {"status": "ok", "assets": self.repo.employee_assets(employee_id)}

    def request_item(self, employee_id: str, item_id: str, justification: str) -> dict:
        emp = self.repo.get_employee(employee_id)
        item = self.repo.get_item(item_id)
        if not emp:
            return {"status": "error", "message": f"Unknown employee id {employee_id}."}
        if not item:
            return {"status": "error", "message": f"Unknown catalog item {item_id}."}

        stock = self.repo.stock(item_id)
        result = evaluate(item, in_stock=1 if stock is None else stock,
                          already_owned=self.repo.has_asset(employee_id, item_id))

        ticket = None
        if result.decision in (Decision.ESCALATED_SECURITY, Decision.ESCALATED_PROCUREMENT):
            kind = "security" if result.decision == Decision.ESCALATED_SECURITY else "procurement"
            ticket = self.snow.create_ticket(
                short_description=f"[AccessPilot] {kind} review: {item['name']} for {emp['name']}",
                description=f"Employee {employee_id} requested {item_id}. "
                            f"Justification: {justification}. Policy: {result.reason}",
                category=kind,
            )

        request_id = self.repo.create_request(
            employee_id, item_id, justification, result.decision.value, result.reason, ticket)

        if result.decision == Decision.AUTO_APPROVED:
            self.repo.fulfil(employee_id, item_id)
            self.repo.update_request(request_id, "FULFILLED")

        return {
            "status": "ok",
            "request_id": request_id,
            "decision": result.decision.value,
            "reason": result.reason,
            "servicenow_ticket": ticket,
            "next_step": _next_step(result.decision, emp),
        }

    def request_status(self, request_id: int) -> dict:
        req = self.repo.get_request(int(request_id))
        if not req:
            return {"status": "error", "message": f"Request {request_id} not found."}
        return {"status": "ok", "request": req}

    # --- approval agent --------------------------------------------------
    def pending_approvals(self, manager_id: str) -> dict:
        return {"status": "ok", "pending": self.repo.pending_for_manager(manager_id)}

    def decide(self, request_id: int, manager_id: str, approve: bool, comment: str = "") -> dict:
        req = self.repo.get_request(int(request_id))
        if not req:
            return {"status": "error", "message": f"Request {request_id} not found."}
        if req["status"] != Decision.PENDING_MANAGER.value:
            return {"status": "error", "message": f"Request {request_id} is {req['status']}, not pending."}
        emp = self.repo.get_employee(req["employee_id"])
        if emp["manager_id"] != manager_id:
            return {"status": "error",
                    "message": f"{manager_id} is not the manager of {emp['id']} and cannot decide."}

        if approve:
            self.repo.update_request(req["id"], "APPROVED", manager_id, comment)
            self.repo.fulfil(req["employee_id"], req["item_id"])
            self.repo.update_request(req["id"], "FULFILLED")
            return {"status": "ok", "request_id": req["id"], "result": "FULFILLED"}
        self.repo.update_request(req["id"], "REJECTED", manager_id, comment)
        return {"status": "ok", "request_id": req["id"], "result": "REJECTED"}


def _public_item(item: dict, stock) -> dict:
    out = {k: item[k] for k in ("id", "name", "category", "risk", "cost", "description")}
    out["cost"] = float(out["cost"])
    out["in_stock"] = "n/a" if stock is None else stock
    return out


def _next_step(decision: Decision, emp: dict) -> str:
    return {
        Decision.AUTO_APPROVED: "Approved automatically and assigned to you.",
        Decision.PENDING_MANAGER: f"Sent to your manager ({emp['manager_id']}) for approval.",
        Decision.ESCALATED_SECURITY: "Security team will review the ServiceNow ticket.",
        Decision.ESCALATED_PROCUREMENT: "Procurement will order the item via the ServiceNow ticket.",
        Decision.REJECTED: "No action taken.",
    }[decision]
