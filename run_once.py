"""Single-cycle runner — US Tax Mortgage Jobs (Wells Fargo / Black Knight style roles)."""
import json
import os
import re
import time
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import config

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
from scraper import fetch_all_jobs, SESSION
from sender import send_job, send_fail_alert

SEEN_FILE = "seen_jobs.json"
STATS_FILE = "stats.json"
STATE_FILE = "bot_state.json"

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
    r"(?<!us\s)(?<!federal\s)finance\s*analyst(?!\s*us)|accounts\s*analyst|^accountant$|"
    r"financial\s*analyst(?!\s*(?:us|tax|mortgage))|finance\s*executive|accounts\s*executive|"
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

# Resume-aligned: Black Knight (loan lifecycle, doc indexing) + Wells Fargo mortgage ops
MORTGAGE_KEYWORDS = [
    "mortgage", "loan servicing", "loan lifecycle", "servicing platform", "black knight",
    "msp mortgage", "empower loan", "wells fargo", "document indexing", "doc centre",
    "doc center", "credit pack", "loan documentation", "loss mitigation", "default servicing",
    "foreclosure", "escrow", "hmda", "fannie mae", "freddie mac", "ginnie mae", "mers",
    "mortgage servicing", "mortgage operations", "mortgage tax", "property tax escrow",
    "1098", "mortgage interest", "tax servicing", "msr", "mbs", "remic", "subservicing",
    "loan number", "production environment", "mis report", "loan origination",
    "servicer", "mortgage compliance", "mortgage analyst", "process associate",
    "form 1098", "irs", "real estate tax",
]

MORTGAGE_DOMAIN_KEYWORDS = {
    "mortgage", "loan servicing", "loan lifecycle", "servicing", "black knight",
    "wells fargo", "escrow", "foreclosure", "hmda", "fannie", "freddie", "ginnie",
    "mers", "msr", "mbs", "credit pack", "document indexing", "loan documentation",
    "loss mitigation", "default servicing", "mortgage tax", "1098", "tax servicing",
}

# Title must contain US Mortgage (e.g. "US Mortgage Analyst", "Senior US Mortgage Associate")
US_MORTGAGE_TITLE = re.compile(
    r"\b(u\.?\s*s\.?\s*mortgage|us\s*mortgage)\b",
    re.IGNORECASE,
)

