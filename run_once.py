"""Single-cycle runner for GitHub Actions — LinkedIn only. Updated: 2026-07-04"""
import json
import os
import re
import time
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
import config

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from scraper import fetch_all_jobs, SESSION
from sender import send_job, send_daily_summary, send_fail_alert
from experience_utils import extract_experience_from_job, pick_linkedin_criteria_experience

SEEN_FILE  = "seen_jobs.json"
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

US_TAX_KEYWORDS = [
    # Tax Forms (1–25)
    "form 1040", "form 1040nr", "form 1040sr", "form 1041", "form 1120", "form 1120s",
    "form 1065", "form 990", "form 1099", "w-2", "w-4", "schedule a", "schedule b",
    "schedule c", "schedule d", "schedule e", "schedule f", "schedule k-1", "schedule se",
    "form 2441", "form 8863", "form 8949", "form 1098", "form 1095", "1040 preparation",
    # IRS / Regulatory (26–40)
    "irs", "irs guidelines", "irs regulations", "irs compliance", "department of revenue",
    "dor", "federal tax", "state tax", "tax compliance", "tax law", "tax code",
    "tax reform", "tax withholding", "tax liability", "tax deductions",
    # Preparation Process (41–55)
    "tax preparation", "tax return preparation", "tax filing", "tax review", "tax reviewer",
    "tax return review", "quality review", "tax advisory", "client returns", "tax planning",
    "tax research", "tax compliance review", "return review", "tax processing", "tax engagement",
    # Tax Software (56–70)
    "lacerte", "proseries", "gosystem", "onesource", "ultratax", "cch axcess",
    "prosystem fx", "drake", "atx", "taxwise", "taxact", "taxslayer", "proconnect",
    "crosslink", "h&r block",
    # Entity Types (71–80)
    "individual tax", "corporate tax", "partnership tax", "s-corporation", "fiduciary tax",
    "non-resident tax", "trust tax", "estate tax", "exempt organization", "self-employed tax",
    # Income Types (81–90)
    "w-2 income", "1099 income", "rental income", "business income", "capital gains",
    "dividend income", "interest income", "self-employment income", "foreign income", "passive income",
    # Skills/Process (91–100)
    "regulatory compliance", "multi-state filing", "federal compliance", "state compliance",
    "tax deadline", "tax documentation", "client interaction", "tax strategy", "tax accuracy",
    # Title keywords (Top 50 roles)
    "us tax preparer", "tax preparer", "senior tax preparer", "individual tax preparer",
    "tax return preparer", "tax preparation specialist", "tax filing specialist",
    "tax preparation analyst", "tax return specialist", "federal tax preparer",
    "tax analyst", "us tax analyst", "senior tax analyst", "tax compliance analyst",
    "us tax compliance analyst", "federal tax analyst", "state tax analyst",
    "tax research analyst", "tax technical analyst", "tax operations analyst",
    "tax reviewer", "senior tax reviewer", "tax review analyst", "tax quality reviewer",
    "tax return reviewer", "tax compliance reviewer", "tax audit reviewer",
    "tax technical reviewer", "qa associate us tax forms", "tax senior reviewer",
    "tax associate", "senior tax associate", "tax staff associate", "us tax associate",
    "tax associate analyst", "tax associate consultant", "tax associate specialist",
    "junior tax associate", "tax process associate", "tax compliance associate",
    "tax consultant", "us tax consultant", "senior tax consultant", "tax advisory consultant",
    "tax compliance consultant", "tax technology consultant", "tax planning consultant",
    "tax transformation consultant", "tax digital consultant", "tax process consultant",
    # US Tax context
    "us tax", "us taxation", "u.s. tax", "enrolled agent", "cpa tax",
]

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

