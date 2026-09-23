import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from uuid import uuid4

from app.jobs import make_prompt, validated_comments
from app.main import CommentIn, delete_video
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

    def test_general_comment_is_optional_and_included_in_chat_context(self):
        self.assertIsNone(CommentIn(body="Overall note").second)
        prompt = make_prompt(
            {"duration_seconds": 27},
            [{"second": None, "author": "human", "body": "Overall note"}],
            [],
            "What are the top issues?",
        )
        self.assertIn("General [human]: Overall note", prompt)

    def test_video_removal_deletes_database_row_and_private_file(self):
        video_id = uuid4()
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = {"object_key": "videos/test.mp4"}
        with patch("app.main.db.connect") as connect, patch("app.main.storage.delete") as delete_file:
            connect.return_value.__enter__.return_value = conn
            self.assertEqual(delete_video(video_id).status_code, 204)
        conn.execute.assert_any_call("DELETE FROM videos WHERE id = %s", (video_id,))
        delete_file.assert_called_once_with("videos/test.mp4")


if __name__ == "__main__":
    unittest.main()
