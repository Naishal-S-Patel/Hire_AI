import re
from datetime import datetime
import fitz  # PyMuPDF

CURRENT_YEAR = 2026
CURRENT_MONTH = 3

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

skills_db = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "php", "ruby", "swift", "kotlin", "scala", "matlab", "perl",
    "react", "reactjs", "angular", "vue", "vuejs", "node.js", "nodejs", "express",
    "django", "flask", "fastapi", "spring", "spring boot", "springboot",
    "asp.net", ".net", "laravel", "rails", "ruby on rails",
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "sklearn", "numpy", "pandas", "scipy", "matplotlib",
    "data science", "data analysis", "nlp", "computer vision", "opencv",
    "neural networks", "artificial intelligence",
    "sql", "postgresql", "postgres", "mysql", "mongodb", "redis", "cassandra",
    "oracle", "sql server", "dynamodb", "elasticsearch", "neo4j",
    "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "google cloud",
    "jenkins", "ci/cd", "terraform", "ansible", "heroku",
    "github actions", "gitlab ci", "circleci",
    "rest api", "restful", "graphql", "microservices", "soap", "grpc",
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "html", "html5", "css", "css3", "sass", "tailwind", "bootstrap", "jquery",
    "webpack", "babel",
    "junit", "pytest", "jest", "mocha", "selenium", "cypress",
    "linux", "unix", "bash", "shell scripting", "agile", "scrum", "kanban",
    "android", "ios", "flutter", "react native", "kotlin", "swift",
    "firebase", "supabase", "vercel", "netlify",
]

locations_db = [
    "ahmedabad", "surat", "mumbai", "delhi", "bangalore", "bengaluru",
    "pune", "hyderabad", "chennai", "kolkata", "jaipur", "lucknow",
    "new york", "san francisco", "london", "singapore", "dubai",
    "toronto", "sydney", "berlin", "paris", "tokyo",
]

# ── Date parsing helpers ──────────────────────────────────────────────────────

# Matches: "Nov 2020", "November 2020", "11/2020", "2020"
_MONTH_YEAR_RE = re.compile(
    r'(?P<month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
    r'|\d{1,2})'
    r'[\s/\-]*'
    r'(?P<year>20\d{2}|19\d{2})',
    re.IGNORECASE,
)

# Matches a full date range: "Nov 2020 - Jan 2021", "2019 - Present", "2018-2023"
_DATE_RANGE_RE = re.compile(
    r'(?P<s_month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
    r'|\d{1,2})?'
    r'[\s/\-]*'
    r'(?P<s_year>20\d{2}|19\d{2})'
    r'\s*[-\u2013\u2014to]+\s*'
    r'(?:'
        r'(?P<e_month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
        r'|\d{1,2})?'
        r'[\s/\-]*'
        r'(?P<e_year>20\d{2}|19\d{2})'
        r'|(?P<present>present|current|now|till\s+date|till\s+now)'
    r')',
    re.IGNORECASE,
)


def _month_num(name: str) -> int:
    if not name:
        return 1
    name = name.strip().lower()[:3]
    try:
        return int(name)
    except ValueError:
        return MONTH_MAP.get(name, 1)


def _range_months(m) -> int:
    """Return number of months for a _DATE_RANGE_RE match."""
    s_year = int(m.group("s_year"))
    s_month = _month_num(m.group("s_month") or "")

    if m.group("present"):
        e_year, e_month = CURRENT_YEAR, CURRENT_MONTH
    else:
        e_year = int(m.group("e_year"))
        e_month = _month_num(m.group("e_month") or "")

    total = (e_year * 12 + e_month) - (s_year * 12 + s_month)
    return max(0, total)


def _range_start_end(m):
    """Return (start_str, end_str) for display."""
    s_month = m.group("s_month") or ""
    s_year = m.group("s_year")
    start = f"{s_month} {s_year}".strip() if s_month else s_year

    if m.group("present"):
        end = "Present"
    else:
        e_month = m.group("e_month") or ""
        e_year = m.group("e_year")
        end = f"{e_month} {e_year}".strip() if e_month else e_year

    return start, end


# ── Section splitter ──────────────────────────────────────────────────────────

# Section headers we care about — using broad regex to catch variants like
# "PROFESSIONAL EXPERIENCE/INTERNSHIPS", "Work Experience & Projects", etc.
_EXP_SECTION_RE = re.compile(
    r'^\s*(?:professional\s+)?(?:work\s+)?'
    r'(?:experience|employment|internship[s]?|career|history)'
    r'(?:[/&,\s](?:internship[s]?|experience|history|projects))?\s*[:\-]?\s*$',
    re.IGNORECASE,
)

