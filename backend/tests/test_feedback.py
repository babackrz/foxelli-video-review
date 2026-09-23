import unittest
from unittest.mock import patch
from types import SimpleNamespace

from app.jobs import validated_comments
from app.video import duration_seconds, post_requested, valid_second


class FeedbackRulesTest(unittest.TestCase):
    def test_upload_requires_video_stream(self):
        with patch("app.video.subprocess.run", return_value=SimpleNamespace(stdout='{"streams":[{"codec_type":"audio"}],"format":{"duration":"2.0"}}')):
            with self.assertRaisesRegex(ValueError, "no video stream"):
                duration_seconds("audio.mp4")

    def test_posting_requires_explicit_request_and_valid_seconds(self):
        self.assertTrue(post_requested("Post the top 3 issues as timeline comments."))
        self.assertFalse(post_requested("What would you say about 0:08?"))
        self.assertFalse(valid_second(27, 27))
        self.assertFalse(valid_second(True, 27))
        proposed = [
            {"second": 8, "text": "Sharper frame needed"},
            {"second": 8, "text": " sharper frame needed "},
            {"second": 27, "text": "Outside clip"},
            {"second": 5, "text": "Already covered"},
            {"second": 4, "text": "Clearer text"},
        ]
        existing = [{"second": 5, "body": "Already covered"}]
        self.assertEqual(validated_comments(proposed, existing, 27, False), [])
        self.assertEqual(validated_comments(proposed, existing, 27, True), [(8, "Sharper frame needed"), (4, "Clearer text")])


if __name__ == "__main__":
    unittest.main()
