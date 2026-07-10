"""Professional + creative Telegram posts — 100 weekly hooks, no repeats."""
import hashlib
from datetime import datetime, timedelta

IST = timedelta(hours=5, minutes=30)

# 100 hooks — 7 day pools (~14-15 each). {co} = company name.
# weekday(): 0=Mon … 6=Sun
WEEKLY_HOOKS = {
    0: [  # Monday — fresh week
        "☕ *{co}* opened a new role — start your week strong 👇",
        "🌅 Monday mood: *{co}* is hiring — see the opening below",
        "💼 New week, new chance — *{co}* has a role for you 👀",
        "🚀 *{co}* just posted — could this be your Monday win?",
        "✨ *{co}* is looking for someone like you — check below 👇",
        "👀 *{co}* dropped a fresh opening — worth a look today",
        "📋 *{co}* has a new opportunity — details below 👇",
        "🔥 *{co}* is hiring today — come see & apply 👇",
        "💡 *{co}* posted a role that might fit you — scroll down",
        "📢 Monday alert: *{co}* wants new talent — see below 👀",
        "⚡ *{co}* just listed an opening — don't miss this one 👇",
        "🎯 *{co}* is calling — new role details below 📋",
        "🌟 *{co}* has something for you this Monday 👀",
        "👇 *{co}* is open for hiring — check the role below",
        "📞 Someone at *{co}* is looking for you — apply below 👇",
    ],
    1: [  # Tuesday
        "🌞 *{co}* has a new role — Tuesday pick for you 👀",
        "💼 *{co}* is hiring — your next move could start here 🚀",
        "👀 *{co}* posted a role — see if it matches you 👇",
        "✨ Fresh from *{co}* — new opening below 👀",
        "🔥 *{co}* wants talent like you — details below 👇",
        "📋 *{co}* just opened a position — come see & apply",
        "⚡ Tuesday drop: *{co}* is hiring — check below 👀",
        "🎯 *{co}* posted a new role — scroll down & apply 👇",
        "💡 *{co}* is looking for you — role details below",
        "📢 *{co}* has a fresh opening waiting for you 👀",
        "🚀 *{co}* is expanding the team — could it be you?",
        "😄 Plot twist: *{co}* might be your next company 👇",
        "🌟 *{co}* listed a new job — worth checking today 👀",
        "👇 Stop scrolling — *{co}* has an opening for you",
        "📲 *{co}* is hiring — tap below to see the role 👇",
    ],
    2: [  # Wednesday — midweek
        "⚡ Midweek alert — *{co}* has a new role for you 👀",
        "💼 *{co}* is hiring — hump day opportunity below 👇",
        "👀 *{co}* posted something you should see — apply below",
        "✨ *{co}* has a fresh opening — midweek check 👇",
        "🔥 *{co}* wants someone like you — role below 👀",
        "📋 Wednesday pick: *{co}* is open for hiring 👇",
        "🎯 *{co}* just dropped a new role — see details below",
        "💡 *{co}* is calling — new opportunity below 👀",
        "📢 *{co}* posted a role — come see & apply 👇",
        "🚀 *{co}* has an opening — your skills might fit 👀",
        "🌟 *{co}* is hiring today — check the role below 👇",
        "👇 *{co}* listed a new job — details below 👀",
        "📞 Someone at *{co}* needs you — see the role below",
        "⚡ *{co}* fresh opening — apply before the week ends 👇",
    ],
    3: [  # Thursday
        "🌆 *{co}* has a new role — Thursday opportunity 👀",
        "💼 *{co}* is hiring — one opening worth your time 👇",
        "👀 *{co}* just posted — check if this fits you",
        "✨ *{co}* opened a position — see below & apply 👇",
        "🔥 *{co}* wants new talent — role details below 👀",
        "📋 *{co}* has something for you — scroll down 👇",
        "🎯 Thursday alert: *{co}* is hiring today 👀",
        "💡 *{co}* posted a fresh role — come see below 👇",
        "📢 *{co}* is looking for you — apply below 👀",
        "🚀 *{co}* dropped a new opening — don't skip this 👇",
        "🌟 *{co}* listed a job — could this be yours? 👀",
        "👇 *{co}* is open — new role waiting below",
        "📲 *{co}* is hiring — details below 👇",
        "⚡ *{co}* has a role for you — see & apply below 👀",
    ],
    4: [  # Friday
        "🎉 *{co}* has a new role — end the week on a high 👇",
        "💼 Friday pick: *{co}* is hiring — see below 👀",
        "👀 *{co}* posted before the weekend — check it out 👇",
        "✨ *{co}* wants talent like you — apply below 👀",
        "🔥 *{co}* just opened a role — Friday opportunity 👇",
        "📋 *{co}* is hiring — one last look before the weekend 👀",
        "🎯 *{co}* has a fresh opening — see details below 👇",
        "💡 *{co}* is calling — new role alert below 👀",
        "📢 *{co}* posted a job — come see & apply 👇",
        "🚀 *{co}* is expanding — could you be the one? 👀",
        "🌟 *{co}* listed an opening — worth a Friday check 👇",
        "👇 *{co}* has something for you — role below 👀",
        "📞 Someone at *{co}* is hiring — apply below 👇",
        "⚡ Friday drop from *{co}* — new role below 👀",
        "😄 Weekend plans? First check *{co}* — they're hiring 👇",
    ],
    5: [  # Saturday
        "🌞 *{co}* has a new role — weekend opportunity 👀",
        "💼 *{co}* is hiring — Saturday opening below 👇",
        "👀 *{co}* posted a role — check when you get time",
        "✨ *{co}* wants someone like you — see below 👇",
        "🔥 *{co}* fresh drop — new job details below 👀",
        "📋 *{co}* is open for hiring — role below 👇",
        "🎯 *{co}* listed a new opening — apply below 👀",
        "💡 *{co}* is looking for talent — check the role 👇",
        "📢 Saturday alert: *{co}* posted a new job 👀",
        "🚀 *{co}* has an opportunity — see details below 👇",
        "🌟 *{co}* is hiring — weekend check worth it 👀",
        "👇 *{co}* dropped a role — scroll down & apply 👇",
        "📲 *{co}* wants you — new opening below 👀",
        "⚡ *{co}* just posted — apply before Monday rush 👇",
    ],
    6: [  # Sunday
        "🌙 *{co}* has a new role — Sunday evening check 👀",
        "💼 *{co}* is hiring — get ahead before Monday 👇",
        "👀 *{co}* posted a role — prep for the new week 👇",
        "✨ *{co}* has a fresh opening — see below 👀",
        "🔥 *{co}* wants talent — role details below 👇",
        "📋 Sunday pick: *{co}* is open for hiring 👀",
        "🎯 *{co}* listed a new job — check before tomorrow 👇",
        "💡 *{co}* is calling — opportunity below 👀",
        "📢 *{co}* posted — one opening worth reviewing 👇",
        "🚀 *{co}* has something for you — apply below 👀",
        "🌟 *{co}* is hiring — Sunday scroll stop 👇",
        "👇 *{co}* new role — see & apply below 👀",
        "📞 *{co}* is looking for you — details below 👇",
    ],
}

