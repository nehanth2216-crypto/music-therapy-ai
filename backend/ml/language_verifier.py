import re
from typing import Dict, Any, List

# Unicode Character Range Definitions
UNICODE_RANGES = {
    "Telugu": r"[\u0C00-\u0C7F]",
    "Hindi": r"[\u0900-\u097F]",
    "Marathi": r"[\u0900-\u097F]",
    "Tamil": r"[\u0B80-\u0BFF]",
    "Kannada": r"[\u0C80-\u0CFF]",
    "Malayalam": r"[\u0D00-\u0D7F]",
    "Bengali": r"[\u0980-\u09FF]",
    "Gujarati": r"[\u0A80-\u0AFF]",
    "Punjabi": r"[\u0A00-\u0A7F]",
    "Urdu": r"[\u0600-\u06FF]",
    "Japanese": r"[\u3040-\u30FF\u4E00-\u9FFF]",
    "Korean": r"[\uAC00-\uD7AF\u1100-\u11FF]",
    "Chinese": r"[\u4E00-\u9FFF]"
}

# Known Artists & Movie Keywords per Language
LANGUAGE_ARTIST_CATALOG = {
    "Telugu": [
        "telugu", "tollywood", "sid sriram", "hesham abdul wahab", "anirudh ravichander",
        "anurag kulkarni", "s.s. thaman", "thaman s", "thaman", "devi sri prasad", "dsp",
        "m.m. keeravani", "keeravani", "shreya ghoshal", "armaan malik", "haricharan",
        "jonita gandhi", "kaala bhairava", "ramya behara", "madhu priya", "mangli",
        "s.p. balasubrahmanyam", "spb", "k.s. chithra", "chithra", "ghantasala", "ilayaraja",
        "gopi sundar", "jakes bejoy", "mickey j meyer", "radhan", "mahathi swara sagar",
        "rahul sipligunj", "vijay devarakonda", "hi nanna", "devara", "rrr",
        "ala vaikunthapurramuloo", "pushpa", "kalki 2898 ad", "kalki", "tillu square",
        "guntur kaaram", "taxiwaala", "geetha govindam", "fidaa", "arjun reddy",
        "rangasthalam", "jersey", "uppena", "kushi", "samajavaragamana", "maate vinadhuga",
        "samayama", "inkem inkem", "o ranga ranga", "nee pathali", "fear song", "sitaramam",
        "sita ramam", "hanuman", "salaar", "saripodhaa sanivaaram", "thandel", "game changer",
        "chuttamalle", "kadalalle", "priyathama", "undiporaadhey", "ay pilla", "saranga dariya",
        "sirivennela", "manasa manasa", "naa kanulu yepudu", "priya mithunam", "love story",
        "majili", "hushaaru", "varudu kavalenu", "most eligible bachelor", "shyam singha roy", "rang de",
        "ram miriyala", "shilpa rao", "chinmayi", "pawan kalyan", "mahesh babu", "ntr", "jr ntr", "ram charan", "prabhas", "allu arjun",
        "nani", "balakrishna", "venkatesh", "nagarjuna", "chiranjeevi"
    ],
    "Hindi": [
        "arijit singh", "pritam", "shreya ghoshal", "atif aslam", "a.r. rahman hindi",
        "mohit chauhan", "sonu nigam", "jubin nautiyal", "b praak hindi", "neha kakkar",
        "vishal shekhar", "amit trivedi", "shankar ehsaan loy", "armaan malik", "papón",
        "brahmastra", "animal", "jawan", "dunki", "stree 2", "pathaan", "kesariya",
        "tum se hi", "raataan lambiyan", "jab we met", "rockstar", "tamasha", "kabir singh",
        "bollywood", "hindi"
    ],
    "Tamil": [
        "anirudh ravichander", "a.r. rahman", "yuvan shankar raja", "harris jayaraj",
        "sid sriram", "dhanush", "santhosh narayanan", "g.v. prakash kumar",
        "pradeep kumar", "jonita gandhi", "bombay jayashri", "dhee",
        "leo", "jailer", "vettaiyan", "vikram", "varisu", "thunivu", "beast", "doctor",
        "master", "soorarai pottru", "neeyum naanum", "naan pizhai", "marakkuma nenjam",
        "kollywood", "tamil"
    ],
    "Malayalam": [
        "hesham abdul wahab", "sushin shyam", "vijay yesudas", "k.s. chithra",
        "job kurian", "vineeth sreenivasan", "shaan rahman", "gopi sundar", "bijibal",
        "hridayam", "manjummel boys", "premam", "lucifer", "minnal murali", "darshana", "malare",
        "mollywood", "malayalam"
    ],
    "Kannada": [
        "sanjith hegde", "sonu nigam", "vijay prakash", "arjun janya", "charan raj",
        "b. ajaneesh loknath", "raghu dixit", "kgf", "kantara", "777 charlie", "vikrant rona", "singara siriye",
        "sandalwood", "kannada"
    ],
    "Punjabi": [
        "diljit dosanjh", "ap dhillon", "gurinder gill", "sidhu moose wala", "b praak",
        "jasleen royal", "shubh", "karan aujla", "guru randhawa", "qismat", "sufna", "punjabi"
    ],
    "Marathi": [
        "ajay-atul", "ajay gogavale", "swapnil bandodkar", "shreya ghoshal", "sairat", "ved", "yad lagla", "marathi"
    ]
}

