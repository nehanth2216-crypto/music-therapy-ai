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

# Known Artists, Soundtracks & Cultural Keywords per Language
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
        "nani", "balakrishna", "venkatesh", "nagarjuna", "chiranjeevi", "karthik", "shweta mohan",
        "sunitha", "dhanunjay", "deepu", "sri krishna", "sahithi chaganti", "sithara",
        "vachindamma", "ramuloo ramulaa", "srivalli", "butta bomma", "chitti", "hoyna hoyna",
        "dheera dheera", "jaragandi", "ninnila ninnila", "kallalo unna prema", "magadheera", "tholi prema",
        "inthandham", "na roja nuvve", "gaaju bomma", "adhento gaani", "o rendu prema meghaalila", "baby",
        "vellake", "dheevara", "dhivara", "mind block", "sarileru neekevvaru", "naatu naatu", "komuram bheemudo",
        "oohale", "jaanu", "baahubali", "vishal chandrashekar", "s.p. charan", "spb charan", "vijai bulganin",
        "sreerama chandra", "yazin nizar", "govind vasantha", "dear comrade"
    ],
    "Hindi": [
        "arijit singh", "pritam", "shreya ghoshal", "atif aslam", "a.r. rahman",
        "mohit chauhan", "sonu nigam", "jubin nautiyal", "b praak", "neha kakkar",
        "vishal shekhar", "amit trivedi", "shankar ehsaan loy", "armaan malik", "papón",
        "brahmastra", "animal", "jawan", "dunki", "stree 2", "pathaan", "kesariya",
        "tum se hi", "raataan lambiyan", "jab we met", "rockstar", "tamasha", "kabir singh",
        "bollywood", "hindi", "anuv jain", "prateek kuhad", "lata mangeshkar", "kishore kumar"
    ],
    "Tamil": [
        "anirudh ravichander", "a.r. rahman", "yuvan shankar raja", "harris jayaraj",
        "sid sriram", "dhanush", "santhosh narayanan", "g.v. prakash kumar",
        "pradeep kumar", "jonita gandhi", "bombay jayashri", "dhee",
        "leo", "jailer", "vettaiyan", "vikram", "varisu", "thunivu", "beast", "doctor",
        "master", "soorarai pottru", "neeyum naanum", "naan pizhai", "marakkuma nenjam",
        "kollywood", "tamil", "ilayaraja", "karthik", "chinmayi"
    ],
    "Malayalam": [
        "hesham abdul wahab", "sushin shyam", "vijay yesudas", "k.s. chithra",
        "job kurian", "vineeth sreenivasan", "shaan rahman", "gopi sundar", "bijibal",
        "hridayam", "manjummel boys", "premam", "lucifer", "minnal murali", "darshana", "malare",
        "mollywood", "malayalam", "avesham", "kishkindha kaandam"
    ],
    "Kannada": [
        "sanjith hegde", "sonu nigam", "vijay prakash", "arjun janya", "charan raj",
        "b. ajaneesh loknath", "raghu dixit", "kgf", "kantara", "777 charlie", "vikrant rona", "singara siriye",
        "sandalwood", "kannada", "vasuki vaibhav"
    ],
    "Punjabi": [
        "diljit dosanjh", "ap dhillon", "gurinder gill", "sidhu moose wala", "b praak",
        "jasleen royal", "shubh", "karan aujla", "guru randhawa", "qismat", "sufna", "punjabi", "amrinder gill"
    ],
    "Marathi": [
        "ajay-atul", "ajay gogavale", "swapnil bandodkar", "shreya ghoshal", "sairat", "ved", "yad lagla", "marathi"
    ],
    "Gujarati": [
        "sachin-jigar", "darshan raval", "osman mir", "geeta rabari", "kinjal dave", "aditya gadhvi", "gujarati", "dhollywood", "mor bani thangat"
    ],
    "Bengali": [
        "anupam roy", "shreya ghoshal", "rupam islam", "rabindra sangeet", "hemanta mukherjee", "manna dey", "bengali", "somlata", "shaan"
    ],
    "Urdu": [
        "nusrat fateh ali khan", "rahat fateh ali khan", "atif aslam", "ghulam ali", "mehdi hassan", "ali zafar", "coke studio", "urdu", "ghazal", "qawwali", "kaifi khalil"
    ],
    "Japanese": [
        "joe hisaishi", "radwimps", "yoasobi", "kenshi yonezu", "aimer", "lisa", "ghibli", "anime", "j-pop", "japanese", "fujii kaze", "hikaru utada"
    ],
    "Korean": [
        "bts", "iu", "blackpink", "newjeans", "crush", "paul kim", "taeyeon", "k-pop", "korean", "k-drama", "kdrama", "ost", "exo", "twice"
    ],
    "Chinese": [
        "jay chou", "jj lin", "teresa teng", "g.e.m.", "faye wong", "mandopop", "c-pop", "chinese", "erhu", "guzheng", "charlie zhou"
    ],
    "Spanish": [
        "bad bunny", "rosalía", "rosalia", "luis fonsi", "alejandro sanz", "enrique iglesias", "shakira", "j balvin", "flamenco", "spanish", "guitarra española"
    ],
    "French": [
        "stromae", "indila", "daft punk", "zaz", "edith piaf", "yann tiersen", "amelie", "french", "chanson", "pomme"
    ],
    "German": [
        "rammstein", "hans zimmer", "cro", "nena", "german", "peter fox", "max richter", "ludwig van beethoven", "bach"
    ],
    "Italian": [
        "ludovico einaudi", "andrea bocelli", "laura pausini", "eros ramazzotti", "maneskin", "italian", "ennio morricone", "vivaldi"
    ],
    "English": [
        "english", "pop", "acoustic", "lo-fi", "chill", "classical", "instrumental"
    ]
}

