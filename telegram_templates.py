"""Professional Telegram posts — B.Tech-style layout with creative hook first."""
import hashlib
from datetime import datetime, timedelta
from hooks_100 import HOOKS_100

IST = timedelta(hours=5, minutes=30)

CTAS = [
    "🔗 *Apply here* 👇",
    "🔗 *View & apply* 👇",
    "🔗 *Tap below to apply* 👇",
    "🔗 *Interested? Apply now* 👇",
    "🔗 *See details & apply* 👇",
]

# Rotating creative divider — between hook and company (unique per job/day)
DIVIDERS = [
    "✦ ─── ✦ ─── ✦",
    "⋆｡°✩ *OPENING* ✩°｡⋆",
    "━ ━ ✨ *HOT ROLE* ✨ ━ ━",
    "· · · ✦ · · ·",
    "⭐ ━━━ ⭐ ━━━ ⭐",
    "～～～ ✦ ～～～",
    "─── ✨ *NEW OPPORTUNITY* ✨ ───",
    "◆ ─ ◆ ─ ◆ ─ ◆",
    "✨ · · ✨ · · ✨",
    "══════ 🔥 ══════",
    "·✦·✦·✦·✦·✦·",
    "── ✨ *NOW HIRING* ✨ ──",
    "⋆ ⋆ ⋆ ⋆ ⋆ ⋆ ⋆",
    "╭── ✦ ──╮",
    "✧ *details below* ✧",
    "▰▱▰▱▰▱▰▱▰▱▰▱",
    "✦ ✧ ✦ ✧ ✦ ✧ ✦",
    "— — ✦ — — ✦ — —",
    "✨ ━━━ *FRESH POST* ━━━ ✨",
    "◈ ◈ ◈ ◈ ◈",
    "·:*✧ OPEN ROLE ✧*:·",
    "╌╌╌ ✦ ╌╌╌",
    "★ · ★ · ★ · ★",
    "─── 🔥 *DON'T MISS* 🔥 ───",
    "✧･ﾟ: *✧･ﾟ:* ✧･ﾟ: *✧･ﾟ:*",
    "▬▬▬ ✦ ▬▬▬",
    "· · ✨ · · ✨ · ·",
    "◆━━◆━━◆━━◆",
    "✦ rolling in ✦",
    "── ⭐ *YOUR MOVE* ⭐ ──",
    "⋆｡°✩ grab it ✩°｡⋆",
    "✨ ═══ ✨ ═══ ✨",
    "·✧·✧·✧·✧·",
    "━━ 🔥 *LIVE NOW* 🔥 ━━",
    "✦ · ✦ · ✦ · ✦",
    "╭ ✨ ╮",
    "◈ ── ◈ ── ◈",
    "★ ━━━ ★ ━━━ ★",
    "· · · 🔥 · · ·",
]


def _ist_now():
    return datetime.utcnow() + IST


def _today():
    return _ist_now().strftime("%Y-%m-%d")


def _pick_idx(job, n, salt):
    key = f"{_today()}|{job.get('title', '')}|{job.get('company', '')}|{_ist_now().hour}|{salt}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % n


def _creative_hook(job, co):
    template = HOOKS_100[_pick_idx(job, len(HOOKS_100), "hook")]
    return template.format(co=co)


def _creative_divider(job):
    return DIVIDERS[_pick_idx(job, len(DIVIDERS), "divider")]


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
    co = escape(company)
    ti = escape(title)
    lo = escape(location)
    ex = escape(experience) if experience else "See job description"
    ps = escape(posted_str) if posted_str else "Recently posted"

    hook = _creative_hook(job, co)
    divider = _creative_divider(job)
    cta = CTAS[_pick_idx(job, len(CTAS), "cta")]

    lines = [
        hook,
        "",
        divider,
        "",
        f"🏢 *_Company:_* 🔥 *{co}* 🔥",
        "",
        f"💼 *_Role:_* *{ti}*",
        "",
        f"📍 *_Location:_* *{lo}*",
        "",
        f"🎯 *_Experience:_* *{ex}*",
        "",
        f"⏰ *_Posted:_* *{ps}*",
    ]

    if salary and salary.lower() not in ("not mentioned", "", "n/a"):
        lines += ["", f"💰 *_Salary:_* *{escape(salary)}*"]

    lines += [
        "",
        cta,
        url,
    ]

    if source:
        lines += ["", f"📋 _{escape(source)}_"]

    return "\n".join(lines)