BLOCKLIST = re.compile(
    r"\b("
    r"recruiter|recruitment|talent\s*acquisition|bench\s*sales|"
    r"us\s*it\s*recruiter|it\s*recruiter|"
    r"software\s*engineer(?!\s*tax)|software\s*developer(?!\s*tax)|"
    r"selenium|automation\s*tester|manual\s*tester|"
    r"payroll(?!\s*tax)|accounts\s*payable|accounts\s*receivable|"
    r"statutory\s*audit|business\s*development|sales\s*executive|"
    # Indian tax roles - GST (1-10)
    r"\bgst\b|goods\s*and\s*services\s*tax|gstn|gst\s*compliance|gst\s*specialist|gst\s*manager|gst\s*consultant|gst\s*filing|gst\s*returns|gst\s*audit|gst\s*advisory|"
    # Income Tax India (11-20)
    r"income\s*tax\s*(?!withholding)|income\s*tax\s*consultant|income\s*tax\s*executive|"
    r"direct\s*tax(?!\s*analyst\s*(?:us|federal|state))|india\s*tax|domestic\s*tax|indian\s*tax|"
    # TDS / TCS (21-25)
    r"\btds\b|\btcs\b|tax\s*deducted|tax\s*collected|tds\s*analyst|tds\s*filing|"
    # Indirect Tax India (26-35)
    r"indirect\s*tax(?!\s*analyst\s*(?:us|federal))|"
    r"\bvat\b(?!\s*us)|service\s*tax|excise\s*duty|customs\s*duty|"
    r"transfer\s*pricing|tax\s*litigation|"
    # CA / Finance Related (36-45)
    r"chartered\s*accountant|ca\s*article|ca\s*analyst|"
    r"(?<!us\s)(?<!federal\s)finance\s*analyst(?!\s*us)|accounts\s*analyst|^accountant$|"
    r"financial\s*analyst(?!\s*(?:us|tax))|finance\s*executive|accounts\s*executive|"
    # Other Indian Tax (46-50)
    r"tax\s*auditor|statutory\s*compliance|tax\s*compliance\s*executive(?!\s*us)"
    r")\b",
    re.IGNORECASE,
)

# STRICT: Reject all Indian tax roles - no US Tax jobs should have these keywords
# Title match — US Tax roles (primary accept rule)
US_TAX_TITLE = re.compile(
    r"\b("
    # Preparer (1–10)
    r"(?:us|u\.s\.|federal|individual|senior)\s*tax\s*prepar(?:er|ation)|"
    r"tax\s*prepar(?:er|ation)|tax\s*return\s*prepar(?:er|ation)?|"
    r"tax\s*filing\s*specialist|tax\s*preparation\s*(?:specialist|analyst)|"
    r"tax\s*return\s*specialist|"
    # Analyst (11–20)
    r"(?:us|u\.s\.|federal|state|senior)\s*tax\s*analyst|"
    r"tax\s*(?:compliance|research|technical|operations)\s*analyst|"
    r"tax\s*analyst|"
    # Reviewer (21–30)
    r"(?:senior|quality|return|compliance|audit|technical)?\s*tax\s*review(?:er|ing)?|"
    r"tax\s*review\s*analyst|tax\s*senior\s*reviewer|"
    r"qa\s*associate.{0,20}(?:us\s*)?tax\s*forms|"
    # Associate (31–40)
    r"(?:us|u\.s\.|senior|junior|staff|process|compliance)\s*tax\s*associate|"
    r"tax\s*associate(?:\s*(?:analyst|consultant|specialist))?|"
    # Consultant (41–50)
    r"(?:us|u\.s\.|senior)\s*tax\s*consultant|"
    r"tax\s*(?:advisory|compliance|technology|planning|transformation|digital|process)\s*consultant|"
    r"tax\s*consultant|"
    # US Tax general
    r"u\.?\s*s\.?\s*tax(?:ation)?|us\s*tax(?:ation)?|"
    r"enrolled\s*agent|cpa\s*(?:us\s*)?tax|tax\s*cpa"
    r")\b",
    re.IGNORECASE,
)

