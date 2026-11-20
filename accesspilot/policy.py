"""Approval policy.

Decisions are made by plain code, never by the LLM, so the same request always
gets the same outcome and the model cannot talk itself into granting access.
"""
from dataclasses import dataclass
from enum import Enum

from . import config


class Decision(str, Enum):
    AUTO_APPROVED = "AUTO_APPROVED"            # standard item, low cost, in stock
    PENDING_MANAGER = "PENDING_MANAGER"        # needs the requester's manager
    ESCALATED_SECURITY = "ESCALATED_SECURITY"  # privileged access -> ServiceNow security review
    ESCALATED_PROCUREMENT = "ESCALATED_PROCUREMENT"  # hardware out of stock -> ServiceNow
    REJECTED = "REJECTED"


@dataclass
class PolicyResult:
    decision: Decision
    reason: str


def evaluate(item: dict, in_stock: int, already_owned: bool) -> PolicyResult:
    """Return the policy decision for one catalog item request."""
    if already_owned:
        return PolicyResult(Decision.REJECTED, "Requester already has this item.")

    risk = item["risk"]
    if risk == "privileged":
        return PolicyResult(
            Decision.ESCALATED_SECURITY,
            "Privileged access always needs a security review.",
        )

    if item["category"] == "hardware" and in_stock <= 0:
        return PolicyResult(
            Decision.ESCALATED_PROCUREMENT,
            "Item is out of stock; a procurement ticket is needed.",
        )

    if risk == "sensitive":
        return PolicyResult(Decision.PENDING_MANAGER, "Sensitive item needs manager approval.")

    if item["cost"] > config.AUTO_APPROVE_MAX_COST:
        return PolicyResult(
            Decision.PENDING_MANAGER,
            f"Cost above {config.AUTO_APPROVE_MAX_COST:.0f} USD needs manager approval.",
        )

    return PolicyResult(Decision.AUTO_APPROVED, "Standard item within policy.")
