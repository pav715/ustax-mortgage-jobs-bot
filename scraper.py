"""Multi-source job scraper — LinkedIn, Naukri (v2), Indeed."""
import hashlib
import re
import time
import random
from datetime import datetime
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import config

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
})

NAUKRI_HEADERS = {
    "User-Agent": SESSION.headers["User-Agent"],
    "appid": "109",
    "systemid": "109",
    "Accept": "application/json",
}

PORTAL_KEYWORD_LIMIT = getattr(config, "PORTAL_KEYWORD_LIMIT", 12)
PORTAL_LOCATION_LIMIT = 6
NAUKRI_JOBS_PER_SEARCH = 8
_INDEED_BLOCKED = False


def _job_id(url, title, company):
    raw = f"{url}{title}{company}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _delay():
    time.sleep(random.uniform(0.6, 1.2))


def _strip_html(text):
    if not text:
        return ""
    return BeautifulSoup(str(text), "html.parser").get_text(" ", strip=True)


def _make_job(title, company, location, url, posted="", source="LinkedIn", description=""):
    return {
        "id": _job_id(url, title, company),
        "title": title,
        "company": company,
        "location": location,
        "url": url,
        "posted": posted,
        "experience": "",
        "skills": "",
        "description": description or "",
        "source": source,
        "fetched_at": datetime.now().isoformat(),
    }


def scrape_linkedin(keyword, location, since_seconds=86400):
    jobs = []
    try:
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
            f"keywords={quote(keyword)}&location={quote(location)}"
            f"&f_TPR=r{since_seconds}&sortBy=DD&start=0"
        )
        for attempt in range(3):
            r = SESSION.get(url, timeout=8)
            if r.status_code == 200:
                break
            if r.status_code in (429, 503) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            print(f"  [LinkedIn] HTTP {r.status_code} — '{keyword}' / {location}")
            return jobs

        soup = BeautifulSoup(r.content, "html.parser")
        for card in soup.find_all("li")[:15]:
            try:
                h3 = card.find("h3")
                h4 = card.find("h4")
                loc_tag = card.find("span", class_=re.compile("job-search-card__location"))
                a_tag = card.find("a", href=True)
                t_tag = card.find("time")
                title = h3.get_text(strip=True) if h3 else ""
                company = h4.get_text(strip=True) if h4 else ""
                loc_str = loc_tag.get_text(strip=True) if loc_tag else location
                link = a_tag["href"].split("?")[0] if a_tag else ""
                posted = t_tag.get("datetime", "") if t_tag else ""
                if title and link:
                    jobs.append(_make_job(title, company, loc_str, link, posted, "LinkedIn"))
            except Exception:
                pass
    except Exception as e:
        print(f"  [LinkedIn] Error: {e}")
    print(f"  [LinkedIn] '{keyword}' / {location} — {len(jobs)} jobs")
    return jobs


def _naukri_fetch_job(job_id):
    """Fetch single job via Naukri v2 API (v3 blocked by recaptcha)."""
    try:
        r = requests.get(
            f"https://www.naukri.com/jobapi/v2/job/{job_id}",
            headers=NAUKRI_HEADERS,
            timeout=12,
        )
        if r.status_code != 200:
            return None
        j = r.json().get("job") or {}
        title = (j.get("post") or "").strip()
        company = (j.get("companyName") or j.get("CONTCOM") or "").strip()
        path = (j.get("job_static_url") or "").strip()
        if not title or not path:
            return None
        jurl = path if path.startswith("http") else f"https://www.naukri.com{path}"
        desc = _strip_html(j.get("jobDesc", ""))
        loc_str = _strip_html(j.get("cityfield", "")) or ""
        if loc_str:
            loc_str = re.sub(r"\s+", " ", loc_str).strip()[:120]
        min_exp = j.get("minExp")
        max_exp = j.get("maxExp")
        exp = ""
        if min_exp is not None and max_exp is not None:
            exp = f"{min_exp}-{max_exp} Years"
        elif min_exp is not None:
            exp = f"{min_exp}+ Years"
        job = _make_job(title, company, loc_str or "", jurl, "", "Naukri", desc)
        if exp:
            job["experience"] = exp
        return job
    except Exception:
        return None


