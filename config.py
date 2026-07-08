import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

# LinkedIn search keywords — US Tax + Mortgage / Loan Servicing
KEYWORDS = [
    "US Mortgage",
    "Mortgage Tax",
    "Mortgage Servicing",
    "Loan Servicing",
    "Mortgage Operations",
    "US Mortgage Underwriting",
    "Mortgage Underwriter",
    "Mortgage Loan Originator",
    "Mortgage Loan Officer",
    "Mortgage Loan Processor",
    "Mortgage Closing",
    "Mortgage Specialist",
    "Live Underwriting",
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
CHECK_INTERVAL_LABEL = "1 hour"
