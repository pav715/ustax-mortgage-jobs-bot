"""Professional + creative Telegram posts — 100 rotating daily hooks."""
import hashlib
from datetime import datetime, timedelta
from hooks_100 import HOOKS_100

IST = timedelta(hours=5, minutes=30)

CTAS = [
    "*Apply here* 👇",
    "*View & apply* 👇",
    "*Tap below to apply* 👇",
    "*Interested? Apply now* 👇",
    "*See details & apply* 👇",
    "*Click below to apply* 👇",
]

LINES = [
    "────────────────────────",
    "━━━━━━━━━━━━━━━━━━━━━━━━",
]


def _ist_now():
    return datetime.utcnow() + IST


def _today():
    return _ist_now().strftime("%Y-%m-%d")


def _pick_idx(job, n, salt):
    # Date in key → different hook each day, less repeat
    key = f"{_today()}|{job.get('title', '')}|{job.get('company', '')}|{_ist_now().hour}|{salt}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % n


def _creative_hook(job, co):
    template = HOOKS_100[_pick_idx(job, len(HOOKS_100), "hook")]
    return template.format(co=co)


def _layout_idx(job):
    return _pick_idx(job, 3, "layout")


def render_job_post(
    brand_key,
    job,
    escape,
    company,
    title,
    location,
    experience,
    qualification,
    posted_str,
    url,
    source="",
    posted_today=False,
    salary="",
):
    co, ti, lo = escape(company), escape(title), escape(location)
    ex = escape(experience) if experience else ""
    ps = escape(posted_str) if posted_str else ""

    hook = _creative_hook(job, co)
    cta = CTAS[_pick_idx(job, len(CTAS), "cta")]
    layout = _layout_idx(job)
    line = LINES[layout % len(LINES)]

    meta = []
    if ex:
        meta.append(f"Experience : {ex}")
    if ps:
        meta.append(f"Posted : {ps}")
    if salary and salary.lower() not in ("not mentioned", ""):
        meta.append(f"Salary : {escape(salary)}")
    meta_line = "  ·  ".join(meta) if meta else ""

    apply = f"\n{cta}\n{url}"
    if source:
        apply += f"\n\n_via {escape(source)}_"

    details = [
        f"Company : *{co}*",
        f"Role       : *{ti}*",
        f"Location : {lo}",
    ]
    if meta_line:
        details.append(f"_{meta_line}_")

    if layout == 0:
        body = [hook, "", line] + details + [line, apply]
    elif layout == 1:
        body = [hook, ""] + details + ["", apply]
    else:
        body = [hook, "", line] + details + ["", apply]

    return "\n".join(body)