CTAS = [
    "*Apply here* 👇",
    "*View & apply* 👇",
    "*Tap below to apply* 👇",
    "*Interested? Apply now* 👇",
    "*See full details & apply* 👇",
    "*Click below to apply* 👇",
]

LINES = [
    "────────────────────────",
    "━━━━━━━━━━━━━━━━━━━━━━━━",
]


def _ist_now():
    return datetime.utcnow() + IST


def _pick_idx(job, n, salt):
    key = f"{job.get('title', '')}|{job.get('company', '')}|{salt}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % n


def _creative_hook(job, co):
    now = _ist_now()
    weekday = now.weekday()
    week_num = now.isocalendar()[1]
    hour = now.hour
    pool = WEEKLY_HOOKS[weekday]
    # Week + day + hour rotates pool; job hash picks unique line per post
    salt = f"hook_w{week_num}_d{weekday}_h{hour}"
    idx = _pick_idx(job, len(pool), salt)
    return pool[idx].format(co=co)


def _layout_idx(job):
    now = _ist_now()
    salt = f"layout_w{now.isocalendar()[1]}_d{now.weekday()}"
    return _pick_idx(job, 3, salt)


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
    cta = CTAS[_pick_idx(job, len(CTAS), f"cta_w{_ist_now().isocalendar()[1]}")]
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
