"""ServiceNow incident client with an in-memory mock for offline runs."""
import itertools

from . import config


class MockServiceNow:
    def __init__(self):
        self._seq = itertools.count(10001)
        self.tickets: list[dict] = []

    def create_ticket(self, short_description: str, description: str, category: str) -> str:
        number = f"INC{next(self._seq)}"
        self.tickets.append(
            {"number": number, "short_description": short_description,
             "description": description, "category": category}
        )
        return number


class ServiceNowClient:
    """Minimal Table API client. Only used when SERVICENOW_INSTANCE is set."""

    def __init__(self, instance: str, user: str, password: str):
        self.url = f"https://{instance}.service-now.com/api/now/table/incident"
        self.auth = (user, password)

    def create_ticket(self, short_description: str, description: str, category: str) -> str:
        import requests  # optional dependency

        resp = requests.post(
            self.url,
            auth=self.auth,
            headers={"Accept": "application/json"},
            json={"short_description": short_description, "description": description,
                  "category": category},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["result"]["number"]


def make_client():
    if config.SERVICENOW_INSTANCE:
        return ServiceNowClient(
            config.SERVICENOW_INSTANCE, config.SERVICENOW_USER, config.SERVICENOW_PASSWORD
        )
    return MockServiceNow()
