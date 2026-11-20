"""Demo data shared by the SQLite and AlloyDB backends."""

EMPLOYEES = [
    # id, name, team, manager_id
    ("E100", "Asha Rao", "Engineering", "M200"),
    ("E101", "Rahul Mehta", "Finance", "M201"),
    ("E102", "Priya Nair", "Engineering", "M200"),
    ("M200", "Kiran Kumar", "Engineering", None),
    ("M201", "Neha Shah", "Finance", None),
]

CATALOG = [
    # id, name, category, risk, cost_usd, description
    ("HW-LAP-STD", "Standard Laptop (14in, 16GB)", "hardware", "standard", 900,
     "Default business laptop for office work, email, documents and video calls."),
    ("HW-LAP-DEV", "Developer Laptop (16in, 32GB)", "hardware", "standard", 1800,
     "High-performance laptop for software development, containers and local builds."),
    ("HW-MON-27", "27in Monitor", "hardware", "standard", 250,
     "External 27 inch display for a second screen at the desk."),
    ("HW-HEADSET", "Noise-cancelling Headset", "hardware", "standard", 120,
     "Headset with microphone for calls and online meetings."),
    ("SW-VSCODE", "VS Code Enterprise Extensions", "software", "standard", 0,
     "Code editor extensions pack for developers."),
    ("SW-ADOBE", "Adobe Acrobat Pro", "software", "standard", 240,
     "Create, edit and sign PDF documents."),
    ("SW-TABLEAU", "Tableau Creator Licence", "software", "sensitive", 840,
     "Data visualisation and dashboard tool; licence is costly and tracked."),
    ("AC-GITHUB", "GitHub Organisation Access", "access", "standard", 0,
     "Read and write access to company source code repositories."),
    ("AC-FIN-SAP", "SAP Finance Module Access", "access", "sensitive", 0,
     "Access to financial ledgers and payments in SAP; contains confidential data."),
    ("AC-PROD-DB", "Production Database Admin", "access", "privileged", 0,
     "Administrator rights on production customer databases."),
    ("AC-VPN", "VPN Access", "access", "standard", 0,
     "Remote network access to connect to internal systems from home."),
]

# item_id -> units in stock (hardware only; software/access are unlimited)
INVENTORY = {
    "HW-LAP-STD": 12,
    "HW-LAP-DEV": 0,
    "HW-MON-27": 30,
    "HW-HEADSET": 25,
}

# employee_id -> item_ids already assigned
ASSETS = {
    "E100": ["HW-LAP-STD", "AC-GITHUB"],
    "E101": ["HW-LAP-STD", "SW-ADOBE"],
    "E102": ["HW-LAP-DEV"],
}
