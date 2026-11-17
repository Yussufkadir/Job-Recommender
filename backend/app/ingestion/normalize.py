"""Turns source-specific location/title text into the fields search filters on."""
import html
import re
from typing import Iterable, Optional

SUPPORTED_COUNTRIES = ["pl", "de", "fr", "gb", "us", "nl", "se", "ca", "it"]
EUROPE = ["pl", "de", "fr", "gb", "nl", "se", "it"]
NORTH_AMERICA = ["us", "ca"]

COUNTRY_NAMES = {
    "pl": "Poland", "de": "Germany", "fr": "France", "gb": "United Kingdom", "us": "United States",
    "nl": "Netherlands", "se": "Sweden", "ca": "Canada", "it": "Italy",
}

# English names plus local and German spellings ("Nederland", "Niederlande"): some feeds, like
# Arbeitnow, write locations in the local language, and an unrecognized country falls back to the
# feed's default (Germany).
_PLACE_TERMS = {
    "pl": ["poland", "polska", "polen", "warsaw", "warszawa", "krakow", "kraków", "cracow", "wroclaw",
           "wrocław", "gdansk", "gdańsk", "poznan", "poznań", "lodz", "łódź", "katowice", "gdynia",
           "lublin"],
    "de": ["germany", "deutschland", "niemcy", "berlin", "munich", "münchen", "muenchen", "hamburg",
           "frankfurt", "cologne", "köln", "koeln", "stuttgart", "düsseldorf", "dusseldorf", "leipzig",
           "dresden", "nuremberg", "nürnberg", "hannover", "bonn", "karlsruhe", "mannheim", "essen",
           "dortmund"],
    "fr": ["france", "frankreich", "paris", "lyon", "marseille", "toulouse", "nantes", "lille", "bordeaux",
           "nice", "montpellier", "grenoble", "rennes", "strasbourg", "sophia antipolis"],
    "gb": ["united kingdom", "uk", "u.k.", "england", "scotland", "wales", "great britain", "britain",
           "vereinigtes königreich", "großbritannien", "grossbritannien", "royaume-uni",
           "london", "manchester", "edinburgh", "glasgow", "birmingham", "bristol", "oxford", "leeds",
           "belfast", "cardiff", "reading", "brighton", "newcastle", "sheffield", "nottingham"],
    "us": ["united states", "usa", "u.s.", "us", "new york", "nyc", "san francisco", "seattle", "austin",
           "boston", "chicago", "los angeles", "denver", "atlanta", "washington, dc", "washington dc",
           "miami", "san diego", "san jose", "palo alto", "mountain view", "menlo park", "sunnyvale",
           "dallas", "houston", "philadelphia", "pittsburgh", "salt lake city", "bay area", "brooklyn",
           "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
           "delaware", "florida", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas",
           "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota",
           "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
           "new mexico", "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
           "pennsylvania", "rhode island", "south carolina", "south dakota", "tennessee", "texas",
           "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming"],
    "nl": ["netherlands", "the netherlands", "nederland", "niederlande", "holland", "amsterdam", "rotterdam",
           "utrecht", "eindhoven", "the hague", "den haag", "delft", "groningen", "zwolle", "haarlem",
           "leiden", "arnhem", "nijmegen", "tilburg", "breda", "maastricht", "enschede", "amersfoort"],
    "se": ["sweden", "sverige", "schweden", "stockholm", "gothenburg", "göteborg", "goteborg", "malmö",
           "malmo", "uppsala", "lund"],
    "ca": ["canada", "toronto", "vancouver", "montreal", "montréal", "ottawa", "calgary", "waterloo",
           "edmonton", "quebec", "québec"],
    "it": ["italy", "italia", "italien", "milan", "milano", "rome", "roma", "turin", "torino", "bologna",
           "florence", "firenze", "naples", "napoli"],
}
_REGION_TERMS = {
    "europe": EUROPE, "european union": EUROPE, "eu": EUROPE, "emea": EUROPE, "eea": EUROPE,
    "north america": NORTH_AMERICA, "americas": NORTH_AMERICA,
    "worldwide": SUPPORTED_COUNTRIES, "anywhere": SUPPORTED_COUNTRIES,
}

_UNSUPPORTED_PLACE_TERMS = [
    "switzerland", "schweiz", "suisse", "zurich", "zürich", "basel", "bern", "geneva", "genève",
    "lausanne", "winterthur", "schlieren", "zug", "lucerne", "luzern", "st. gallen",
    "austria", "österreich", "vienna", "wien", "graz", "linz", "salzburg", "innsbruck",
    "liechtenstein", "luxembourg", "belgium", "belgië", "belgique", "belgien", "brussels", "denmark",
    "danmark", "dänemark", "copenhagen", "spain", "españa", "spanien", "madrid", "barcelona", "portugal",
    "lisbon", "czech", "czechia", "česko", "prague", "ireland", "irland", "dublin", "svizzera",
]

