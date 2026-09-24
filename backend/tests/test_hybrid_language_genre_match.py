import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import _is_language_match, _is_genre_match, fetch_hybrid_recommendations

class TestHybridLanguageGenreMatch(unittest.TestCase):

    def test_language_match_rejects_foreign_artists_for_english(self):
        # Arijit Singh is a known Hindi artist; must not be allowed as English
        track = {"title": "Apna Bana Le", "artist": "Arijit Singh", "album": "Bhediya"}
        self.assertFalse(_is_language_match(track, "English"))

    def test_language_match_accepts_english_artists_for_english(self):
        track = {"title": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours"}
        self.assertTrue(_is_language_match(track, "English"))

    def test_language_match_accepts_telugu_artists_for_telugu(self):
        track = {"title": "Samayama", "artist": "Hesham Abdul Wahab, Anurag Kulkarni", "album": "Hi Nanna"}
        self.assertTrue(_is_language_match(track, "Telugu"))

    def test_language_match_rejects_unrelated_english_for_telugu(self):
        track = {"title": "Flowers", "artist": "Miley Cyrus", "album": "Endless Summer"}
        self.assertFalse(_is_language_match(track, "Telugu"))

    def test_genre_match_validates_real_genre_keywords(self):
        # Lo-fi keywords: lofi, chill beats, study beats
        lofi_track = {"title": "Study Beats Chillhop", "album": "Lofi Day", "genre": "Electronic"}
        self.assertTrue(_is_genre_match(lofi_track, "Lo-fi"))

        # Classical keywords: classical, piano, orchestra, etc.
        classical_track = {"title": "Piano Sonata No. 14", "album": "Moonlight", "genre": "Classical"}
        self.assertTrue(_is_genre_match(classical_track, "Classical"))

        # Pop keywords: pop, dance, hits
        pop_track = {"title": "Dance Hits 2024", "album": "Top 40", "genre": "Pop"}
        self.assertTrue(_is_genre_match(pop_track, "Pop"))

        # Incompatible genre check
        rock_track = {"title": "Heavy Metal Rock Band", "album": "Hard Rock", "genre": "Rock"}
        self.assertFalse(_is_genre_match(rock_track, "Classical"))

    def test_fetch_hybrid_recommendations_no_cross_language_leakage(self):
        for lang in ["Telugu", "Hindi", "Tamil", "Malayalam", "English"]:
            recs = fetch_hybrid_recommendations(
                mood="Calm",
                language=lang,
                genre="Lo-fi",
                activity="Relaxation",
                limit=10
            )
            self.assertGreaterEqual(len(recs), 2, f"Should return tracks for {lang}")
            for r in recs:
                # Every track must match the requested language
                self.assertTrue(
                    _is_language_match(r, lang),
                    f"Track '{r.get('title')}' by '{r.get('artist')}' failed language match for {lang}"
                )

if __name__ == "__main__":
    unittest.main()
