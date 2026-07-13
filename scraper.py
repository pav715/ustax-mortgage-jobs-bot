"""Multi-source job scraper — LinkedIn, Naukri, Indeed."""
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
}

PORTAL_KEYWORD_LIMIT = 12


def _job_id(url, title, company):
    raw = f"{url}{title}{company}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _delay():
    time.sleep(random.uniform(0.6, 1.2))


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


def scrape_naukri(keyword, location):
    jobs = []
    try:
        kw = quote(keyword)
        loc = quote(location)
        url = (
            f"https://www.naukri.com/jobapi/v3/search?"
            f"noOfResults=20&urlType=search_by_keyword&searchType=adv"
            f"&keyword={kw}&location={loc}&jobAge=3&src=jobsearchDesk&latLong="
        )
        r = requests.get(url, headers=NAUKRI_HEADERS, timeout=12)
        if r.status_code != 200:
            print(f"  [Naukri] HTTP {r.status_code} — '{keyword}' / {location}")
            return jobs
        for j in r.json().get("jobDetails", []):
            title = (j.get("title") or "").strip()
            company = (j.get("companyName") or "").strip()
            jurl = j.get("jdURL", "")
            if jurl and not jurl.startswith("http"):
                jurl = f"https://www.naukri.com{jurl}"
            posted = j.get("footerPlaceholderLabel", "") or j.get("createdDate", "")
            desc_parts = [
                j.get("jobDesc", ""),
                j.get("jobHighlight", ""),
                " ".join(j.get("tagsAndHighlights", {}).get("highlights", [])),
                j.get("experienceText", ""),
            ]
            desc = " ".join(str(p) for p in desc_parts if p)
            exp = (j.get("experienceText") or "").strip()
            loc_str = (j.get("placeholders") or [{}])[0].get("label", location) if j.get("placeholders") else location
            if title and jurl:
                job = _make_job(title, company, loc_str or location, jurl, posted, "Naukri", desc)
                if exp:
                    job["experience"] = exp
                jobs.append(job)
    except Exception as e:
        print(f"  [Naukri] Error ({keyword}/{location}): {e}")
    print(f"  [Naukri] '{keyword}' / {location} — {len(jobs)} jobs")
    return jobs


def scrape_indeed(keyword, location):
    jobs = []
    try:
        kw = quote(keyword.replace(" ", "+"))
        loc = quote(location.replace(" ", "+"))
        url = f"https://in.indeed.com/rss?q={kw}&l={loc}&sort=date&fromage=3"
        r = requests.get(url, headers={"User-Agent": SESSION.headers["User-Agent"]}, timeout=12)
        if r.status_code != 200:
            print(f"  [Indeed] HTTP {r.status_code} — '{keyword}' / {location}")
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
    print(f"\n[Naukri] Scanning top {len(portal_kws)} keywords...")
    for kw in portal_kws:
        for loc in config.LOCATIONS[:6]:
            _add(scrape_naukri(kw, loc))
            _delay()

    print(f"\n[Indeed] Scanning top {len(portal_kws)} keywords...")
    for kw in portal_kws:
        for loc in config.LOCATIONS[:6]:
            _add(scrape_indeed(kw, loc))
            _delay()

    all_jobs.sort(key=lambda j: j.get("posted") or j.get("fetched_at") or "", reverse=True)
    print(f"\n  Total unique jobs (LinkedIn + Naukri + Indeed): {len(all_jobs)}")
    return all_jobs