_CERT_SECTION_RE = re.compile(
    r'^\s*(?:certifications?|certificates?|licenses?|credentials?|professional\s+certifications?)\s*[:\-]?\s*$',
    re.IGNORECASE,
)

_STOP_SECTION_RE = re.compile(
    r'^\s*(?:education|academic|skills?|technical\s+skills?|projects?|'
    r'awards?|publications?|references?|languages?|interests?|hobbies|'
    r'achievements?|volunteer|extra.?curricular|activities|personal)\s*[:\-]?\s*$',
    re.IGNORECASE,
)


def _get_section_lines(text: str, section_re: re.Pattern) -> list[str]:
    """Extract lines under the first matching section header."""
    lines = text.split('\n')
    in_section = False
    result = []
    for line in lines:
        stripped = line.strip()
        if section_re.match(stripped):
            in_section = True
            continue
        if in_section and _STOP_SECTION_RE.match(stripped):
            break
        if in_section and stripped:
            result.append(stripped)
    return result


# ── Core extractors ───────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")


def extract_name(text: str) -> str:
    for line in text.strip().split('\n')[:10]:
        line = line.strip()
        if 2 < len(line) < 50 and '@' not in line and not line[:3].strip().isdigit():
            alpha_ratio = sum(c.isalpha() or c.isspace() for c in line) / len(line)
            if alpha_ratio > 0.7:
                return line
    return "Unknown"


def extract_email(text: str):
    m = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return m.group(0) if m else None


def extract_phone(text: str):
    m = re.search(r"\+?\d[\d\s\-\(\)]{8,15}", text)
    if m:
        return re.sub(r'\s+', ' ', m.group(0).strip())
    return None


def extract_location(text: str):
    tl = text.lower()
    for loc in locations_db:
        if loc in tl:
            return loc.title()
    return None


def extract_skills(text: str) -> list[str]:
    found = []
    tl = text.lower()
    for skill in skills_db:
        sl = skill.lower()
        if sl in ("go", "golang"):
            pat = r'\b(go|golang)\b.{0,50}(language|developer|programming|backend|engineer)'
            rpat = r'(language|developer|programming|backend|engineer).{0,50}\b(go|golang)\b'
            if (re.search(pat, tl) or re.search(rpat, tl)) and "go" not in [s.lower() for s in found]:
                found.append("go")
        elif sl == "r":
            pat = r'\b(r)\b.{0,50}(language|programming|statistical|data|analysis|studio)'
            rpat = r'(language|programming|statistical|data|analysis|studio).{0,50}\b(r)\b'
            if (re.search(pat, tl) or re.search(rpat, tl)) and "r" not in [s.lower() for s in found]:
                found.append("R")
        elif sl in tl and sl not in [s.lower() for s in found]:
            found.append(skill)
    return found


def extract_experience_years(text: str) -> float:
    """
    Compute total experience in years by summing ALL date ranges found anywhere
    in the resume — including internships, part-time, freelance, etc.
    Falls back to explicit "N years experience" mentions.
    """
    total_months = 0
    seen_ranges: list[tuple[int, int]] = []  # (start_abs_month, end_abs_month)

    for m in _DATE_RANGE_RE.finditer(text):
        months = _range_months(m)
        if months <= 0:
            continue
        s_year = int(m.group("s_year"))
        s_month = _month_num(m.group("s_month") or "")
        start_abs = s_year * 12 + s_month

        if m.group("present"):
            end_abs = CURRENT_YEAR * 12 + CURRENT_MONTH
        else:
            e_year = int(m.group("e_year"))
            e_month = _month_num(m.group("e_month") or "")
            end_abs = e_year * 12 + e_month

        # Avoid double-counting overlapping ranges
        overlap = False
        for (sa, ea) in seen_ranges:
            overlap_start = max(start_abs, sa)
            overlap_end = min(end_abs, ea)
            if overlap_end > overlap_start:
                # Partial overlap — add only non-overlapping portion
                months = max(0, (end_abs - start_abs) - (overlap_end - overlap_start))
                overlap = True
                break
        seen_ranges.append((start_abs, end_abs))
        total_months += months

    if total_months > 0:
        return round(min(total_months / 12.0, 50), 1)

    # Fallback: explicit "N years experience" text
    for pat in [
        r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
        r'experience[:\s]+(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional|work|industry)',
    ]:
        matches = re.findall(pat, text, re.IGNORECASE)
        if matches:
            return float(max(int(x) for x in matches))

    return 0.0


