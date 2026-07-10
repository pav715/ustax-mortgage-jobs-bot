"""Creative Telegram job posts — hook first, clean labels, rotating layouts."""
import hashlib
from datetime import datetime, timedelta

IST = timedelta(hours=5, minutes=30)

BRANDS = {
    "tax": {"label": "US Tax Jobs", "icon": "💼", "spark": "🇺🇸"},
    "testing": {"label": "Tax Software QA", "icon": "🧪", "spark": "⚗️"},
    "mortgage": {"label": "Mortgage & Loan", "icon": "🏠", "spark": "🏦"},
}

TIME_SLOTS = [
    (8, 11, "morning"),
    (12, 15, "afternoon"),
    (16, 18, "late_afternoon"),
    (19, 21, "evening"),
    (22, 23, "night"),
]

HOOKS = {
    "morning": [
        "☕ *Good morning!* A new opportunity is looking for you 👀",
        "🌅 *Rise & shine!* Someone is calling you to join here 📞",
        "🥐 *Morning tea done?* This job is waiting for you ☕",
        "☀️ *New day, new role!* Don't scroll past this one 👇",
        "🌞 *Good morning hire!* Your next move starts here 🚀",
        "⏰ *Alarm went off?* So did this job posting 🔔",
        "🌄 *Fresh morning drop!* Opportunity knocking at your door 🚪",
        "💡 *Start your day right* — a role just opened up ✨",
    ],
    "afternoon": [
        "🍽️ *Lunch break over?* A new opportunity is looking for you 👀",
        "🔥 *Afternoon alert!* Someone is calling you to join here 📞",
        "⚡ *Midday magic!* This role won't wait forever ⏳",
        "🎯 *Still browsing LinkedIn?* Stop — see below 👇",
        "💼 *New opportunity alert!* Your skills are needed here 🙌",
        "🚀 *Afternoon boost!* A company wants YOU today 💪",
        "👀 *Psst...* a hot role just landed. Check it out 🔥",
        "📢 *Breaking!* Someone posted a job with your name on it 😏",
    ],
    "late_afternoon": [
        "⚡ *Evening rush hour?* A new job is also rushing in 🏃",
        "🌆 *Day not over yet!* Someone is calling you to join here 📞",
        "🔥 *Last-minute drop!* Opportunity is looking for you 👀",
        "💥 *Power hour!* Don't leave today without checking this 👇",
        "🎯 *Still at the same desk?* A new job is waiting — see below 👀",
        "⏰ *5 PM mood?* This opening says apply NOW 🚨",
        "🌇 *Golden hour hire!* Perfect role before you log off ✨",
        "📲 *Your phone is buzzing* — it's this job calling 📞",
    ],
    "evening": [
        "🌆 *Evening vibes!* A new opportunity is looking for you 👀",
        "🍿 *Netflix can wait!* Someone is calling you to join here 📞",
        "✨ *Evening special!* Still at the same company? New job below 👇",
        "🌙 *Before you unwind* — check this opening real quick 👀",
        "💫 *Plot twist!* A role just opened while you were working 😮",
        "🏠 *Heading home?* Take this opportunity with you 🎒",
        "🔔 *Evening bell!* Your next career move is here 🚀",
        "👀 *One more scroll?* This job is worth it — see below 👇",
    ],
    "night": [
        "🌙 *Night owl?* A new opportunity is looking for you 👀",
        "⭐ *Late night drop!* Someone is calling you to join here 📞",
        "🦉 *Still awake?* Good — this job is waiting for you 🌙",
        "💤 *Can't sleep?* Maybe it's this role calling you 📞",
        "🌃 *Midnight opportunity!* Apply before others wake up 😏",
        "✨ *Night shift special* — fresh opening just for you 🔥",
        "👀 *Last check before bed?* Don't miss this one 👇",
        "🚀 *While others sleep* — you could be applying 🌙",
    ],
    "default": [
        "🔥 *Fresh drop!* A new opportunity is looking for you 👀",
        "📞 *Ring ring!* Someone is calling you to join here",
        "👀 *Still at the same company?* A new job is waiting — see below 👇",
        "✨ *New role alert!* Your next chapter starts here 🚀",
        "💼 *Opportunity knocking!* Open the door below 👇",
        "🎯 *This one's for you!* Check the details below 👀",
        "⚡ *Just landed!* Don't let someone else grab it 🏃",
        "🚨 *Job alert!* Someone wants YOU on their team 🙌",
    ],
}

