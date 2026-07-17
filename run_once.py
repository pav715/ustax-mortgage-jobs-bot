"""Single-cycle runner — US Tax Mortgage Jobs (Wells Fargo / Black Knight style roles)."""
import json
import os
import re
import time
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
import config

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
from scraper import fetch_all_jobs, SESSION
from sender import send_job, send_fail_alert
from experience_utils import extract_experience_from_job, pick_linkedin_criteria_experience

SEEN_FILE = "seen_jobs.json"
STATS_FILE = "stats.json"
STATE_FILE = "bot_state.json"


def _write_cycle_report(scraped=0, india=0, matched=0, new=0, sent=0, seen_total=0, **extra):
    data = {
        "scraped": scraped, "india": india, "matched": matched,
        "new": new, "sent": sent, "seen_total": seen_total, **extra,
        "at": datetime.utcnow().isoformat(),
    }
    try:
        with open("last_cycle.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _check_telegram():
    try:
        base = f"https://api.telegram.org/bot{config.BOT_TOKEN}"
        me = requests.get(f"{base}/getMe", timeout=10)
        chat = requests.get(f"{base}/getChat", params={"chat_id": config.CHAT_ID}, timeout=10)
        ok = me.status_code == 200 and chat.status_code == 200
        return ok, f"getMe={me.status_code} getChat={chat.status_code} {chat.text[:80]}"
    except Exception as e:
        return False, str(e)

BLOCKLIST = re.compile(
    r"\b("
    r"recruiter|recruitment|talent\s*acquisition|bench\s*sales|"
    r"us\s*it\s*recruiter|it\s*recruiter|"
    r"software\s*engineer(?!\s*(?:tax|mortgage))|software\s*developer(?!\s*(?:tax|mortgage))|"
    r"selenium|automation\s*tester|manual\s*tester|"
    r"construction\s*supervisor|site\s*supervisor|civil\s*engineer|"
    r"payroll(?!\s*tax)|accounts\s*payable|accounts\s*receivable|"
    r"statutory\s*audit|business\s*development|sales\s*executive|"
    r"\bgst\b|goods\s*and\s*services\s*tax|gstn|gst\s*compliance|gst\s*specialist|"
    r"income\s*tax\s*(?!withholding)|income\s*tax\s*consultant|income\s*tax\s*executive|"
    r"direct\s*tax(?!\s*analyst\s*(?:us|federal|state))|india\s*tax|domestic\s*tax|indian\s*tax|"
    r"\btds\b|\btcs\b|tax\s*deducted|tax\s*collected|tds\s*analyst|"
    r"indirect\s*tax(?!\s*analyst\s*(?:us|federal))|"
    r"\bvat\b(?!\s*us)|service\s*tax|excise\s*duty|customs\s*duty|"
    r"transfer\s*pricing|tax\s*litigation|"
    r"chartered\s*accountant|ca\s*article|ca\s*analyst|"
    r"accounts\s*analyst|^accountant$|"
    r"finance\s*executive|accounts\s*executive|"
    r"tax\s*auditor|statutory\s*compliance"
    r")\b",
    re.IGNORECASE,
)

INDIAN_TAX_BLOCKLIST = re.compile(
    r"\b("
    r"gst\s*analyst|gst\s*compliance|gst\s*executive|gst\s*specialist|gst\s*manager|"
    r"gst\s*consultant|gst\s*filing|gst\s*returns|gst\s*audit|gst\s*advisory|"
    r"income\s*tax\s*analyst|income\s*tax\s*consultant|income\s*tax\s*executive|"
    r"direct\s*tax\s*analyst|direct\s*tax\s*consultant|direct\s*tax\s*manager|"
    r"india\s*tax\s*analyst|india\s*tax\s*consultant|domestic\s*tax|"
    r"tds\s*analyst|tds\s*compliance|tcs\s*analyst|tds\s*executive|tds\s*filing|"
    r"indirect\s*tax\s*analyst|indirect\s*tax\s*consultant|indirect\s*tax\s*manager|"
    r"vat\s*analyst|service\s*tax|excise\s*duty|customs\s*duty|"
    r"tax\s*litigation|indirect\s*tax\s*specialist|"
    r"tax\s*auditor|transfer\s*pricing|"
    r"itr|itr-1|itr-2|itr-3|itr-4|itr-5|itr-6|itr-7|"
    r"form\s*16|form\s*16a|form\s*24q|"
    r"pan\s*number|aadhar|aadhaar|cin|gstin|"
    r"goods\s*and\s*services\s*tax|section\s*80|fy20[0-9]{2}|ay20[0-9]{2}|"
    r"tds|tcs|advance\s*tax|challan|saral|"
    r"indian\s*tax|india\s*tax|ato"
    r")\b",
    re.IGNORECASE,
)

# 100 keywords + 50 title keywords — loan / mortgage / financial services
MORTGAGE_KEYWORDS = [
    # Financial / Loan (1–20)
    "financial analysis", "loan lifecycle", "loan portfolio", "loan management",
    "loan processing", "loan approval", "loan documentation", "credit risk assessment",
    "credit analysis", "credit pack", "credit policy", "loan portfolio management",
    "portfolio review", "portfolio analysis", "portfolio performance", "loan origination",
    "loan servicing", "loan underwriting", "mortgage operations", "mortgage processing",
    # Analysis / Reporting (21–40)
    "financial modelling", "variance analysis", "mis reporting", "financial reporting",
    "dashboard reporting", "performance metrics", "financial data analysis", "data analysis",
    "business intelligence", "risk exposure", "delinquency analysis", "delinquency trends",
    "financial indicators", "key performance indicators", "exception handling", "trend analysis",
    "benchmarking analysis", "comparative analysis", "forecasting", "budget analysis",
    # Compliance / Regulatory (41–60)
    "regulatory compliance", "compliance monitoring", "federal regulations", "state regulations",
    "regulatory requirements", "regulatory updates", "regulatory reporting", "compliance standards",
    "credit policy adherence", "policy compliance", "risk management", "risk mitigation",
    "internal controls", "audit compliance", "sox compliance", "anti-money laundering",
    "know your customer", "regulatory guidelines", "compliance framework", "risk assessment",
    # Operations / Process (61–80)
    "document management", "credit pack indexing", "document indexing", "pdf processing",
    "document processing", "data management", "database management", "data integrity",
    "data quality", "remote desktop operations", "production environment", "process documentation",
    "process improvement", "process optimization", "workflow management", "quality control",
    "quality assurance", "standard operating procedures", "process compliance",
    # Banking / Companies (81–90)
    "wells fargo", "black knight", "mortgage banking", "commercial banking", "retail banking",
    "investment banking", "banking operations", "banking systems", "financial services",
    # Coordination / Management (91–100)
    "cross-functional coordination", "stakeholder management", "stakeholder reporting",
    "team collaboration", "team training", "knowledge management", "process training",
    "cost monitoring", "exception management", "workflow planning",
    # Mortgage-specific (retained)
    "mortgage", "home loan", "housing loan", "escrow", "foreclosure", "hmda",
    "fannie mae", "freddie mac", "loss mitigation", "default servicing", "msr", "mers",
    "property tax escrow", "1098", "mortgage tax", "tax servicing", "subservicing",
    # Title keywords (50 roles)
    "financial analyst", "senior financial analyst", "junior financial analyst",
    "financial data analyst", "financial modelling analyst", "financial operations analyst",
    "financial planning analyst", "financial performance analyst", "financial systems analyst",
    "financial reporting analyst", "loan analyst", "senior loan analyst", "credit analyst",
    "senior credit analyst", "credit risk analyst", "loan operations analyst",
    "loan documentation analyst", "loan processing analyst", "mortgage analyst",
    "mortgage operations analyst", "compliance analyst", "senior compliance analyst",
    "regulatory compliance analyst", "risk analyst", "senior risk analyst",
    "portfolio risk analyst", "compliance officer", "regulatory affairs analyst",
    "audit analyst", "internal compliance analyst", "operations analyst",
    "senior operations analyst", "mis analyst", "business analyst", "process analyst",
    "process improvement analyst", "quality assurance analyst", "banking operations analyst",
    "finance operations analyst", "process associate", "senior process associate",
    "process manager", "team lead", "operations manager", "portfolio manager",
    "relationship manager", "account manager", "project analyst", "document analyst",
    # Expanded mortgage / loan titles
    "mortgage underwriter", "mortgage loan officer", "mortgage closer", "mortgage post closer",
    "escrow analyst", "foreclosure analyst", "loss mitigation analyst", "default servicing analyst",
    "hmda analyst", "msr analyst", "home loan analyst", "housing loan analyst",
    "loan origination analyst", "commercial loan analyst", "consumer loan analyst",
    "credit pack analyst", "credit policy analyst", "mortgage quality analyst",
    "mortgage document analyst", "mortgage risk analyst", "regulatory reporting analyst",
    "aml analyst", "kyc analyst", "sox compliance analyst", "workflow analyst",
    "document indexing analyst", "credit pack indexing", "loan servicing specialist",
    "mortgage servicing specialist", "servicing analyst", "reo analyst", "collection analyst mortgage",
    "fannie mae analyst", "freddie mac analyst", "subservicing analyst", "mers analyst",
    "property tax escrow analyst", "1098 analyst", "mortgage tax analyst",
]

# Loan / mortgage / financial services signal — generic titles need one of these
REQUIRED_MORTGAGE_SIGNAL = re.compile(
    r"\b("
    r"mortgage|(?:\b|\s)loan\b|(?:\b|\s)credit\b|loan\s*servic|loan\s*process|loan\s*document|"
    r"loan\s*lifecycle|loan\s*portfolio|loan\s*underwrit|loan\s*originat|"
    r"credit\s*pack|credit\s*risk|document\s*index|credit\s*analysis|"
    r"wells\s*fargo|black\s*knight|mortgage\s*bank|banking\s*operat|"
    r"financial\s*services|loan\s*management|servicing|delinquency|"
    r"escrow|foreclosure|mortgage\s*operat|regulatory\s*compliance|"
    r"compliance\s*monitor|risk\s*management|portfolio\s*risk|"
    r"hmda|msr|mers|fannie\s*mae|freddie\s*mac|subservic|reo|"
    r"mortgage\s*clos|loan\s*clos|escrow|foreclosure|loss\s*mitigation|"
    r"aml|kyc|sox|regulatory\s*reporting|home\s*loan|housing\s*loan"
    r")\b",
    re.IGNORECASE,
)

# Generic titles — need loan/mortgage signal in full text
GENERIC_FINANCE_TITLE = re.compile(
    r"\b("
    r"financial\s*analyst|financial\s*data\s*analyst|financial\s*modelling\s*analyst|"
    r"financial\s*planning\s*analyst|financial\s*performance\s*analyst|"
    r"financial\s*systems\s*analyst|financial\s*reporting\s*analyst|"
    r"operations\s*analyst|mis\s*analyst|data\s*analyst|business\s*analyst|"
    r"process\s*analyst|process\s*improvement\s*analyst|quality\s*assurance\s*analyst|"
    r"process\s*associate|process\s*manager|team\s*lead|operations\s*manager|"
    r"portfolio\s*manager|relationship\s*manager|account\s*manager|"
    r"project\s*analyst|document\s*analyst|audit\s*analyst"
    r")\b",
    re.IGNORECASE,
)

MORTGAGE_ROLE_TITLE = re.compile(
    r"\b("
    # Financial Analyst (1–10)
    r"(?:senior|junior|financial\s*)?financial\s*(?:data|modelling|operations|planning|performance|systems|reporting)?\s*analyst|"
    # Loan / Credit (11–20)
    r"(?:senior\s*)?loan\s*analyst|(?:senior\s*)?credit\s*(?:risk\s*)?analyst|"
    r"loan\s*(?:operations|documentation|processing)\s*analyst|"
    r"mortgage\s*(?:operations\s*)?analyst|"
    # Compliance / Risk (21–30)
    r"(?:senior\s*|regulatory\s*|internal\s*)?compliance\s*(?:analyst|officer)|"
    r"regulatory\s*(?:compliance|affairs)\s*analyst|"
    r"(?:senior\s*|portfolio\s*)?risk\s*analyst|audit\s*analyst|"
    # Operations / MIS (31–40)
    r"(?:senior\s*)?operations\s*analyst|mis\s*analyst|"
    r"(?:banking|finance)\s*operations\s*analyst|"
    r"process\s*(?:improvement\s*)?analyst|quality\s*assurance\s*analyst|"
    # Process / Management (41–50)
    r"(?:senior\s*)?process\s*(?:associate|manager)|"
    r"team\s*lead|operations\s*manager|portfolio\s*manager|"
    r"relationship\s*manager|account\s*manager|project\s*analyst|document\s*analyst|"
    # Mortgage / loan core (retained)
    r"mortgage|home\s*loan|housing\s*loan|loan\s*servic(?:ing|er)?|"
    r"mortgage\s*underwrit(?:ing|er)?|underwrit(?:ing|er)|"
    r"mortgage\s*loan\s*(?:originator|officer|processor)|"
    r"mortgage\s*(?:specialist|associate|consultant|banking|operat(?:ions?|ional)?)|"
    r"loan\s*(?:officer|originator|processor|admin(?:istrator)?)|"
    r"process\s*associate|credit\s*pack|document\s*index|"
    r"escrow|foreclosure|loss\s*mitigation|default\s*servic(?:ing|er)?|"
    r"mortgage\s*tax|tax\s*servic(?:ing|er)?|property\s*tax|1098|"
    r"mortgage\s*(?:closer|post\s*closer|underwrit(?:er|ing)?|loan\s*officer|quality)|"
    r"home\s*loan|housing\s*loan|hmda|msr|mers|reo|subservic|"
    r"fannie\s*mae|freddie\s*mac|loan\s*originat|commercial\s*loan|consumer\s*loan|"
    r"aml|kyc|sox\s*compliance|regulatory\s*reporting|servicing\s*analyst"
    r")\b",
    re.IGNORECASE,
)

MORTGAGE_COMPANY_HINTS = re.compile(
    r"\b("
    r"wells\s*fargo|black\s*knight|ice\s*mortgage|intercontinental\s*exchange|"
    r"mr\.?\s*cooper|servicemac|cenlar|loancare|roundpoint|nationstar|"
    r"pennymac|flagstar|shellpoint|dovenmuehle|phh\s*mortgage|ocwen|"
    r"caliber\s*home|computershare|fis\s|fidelity\s*national|fnf|"
    r"rocket\s*mortgage|quicken\s*loans|uwm|united\s*wholesale|"
    r"loan\s*care|specialized\s*loan|selene|cooper\s*holdings|"
    r"american\s*home\s*mortgage|freedom\s*mortgage|newrez|"
    r"maxim\s*capital|dmi\s*mortgage|mortgage\s*connect|"
    r"docutech|lendsmart|nationwide\s*title|stewart\s*title|"
    r"cenlar|loancare|mr\.?\s*cooper|servicemac|rocket\s*mortgage|"
    r"pennymac|flagstar|newrez|freedom\s*mortgage|uwm|quicken\s*loans"
    r")\b",
    re.IGNORECASE,
)


INDIA_LOCATION_KEYWORDS = [
    "india", "hyderabad", "bangalore", "bengaluru", "chennai", "mumbai", "pune", "delhi",
    "gurgaon", "gurugram", "noida", "kolkata", "ahmedabad", "jaipur", "indore", "chandigarh",
    "kochi", "coimbatore", "lucknow", "visakhapatnam", "vizag",
]

FOREIGN_LOCATION_KEYWORDS = [
    "usa", "united states", "u.s.", "canada", "uk", "united kingdom", "australia", "europe",
    "egypt", "middle east", "africa", "singapore", "malaysia", "sweden", "sverige", "japan",
    "dubai", "germany", "france",
]


def _keyword_hits(text, keywords):
    hits = []
    for kw in keywords:
        if len(kw) <= 4:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                hits.append(kw)
        elif kw in text:
            hits.append(kw)
    return hits


def is_india_location(job):
    loc = (job.get("location") or "").lower()
    search_loc = (job.get("search_location") or "").lower()
    title = (job.get("title") or "").lower()

    if search_loc and any(kw in search_loc for kw in INDIA_LOCATION_KEYWORDS):
        return True

    if not loc.strip():
        return True

    if any(kw in loc for kw in FOREIGN_LOCATION_KEYWORDS):
        return False
    if any(kw in loc for kw in INDIA_LOCATION_KEYWORDS):
        return True
    if "remote" in loc:
        context = f"{loc} {title}"
        return "india" in context or any(kw in context for kw in INDIA_LOCATION_KEYWORDS)
    return False


_MORTGAGE_INTENT = re.compile(
    r"\b(mortgage|loan|credit|servicing|underwrit|financial|compliance|risk|banking|escrow|foreclosure|portfolio)\b",
    re.IGNORECASE,
)


def _title_matches_search(title, keyword):
    if not title or not keyword:
        return False
    tl = title.lower()
    kw_l = keyword.lower()
    domain_words = (
        "mortgage", "loan", "credit", "tax", "servicing", "underwrit",
        "financial", "compliance", "testing", "software", "banking", "escrow",
    )
    for d in domain_words:
        if d in kw_l:
            return d in tl
    words = [w for w in re.findall(r"[a-z]+", kw_l) if len(w) > 3]
    return bool(words) and all(w in tl for w in words)


def _passes_mortgage_search_trust(job):
    """Trust LinkedIn mortgage/loan keyword search when title aligns."""
    sk = (job.get("search_keyword") or "")
    sk_l = sk.lower()
    title = (job.get("title") or "").lower()
    if not sk_l or not _MORTGAGE_INTENT.search(sk_l):
        return False
    if INDIAN_TAX_BLOCKLIST.search(title) or BLOCKLIST.search(title):
        return False
    if _MORTGAGE_INTENT.search(title):
        return True
    if _title_matches_search(job.get("title", ""), sk):
        return True
    if re.search(
        r"\b(analyst|specialist|associate|officer|underwriter|processor|closer|servicing|manager|lead|consultant)\b",
        title,
    ):
        return True
    return False


def _passes_early_filter(job, role_title_pattern):
    """Only let likely mortgage/loan roles through before enrich."""
    title = job.get("title") or ""
    company = job.get("company") or ""
    title_l = title.lower()
    company_l = company.lower()
    sk = (job.get("search_keyword") or "").lower()
    if INDIAN_TAX_BLOCKLIST.search(title_l) or INDIAN_TAX_BLOCKLIST.search(company_l):
        return False
    if BLOCKLIST.search(title_l) or BLOCKLIST.search(company_l):
        return False
    if _passes_mortgage_search_trust(job):
        return True
    if sk and _MORTGAGE_INTENT.search(sk) and (_title_matches_search(title, sk) or _MORTGAGE_INTENT.search(title_l)):
        return True
    if MORTGAGE_COMPANY_HINTS.search(company_l):
        return True
    if re.search(
        r"\b(mortgage|loan|credit|servicing|underwrit|escrow|foreclosure|home\s*loan|housing\s*loan|financial\s*services)\b",
        title_l,
    ):
        return True
    if role_title_pattern.search(title_l):
        if GENERIC_FINANCE_TITLE.search(title_l):
            return bool(
                MORTGAGE_COMPANY_HINTS.search(company_l)
                or re.search(r"\b(mortgage|loan|credit|banking|financial\s*services)\b", title_l)
            )
        return True
    return False


def _has_mortgage_signal(text):
    return bool(REQUIRED_MORTGAGE_SIGNAL.search(text))


def is_mortgage_tax_job(job):
    """50 loan/financial services titles + 100 keywords — generic titles need loan signal."""
    desc = (job.get("description") or "").lower()
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    blob = f"{title} {company} {desc}"

    if INDIAN_TAX_BLOCKLIST.search(title) or INDIAN_TAX_BLOCKLIST.search(company):
        return False
    if BLOCKLIST.search(title) or BLOCKLIST.search(company):
        return False

    if _passes_mortgage_search_trust(job):
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: search keyword trust")
        return True

    sk = (job.get("search_keyword") or "")
    sk_l = sk.lower()
    # Title-based pass without description (avoids LinkedIn enrich rate limits)
    if re.search(
        r"\b(mortgage|loan|credit|servicing|underwrit|escrow|foreclosure|home\s*loan|housing\s*loan|financial)\b",
        title,
    ):
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: loan/mortgage title")
        return True
    if sk_l and _MORTGAGE_INTENT.search(sk_l) and _title_matches_search(title, sk):
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: search keyword")
        return True

    if MORTGAGE_ROLE_TITLE.search(title):
        if BLOCKLIST.search(title) or BLOCKLIST.search(company):
            return False
        if GENERIC_FINANCE_TITLE.search(title) and not _has_mortgage_signal(blob):
            if not re.search(r"\b(loan|credit|mortgage|compliance|risk|banking|financial)\b", title):
                return False
        elif not _has_mortgage_signal(blob) and not MORTGAGE_COMPANY_HINTS.search(company):
            # Loan-specific titles (credit/loan/mortgage/compliance) pass without extra signal
            if not re.search(
                r"\b(loan|credit|mortgage|compliance|risk|banking\s*operat|finance\s*operat)\b",
                title,
            ):
                return False
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: mortgage role title")
        return True

    if MORTGAGE_COMPANY_HINTS.search(company):
        if BLOCKLIST.search(title) or BLOCKLIST.search(company):
            return False
        if MORTGAGE_ROLE_TITLE.search(title) or _has_mortgage_signal(blob):
            print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: mortgage company")
            return True
        return False

    if BLOCKLIST.search(blob):
        return False
    if INDIAN_TAX_BLOCKLIST.search(blob):
        return False
    if not _has_mortgage_signal(blob):
        return False

    matched = _keyword_hits(blob, MORTGAGE_KEYWORDS)
    if len(matched) >= 1:
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: {matched}")
        return True
    return False


def _mark_run_complete(state):
    state["last_run_at"] = datetime.utcnow().isoformat()
    save_state(state)


IST = timedelta(hours=5, minutes=30)


def _ist_now():
    return datetime.utcnow() + IST


def _job_posted_ist(job):
    """Parse job posted timestamp as naive IST datetime."""
    posted = (job.get("posted") or "").strip()
    if not posted:
        return None
    iso = posted.replace("Z", "").split("+")[0]
    try:
        if re.match(r"\d{4}-\d{2}-\d{2}", iso):
            return datetime.fromisoformat(iso[:19]) + IST
    except Exception:
        pass
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(posted)
        if dt.tzinfo:
            dt = dt.utctimetuple()
            dt = datetime(*dt[:6])
        return dt + IST
    except Exception:
        pass
    return None


def _cycle_cutoff_ist(state):
    """Jobs must be posted after last successful run (≈ last hour)."""
    last = (state.get("last_run_at") or "").strip()
    now = _ist_now()
    if last:
        try:
            return datetime.fromisoformat(last[:19]) + IST
        except Exception:
            pass
    return now - timedelta(hours=1)


def _passes_post_window(job, cutoff_ist):
    """Today (IST) only, and posted since last schedule run."""
    dt = _job_posted_ist(job)
    if not dt:
        return False
    if dt.date() != _ist_now().date():
        return False
    return dt >= cutoff_ist


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"paused": False, "last_update_id": 0, "last_run_at": ""}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def load_stats():
    today = date.today().isoformat()
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE) as f:
                s = json.load(f)
            if s.get("date") == today:
                return s
        except Exception:
            pass
    return {"date": today, "sent": 0, "companies": {}, "summary_sent": False}