INDIAN_TAX_BLOCKLIST = re.compile(
    r"\b("
    # GST Related (1-10) — includes bare "gst" now
    r"gst|gst\s*analyst|gst\s*compliance|gst\s*executive|gst\s*specialist|gst\s*manager|"
    r"gst\s*consultant|gst\s*filing|gst\s*returns|gst\s*audit|gst\s*advisory|gstin|"
    # Income Tax India (11-20)
    r"income\s*tax\s*analyst|income\s*tax\s*consultant|income\s*tax\s*executive|"
    r"direct\s*tax\s*analyst|direct\s*tax\s*consultant|direct\s*tax\s*manager|"
    r"india\s*tax\s*analyst|india\s*tax\s*consultant|domestic\s*tax|"
    # TDS / TCS (21-25)
    r"tds\s*analyst|tds\s*compliance|tcs\s*analyst|tds\s*executive|tds\s*filing|"
    # Indirect Tax India (26-35)
    r"indirect\s*tax\s*analyst|indirect\s*tax\s*consultant|indirect\s*tax\s*manager|"
    r"vat\s*analyst|service\s*tax|excise\s*duty|customs\s*duty|"
    r"tax\s*litigation|indirect\s*tax\s*specialist|"
    # Other Indian Tax (46-50)
    r"tax\s*auditor|tax\s*litigation\s*specialist|transfer\s*pricing|"
    r"tax\s*compliance\s*executive|statutory\s*compliance|"
    # Indian payroll / statutory terms not tax-titled but India-only context
    r"provident\s*fund|\bpf\s*(?:compliance|filing|deduction|withdrawal)|\besi\b|epfo|"
    r"professional\s*tax|labour\s*welfare\s*fund|"
    # Keywords that indicate Indian context
    r"itr|itr-1|itr-2|itr-3|itr-4|itr-5|itr-6|itr-7|"
    r"form\s*16|form\s*16a|form\s*24q|"
    r"pan\s*number|aadhar|aadhaar|\bcin\b|"
    r"goods\s*and\s*services\s*tax|section\s*80|fy20[0-9]{2}|ay20[0-9]{2}|"
    r"tds|tcs|advance\s*tax|challan|saral|"
    r"indian\s*tax|india\s*tax"
    r")\b",
    re.IGNORECASE,
)




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
    """Accept: India search + India on-site/remote. Accept USA REMOTE. Reject US state on-site."""
    loc = (job.get("location") or "").lower()
    search_loc = (job.get("search_location") or "").lower()
    title = (job.get("title") or "").lower()

    # Rule 1: India search location always passes
    if search_loc and any(kw in search_loc for kw in INDIA_LOCATION_KEYWORDS):
        return True

    # Empty location = UNKNOWN, accept for US tax jobs (return False)
    if not loc.strip():
        return False

    # Rule 2: Reject non-India foreign locations
    if any(kw in loc for kw in FOREIGN_LOCATION_KEYWORDS):
        # Exception: Allow USA if it's remote
        if "usa" in loc and "remote" in loc:
            return True
        return False

    # Rule 3: Accept India on-site jobs
    if any(kw in loc for kw in INDIA_LOCATION_KEYWORDS):
        return True

    # Rule 4: Remote jobs - accept India context, reject US state on-site
    if "remote" in loc:
        # If location contains USA + remote, accept
        if "usa" in loc:
            return True
        # Check for India context in other remote jobs
        context = f"{loc} {title}"
        return "india" in context or any(kw in context for kw in INDIA_LOCATION_KEYWORDS)

    # Rule 5: Reject onsite US state jobs
    us_states = ["ohio", "new york", "california", "texas", "florida", "illinois",
                 "pennsylvania", "georgia", "north carolina", "michigan", "arizona",
                 "colorado", "washington", "ny", "ca", "tx", "fl", "il", "pa", "ga", "nc", "mi", "az", "co", "wa", "oh"]
    if any(state in loc for state in us_states):
        return False

    return False


def _passes_early_filter(job, role_title_pattern):
    title = job.get("title") or ""
    company = job.get("company") or ""
    sk = job.get("search_keyword") or ""
    title_l = title.lower()
    company_l = company.lower()
    if INDIAN_TAX_BLOCKLIST.search(title_l) or INDIAN_TAX_BLOCKLIST.search(company_l):
        return False
    if BLOCKLIST.search(title_l) or BLOCKLIST.search(company_l):
        return False
    if re.search(r"\btax\b", title_l):
        return True
    if sk and _title_matches_search(title, sk):
        return True
    if role_title_pattern.search(title_l):
        return True
    return False


def _title_matches_search(title, keyword):
    """Require the domain word AND at least one other substantive keyword word in the title."""
    if not title or not keyword:
        return False
    tl = title.lower()
    kw_l = keyword.lower()
    domain_words = (
        "mortgage", "loan", "credit", "tax", "servicing", "underwrit",
        "financial", "compliance", "testing", "software", "banking", "escrow",
    )
    words = [w for w in re.findall(r"[a-z]+", kw_l) if len(w) > 3]
    matched_domain = next((d for d in domain_words if d in kw_l), None)
    if matched_domain:
        if matched_domain not in tl:
            return False
        other_words = [w for w in words if w not in matched_domain and matched_domain not in w]
        if not other_words:
            return True
        return any(w in tl for w in other_words)
    return bool(words) and all(w in tl for w in words)


