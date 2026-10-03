import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")

# LinkedIn search — Top 50 US Tax Preparation titles
KEYWORDS = [
    # Preparer (1–10)
    "US Tax Preparer",
    "Tax Preparer",
    "Senior Tax Preparer",
    "Individual Tax Preparer",
    "Tax Return Preparer",
    "Tax Preparation Specialist",
    "Tax Filing Specialist",
    "Tax Preparation Analyst",
    "Tax Return Specialist",
    "Federal Tax Preparer",
    # Analyst (11–20)
    "Tax Analyst",
    "US Tax Analyst",
    "Senior Tax Analyst",
    "Tax Compliance Analyst",
    "US Tax Compliance Analyst",
    "Federal Tax Analyst",
    "State Tax Analyst",
    "Tax Research Analyst",
    "Tax Technical Analyst",
    "Tax Operations Analyst",
    # Reviewer (21–30)
    "Tax Reviewer",
    "Senior Tax Reviewer",
    "Tax Review Analyst",
    "Tax Quality Reviewer",
    "Tax Return Reviewer",
    "Tax Compliance Reviewer",
    "Tax Audit Reviewer",
    "Tax Technical Reviewer",
    "QA Associate US Tax Forms",
    "Tax Senior Reviewer",
    # Associate (31–40)
    "Tax Associate",
    "Senior Tax Associate",
    "Tax Staff Associate",
    "US Tax Associate",
    "Tax Associate Analyst",
    "Tax Associate Consultant",
    "Tax Associate Specialist",
    "Junior Tax Associate",
    "Tax Process Associate",
    "Tax Compliance Associate",
    # Consultant (41–50)
    "Tax Consultant",
    "US Tax Consultant",
    "Senior Tax Consultant",
    "Tax Advisory Consultant",
    "Tax Compliance Consultant",
    "Tax Technology Consultant",
    "Tax Planning Consultant",
    "Tax Transformation Consultant",
    "Tax Digital Consultant",
    "Tax Process Consultant",
]

LOCATIONS = [
    "Hyderabad",
    "Bangalore",
    "Chennai",
    "Kochi",
    "Visakhapatnam",
    "Mumbai",
    "Pune",
    "Delhi",
    "Noida",
    "Gurgaon",
    "Ahmedabad",
    "Kolkata",
]

MAX_JOBS_PER_CYCLE = 15
LINKEDIN_KEYWORD_LIMIT = 40
LINKEDIN_LOCATION_LIMIT = 10
SCRAPE_WINDOW_SECONDS = 86400  # 24h — LinkedIn 1h window returns 0 jobs for niche roles
MAX_ENRICH_PER_CYCLE = 50
CHECK_INTERVAL_LABEL = "1 hour"

PRIORITY_KEYWORDS = [
    "US Tax Preparer",
    "Tax Preparer",
    "Senior Tax Preparer",
    "Tax Analyst",
    "US Tax Analyst",
    "Senior Tax Analyst",
    "Tax Associate",
    "US Tax Associate",
    "Tax Consultant",
    "Tax Reviewer",
    "Tax Compliance Analyst",
    "Federal Tax Preparer",
    "Tax Return Preparer",
    "Tax Operations Analyst",
    "Senior Tax Associate",
]