def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)


def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE) as f:
                data = json.load(f)
            if isinstance(data, list):
                return set(data)
            if isinstance(data, dict):
                return set(data.keys()) if data else set()
        except Exception:
            pass
    return set()


def save_seen(seen_set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_set)[-5000:], f)


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def _norm_dedup_text(s):
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s&]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _dedup_keys(job):
    title = _norm_dedup_text(job.get("title"))
    company = _norm_dedup_text(job.get("company"))
    keys = {f"{title}|{company}"}
    url = job.get("url") or ""
    m = re.search(r"/(\d{8,})", url)
    if m:
        keys.add(f"lid:{m.group(1)}")
    return keys


def _is_seen(job, seen):
    return any(k in seen for k in _dedup_keys(job))


def _mark_seen(job, seen):
    for k in _dedup_keys(job):
        seen.add(k)


def handle_commands(state, stats):
    if not config.BOT_TOKEN:
        return state
    try:
        offset = state.get("last_update_id", 0) + 1
        r = requests.get(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/getUpdates",
            params={"offset": offset, "timeout": 5, "limit": 10},
            timeout=10,
        )
        if r.status_code != 200:
            return state

        for update in r.json().get("result", []):
            state["last_update_id"] = update["update_id"]
            msg = update.get("message") or update.get("channel_post") or {}
            text = msg.get("text", "").strip().lower()
            chat_id = str(msg.get("chat", {}).get("id", ""))
            if not chat_id or chat_id != str(config.CHAT_ID):
                continue

            api = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
            if text.startswith("/status"):
                reply = (
                    f"🏠 *US Tax Mortgage Jobs Bot — Status*\n\n"
                    f"{'⏸ PAUSED' if state.get('paused') else '✅ RUNNING'}\n\n"
                    f"📊 *Today ({stats['date']}):*\n"
                    f"• Jobs sent: *{stats['sent']}*\n"
                    f"• Companies: *{len(stats['companies'])}*\n"
                    f"⏱ Checks every *{config.CHECK_INTERVAL_LABEL}*\n"
                    f"🕐 {datetime.now().strftime('%d %b %Y %H:%M IST')}"
                )
                requests.post(api, json={"chat_id": chat_id, "text": reply, "parse_mode": "Markdown"}, timeout=10)
            elif text == "/pause":
                state["paused"] = True
                requests.post(api, json={"chat_id": chat_id, "text": "⏸ *Bot paused.*", "parse_mode": "Markdown"}, timeout=10)
            elif text == "/resume":
                state["paused"] = False
                requests.post(api, json={"chat_id": chat_id, "text": "▶️ *Bot resumed.*", "parse_mode": "Markdown"}, timeout=10)
            elif text == "/help":
                requests.post(
                    api,
                    json={"chat_id": chat_id, "text": "🤖 /status /pause /resume /help", "parse_mode": "Markdown"},
                    timeout=10,
                )
    except Exception as e:
        log(f"[Commands] Error: {e}")
    return state


