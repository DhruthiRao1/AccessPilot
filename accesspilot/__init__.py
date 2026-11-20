"""AccessPilot: multi-agent IT asset & access request assistant (Google ADK + Gemini + AlloyDB)."""

try:  # `adk web` / `adk deploy` look for `root_agent` in this package
    from . import agent  # noqa: F401
except ImportError:  # google-adk not installed: the service layer still works offline
    pass