# Known English Tracks that must NEVER be shown when non-English target is selected
ENGLISH_ONLY_TITLES = {
    "weightless", "sunflower", "you are my sunshine", "twinkle twinkle little star",
    "clair de lune", "gymnopédie no. 1", "river flows in you", "moonlight sonata",
    "deep forest rain", "ocean waves & wind", "tibetan healing bowls", "acoustic campfire",
    "summer anthem", "good times pop", "electric workout", "closer", "soundhelix",
    "melodies from heaven", "stereo hearts", "gratitude"
}

# Known Western / English Artists that must NEVER be associated with non-English targets
KNOWN_WESTERN_ARTISTS = [
    "kirk franklin", "gym class heroes", "adam levine", "brandon lake", "marconi union",
    "dua lipa", "adele", "coldplay", "taylor swift", "ed sheeran", "the weeknd", "drake",
    "sza", "billie eilish", "justin bieber", "post malone", "ariana grande", "bruno mars",
    "beyoncé", "beyonce", "rihanna", "eminem", "kendrick lamar", "imagine dragons", "soundhelix",
    "maroon 5", "david guetta", "calvin harris", "the chainsmokers", "avicii", "kygo", "zedd",
    "bebe rexha", "halsey", "olivia rodrigo", "charlie puth", "sam smith", "sia", "harry styles",
    "lorde", "lana del rey", "hozier", "khalid", "benson boone", "teddy swims", "lady gaga",
    "miley cyrus", "kanye west", "travis scott", "twenty one pilots", "marshmello", "alan walker",
    "martin garrix", "fleetwood mac", "queen", "the beatles", "pink floyd", "led zeppelin",
    "linkin park", "radiohead", "arctic monkeys", "green day", "shawn mendes", "camila cabello"
]

class LanguageVerifier:
    """Strict language verification utility ensuring ZERO cross-language leakage."""

    @staticmethod
    def verify_track_language(track: Dict[str, Any], target_language: str) -> bool:
        """
        Returns True ONLY if track is verified to belong to target_language.
        Returns False if the track is in a different language or fails verification.
        """
        if not target_language:
            return True

        t_lang = (target_language or "English").strip().title()
        track_lang = (track.get("language") or "").strip().title()
        title = (track.get("title") or track.get("song") or "").strip().lower()
        artist = (track.get("artist") or track.get("artist_or_source") or "").strip().lower()
        album = (track.get("album") or track.get("movie") or "").strip().lower()

        full_text = f"{title} {artist} {album}"

        # If target is non-English, STRICTLY reject known Western artists and English-only titles
        if t_lang.lower() != "english":
            if any(wa in artist for wa in KNOWN_WESTERN_ARTISTS):
                return False
            if any(eng in title for eng in ENGLISH_ONLY_TITLES):
                return False

        # If track has explicit language set and it's DIFFERENT from target, reject immediately
        if track_lang and track_lang.lower() != t_lang.lower():
            return False

        # If track is from verified internal catalog or test fixture
        if track.get("is_catalog_verified") or track.get("is_verified"):
            return True

        # Check Native Unicode Character Script matching for this target language
        if t_lang in UNICODE_RANGES:
            pattern = UNICODE_RANGES[t_lang]
            if re.search(pattern, full_text):
                return True

        # Check Artist/Movie Catalog matches
        if t_lang in LANGUAGE_ARTIST_CATALOG:
            keywords = LANGUAGE_ARTIST_CATALOG[t_lang]
            if any(kw in full_text for kw in keywords):
                return True

        # Check explicit language name keyword in track text (e.g. "Telugu Songs")
        if t_lang.lower() in full_text:
            return True

        # For English target language: MUST NOT contain regional Indian/Asian characters or regional artists
        if t_lang.lower() == "english":
            for lang, pattern in UNICODE_RANGES.items():
                if lang not in ["English", "Spanish", "French", "German", "Italian"]:
                    if re.search(pattern, full_text):
                        return False
            for reg_lang, keywords in LANGUAGE_ARTIST_CATALOG.items():
                if reg_lang != "English":
                    for kw in keywords:
                        if len(kw) > 4 and kw in artist:
                            return False
            return True

        # Non-external search results that already claim the target language (e.g., test mocks)
        is_search_result = track.get("is_search_result", False) or track.get("is_spotify", False) or track.get("is_itunes", False)
        if not is_search_result and track_lang and track_lang.lower() == t_lang.lower():
            return True

        # For regional non-English targets from external web searches:
        # If it did NOT match catalog, Unicode, regional artist, or language keyword,
        # it CANNOT be considered authentic Telugu/Hindi/etc. Do not blindly accept it.
        return False