def enrich_job(job):
    if job.get("description") and len(job["description"]) > 200:
        return job
    url = job.get("url", "")
    fetched = False
    try:
        if "linkedin.com" in url:
            match = re.search(r"/(\d{8,})", url)
            if match:
                jid = match.group(1)
                detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}"
                r = SESSION.get(detail_url, timeout=12)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.content, "html.parser")
                    desc_div = (
                        soup.find("div", class_=re.compile(r"show-more-less-html|description__text"))
                        or soup.find("section", class_=re.compile(r"description"))
                    )
                    if desc_div:
                        job["description"] = desc_div.get_text(" ", strip=True)[:4000]
                        fetched = True
                    criteria = soup.find_all("span", class_=re.compile(r"description__job-criteria-text"))
                    exp_line = pick_linkedin_criteria_experience(criteria)
                    if exp_line:
                        job["experience"] = exp_line
    except Exception as e:
        log(f"  [Enrich] error: {e}")
    if fetched:
        time.sleep(1.0)
    return job


def extract_experience(desc, title="", raw_exp=""):
    return extract_experience_from_job(desc, raw_exp)


def extract_qualification(desc):
    qual_match = re.search(
        r"(B\.?Com|B\.?Tech|MBA|CA|CPA|EA|Bachelor|Master|Graduate)[^\n.]{0,80}",
        desc,
        re.IGNORECASE,
    )
    if qual_match:
        return qual_match.group(0).strip()[:120]
    return "Graduate / MBA Finance (preferred)"


