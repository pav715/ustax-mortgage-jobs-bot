import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

# LinkedIn search — mortgage / loan servicing / underwriting
KEYWORDS = [
    "US Mortgage",
    "Mortgage Tax",
    "Mortgage Servicing",
    "Loan Servicing",
    "Mortgage Operations",
    "Mortgage Underwriter",
    "Mortgage Loan Originator",
    "Mortgage Loan Officer",
    "Mortgage Loan Processor",
    "Mortgage Closing",
    "Mortgage Specialist",
    "Mortgage Analyst",
    "Mortgage Associate",
    "Mortgage Consultant",
    "US Mortgage Underwriting",
    "Live Underwriting",
    "Default Servicing",
    "Loss Mitigation",
    "Loan Officer",
    "Loan Processor",
    "Home Loan",
    "Housing Loan",
    "Mortgage Banking",
    "Escrow Analyst",
    "Foreclosure Specialist",
    "Credit Pack",
    "Document Indexing",
    "Black Knight",
    "Wells Fargo Mortgage",
    "MSR Mortgage",
    "Mortgage Compliance",
    "Tax Servicing",
    "Property Tax Escrow",
    "Loan Documentation",
    "Mortgage Post Closer",
    "Subservicing",
    "Mortgage",
    "Underwriter",
    "Loan Origination",
    "Mortgage Processor",
    "Servicing Analyst",
    "Mortgage Collections",
    "REO Specialist",
    "Loan Modification",
    "Mortgage QA",
    "Mortgage Technology",
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