def scrape_naukri(keyword, location):
    """Naukri v2: search for IDs, then fetch each job (v3 API requires recaptcha)."""
    jobs = []
    try:
        url = (
            f"https://www.naukri.com/jobapi/v2/search?"
            f"noOfResults=20&urlType=search_by_keyword&searchType=adv"
            f"&keyword={quote(keyword)}&location={quote(location)}"
            f"&jobAge=7&src=jobsearchDesk&latLong="
        )
        r = requests.get(url, headers=NAUKRI_HEADERS, timeout=12)
        if r.status_code != 200:
            print(f"  [Naukri] HTTP {r.status_code} — '{keyword}' / {location}")
            return jobs
        job_ids = (r.json().get("srpJobIds") or [])[:NAUKRI_JOBS_PER_SEARCH]
        for jid in job_ids:
            job = _naukri_fetch_job(jid)
            if job:
                if not job.get("location"):
                    job["location"] = location
                jobs.append(job)
            time.sleep(0.3)
    except Exception as e:
        print(f"  [Naukri] Error ({keyword}/{location}): {e}")
    print(f"  [Naukri] '{keyword}' / {location} — {len(jobs)} jobs")
    return jobs


def scrape_indeed(keyword, location):
    global _INDEED_BLOCKED
    if _INDEED_BLOCKED:
        return []
    jobs = []
    try:
        kw = quote(keyword.replace(" ", "+"))
        loc = quote(location.replace(" ", "+"))
        url = f"https://in.indeed.com/rss?q={kw}&l={loc}&sort=date&fromage=7"
        r = requests.get(
            url,
            headers={
                "User-Agent": SESSION.headers["User-Agent"],
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
            timeout=12,
        )
        if r.status_code != 200 or "<rss" not in r.text[:500].lower():
            print(f"  [Indeed] HTTP {r.status_code} (blocked) — '{keyword}' / {location}")
            if r.status_code in (403, 429):
                _INDEED_BLOCKED = True
                print("  [Indeed] Skipping remaining Indeed calls this cycle (bot block).")
            return jobs
        soup = BeautifulSoup(r.content, "xml")
        for item in soup.find_all("item")[:15]:
            title = item.find("title").get_text(strip=True) if item.find("title") else ""
            link = item.find("link").get_text(strip=True) if item.find("link") else ""
            company_tag = item.find("source")
            company = company_tag.get_text(strip=True) if company_tag else "Unknown"
            pub = item.find("pubDate")
            posted = pub.get_text(strip=True) if pub else ""
            desc_tag = item.find("description")
            desc = desc_tag.get_text(separator=" ", strip=True) if desc_tag else ""
            if title and link:
                jobs.append(_make_job(title, company, location, link, posted, "Indeed", desc))
    except Exception as e:
        print(f"  [Indeed] Error ({keyword}/{location}): {e}")
    print(f"  [Indeed] '{keyword}' / {location} — {len(jobs)} jobs")
    return jobs


def _portal_keywords():
    return getattr(config, "KEYWORDS", [])[:PORTAL_KEYWORD_LIMIT]


def fetch_all_jobs(since_seconds=86400):
    global _INDEED_BLOCKED
    _INDEED_BLOCKED = False
    all_jobs = []
    seen = set()

    def _add(job_list):
        for job in job_list:
            key = job.get("url") or job.get("id")
            if key and key not in seen:
                seen.add(key)
                all_jobs.append(job)

    print(f"\n[LinkedIn] Scanning (last {since_seconds // 3600}h)...")
    for kw in config.KEYWORDS:
        for loc in config.LOCATIONS:
            _add(scrape_linkedin(kw, loc, since_seconds))
            _delay()

    portal_kws = _portal_keywords()
    portal_locs = config.LOCATIONS[:PORTAL_LOCATION_LIMIT]

    print(f"\n[Naukri] Scanning top {len(portal_kws)} keywords (v2 API)...")
    for kw in portal_kws:
        for loc in portal_locs:
            _add(scrape_naukri(kw, loc))
            _delay()

    print(f"\n[Indeed] Scanning top {len(portal_kws)} keywords...")
    for kw in portal_kws:
        for loc in portal_locs:
            _add(scrape_indeed(kw, loc))
            if _INDEED_BLOCKED:
                break
            _delay()
        if _INDEED_BLOCKED:
            break

    all_jobs.sort(key=lambda j: j.get("posted") or j.get("fetched_at") or "", reverse=True)
    print(f"\n  Total unique jobs: {len(all_jobs)}")
    return all_jobs