CTAS = [
    "👇👇 *Tap below — your future is waiting* 👇👇",
    "👉👉 *Someone is calling you — apply here* 👉👉",
    "⬇️⬇️ *New opportunity below — don't scroll past!* ⬇️⬇️",
    "👇 *Still reading? Just apply already* 😄👇",
    "🔗 *Your sign is here ↓ Click & apply*",
    "📲 *They're waiting for your application ↓*",
    "🏃 *Run don't walk — apply link below* 👇",
    "✨ *One click away from your next role ↓*",
]

COMPANY_DIVIDERS = [
    "----------------------------------------",
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "════════════════════════════════════════",
    "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓",
    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
    "────────────────────────────────────────",
    "╔════════════════════════════════════════╗",
    "╭────────────────────────────────────────╮",
    "★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★",
    "✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦",
    "◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆◆",
    "▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
]

ROLE_DIVIDERS = [
    "----------------------------------------",
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "════════════════════════════════════════",
    "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓",
    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
    "────────────────────────────────────────",
    "╚════════════════════════════════════════╝",
    "╰────────────────────────────────────────╯",
    "☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆",
    "✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧✧",
    "◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇",
    "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░",
]

COMPANY_PREFIX = ["🏢", "🔥", "⭐", "💼", "🌟", "🏆", "🔹", "✨"]
ROLE_PREFIX = ["💼", "🎯", "⭐", "🔥", "✨", "🚀", "💫", "📌"]


def _boxed(divider, middle_line):
    return [divider, middle_line, divider]


def _pick_idx(job, n, salt):
    key = f"{job.get('title', '')}|{job.get('company', '')}|{salt}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % n


def _pick_divider(job, pool, salt):
    idx = _pick_idx(job, len(pool), salt)
    return pool[idx]


def _ist_hour():
    return (datetime.utcnow() + IST).hour


def _theme_slot():
    h = _ist_hour()
    for start, end, slot in TIME_SLOTS:
        if start <= h <= end:
            return slot
    return "default"


def _pick(pool, job, salt=""):
    key = f"{job.get('title', '')}|{job.get('company', '')}|{_ist_hour()}|{salt}"
    idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(pool)
    return pool[idx]


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
    brand = BRANDS[brand_key]
    hook = _pick(HOOKS.get(_theme_slot(), HOOKS["default"]), job, "hook")
    cta = _pick(CTAS, job, "cta")
    layout = _layout_idx(job)
    co_div = _pick_divider(job, COMPANY_DIVIDERS, "co_div")
    role_div = _pick_divider(job, ROLE_DIVIDERS, "role_div")
    if co_div == role_div:
        role_div = ROLE_DIVIDERS[(_pick_idx(job, len(ROLE_DIVIDERS), "role_div") + 1) % len(ROLE_DIVIDERS)]
    co_prefix = COMPANY_PREFIX[_pick_idx(job, len(COMPANY_PREFIX), "co_pre")]
    role_prefix = ROLE_PREFIX[_pick_idx(job, len(ROLE_PREFIX), "role_pre")]

    co, ti, lo = escape(company), escape(title), escape(location)
    ex = escape(experience) if experience else ""
    ps = escape(posted_str) if posted_str else ""

    company_box = _boxed(co_div, f"{co_prefix} Company name : *{co}*")
    role_box = _boxed(role_div, f"{role_prefix} Role : *{ti}*")
    loc_line = f"📍 Location : *{lo}*"

    extras = []
    if ex:
        extras.append(f"👨‍💻 Experience : {ex}")
    if ps:
        extras.append(f"⏰ Posted : {ps}")
    if salary and salary.lower() not in ("not mentioned", ""):
        extras.append(f"💰 Salary : {escape(salary)}")
    extra_block = "\n\n".join(extras) if extras else ""

    apply = f"\n\n{cta}\n\n🔗 {url}"
    if source:
        apply += f"\n\n📋 _via {escape(source)}_"

    parts = [hook, ""]
    if layout == 1:
        parts.extend([f"{brand['icon']} {brand['spark']}", ""])
    parts.extend(company_box)
    if layout == 2:
        parts.extend(["", f"📢 *{co}* is hiring!", ""])
    else:
        parts.append("")
    parts.extend(role_box)
    parts.extend(["", loc_line])
    if extra_block:
        parts.extend(["", extra_block])
    parts.append(apply)

    return "\n".join(x for x in parts if x is not None)