def extract_work_experience(text: str) -> list[dict]:
    """
    Extract work/internship entries from the experience section.
    Handles tabular layouts (company | title | date on same or adjacent lines).
    """
    section_lines = _get_section_lines(text, _EXP_SECTION_RE)

    # If section detection failed, fall back to scanning full text for date ranges
    if not section_lines:
        section_lines = [l.strip() for l in text.split('\n') if l.strip()]

    intern_re = re.compile(r'\bintern(ship)?\b', re.IGNORECASE)
    entries: list[dict] = []
    current: dict | None = None

    for line in section_lines:
        m = _DATE_RANGE_RE.search(line)
        if m:
            if current:
                current["description"] = " ".join(current["description"])[:400]
                entries.append(current)

            start_str, end_str = _range_start_end(m)
            # Everything before the date on this line is title/company info
            prefix = line[:m.start()].strip().strip('|\u2013\u2014-–').strip()
            is_intern = bool(intern_re.search(line)) or bool(intern_re.search(prefix))

            current = {
                "title": prefix or "Unknown Role",
                "company": "",
                "start": start_str,
                "end": end_str,
                "is_internship": is_intern,
                "description": [],
            }
        elif current is not None:
            stripped = line.lstrip('•-*·\u2022 ')
            # First non-bullet line after a date line = company name
            if not current["company"] and not line.startswith(('•', '-', '*', '·', '\u2022')):
                current["company"] = line[:100]
            else:
                if stripped:
                    current["description"].append(stripped)

    if current:
        current["description"] = " ".join(current["description"])[:400]
        entries.append(current)

    return entries


def extract_certifications(text: str):
    section_lines = _get_section_lines(text, _CERT_SECTION_RE)

    cert_patterns = [
        r'(AWS\s+Certified[^,\n]{0,60})',
        r'(Google\s+(?:Cloud\s+)?Certified[^,\n]{0,60})',
        r'(Microsoft\s+Certified[^,\n]{0,60})',
        r'(Oracle\s+Certified[^,\n]{0,60})',
        r'(Certified\s+\w[\w\s]{0,50})',
        r'(PMP\b[^,\n]{0,40})',
        r'(CISSP\b[^,\n]{0,40})',
        r'(Scrum\s+Master[^,\n]{0,40})',
        r'(CompTIA[^,\n]{0,60})',
    ]

    year_re = re.compile(r'\b(20\d{2}|19\d{2})\b')
    issuer_re = re.compile(
        r'\b(AWS|Amazon|Google|Microsoft|Oracle|Cisco|CompTIA|PMI|'
        r'Scrum Alliance|Coursera|Udemy|LinkedIn|IBM|Meta|Salesforce)\b',
        re.IGNORECASE,
    )

    certs: list[dict] = []
    seen: set[str] = set()

    def add(name: str, issuer: str = "", year: str = ""):
        name = name.strip()[:120]
        if not name or name.lower() in seen:
            return
        seen.add(name.lower())
        certs.append({"name": name, "issuer": issuer, "year": year})

    for line in section_lines:
        yr = year_re.search(line)
        isr = issuer_re.search(line)
        add(line, isr.group(0) if isr else "", yr.group(0) if yr else "")

    if not certs:
        for pat in cert_patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                ct = match.group(1).strip()
                yr = year_re.search(ct)
                isr = issuer_re.search(ct)
                add(ct, isr.group(0) if isr else "", yr.group(0) if yr else "")

    return certs if certs else None


def parse_resume_text(text: str) -> dict:
    """Full resume parsing pipeline."""
    work_exp = extract_work_experience(text)
    exp_years = extract_experience_years(text)

    # If explicit date-range parsing gave 0 but we found work entries, estimate from entries
    if exp_years == 0 and work_exp:
        total = 0
        for e in work_exp:
            # Try to parse start/end from stored strings
            sm = _MONTH_YEAR_RE.search(e.get("start", ""))
            em = _MONTH_YEAR_RE.search(e.get("end", "") or "present")
            if sm:
                sy = int(sm.group("year"))
                smo = _month_num(sm.group("month"))
                if em:
                    ey = int(em.group("year"))
                    emo = _month_num(em.group("month"))
                else:
                    ey, emo = CURRENT_YEAR, CURRENT_MONTH
                total += max(0, (ey * 12 + emo) - (sy * 12 + smo))
        if total > 0:
            exp_years = round(min(total / 12.0, 50), 1)

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "location": extract_location(text),
        "skills": extract_skills(text),
        "education": [],
        "experience_years": exp_years,
        "work_experience": work_exp,
        "certifications": extract_certifications(text),
    }