def is_us_tax_job(job):
    """Accept US Tax titled roles first; then keyword match in full text."""
    desc = (job.get("description") or "").lower()
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    blob = f"{title} {company} {desc}"

    if INDIAN_TAX_BLOCKLIST.search(title) or INDIAN_TAX_BLOCKLIST.search(company):
        return False

    sk = (job.get("search_keyword") or "")
    if sk and "tax" in sk.lower() and re.search(r"\btax\b", title):
        if not BLOCKLIST.search(title) and not INDIAN_TAX_BLOCKLIST.search(blob):
            if _title_matches_search(title, sk) or US_TAX_TITLE.search(title):
                print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: search keyword + tax")
                return True

    if US_TAX_TITLE.search(title):
        if BLOCKLIST.search(title) or BLOCKLIST.search(company):
            return False
        if INDIAN_TAX_BLOCKLIST.search(blob):
            return False
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: us tax title")
        return True

    if BLOCKLIST.search(blob):
        return False
    if INDIAN_TAX_BLOCKLIST.search(blob):
        return False

    # Require the literal word "tax" plus at least 2 strong US-tax signals —
    # prevents generic HR boilerplate ("regulatory compliance", "quality review")
    # from passing on a single weak keyword hit with no real tax content.
    if not re.search(r"\btax\b", blob):
        return False
    matched = _keyword_hits(blob, US_TAX_KEYWORDS)
    if len(matched) >= 2:
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: {matched}")
        return True
    return False


def _mark_run_complete(state):
    state["last_run_at_ist"] = _ist_now().isoformat()
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
    now = _ist_now()
    last_ist = (state.get("last_run_at_ist") or "").strip()
    if last_ist:
        try:
            return datetime.fromisoformat(last_ist[:19])
        except Exception:
            pass
    # Backward-compat: old state files only stored last_run_at as raw UTC.
    last_utc = (state.get("last_run_at") or "").strip()
    if last_utc:
        try:
            return datetime.fromisoformat(last_utc[:19]) + IST
        except Exception:
            pass
    return now - timedelta(hours=1)


def _passes_post_window(job, cutoff_ist=None):
    """Job posted after last successful run (cutoff)."""
    if not cutoff_ist:
        cutoff_ist = _ist_now() - timedelta(hours=1)
    dt = _job_posted_ist(job)
    if not dt:
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
    """Load seen job IDs. Handles [], {}, and corrupt files gracefully."""
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                return set(data)
            if isinstance(data, dict):
                return set(data.keys()) if data else set()
        except Exception:
            pass
    return set()


