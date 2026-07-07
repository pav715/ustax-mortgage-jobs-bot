"""Telegram sender — US Tax Mortgage Jobs channel."""
import requests
import re
import time
from datetime import datetime, date, timedelta
import config

API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"


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


def format_job(job):
    title = job.get("title", "")
    company = job.get("company", "")
    loc = job.get("location", "India / Remote")
    url = job.get("url", "")
    posted = job.get("posted", "")

    qual = job.get("_qualification", "Graduate / MBA Finance (preferred)")
    exp = job.get("_experience", "2-5 Years (US Tax Mortgage)")

    if "remote" in loc.lower():
        loc_str = f"{loc} (Remote)"
    elif "hyderabad" in loc.lower():
        loc_str = "Hyderabad (Hybrid)"
    else:
        loc_str = loc

    lines = []
    urgency = _urgency_tag(posted)
    if urgency:
        lines.append(urgency.strip())
        lines.append("")

    lines += [
        f"🏠 *Job Opportunity at {_escape(company)}*",
        "",
        f"💼 *Role:* {_escape(title)}",
        f"📍 *Location:* {_escape(loc_str)}",
    ]
    if exp:
        lines.append(f"👨‍💻 *Experience:* {_escape(exp)}")

    posted_str = _format_posted(posted, job.get("fetched_at", ""))
    if posted_str:
        lines.append(f"⏰ *Posted:* {_escape(posted_str)}")

    lines += ["", f"🔗 *Apply Here:*\n{url}"]
    if job.get("source"):
        lines.append(f"\n📋 _{_escape(job['source'])}_")

    return "\n".join(lines)


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
