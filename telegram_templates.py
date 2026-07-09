"""Creative Telegram job posts — time-of-day hooks, funny openers, rotating layouts."""
import hashlib
from datetime import datetime, timedelta

IST = timedelta(hours=5, minutes=30)

BRANDS = {
    "tax": {"label": "US Tax Jobs", "icon": "💼", "spark": "🇺🇸", "tag": "tax"},
    "testing": {"label": "Tax Software QA", "icon": "🧪", "spark": "⚗️", "tag": "QA"},
    "mortgage": {"label": "Mortgage & Loan", "icon": "🏠", "spark": "🏦", "tag": "loan"},
}

TIME_SLOTS = [
    (8, 11, "morning", "╭━━ 🌞 MORNING DROP 🌞 ━━╮"),
    (12, 15, "afternoon", "▰▰▰ 🔥 HOT JOB 🔥 ▰▰▰"),
    (16, 18, "late_afternoon", "━━ ⚡ FRESH OPENING ⚡ ━━"),
    (19, 21, "evening", "✦ ─── ✦ ─── ✦ ─── ✦"),
    (22, 23, "night", "◇ ─── ◇ ─── ◇ ─── ◇"),
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


def _ist_hour():
    return (datetime.utcnow() + IST).hour


def _theme():
    h = _ist_hour()
    for start, end, slot, divider in TIME_SLOTS:
        if start <= h <= end:
            return {"slot": slot, "divider": divider}
    return {"slot": "default", "divider": "━━━━━━━━━━━━━━━━━━━━"}


def _pick(pool, job, salt=""):
    key = f"{job.get('title', '')}|{job.get('company', '')}|{_ist_hour()}|{salt}"
    idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(pool)
    return pool[idx]


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
    theme = _theme()
    slot = theme["slot"]
    hooks = HOOKS.get(slot, HOOKS["default"])
    hook = _pick(hooks, job, "hook")
    cta = _pick(CTAS, job, "cta")
    layout = int(hashlib.md5(
        f"{job.get('title', '')}|{job.get('company', '')}|layout".encode()
    ).hexdigest(), 16) % 6

    co, ti, lo = escape(company), escape(title), escape(location)
    ex = escape(experience) if experience else ""
    qu = escape(qualification) if qualification else ""
    ps = escape(posted_str) if posted_str else ""

    extras = []
    if ex:
        extras.append(f"👨‍💻 *Experience:* {ex}")
    if qu:
        extras.append(f"🎓 *Qualification:* {qu}")
    if ps:
        extras.append(f"⏰ *Posted:* {ps}")
    if salary and salary.lower() not in ("not mentioned", ""):
        extras.append(f"💰 *Salary:* {escape(salary)}")
    extra = "\n".join(extras)

    urgent = "🚨 *Posted TODAY — apply fast!* 🚨" if posted_today else ""
    company_block = f"🔥🔥 *{co}* 🔥🔥"
    role = f"💼 *Role:*\n*{ti}*"
    loc = f"📍 *Location:*\n*{lo}*"
    apply = f"\n{cta}\n\n🔗 {url}"
    if source:
        apply += f"\n\n📋 _via {escape(source)}_"

    if layout == 0:
        body = [hook, urgent, "", company_block, theme["divider"], role, loc, extra, apply]
    elif layout == 1:
        body = [hook, urgent, f"{brand['icon']} {brand['spark']}", company_block, role.replace("💼", "🎯"), loc, extra, apply]
    elif layout == 2:
        body = [hook, urgent, theme["divider"], company_block, f"▸ *Role* → *{ti}*", f"▸ *Location* → *{lo}*", extra, apply]
    elif layout == 3:
        body = [hook, urgent, f"🏢 *{co}* {brand['spark']}🔥", "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈", f"💼 *{ti}*", f"📍 *{lo}*", extra, apply]
    elif layout == 4:
        body = [hook, urgent, f"📢 *{co}* wants someone like you!", theme["divider"], role, loc, extra, apply]
    else:
        body = [hook, urgent, company_block, theme["divider"], role, loc, extra, apply]

    return "\n".join(x for x in body if x)