def save_seen(seen_set):
    data = list(seen_set)[-5000:]
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


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

        updates = r.json().get("result", [])
        for update in updates:
            state["last_update_id"] = update["update_id"]
            msg = (update.get("message") or update.get("channel_post") or {})
            text = msg.get("text", "").strip().lower()
            chat_id = str(msg.get("chat", {}).get("id", ""))
            if not chat_id or chat_id != str(config.CHAT_ID):
                continue

            api = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"

            if text.startswith("/status"):
                reply = (
                    f"🤖 *US Tax Jobs Bot — Status*\n\n"
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
                requests.post(api, json={"chat_id": chat_id, "text": "⏸ *Bot paused.* Send /resume to restart.", "parse_mode": "Markdown"}, timeout=10)
            elif text == "/resume":
                state["paused"] = False
                requests.post(api, json={"chat_id": chat_id, "text": "▶️ *Bot resumed.* Notifications are back on.", "parse_mode": "Markdown"}, timeout=10)
            elif text == "/help":
                reply = "🤖 *Commands:*\n/status — Bot status\n/pause — Pause\n/resume — Resume\n/help — Help"
                requests.post(api, json={"chat_id": chat_id, "text": reply, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        log(f"[Commands] Error: {e}")
    return state


def enrich_job(job):
    """Fetch full job description from LinkedIn detail page."""
    if job.get("description") and len(job["description"]) > 200:
        return job
    url = job.get("url", "")
    fetched = False
    try:
        if "linkedin.com" in url:
            match = re.search(r'/(\d{8,})', url)
            if match:
                jid = match.group(1)
                detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}"
                r = SESSION.get(detail_url, timeout=12)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.content, "html.parser")
                    desc_div = (
                        soup.find("div", class_=re.compile(r"show-more-less-html|description__text")) or
                        soup.find("section", class_=re.compile(r"description"))
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


def extract_qualification(desc, title):
    qual_match = re.search(
        r"(B\.?Com|B\.?Tech|MBA|CA|CPA|EA|Bachelor|Master|Graduate|Post.?Graduate)[^\n.]{0,80}",
        desc, re.IGNORECASE,
    )
    if qual_match:
        return qual_match.group(0).strip()[:120]
    return "Graduate / Post-Graduate (Accounting / Finance preferred)"


def main():
    log("=" * 50)
    log("US Tax Jobs Bot — LinkedIn Only")
    log("=" * 50)

    if not config.BOT_TOKEN or not config.CHAT_ID:
        log("ERROR: BOT_TOKEN or CHAT_ID not set in environment.")
        sys.exit(1)

    log(f"BOT_TOKEN present: {len(config.BOT_TOKEN)} chars")
    log(f"CHAT_ID: {config.CHAT_ID}")
    tg_ok, tg_msg = _check_telegram()
    log(f"Telegram check: {tg_msg}")

    state = load_state()
    stats = load_stats()

    state = handle_commands(state, stats)
    save_state(state)

    if state.get("paused"):
        log("Bot is PAUSED. Send /resume to restart.")
        return

    # Dynamic scrape window: fetch only jobs since last successful run (approx. 1 hour for hourly runs)
    cutoff_ist = _cycle_cutoff_ist(state)
    now_ist = _ist_now()
    since_seconds = max(300, int((now_ist - cutoff_ist).total_seconds()))  # min 5 min
    log(f"Fetch window: {since_seconds}s ({since_seconds // 60}m) — since last run at {cutoff_ist.strftime('%H:%M IST')}")

    seen = load_seen()
    log(f"Loaded {len(seen)} previously seen jobs.")

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
        log(f"Seed mode: marked {len(jobs)} jobs as seen, sent 0.")
        return

    print(f"DEBUG: Total jobs scraped: {len(jobs)}")
    log(f"Total jobs scraped: {len(jobs)}")

    india_jobs = [j for j in jobs if is_india_location(j)]
    log(f"India/Remote: {len(india_jobs)} out of {len(jobs)} total.")

    us_tax_jobs = []
    enrich_budget = getattr(config, "MAX_ENRICH_PER_CYCLE", 30)
    enriched = 0
    for job in india_jobs:
        if not _passes_early_filter(job, US_TAX_TITLE):
            continue
        if is_us_tax_job(job):
            us_tax_jobs.append(job)
            continue
        if enriched >= enrich_budget:
            continue
        job = enrich_job(job)
        enriched += 1
        if is_us_tax_job(job):
            us_tax_jobs.append(job)

    log(f"Enriched {enriched} jobs (budget {enrich_budget})")

    log(f"US Tax relevant: {len(us_tax_jobs)} out of {len(india_jobs)} India jobs.")

    cutoff_ist = _cycle_cutoff_ist(state)
    log(f"Post window: since last run at {cutoff_ist.strftime('%Y-%m-%d %H:%M IST')}")
    fresh_jobs = [j for j in us_tax_jobs if _passes_post_window(j, cutoff_ist)]
    log(f"Posted since cutoff: {len(fresh_jobs)} (from {len(us_tax_jobs)} matched)")

    new_jobs = [j for j in fresh_jobs if not _is_seen(j, seen)]
    new_jobs.sort(key=lambda j: str(j.get("posted") or j.get("fetched_at") or ""))
    log(f"New jobs to send: {len(new_jobs)}")

    if not new_jobs:
        log("No new US Tax jobs this cycle.")
        save_seen(seen)
        save_stats(stats)
        _mark_run_complete(state)
        _write_cycle_report(len(jobs), len(india_jobs), len(us_tax_jobs), 0, 0, len(seen), fresh_today=len(fresh_jobs), telegram_ok=tg_ok, telegram_detail=tg_msg)
        return

    if len(new_jobs) > config.MAX_JOBS_PER_CYCLE:
        log(f"Capping to {config.MAX_JOBS_PER_CYCLE} jobs this cycle.")
        new_jobs = new_jobs[:config.MAX_JOBS_PER_CYCLE]

    sent = 0
    for job in new_jobs:
        desc  = job.get("description", "")
        title = job.get("title", "")
        if not job.get("_experience"):
            job["_experience"] = extract_experience(desc, title, job.get("experience", ""))
        if not job.get("_qualification"):
            job["_qualification"] = extract_qualification(desc, title)

        try:
            ok = send_job(job)
            if ok:
                _mark_seen(job, seen)
                sent += 1
                stats["sent"] += 1
                company = job.get("company", "Other")
                stats["companies"][company] = stats["companies"].get(company, 0) + 1
                log(f"  Sent: {job['title']} @ {job['company']}")
            else:
                log(f"  Failed: {job['title']}")
        except Exception as e:
            log(f"  Error: {e}")

    save_seen(seen)
    save_stats(stats)
    _mark_run_complete(state)
    _write_cycle_report(len(jobs), len(india_jobs), len(us_tax_jobs), len(new_jobs), sent, len(seen), fresh_today=len(fresh_jobs), telegram_ok=tg_ok, telegram_detail=tg_msg)
    log(f"Done. Sent {sent} new jobs. Today total: {stats['sent']}. Tracked: {len(seen)}")


if __name__ == "__main__":
    main()
