"""Shared experience parsing — LinkedIn criteria first, then JD text."""
import re


def _parse_linkedin_experience(raw):
    if not raw or not str(raw).strip():
        return ""
    text = str(raw).strip()
    m = re.search(
        r"(\d+\s*\+?\s*(?:to|\-|–)\s*\d+\s*\+?\s*(?:years?|yrs?)|"
        r"\d+\s*\+?\s*(?:years?|yrs?)(?:\s+of\s+(?:experience|exp))?)",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    if re.search(r"year|experience|yrs|entry|mid|senior|associate|director|intern", text, re.I):
        return text[:120]
    return ""


def extract_experience_from_job(desc, raw_exp=""):
    """Return experience from LinkedIn header or job description — no title guessing."""
    linkedin = _parse_linkedin_experience(raw_exp)
    if linkedin:
        return linkedin

    desc = desc or ""
    patterns = [
        r"((?:minimum|min\.?|at\s*least|atleast)\s*\d+\+?\s*(?:to|\-|–)\s*\d*\+?\s*(?:years?|yrs?)[^\n.]*)",
        r"(\d+\+?\s*(?:to|\-|–)\s*\d+\+?\s*(?:years?|yrs?)(?:\s+of\s+(?:experience|exp))?[^\n.]*)",
        r"(\d+\+?\s*(?:years?|yrs?)\s*(?:of\s*(?:relevant\s*)?(?:experience|exp))[^\n.]*)",
        r"(\d+\s*\+\s*(?:years?|yrs?)[^\n.]*)",
    ]
    for p in patterns:
        m = re.search(p, desc, re.IGNORECASE)
        if m:
            return m.group(1).strip()[:120]
    return ""


def pick_linkedin_criteria_experience(criteria_spans):
    """Pick best experience line from LinkedIn job criteria spans."""
    candidates = []
    for c in criteria_spans:
        text = c.get_text(strip=True)
        if re.search(r"year|experience|yrs|senior|entry|associate|director|intern", text, re.I):
            candidates.append(text)
    if not candidates:
        return ""
    return max(candidates, key=lambda t: (bool(re.search(r"\d", t)), len(t)))