TITLE_HINTS = re.compile(
    r"\b("
    r"mortgage|loan\s*servic|servicing|process\s*associate|mortgage\s*tax|"
    r"document\s*index|credit\s*pack|loss\s*mitigation|escrow|foreclosure|"
    r"mortgage\s*operat|mortgage\s*analyst|loan\s*operat|tax\s*servic|"
    r"default\s*servic|hmda|mers|msr|black\s*knight|wells\s*fargo"
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
    title = (job.get("title") or "").lower()

    if any(kw in loc for kw in FOREIGN_LOCATION_KEYWORDS):
        return False
    if any(kw in loc for kw in INDIA_LOCATION_KEYWORDS):
        return True
    if "remote" in loc:
        context = f"{loc} {title}"
        return "india" in context or any(kw in context for kw in INDIA_LOCATION_KEYWORDS)
    return False


def is_mortgage_tax_job(job):
    """Accept US Mortgage titled roles, or 2+ mortgage keywords + domain + title hint."""
    desc = (job.get("description") or "").lower()
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    blob = f"{title} {company} {desc}"

    if BLOCKLIST.search(blob):
        return False
    if INDIAN_TAX_BLOCKLIST.search(blob):
        return False

    if US_MORTGAGE_TITLE.search(title):
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: us mortgage title")
        return True

    matched = _keyword_hits(blob, MORTGAGE_KEYWORDS)
    has_domain = any(kw in blob for kw in MORTGAGE_DOMAIN_KEYWORDS)
    title_ok = bool(TITLE_HINTS.search(title) or TITLE_HINTS.search(company))

    if len(matched) >= 2 and has_domain and title_ok:
        print(f"DEBUG: '{job.get('title')}' @ {job.get('company')} matched: {matched}")
        return True
    return False


def _mark_run_complete(state):
    state["last_run_at"] = datetime.utcnow().isoformat()
    save_state(state)


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


def _dedup_key(job):
    title = (job.get("title") or "").lower().strip()
    company = (job.get("company") or "").lower().strip()
    return f"{title}|{company}"


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
    if job.get("description") and len(job["description"]) > 300:
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
                        job["description"] = desc_div.get_text(" ", strip=True)[:2000]
                        fetched = True
    except Exception as e:
        log(f"  [Enrich] error: {e}")
    if fetched:
        time.sleep(1.0)
    return job


def extract_experience(desc, title):
    for p in [
        r"(\d+\+?\s*(?:to|-)\s*\d*\+?\s*years?[^\n.]*)",
        r"(\d+\+?\s*years?\s*(?:of\s*)?experience[^\n.]*)",
    ]:
        m = re.search(p, desc, re.IGNORECASE)
        if m:
            return m.group(1).strip()[:100]
    t = title.lower()
    if any(x in t for x in ["senior", "manager", "lead"]):
        return "5+ Years (Mortgage / Loan Servicing)"
    if any(x in t for x in ["associate", "junior", "jr"]):
        return "1-3 Years (Mortgage Operations)"
    return "2-5 Years (US Tax Mortgage)"


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
    log("US Tax Mortgage Jobs Bot — LinkedIn")
    log("=" * 50)

    if not config.BOT_TOKEN or not config.CHAT_ID:
        log("ERROR: BOT_TOKEN or CHAT_ID not set.")
        sys.exit(1)

    state = load_state()
    stats = load_stats()
    state = handle_commands(state, stats)
    save_state(state)

    if state.get("paused"):
        log("Bot is PAUSED.")
        return

    last_run = state.get("last_run_at", "")
    if last_run:
        try:
            elapsed = (datetime.utcnow() - datetime.fromisoformat(last_run)).total_seconds()
            since_seconds = int(elapsed) + 300
        except Exception:
            since_seconds = 2400
    else:
        since_seconds = 2400
    since_seconds = max(1800, min(since_seconds, 7200))

    seen = load_seen()
    try:
        jobs = fetch_all_jobs(since_seconds=since_seconds)
    except Exception as e:
        log(f"Scrape error: {e}")
        send_fail_alert(str(e))
        sys.exit(1)

    if os.environ.get("SEED_MODE", "").lower() == "true":
        for job in jobs:
            seen.add(_dedup_key(job))
        save_seen(seen)
        _mark_run_complete(state)
        log(f"Seed mode: marked {len(jobs)} jobs as seen.")
        return

    india_jobs = [j for j in jobs if is_india_location(j)]
    log(f"India jobs: {len(india_jobs)} / {len(jobs)}")

    matched_jobs = []
    for job in india_jobs:
        title = (job.get("title") or "").lower()
        company = (job.get("company") or "").lower()
        if BLOCKLIST.search(title) or BLOCKLIST.search(company):
            continue
        if INDIAN_TAX_BLOCKLIST.search(title) or INDIAN_TAX_BLOCKLIST.search(company):
            continue
        job = enrich_job(job)
        if is_mortgage_tax_job(job):
            matched_jobs.append(job)

    log(f"Mortgage/Tax relevant: {len(matched_jobs)}")

    new_jobs = [j for j in matched_jobs if _dedup_key(j) not in seen]
    new_jobs.sort(key=lambda j: str(j.get("posted") or j.get("fetched_at") or ""))

    if not new_jobs:
        save_seen(seen)
        save_stats(stats)
        _mark_run_complete(state)
        log("No new jobs this cycle.")
        return

    if len(new_jobs) > config.MAX_JOBS_PER_CYCLE:
        new_jobs = new_jobs[: config.MAX_JOBS_PER_CYCLE]

    sent = 0
    for job in new_jobs:
        desc = job.get("description", "")
        title = job.get("title", "")
        job["_experience"] = extract_experience(desc, title)
        job["_qualification"] = extract_qualification(desc)
        if send_job(job):
            seen.add(_dedup_key(job))
            sent += 1
            stats["sent"] += 1
            co = job.get("company", "Other")
            stats["companies"][co] = stats["companies"].get(co, 0) + 1
            log(f"  Sent: {job['title']} @ {job['company']}")

    save_seen(seen)
    save_stats(stats)
    _mark_run_complete(state)
    log(f"Done. Sent {sent} jobs. Today total: {stats['sent']}.")


if __name__ == "__main__":
    main()