def main():
    log("=" * 50)
    log("US Tax Mortgage Jobs Bot — LinkedIn + Naukri + Indeed")
    log("=" * 50)

    if not config.BOT_TOKEN or not config.CHAT_ID:
        log("ERROR: BOT_TOKEN or CHAT_ID not set.")
        sys.exit(1)

    tg_ok, tg_msg = _check_telegram()
    log(f"Telegram check: {tg_msg}")

    state = load_state()
    stats = load_stats()
    state = handle_commands(state, stats)
    save_state(state)

    if state.get("paused"):
        log("Bot is PAUSED.")
        return

    since_seconds = getattr(config, "SCRAPE_WINDOW_SECONDS", 86400)
    log(f"Fetch window: {since_seconds // 3600} hours")

    seen = load_seen()
    try:
        jobs = fetch_all_jobs(since_seconds=since_seconds)
    except Exception as e:
        log(f"Scrape error: {e}")
        send_fail_alert(str(e))
        sys.exit(1)

    if os.environ.get("SEED_MODE", "").lower() == "true":
        for job in jobs:
            _mark_seen(job, seen)
        save_seen(seen)
        _mark_run_complete(state)
        log(f"Seed mode: marked {len(jobs)} jobs as seen.")
        return

    india_jobs = [j for j in jobs if is_india_location(j)]
    log(f"India jobs: {len(india_jobs)} / {len(jobs)}")

    matched_jobs = []
    enrich_budget = getattr(config, "MAX_ENRICH_PER_CYCLE", 30)
    enriched = 0
    for job in india_jobs:
        if not _passes_early_filter(job, MORTGAGE_ROLE_TITLE):
            continue
        if is_mortgage_tax_job(job):
            matched_jobs.append(job)
            continue
        if enriched >= enrich_budget:
            continue
        job = enrich_job(job)
        enriched += 1
        if is_mortgage_tax_job(job):
            matched_jobs.append(job)

    log(f"Enriched {enriched} jobs (budget {enrich_budget})")
    log(f"Mortgage/Tax relevant: {len(matched_jobs)}")

    cutoff_ist = _cycle_cutoff_ist(state)
    log(f"Post window: today IST, since {cutoff_ist.strftime('%Y-%m-%d %H:%M IST')}")
    fresh_jobs = [j for j in matched_jobs if _passes_post_window(j, cutoff_ist)]
    log(f"Within post window: {len(fresh_jobs)} (from {len(matched_jobs)} matched)")

    new_jobs = [j for j in fresh_jobs if not _is_seen(j, seen)]
    new_jobs.sort(key=lambda j: str(j.get("posted") or j.get("fetched_at") or ""))
    log(f"New jobs to send: {len(new_jobs)}")

    if not new_jobs:
        save_seen(seen)
        save_stats(stats)
        _mark_run_complete(state)
        log("No new jobs this cycle.")
        _write_cycle_report(len(jobs), len(india_jobs), len(matched_jobs), 0, 0, len(seen), telegram_ok=tg_ok, telegram_detail=tg_msg)
        return

    if len(new_jobs) > config.MAX_JOBS_PER_CYCLE:
        new_jobs = new_jobs[: config.MAX_JOBS_PER_CYCLE]

    sent = 0
    for job in new_jobs:
        desc = job.get("description", "")
        title = job.get("title", "")
        job["_experience"] = extract_experience(desc, title, job.get("experience", ""))
        job["_qualification"] = extract_qualification(desc)
        if send_job(job):
            _mark_seen(job, seen)
            sent += 1
            stats["sent"] += 1
            co = job.get("company", "Other")
            stats["companies"][co] = stats["companies"].get(co, 0) + 1
            log(f"  Sent: {job['title']} @ {job['company']}")
        else:
            log(f"  Failed to send: {job['title']} @ {job['company']}")

    save_seen(seen)
    save_stats(stats)
    _mark_run_complete(state)
    _write_cycle_report(len(jobs), len(india_jobs), len(matched_jobs), len(new_jobs), sent, len(seen), telegram_ok=tg_ok, telegram_detail=tg_msg)
    log(f"Done. Sent {sent} jobs. Today total: {stats['sent']}.")


if __name__ == "__main__":
    main()
