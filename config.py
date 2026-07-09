import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

# LinkedIn search — 50 Financial Services / Loan / Compliance titles
KEYWORDS = [
    # Financial Analyst (1–10)
    "Financial Analyst",
    "Senior Financial Analyst",
    "Financial Data Analyst",
    "Financial Operations Analyst",
    "Financial Reporting Analyst",
    # Loan / Credit Analyst (11–20)
    "Loan Analyst",
    "Credit Analyst",
    "Credit Risk Analyst",
    "Loan Operations Analyst",
    "Loan Documentation Analyst",
    "Loan Processing Analyst",
    "Mortgage Analyst",
    "Mortgage Operations Analyst",
    # Compliance / Risk (21–30)
    "Compliance Analyst",
    "Regulatory Compliance Analyst",
    "Risk Analyst",
    "Portfolio Risk Analyst",
    "Regulatory Affairs Analyst",
    "Internal Compliance Analyst",
    # Operations / MIS (31–40)
    "Banking Operations Analyst",
    "Finance Operations Analyst",
    "MIS Analyst Banking",
    "Process Analyst Loan",
    "Quality Assurance Analyst Mortgage",
    # Process / Management (41–50)
    "Process Associate Mortgage",
    "Senior Process Associate Loan",
    "Document Analyst Loan",
    "Loan Servicing Analyst",
    "Mortgage Loan Processor",
    "Mortgage Servicing",
    "Loan Servicing",
    "Credit Pack Indexing",
    "Document Indexing Mortgage",
    "Wells Fargo Analyst",
    "Black Knight Analyst",
    "Mortgage Banking Analyst",
    "Loan Portfolio Analyst",
    "Mortgage Compliance Analyst",
    "Loan Underwriting Analyst",
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
