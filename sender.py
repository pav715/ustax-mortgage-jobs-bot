"""Telegram sender — US Tax Mortgage Jobs channel."""
import requests
import re
import time
from datetime import datetime, date, timedelta
import config
from telegram_templates import render_job_post

API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"
BRAND = "mortgage"


def _escape(text):
    if not text:
        return ""
    for ch in ["_", "*", "`", "["]:
        text = text.replace(ch, f"\\{ch}")
    return text


def _post(text, chat_id=None, retry=2):
    cid = str(chat_id or config.CHAT_ID)
    if not cid or cid == "None" or not config.BOT_TOKEN:
        return False
    try:
        for attempt in range(retry):
            r = requests.post(
                f"{API}/sendMessage",
                json={"chat_id": cid, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False},
                timeout=15,
            )
            if r.status_code == 200:
                return True
            if attempt < retry - 1:
                time.sleep(1)
        r2 = requests.post(
            f"{API}/sendMessage",
            json={"chat_id": cid, "text": re.sub(r"[*_`\[\]]", "", text), "disable_web_page_preview": False},
            timeout=15,
        )
        return r2.status_code == 200
    except Exception as e:
        print(f"[Telegram] Send error: {e}")
        return False


def _format_posted(posted, fetched_at=""):
    IST_OFFSET = timedelta(hours=5, minutes=30)
    p = str(posted or "").strip()
    if p and re.match(r"\d{4}-\d{2}-\d{2}", p):
        try:
            dt = datetime.fromisoformat(p[:19])
            if len(p) >= 16:
                return (dt + IST_OFFSET).strftime("%d %b %Y, %I:%M %p IST")
            return dt.strftime("%d %b %Y")
        except Exception:
            pass
    if p:
        return p
    if fetched_at:
        try:
            dt = datetime.fromisoformat(str(fetched_at)[:19])
            return f"Found at {(dt + IST_OFFSET).strftime('%d %b %Y, %I:%M %p IST')}"
        except Exception:
            pass
    return ""


def _urgency_tag(posted):
    if not posted:
        return ""
    try:
        if (date.today() - date.fromisoformat(str(posted)[:10])).days == 0:
            return "🔴 *Posted Today!*\n"
    except Exception:
        pass
    return ""


def _format_location(loc):
    loc = (loc or "India").strip()
    ll = loc.lower()
    if "remote" in ll and "(remote)" not in ll and "· remote" not in ll:
        return loc
    if "hyderabad" in ll and "hybrid" not in ll and "· hybrid" not in ll:
        return f"{loc} · Hybrid"
    return loc


def _experience_display(job):
    exp = (job.get("_experience") or job.get("experience") or "").strip()
    if exp and exp.lower() not in ("not mentioned", "n/a", ""):
        return exp
    return "See job description ↓"


def _posted_today(posted):
    if not posted:
        return False
    try:
        return (date.today() - date.fromisoformat(str(posted)[:10])).days == 0
    except Exception:
        return False


def format_job(job):
    title = job.get("title", "")
    company = job.get("company", "")
    loc = job.get("location", "India / Remote")
    url = job.get("url", "")
    posted = job.get("posted", "")

    qual = job.get("_qualification", "")
    exp = _experience_display(job)
    loc_str = _format_location(loc)
    posted_str = _format_posted(posted, job.get("fetched_at", ""))

    return render_job_post(
        BRAND,
        job,
        _escape,
        company,
        title,
        loc_str,
        exp,
        qual if qual and qual.lower() not in ("not mentioned", "") else "",
        posted_str,
        url,
        source=job.get("source", ""),
        posted_today=_posted_today(posted),
    )


def send_job(job):
    ok = _post(format_job(job))
    if ok:
        time.sleep(2)
    return ok


def send_fail_alert(error_msg=""):
    msg = (
        "❌ *US Tax Mortgage Jobs Bot — Error*\n\n"
        f"`{_escape(str(error_msg)[:200])}`\n\n"
        f"🕐 {datetime.now().strftime('%d %b %Y %H:%M')}"
    )
    _post(msg)