# Known English Tracks that must NEVER be shown when non-English target is selected
ENGLISH_ONLY_TITLES = {
    "weightless", "sunflower", "you are my sunshine", "twinkle twinkle little star",
    "clair de lune", "gymnopédie no. 1", "river flows in you", "moonlight sonata",
    "deep forest rain", "ocean waves & wind", "tibetan healing bowls", "acoustic campfire",
    "summer anthem", "good times pop", "electric workout", "closer", "soundhelix"
}

class LanguageVerifier:
    """Strict language verification utility."""

    @staticmethod
    def verify_track_language(track: Dict[str, Any], target_language: str) -> bool:
        """
        Returns True ONLY if track is verified to belong to target_language.
        Returns False if the track is in a different language or fails verification.
        """
        if not target_language:
            return True

        t_lang = (target_language or "English").strip()
        track_lang = (track.get("language") or "").strip()
        title = (track.get("title") or "").strip().lower()
        artist = (track.get("artist") or "").strip().lower()
        album = (track.get("album") or "").strip().lower()

        full_text = f"{title} {artist} {album}"

        # 1. If target is non-English, reject known English-only titles
        if t_lang.lower() != "english":
            if any(eng in title for eng in ENGLISH_ONLY_TITLES):
                return False

        # 2. Check Native Unicode Character Script matching
        if t_lang in UNICODE_RANGES:
            pattern = UNICODE_RANGES[t_lang]
            if re.search(pattern, full_text):
                return True

        # 3. Check Artist/Movie Catalog matches
        if t_lang in LANGUAGE_ARTIST_CATALOG:
            keywords = LANGUAGE_ARTIST_CATALOG[t_lang]
            if any(kw in full_text for kw in keywords):
                return True

        # 4. Catalog or Search Result matching target language
        if track.get("is_catalog_verified"):
            return True

        if track.get("is_search_result"):
            if t_lang.lower() != "english":
                keywords = LANGUAGE_ARTIST_CATALOG.get(t_lang, [])
                has_keyword = any(kw in full_text for kw in keywords) or t_lang.lower() in full_text
                if not has_keyword:
                    return False
            for lang, pattern in UNICODE_RANGES.items():
                if lang != t_lang and lang != "English":
                    if re.search(pattern, full_text):
                        return False
            return True

        # 5. Explicit Track Language Attribute match (strictly reject if mismatching)
        if track_lang:
            if track_lang.lower() == t_lang.lower():
                for lang, pattern in UNICODE_RANGES.items():
                    if lang != t_lang and lang != "English":
                        if re.search(pattern, full_text):
                            return False
                return True
            else:
                return False

        # 6. For English target, check standard latin characters without non-English native script
        if t_lang.lower() == "english":
            for lang, pattern in UNICODE_RANGES.items():
                if lang not in ["English", "Spanish", "French", "German", "Italian"]:
                    if re.search(pattern, full_text):
                        return False
            return True

        # 7. Fallback for non-English queries if fetched from target language search
        return False

