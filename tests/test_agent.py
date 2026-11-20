import pytest

pytest.importorskip("google.adk")


def test_agent_tree():
    from accesspilot.agent import root_agent

    assert root_agent.name == "accesspilot"
    names = {a.name for a in root_agent.sub_agents}
    assert names == {"inventory_agent", "approval_agent"}
    inv = next(a for a in root_agent.sub_agents if a.name == "inventory_agent")
    assert {t.__name__ for t in inv.tools} >= {"search_catalog", "submit_request"}