_US_STATES = {
    "AL", "AK", "AZ", "CA", "CT", "FL", "GA", "HI", "ID", "IA", "KS", "KY",
    "LA", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND",
    "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}
_CA_PROVINCES = {"ON", "BC", "QC", "AB", "MB", "SK", "NS", "NB", "PE"}


def _term_pattern(terms: Iterable[str]) -> re.Pattern:
    alternatives = sorted((re.escape(term) for term in terms), key=len, reverse=True)
    return re.compile(r"(?<![\w.])(?:" + "|".join(alternatives) + r")(?![\w])")


_PLACE_PATTERNS = {code: _term_pattern(terms) for code, terms in _PLACE_TERMS.items()}
_REGION_PATTERNS = {region: _term_pattern([region]) for region in _REGION_TERMS}
_UNSUPPORTED_PLACE_PATTERN = _term_pattern(_UNSUPPORTED_PLACE_TERMS)
_MISLEADING_PHRASES = [("new south wales", " "), ("new england", " usa ")]
_STATE_PATTERN = re.compile(r",\s*([A-Z]{2})\b")
_REMOTE_PATTERN = re.compile(r"\b(remote|anywhere|worldwide|work from home|home[- ]based|telecommute)\b", re.I)


def infer_countries(location: Optional[str]) -> list[str]:
    """Supported country codes a location string refers to, in SUPPORTED_COUNTRIES order."""
    if not location:
        return []
    found: set[str] = set()
    lowered = location.lower()
    for phrase, replacement in _MISLEADING_PHRASES:
        lowered = lowered.replace(phrase, replacement)

    for code, pattern in _PLACE_PATTERNS.items():
        if pattern.search(lowered):
            found.add(code)
    for region, pattern in _REGION_PATTERNS.items():
        if pattern.search(lowered):
            found.update(_REGION_TERMS[region])
    for abbreviation in _STATE_PATTERN.findall(location):
        if abbreviation in _US_STATES:
            found.add("us")
        elif abbreviation in _CA_PROVINCES:
            found.add("ca")

    return [code for code in SUPPORTED_COUNTRIES if code in found]


def names_unsupported_place(location: Optional[str]) -> bool:
    return bool(location and _UNSUPPORTED_PLACE_PATTERN.search(location.lower()))


def is_remote(location: Optional[str], flag: Optional[bool] = None) -> bool:
    if flag:
        return True
    return bool(location and _REMOTE_PATTERN.search(location))

_STOPWORDS_BY_LANGUAGE = {
    "en": {"the", "and", "to", "of", "for", "with", "you", "we", "our", "is", "are", "will", "your",
           "this", "that", "be", "have", "who", "an", "on", "as"},
    "de": {"und", "der", "die", "das", "wir", "sie", "mit", "für", "ist", "ein", "eine", "zu", "von",
           "auf", "bei", "du", "dich", "deine", "unser", "unsere", "oder", "nicht", "werden"},
    "fr": {"le", "la", "les", "et", "des", "du", "nous", "vous", "pour", "avec", "est", "une", "dans",
           "sur", "votre", "notre", "au", "aux", "qui", "sont"},
    "pl": {"i", "w", "z", "na", "do", "się", "jest", "oraz", "dla", "nie", "jak", "od", "po", "przez",
           "twoje", "nasz", "nasze", "będziesz", "pracy"},
    "nl": {"de", "het", "een", "en", "van", "je", "jij", "wij", "ons", "onze", "voor", "met", "zijn",
           "bij", "naar", "niet", "ook"},
    "sv": {"och", "att", "det", "som", "en", "på", "är", "för", "med", "vi", "du", "har", "av", "till",
           "vår", "dig"},
    "it": {"il", "di", "che", "e", "la", "per", "un", "una", "con", "sono", "nel", "della", "del",
           "noi", "tuo", "nostro", "nostra"},
}


def looks_english(text: str) -> bool:
    """True unless another language's function words clearly outnumber English ones."""
    words = re.findall(r"[a-zA-ZÀ-ž]+", text[:3000].lower())
    if len(words) < 20:
        return True
    counts = {
        language: sum(word in stopwords for word in words)
        for language, stopwords in _STOPWORDS_BY_LANGUAGE.items()
    }
    english = counts.pop("en")
    return english >= max(counts.values())


_GENDER_TAGS = re.compile(r"\((?:[mwfdx]\s*/\s*)+[mwfdx]\)|\b(?:[mwfdx]/){1,3}[mwfdx]\b", re.I)
_COMPANY_SUFFIXES = re.compile(
    r"\b(inc|llc|ltd|limited|gmbh|ag|se|sa|sas|bv|b\.v|plc|corp|corporation|co|sp\. z o\.o|s\.a)\b\.?", re.I
)


def _normalize_words(value: str) -> str:
    return re.sub(r"[^a-z0-9+#]+", " ", value.lower()).strip()


_TITLE_PARTS = re.compile(r"\s+[-–—]\s+|\s*[|,/()]\s*")
_LOCATION_FILLER = re.compile(
    r"\b(?:remote|hybrid|on-?site|in-office|office|based|area|metro|region|time ?zones?|only|and|or)\b|&"
)
_ALL_PLACE_PATTERNS = [*_PLACE_PATTERNS.values(), *_REGION_PATTERNS.values(), _UNSUPPORTED_PLACE_PATTERN]


def _is_location(part: str) -> bool:
    """True for a title part that names only places: "Germany", "Remote", "Berlin / Munich", "NY"."""
    part = part.strip()
    if part in _US_STATES or part in _CA_PROVINCES:
        return True
    lowered = part.lower()
    for pattern in _ALL_PLACE_PATTERNS:
        lowered = pattern.sub(" ", lowered)
    return not re.search(r"\w", _LOCATION_FILLER.sub(" ", lowered))


def _title_without_locations(title: str) -> str:
    """Drop the location parts of a title: "Staff Engineer - Alerting | Germany | Remote" and
    "Staff Engineer - Alerting | Spain | Remote" are one job posted once per country. The first
    part is the job itself and always stays."""
    first, *rest = _TITLE_PARTS.split(title)
    return " ".join([first, *(part for part in rest if not _is_location(part))])


def dedupe_key(title: str, company: str) -> str:
    """Normalized "title|company", ignoring locations in the title. Cross-source duplicates are
    matched on the title part and then compared with same_company(), since boards spell company
    names differently."""
    title = _title_without_locations(_GENDER_TAGS.sub(" ", html.unescape(title)))
    return f"{_normalize_words(title)}|{company_key(company)}"[:512]


def clean_title(title: str) -> str:
    return re.sub(r"\s{2,}", " ", _GENDER_TAGS.sub("", html.unescape(title))).strip(" -–|")


def company_key(company: str) -> str:
    return _normalize_words(_COMPANY_SUFFIXES.sub(" ", company))


def same_company(left: str, right: str) -> bool:
    """'wolt' and 'wolt english' (one board's display name) are the same company."""
    a, b = company_key(left), company_key(right)
    if not a or not b:
        return False
    shorter, longer = sorted((a, b), key=len)
    return longer == shorter or longer.startswith(shorter + " ")


_MAX_SKILL_CHARS = 40
_MAX_SKILL_WORDS = 4


# The NER was trained on CVs, so job ads' equal-opportunity statements ("regardless of sexual
# orientation, veteran status..."), benefits and well-known company names come out as skills.
_NOT_SKILLS = re.compile(
    r"\b(?:status|orientation|gender|marital|veteran|disability|national origin|religio\w*|ethnicity"
    r"|genetic information|political affiliation|mental ability|pregnan\w*|insurance|rsus?|401k"
    r"|self employed)\b"
)
_COMPANY_NAMES = {
    "lyft", "spotify", "fox", "airbnb", "facebook", "meta", "stripe", "google", "microsoft", "linkedin",
    "yelp", "gmail", "anthropic", "nvidia", "amazon", "apple", "ibm", "uber", "netflix", "openai",
}


def clean_skills(skills: Iterable[str]) -> list[str]:
    """Drop NER spans that are sentences, markup, hiring-policy terms or company names rather
    than skill names."""
    cleaned = set()
    for skill in skills:
        skill = html.unescape(skill).strip().lower()
        if (
            skill
            and "\n" not in skill
            and len(skill) <= _MAX_SKILL_CHARS
            and len(skill.split()) <= _MAX_SKILL_WORDS
            and re.search(r"[a-z]", skill)
            and skill not in {"amp", "nbsp", "quot"}
            and skill not in _COMPANY_NAMES
            and not _NOT_SKILLS.search(skill)
        ):
            cleaned.add(skill)
    return sorted(cleaned)


_SENIORITY_RULES = [
    ("intern", re.compile(r"\b(intern|internship|trainee|praktikant\w*|apprentice\w*|werkstudent\w*|working student|stagiaire|stage|stażysta|staż)\b", re.I)),
    ("senior", re.compile(r"\b(senior|sr\.?|lead|principal|staff|head of|director|vp|vice president|chief|architect)\b", re.I)),
    ("junior", re.compile(r"\b(junior|jr\.?|entry[- ]level|graduate|new grad|associate)\b", re.I)),
]


def seniority_from_title(title: str) -> str:
    for level, pattern in _SENIORITY_RULES:
        if pattern.search(title):
            return level
    return "mid"
