"""Professional + creative Telegram posts — company-first hooks, clean details."""
import hashlib
from datetime import datetime, timedelta

IST = timedelta(hours=5, minutes=30)

TIME_SLOTS = [
    (8, 11, "morning"),
    (12, 15, "afternoon"),
    (16, 18, "late_afternoon"),
    (19, 21, "evening"),
    (22, 23, "night"),
]

# Creative hooks — {co} = company name (bold in message)
COMPANY_HOOKS = [
    "☕ *{co}* just opened a new role for you — come see & apply 👇",
    "🔥 *{co}* is hiring — your next move could start here 🚀",
    "👀 *{co}* posted a role that might fit you — check below",
    "📢 New from *{co}* — open the details & apply 👇",
    "✨ *{co}* has a fresh opening waiting for you 👀",
    "📞 Someone at *{co}* is looking for you — see the role below",
    "🚀 *{co}* wants talent like you — role details below 👇",
    "💼 *{co}* dropped a new opportunity — worth a look 👀",
    "🎯 *{co}* is calling — new role alert below 📋",
    "⚡ Fresh role at *{co}* — scroll down & apply 👇",
    "😄 Plot twist: *{co}* might be your next company 👀",
    "🌟 *{co}* is open for a new hire — could it be you?",
    "👇 Stop scrolling — *{co}* has something for you",
    "🔔 *{co}* just listed a new opening — details below",
    "💡 *{co}* is looking for someone like you — apply below 👇",
]

TIME_HOOKS = {
    "morning": [
        "☕ Good morning! *{co}* has a new role open for you 👀",
        "🌅 Rise & shine — *{co}* is hiring today 🚀",
        "☀️ Start your day right — *{co}* posted a fresh opening",
    ],
    "afternoon": [
        "🌞 Afternoon pick — *{co}* has a new role for you 👀",
        "🍽️ Lunch break done? *{co}* is hiring — see below 👇",
        "💼 *{co}* just posted — check if this fits you",
    ],
    "late_afternoon": [
        "⚡ Before you log off — *{co}* has a new opening 👀",
        "🌆 *{co}* posted a role — quick look before 6 PM?",
        "📲 *{co}* is hiring — one opening worth checking 👇",
    ],
    "evening": [
        "🌆 Evening alert — *{co}* has a new role for you 👀",
        "🍿 Netflix can wait — *{co}* is hiring tonight 😄",
        "✨ *{co}* posted a fresh opening — see below 👇",
    ],
    "night": [
        "🌙 Night owl? *{co}* has a role open for you 👀",
        "⭐ Late drop from *{co}* — check before tomorrow 👇",
        "🦉 Still awake? *{co}* is hiring — details below",
    ],
}

CTAS = [
    "*Apply here* 👇",
    "*View & apply* 👇",
    "*Tap below to apply* 👇",
    "*Interested? Apply now* 👇",
]

LINES = [
    "────────────────────────",
    "━━━━━━━━━━━━━━━━━━━━━━━━",
]


def _ist_hour():
    return (datetime.utcnow() + IST).hour


def _theme_slot():
    h = _ist_hour()
    for start, end, slot in TIME_SLOTS:
        if start <= h <= end:
            return slot
    return "default"


def _pick_idx(job, n, salt):
    key = f"{job.get('title', '')}|{job.get('company', '')}|{_ist_hour()}|{salt}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % n


def _creative_hook(job, co):
    slot = _theme_slot()
    if slot in TIME_HOOKS and _pick_idx(job, 3, "time_mix") == 0:
        pool = TIME_HOOKS[slot]
    else:
        pool = COMPANY_HOOKS
    template = pool[_pick_idx(job, len(pool), "hook")]
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

    # Flow: creative note (with company) → company block → role → details
    if layout == 0:
        body = [
            hook, "",
            line,
            f"🏢  *{co}*",
            f"💼  *{ti}*",
            f"📍  {lo}",
        ]
        if meta_line:
            body.append(f"_{meta_line}_")
        body.extend([line, apply])

    elif layout == 1:
        body = [
            hook, "",
            f"🏢  Company : *{co}*",
            f"💼  Role       : *{ti}*",
            f"📍  Location : {lo}",
        ]
        if meta_line:
            body.append(f"_{meta_line}_")
        body.extend(["", apply])

    else:
        body = [
            hook, "",
            f"🏢  *{co}*",
            "",
            f"💼  Role : *{ti}*",
            f"📍  {lo}",
        ]
        if meta_line:
            body.append(f"_{meta_line}_")
        body.extend(["", apply])

    return "\n".join(body)
