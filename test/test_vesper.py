# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

#!/usr/bin/env python3
"""
Unit tests for Vesper core functionality.
Run with: python -m pytest test/test_vesper.py
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add the repo root to path so we can import `vesper.*` as a package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from github.GithubException import GithubException  # noqa: E402

from vesper.vesper import (  # noqa: E402
    analyze_with_gemini,
    apply_suggestions_to_pr,
    create_branch,
    fetch_pr_diff,
    find_diff_position,
    get_pr_details_webhook,
    handle_pr_comment_command,
    is_quota_exceeded_message,
    load_config,
    parse_diff_for_suggestions,
    post_comment_webhook,
    post_inline_suggestions,
    run_analysis_for_pr,
    verify_webhook_signature,
)


class TestVesper(unittest.TestCase):
    """Test cases for Vesper functionality."""

    def test_verify_webhook_signature_valid(self):
        """Test webhook signature verification with valid signature."""
        payload = b'{"test": "data"}'
        secret = "test-secret"
        import hashlib
        import hmac

        expected_sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        result = verify_webhook_signature(payload, expected_sig, secret)
        self.assertTrue(result)

    def test_verify_webhook_signature_invalid(self):
        """Test webhook signature verification with invalid signature."""
        payload = b'{"test": "data"}'
        secret = "test-secret"
        invalid_sig = "sha256=invalid"

        result = verify_webhook_signature(payload, invalid_sig, secret)
        self.assertFalse(result)

    def test_load_config_defaults(self):
        """Test loading config with defaults when no config file exists."""
        with patch("os.path.exists", return_value=False):
            config = load_config()
            self.assertEqual(config["focus"], "all")
            self.assertEqual(config["model"], "gemini-2.5-flash")
            self.assertEqual(config["max_diff_length"], 4000)
            self.assertEqual(config["temperature"], 0.2)
            self.assertEqual(config["max_output_tokens"], 8192)
            self.assertIn("prompt", config)  # Should include default prompt

    @patch("vesper.vesper.load_config")
    def test_analyze_with_gemini_success(self, mock_load_config):
        """Test successful Gemini analysis."""
        # Mock config with all required keys
        mock_load_config.return_value = {
            "model": "gemini-2.5-flash",
            "focus": "all",
            "max_diff_length": 4000,
            "temperature": 0.2,
            "max_output_tokens": 4096,
            "prompt": "Test prompt {num_files} {files_list} {diff_content} {focus_instruction}",
        }

        # Mock client and response
        mock_client = Mock()
        mock_client.models = Mock()
        mock_response = Mock()
        mock_response.text = "Test analysis"
        mock_client.models.generate_content.return_value = mock_response

        pr_details = {
            "title": "Test PR",
            "body": "Test body",
            "files_changed": ["test.py"],
            "diff": "test diff",
        }

        result = analyze_with_gemini(mock_client, pr_details)
        self.assertEqual(result, "Test analysis")
        mock_client.models.generate_content.assert_called_once()

    @patch("vesper.vesper.time.sleep", return_value=None)
    @patch("vesper.vesper.load_config")
    def test_analyze_with_gemini_retries_on_server_error(self, mock_load_config, _mock_sleep):
        """Retries on 5xx and succeeds when API recovers."""
        from google.genai import errors as genai_errors

        mock_load_config.return_value = {
            "model": "gemini-2.5-flash",
            "focus": "all",
            "max_diff_length": 4000,
            "temperature": 0.2,
            "max_output_tokens": 4096,
            "prompt": "Test prompt {num_files} {files_list} {diff_content} {focus_instruction}",
        }

        mock_client = Mock()
        mock_client.models = Mock()
        mock_response = Mock()
        mock_response.text = "Recovered analysis"

        server_error = genai_errors.ServerError(503, {"error": {"message": "unavailable", "status": "UNAVAILABLE"}}, None)
        mock_client.models.generate_content.side_effect = [
            server_error,
            server_error,
            mock_response,
        ]

        pr_details = {
            "title": "Test PR",
            "body": "Test body",
            "files_changed": ["test.py"],
            "diff": "test diff",
        }
        result = analyze_with_gemini(mock_client, pr_details)
        self.assertEqual(result, "Recovered analysis")
        self.assertEqual(mock_client.models.generate_content.call_count, 3)

    @patch("vesper.vesper.time.sleep", return_value=None)
    @patch("vesper.vesper.load_config")
    def test_analyze_with_gemini_server_error_message_includes_http(self, mock_load_config, _mock_sleep):
        """Server errors return a helpful message with HTTP details."""
        from google.genai import errors as genai_errors

        mock_load_config.return_value = {
            "model": "gemini-2.5-flash",
            "focus": "all",
            "max_diff_length": 4000,
            "temperature": 0.2,
            "max_output_tokens": 4096,
            "prompt": "Test prompt {num_files} {files_list} {diff_content} {focus_instruction}",
        }

        mock_client = Mock()
        mock_client.models = Mock()
        server_error = genai_errors.ServerError(503, {"error": {"message": "unavailable", "status": "UNAVAILABLE"}}, None)
        mock_client.models.generate_content.side_effect = server_error

        pr_details = {
            "title": "Test PR",
            "body": "Test body",
            "files_changed": ["test.py"],
            "diff": "test diff",
        }
        result = analyze_with_gemini(mock_client, pr_details)
        self.assertIn("api unavailable", result.lower())
        self.assertIn("http 503", result.lower())

    @patch("vesper.vesper.load_config")
    def test_analyze_with_gemini_prompt_backcompat_files_diff(self, mock_load_config):
        """Supports legacy {files}/{diff} placeholders in prompt templates."""
        mock_load_config.return_value = {
            "model": "gemini-2.5-flash",
            "focus": "all",
            "max_diff_length": 4000,
            "temperature": 0.2,
            "max_output_tokens": 4096,
            "prompt": "Files:\\n{files}\\nDiff:\\n{diff}\\n{focus_instruction}",
        }

        mock_client = Mock()
        mock_client.models = Mock()
        mock_response = Mock()
        mock_response.text = "OK"
        mock_client.models.generate_content.return_value = mock_response

        pr_details = {
            "title": "Test PR",
            "body": "Test body",
            "files_changed": ["test.py"],
            "diff": "test diff",
        }
        result = analyze_with_gemini(mock_client, pr_details)
        self.assertEqual(result, "OK")
        _args, kwargs = mock_client.models.generate_content.call_args
        self.assertIn("Files:", kwargs["contents"])
        self.assertIn("test.py", kwargs["contents"])
        self.assertIn("Diff:", kwargs["contents"])
        self.assertIn("test diff", kwargs["contents"])

    @patch("vesper.vesper.load_config")
    def test_analyze_with_gemini_keeps_large_response_with_8k_output_budget(self, mock_load_config):
        """An 8k-token output budget should not be cut off by the sanitizer's char cap."""
        mock_load_config.return_value = {
            "model": "gemini-2.5-flash",
            "focus": "all",
            "max_diff_length": 4000,
            "temperature": 0.2,
            "max_output_tokens": 8192,
            "prompt": "Test prompt {num_files} {files_list} {diff_content} {focus_instruction}",
        }

        mock_client = Mock()
        mock_client.models = Mock()
        mock_response = Mock()
        mock_response.text = "A" * 25000
        mock_client.models.generate_content.return_value = mock_response

        pr_details = {
            "title": "Test PR",
            "body": "Test body",
            "files_changed": ["test.py"],
            "diff": "test diff",
        }

        result = analyze_with_gemini(mock_client, pr_details)
        self.assertEqual(result, "A" * 25000)
        self.assertNotIn("... (truncated for length)", result)

    def test_parse_diff_for_suggestions_valid(self):
        """Test parsing diff suggestions."""
        diff_text = """--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-old line
+new line"""
        result = parse_diff_for_suggestions(diff_text)
        self.assertIsNotNone(result)
        self.assertEqual(
            result,
            [
                {
                    "path": "test.py",
                    "start_line": 1,
                    "end_line": 1,
                    "op": "replace",
                    "suggestion": "new line",
                }
            ],
        )

    def test_parse_diff_for_suggestions_simplified_format_valid(self):
        """Supports `file_path`-first diff blocks (no ---/+++ headers)."""
        diff_text = """test.py
@@ -1,1 +1,1 @@
-old line
+new line"""
        result = parse_diff_for_suggestions(diff_text)
        self.assertEqual(
            result,
            [
                {
                    "path": "test.py",
                    "start_line": 1,
                    "end_line": 1,
                    "op": "replace",
                    "suggestion": "new line",
                }
            ],
        )

    def test_parse_diff_for_suggestions_deletion_only(self):
        """Deletion-only hunks are surfaced as delete operations with ranges."""
        diff_text = """test.py
@@ -2,1 +2,0 @@
-remove me"""
        result = parse_diff_for_suggestions(diff_text)
        self.assertEqual(
            result,
            [
                {
                    "path": "test.py",
                    "start_line": 2,
                    "end_line": 2,
                    "op": "delete",
                    "suggestion": None,
                }
            ],
        )

    def test_parse_diff_for_suggestions_invalid(self):
        """Test parsing invalid diff."""
        diff_text = "not a diff"
        result = parse_diff_for_suggestions(diff_text)
        self.assertIsNone(result)

    def test_format_comment_does_not_add_hr(self):
        """Vesper comment should not add extra decorations."""
        from vesper.vesper import format_comment

        formatted = format_comment("hello")
        self.assertNotIn("\n---", formatted)
        self.assertNotIn("badge.svg", formatted)

    def test_format_comment_with_sha(self):
        """Vesper comment should include SHA marker when provided."""
        from vesper.vesper import format_comment

        formatted = format_comment("analysis content", sha="abc123")
        self.assertIn("vesper-sha: abc123", formatted)
        self.assertIn("<details>", formatted)
        self.assertIn("analysis content", formatted)

    def test_format_comment_without_sha(self):
        """Vesper comment should not include SHA marker when not provided."""
        from vesper.vesper import format_comment

        formatted = format_comment("analysis content")
        self.assertNotIn("vesper-sha:", formatted)
        self.assertIn("<details>", formatted)
        self.assertIn("analysis content", formatted)

    def test_format_notice_includes_warning(self):
        """Notice comment should include warning emoji and title."""
        from vesper.vesper import format_notice

        formatted = format_notice("Test Title", "Test details")
        self.assertIn("⚠️ **Vesper Notice: Test Title**", formatted)
        self.assertIn("Test details", formatted)

    def test_format_notice_does_not_include_sha_marker(self):
        """Notice comment should NOT include SHA marker (format_notice no longer accepts sha parameter)."""
        from vesper.vesper import format_notice

        formatted = format_notice("Test Title", "Test details")
        self.assertNotIn("vesper-sha:", formatted)
        self.assertIn("⚠️ **Vesper Notice: Test Title**", formatted)
        self.assertIn("Test details", formatted)

    @patch("vesper.vesper.post_comment_webhook")
    @patch("vesper.vesper.analyze_with_gemini")
    @patch("vesper.vesper.get_pr_details_webhook")
    @patch("vesper.vesper.setup_environment_webhook")
    def test_run_analysis_for_pr_skips_when_sha_already_commented(
        self,
        mock_setup_env,
        mock_get_pr_details,
        mock_analyze,
        mock_post_comment,
    ):
        """Auto analysis skips when the same head SHA is already posted."""
        g = Mock()
        repo = Mock()
        pr = Mock()
        comment = Mock()
        comment.body = "hello\nvesper-sha: deadbeef\n"
        pr.get_issue_comments.return_value = [comment]
        repo.get_pull.return_value = pr
        g.get_repo.return_value = repo

        mock_setup_env.return_value = (g, "token", Mock())
        mock_get_pr_details.return_value = {
            "number": 1,
            "files_changed": ["x.py"],
            "diff": "diff",
            "head_sha": "deadbeef",
        }

        run_analysis_for_pr(123, "o/r", 1)

        mock_analyze.assert_not_called()
        mock_post_comment.assert_not_called()

    @patch("vesper.vesper.time.time")
    @patch("vesper.vesper.analyze_with_gemini")
    @patch("vesper.vesper.get_pr_details_webhook")
    @patch("vesper.vesper.setup_environment_webhook")
    def test_run_analysis_for_pr_skips_when_quota_cooldown_active(
        self,
        mock_setup_env,
        mock_get_pr_details,
        mock_analyze,
        mock_time,
    ):
        mock_time.return_value = 1000
        g = Mock()
        repo = Mock()
        pr = Mock()
        issue = Mock()

        label = Mock()
        label.name = "something-else"
        issue.get_labels.return_value = [label]

        comment = Mock()
        comment.body = "<!-- vesper-quota-until: 2000 -->"
        pr.get_issue_comments.return_value = [comment]

        repo.get_issue.return_value = issue
        repo.get_pull.return_value = pr
        g.get_repo.return_value = repo

        mock_setup_env.return_value = (g, "token", Mock())
        mock_get_pr_details.return_value = {
            "number": 1,
            "files_changed": ["x.py"],
            "diff": "diff",
            "head_sha": "deadbeef",
        }

        run_analysis_for_pr(123, "o/r", 1, force=False)

        mock_analyze.assert_not_called()

    @patch("vesper.vesper.post_comment_webhook")
    @patch("vesper.vesper.analyze_with_gemini")
    @patch("vesper.vesper.get_pr_details_webhook")
    @patch("vesper.vesper.setup_environment_webhook")
    def test_run_analysis_for_pr_force_reruns_even_with_existing_sha_comment(
        self,
        mock_setup_env,
        mock_get_pr_details,
        mock_analyze,
        mock_post_comment,
    ):
        """Manual /analyze forces a re-run even if SHA comment exists."""
        g = Mock()
        repo = Mock()
        pr = Mock()
        comment = Mock()
        comment.body = "hello\nvesper-sha: deadbeef\n"
        pr.get_issue_comments.return_value = [comment]
        repo.get_pull.return_value = pr
        g.get_repo.return_value = repo

        mock_setup_env.return_value = (g, "token", Mock())
        mock_get_pr_details.return_value = {
            "number": 1,
            "files_changed": ["x.py"],
            "diff": "diff",
            "head_sha": "deadbeef",
        }
        mock_analyze.return_value = "analysis text"

        run_analysis_for_pr(123, "o/r", 1, force=True)

        mock_analyze.assert_called_once()
        mock_post_comment.assert_called_once()

    def test_is_quota_exceeded_message(self):
        self.assertTrue(is_quota_exceeded_message("Error generating analysis: API quota exceeded."))
        self.assertTrue(is_quota_exceeded_message("rate limit hit, try later"))
        self.assertFalse(is_quota_exceeded_message("all good"))

    @patch("vesper.vesper.post_notice_comment")
    @patch("vesper.vesper.analyze_with_gemini")
    @patch("vesper.vesper.get_pr_details_webhook")
    @patch("vesper.vesper.setup_environment_webhook")
    @patch("vesper.vesper.time.time")
    def test_run_analysis_for_pr_posts_quota_notice_and_skips_comment_webhook(
        self,
        mock_time,
        mock_setup_env,
        mock_get_pr_details,
        mock_analyze,
        mock_post_notice,
    ):
        mock_time.return_value = 1000
        g = Mock()
        mock_setup_env.return_value = (g, "token", Mock())
        mock_get_pr_details.return_value = {
            "number": 1,
            "files_changed": ["x.py"],
            "diff": "diff",
            "head_sha": "deadbeef",
        }
        mock_analyze.return_value = "Error generating analysis: API quota exceeded."

        with patch("vesper.vesper.post_comment_webhook") as mock_post_comment:
            run_analysis_for_pr(123, "o/r", 1, force=True)
            mock_post_comment.assert_not_called()

        mock_post_notice.assert_called_once()

    @patch("vesper.vesper.requests.get")
    def test_get_pr_details_webhook_uses_auth_header_when_token_provided(self, mock_get):
        g = Mock()
        repo = Mock()
        pr = Mock()
        g.get_repo.return_value = repo
        repo.get_pull.return_value = pr
        pr.get_files.return_value = []
        pr.diff_url = "https://example.invalid/diff"

        mock_get.return_value = Mock(text="diff")

        get_pr_details_webhook(g, "o/r", 1, installation_token="inst-token")

        _args, kwargs = mock_get.call_args
        self.assertIn("Authorization", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["Authorization"], "token inst-token")

    @patch("vesper.vesper.requests.get")
    def test_fetch_pr_diff_returns_empty_on_non_200(self, mock_get):
        response = Mock()
        response.status_code = 403
        response.text = "forbidden"
        mock_get.return_value = response
        self.assertEqual(fetch_pr_diff("https://example.invalid/diff", token="t"), "")

    def test_post_inline_suggestions_creates_review_without_inline(self):
        """When no inline suggestions are valid, still post a review entry."""
        pr = Mock()
        pr_details = {"head_sha": "deadbeef", "diff": ""}
        repo = Mock()
        repo.get_commit.return_value = Mock()

        pr.get_reviews.return_value = []
        post_inline_suggestions(pr, pr_details, [], g=Mock(), repo=repo)

        pr.create_review.assert_called_once()
        _args, kwargs = pr.create_review.call_args
        self.assertEqual(kwargs["event"], "COMMENT")
        self.assertIn("vesper-sha: deadbeef", kwargs["body"])

    def test_post_inline_suggestions_uses_line_based_comments_first(self):
        """Inline suggestions default to modern line-based review comments."""
        pr = Mock()
        pr_details = {
            "head_sha": "deadbeef",
            "diff": "diff --git a/a.txt b/a.txt\n@@ -1,1 +1,1 @@\n-old\n+new\n",
        }
        repo = Mock()
        repo.get_commit.return_value = Mock()

        pr.get_reviews.return_value = []
        suggestions = [
            {
                "path": "a.txt",
                "start_line": 1,
                "end_line": 1,
                "op": "replace",
                "suggestion": "new",
            }
        ]
        post_inline_suggestions(pr, pr_details, suggestions, g=Mock(), repo=repo)

        _args, kwargs = pr.create_review.call_args
        self.assertIn("comments", kwargs)
        self.assertEqual(kwargs["comments"][0]["path"], "a.txt")
        self.assertEqual(kwargs["comments"][0]["line"], 1)
        self.assertEqual(kwargs["comments"][0]["side"], "RIGHT")

    @patch("vesper.vesper.post_inline_suggestions")
    @patch("vesper.vesper.Github")
    @patch("vesper.vesper.load_config")
    def test_post_comment_webhook_force_review_from_config(self, mock_load_config, mock_github, mock_post_inline):
        """Config can opt-in to reposting reviews on manual /analyze."""
        mock_load_config.return_value = {
            "enable_authoring": False,
            "force_review_on_analyze": True,
        }

        repo = Mock()
        pr = Mock()
        pr.get_issue_comments.return_value = []
        repo.get_pull.return_value = pr

        g = Mock()
        g.get_repo.return_value = repo
        mock_github.return_value = g

        pr_details = {"number": 1, "head_sha": "abc123"}
        post_comment_webhook("token", "o/r", pr_details, "analysis text", manual=True, force_review=False)

        _args, kwargs = mock_post_inline.call_args
        self.assertTrue(kwargs["force_review"])

    @patch("vesper.vesper.post_inline_suggestions")
    @patch("vesper.vesper.Github")
    @patch("vesper.vesper.load_config")
    def test_post_comment_webhook_force_review_explicit_arg(self, mock_load_config, mock_github, mock_post_inline):
        """Explicit force_review argument always wins."""
        mock_load_config.return_value = {
            "enable_authoring": False,
            "force_review_on_analyze": False,
        }

        repo = Mock()
        pr = Mock()
        pr.get_issue_comments.return_value = []
        repo.get_pull.return_value = pr

        g = Mock()
        g.get_repo.return_value = repo
        mock_github.return_value = g

        pr_details = {"number": 1, "head_sha": "abc123"}
        post_comment_webhook("token", "o/r", pr_details, "analysis text", manual=True, force_review=True)

        _args, kwargs = mock_post_inline.call_args
        self.assertTrue(kwargs["force_review"])

    @patch("vesper.vesper.handle_merge_command")
    @patch("vesper.vesper.handle_apply_comment")
    @patch("vesper.vesper.run_analysis_for_pr")
    def test_handle_pr_comment_command_dispatches_analyze(self, mock_run_analysis, _mock_apply, _mock_merge):
        result = handle_pr_comment_command(123, "o/r", 1, "/analyze", "alice")
        self.assertEqual(result, ({"status": "ok"}, 200))
        mock_run_analysis.assert_called_once_with(123, "o/r", 1, force=True, force_review=False)

    @patch("vesper.vesper.handle_merge_command")
    @patch("vesper.vesper.handle_apply_comment")
    @patch("vesper.vesper.run_analysis_for_pr")
    def test_handle_pr_comment_command_dispatches_analyze_force_review(self, mock_run_analysis, _mock_apply, _mock_merge):
        result = handle_pr_comment_command(123, "o/r", 1, "/analyze --force-review", "alice")
        self.assertEqual(result, ({"status": "ok"}, 200))
        mock_run_analysis.assert_called_once_with(123, "o/r", 1, force=True, force_review=True)

    @patch("vesper.vesper.handle_merge_command")
    @patch("vesper.vesper.handle_apply_comment")
    @patch("vesper.vesper.run_analysis_for_pr")
    def test_handle_pr_comment_command_dispatches_merge(self, mock_run_analysis, mock_apply, mock_merge):
        mock_merge.return_value = {"status": "merged"}
        result = handle_pr_comment_command(123, "o/r", 1, " /merge ", "alice")
        self.assertEqual(result, {"status": "merged"})
        mock_merge.assert_called_once_with(123, "o/r", 1, "merge", "alice")
        mock_run_analysis.assert_not_called()
        mock_apply.assert_not_called()

    @patch("vesper.vesper.jsonify", side_effect=lambda payload: payload)
    @patch("vesper.vesper.setup_environment_webhook")
    def test_handle_merge_command_rebase_405_returns_notice_not_500(self, mock_setup_env, _mock_jsonify):
        from vesper.vesper import handle_merge_command

        g = Mock()
        repo = Mock()
        pr = Mock()
        g.get_repo.return_value = repo
        repo.get_collaborator_permission.return_value = "write"
        repo.get_pull.return_value = pr
        mock_setup_env.return_value = (g, "token", Mock())

        pr.merged = False
        pr.mergeable = True
        pr.merge.side_effect = GithubException(
            405,
            {"message": "This branch can't be rebased"},
            None,
        )

        payload, status = handle_merge_command(123, "o/r", 8, "rebase", "alice")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "method_not_allowed")
        pr.create_issue_comment.assert_called()
        body = pr.create_issue_comment.call_args[0][0]
        self.assertIn("Merge method not allowed", body)

    @patch("vesper.vesper.jsonify", side_effect=lambda payload: payload)
    @patch("vesper.vesper.setup_environment_webhook")
    def test_handle_merge_command_blocks_non_collaborator_lookup_failure(self, mock_setup_env, _mock_jsonify):
        from vesper.vesper import handle_merge_command

        g = Mock()
        repo = Mock()
        pr = Mock()
        g.get_repo.return_value = repo
        repo.get_collaborator_permission.side_effect = GithubException(404, {"message": "Not Found"}, None)
        repo.get_pull.return_value = pr
        mock_setup_env.return_value = (g, "token", Mock())

        payload, status = handle_merge_command(123, "o/r", 8, "merge", "external-user")

        self.assertEqual(status, 403)
        self.assertEqual(payload["status"], "forbidden")
        pr.create_issue_comment.assert_called_once()

    @patch("vesper.vesper.post_notice_comment")
    @patch("vesper.vesper.setup_environment_webhook")
    def test_handle_pr_comment_command_help_posts_notice(self, mock_setup_env, mock_post_notice):
        mock_setup_env.return_value = (Mock(), "token", Mock())
        result = handle_pr_comment_command(123, "o/r", 1, "/help", "alice")
        self.assertEqual(result, ({"status": "ok"}, 200))
        mock_post_notice.assert_called_once()

    @patch("vesper.vesper.post_notice_comment")
    @patch("vesper.vesper.setup_environment_webhook")
    def test_handle_pr_comment_command_pause_adds_label(self, mock_setup_env, mock_post_notice):
        g = Mock()
        repo = Mock()
        issue = Mock()
        g.get_repo.return_value = repo
        repo.get_issue.return_value = issue
        issue.get_labels.return_value = []
        mock_setup_env.return_value = (g, "token", Mock())

        result = handle_pr_comment_command(123, "o/r", 1, "/pause", "alice")

        self.assertEqual(result, ({"status": "ok"}, 200))
        issue.add_to_labels.assert_called_once()
        mock_post_notice.assert_called_once()

    @patch("vesper.vesper.ensure_label_exists")
    @patch("vesper.vesper.post_notice_comment")
    @patch("vesper.vesper.setup_environment_webhook")
    def test_handle_pr_comment_command_pause_creates_label_if_missing(
        self, mock_setup_env, mock_post_notice, mock_ensure_label
    ):
        g = Mock()
        repo = Mock()
        issue = Mock()
        g.get_repo.return_value = repo
        repo.get_issue.return_value = issue
        issue.get_labels.return_value = []
        issue.add_to_labels.side_effect = [
            GithubException(404, {"message": "Not Found"}, None),
            None,
        ]
        mock_setup_env.return_value = (g, "token", Mock())

        result = handle_pr_comment_command(123, "o/r", 1, "/pause", "alice")

        self.assertEqual(result, ({"status": "ok"}, 200))
        mock_ensure_label.assert_called_once()
        self.assertEqual(issue.add_to_labels.call_count, 2)
        mock_post_notice.assert_called_once()

    @patch("vesper.vesper.post_notice_comment")
    @patch("vesper.vesper.setup_environment_webhook")
    def test_handle_pr_comment_command_resume_removes_label(self, mock_setup_env, mock_post_notice):
        g = Mock()
        repo = Mock()
        issue = Mock()
        g.get_repo.return_value = repo
        repo.get_issue.return_value = issue
        paused_label = Mock()
        paused_label.name = "vesper:paused"
        issue.get_labels.return_value = [paused_label]
        mock_setup_env.return_value = (g, "token", Mock())

        result = handle_pr_comment_command(123, "o/r", 1, "/resume", "alice")

        self.assertEqual(result, ({"status": "ok"}, 200))
        issue.remove_from_labels.assert_called_once()
        mock_post_notice.assert_called_once()

    @patch("vesper.vesper.post_notice_comment")
    @patch("vesper.vesper.setup_environment_webhook")
    @patch.dict(
        "os.environ",
        {"VERCEL_GIT_COMMIT_SHA": "0123456789abcdef", "VERCEL_GIT_COMMIT_REF": "main"},
        clear=False,
    )
    def test_handle_pr_comment_command_status_shows_label_presence(self, mock_setup_env, mock_post_notice):
        g = Mock()
        repo = Mock()
        issue = Mock()
        pr = Mock()

        g.get_repo.return_value = repo
        repo.get_issue.return_value = issue
        repo.get_pull.return_value = pr

        # Enabled (not paused)
        issue.get_labels.return_value = []
        mock_setup_env.return_value = (g, "token", Mock())

        result = handle_pr_comment_command(123, "o/r", 1, "/status", "alice")

        self.assertEqual(result, ({"status": "ok"}, 200))
        _args, kwargs = mock_post_notice.call_args
        details = kwargs.get("details") if "details" in kwargs else _args[4]
        self.assertIn("Auto analysis is **enabled**", details)
        self.assertIn("Paused label not present", details)
        self.assertIn("Build: `0123456`", details)

        # Paused
        mock_post_notice.reset_mock()
        paused_label = Mock()
        paused_label.name = "vesper:paused"
        issue.get_labels.return_value = [paused_label]

        result = handle_pr_comment_command(123, "o/r", 1, "/status", "alice")

        self.assertEqual(result, ({"status": "ok"}, 200))
        _args, kwargs = mock_post_notice.call_args
        details = kwargs.get("details") if "details" in kwargs else _args[4]
        self.assertIn("Auto analysis is **paused**", details)
        self.assertIn("Paused label present", details)
        self.assertIn("Build: `0123456`", details)

    def test_find_diff_position(self):
        """Test finding position in diff hunk."""
        import textwrap

        diff = textwrap.dedent(
            """\
            diff --git a/test.py b/test.py
            @@ -1,3 +1,3 @@
             old line 1
            -old line 2
            +new line 2
             old line 3"""
        ).strip()
        position = find_diff_position(diff, "test.py", 2)
        self.assertEqual(position, 3)

    @patch("vesper.vesper.load_config")
    def test_load_config_with_authoring_defaults(self, mock_load_config):
        """Test loading config with authoring defaults."""
        with patch("os.path.exists", return_value=False):
            config = load_config()
            self.assertFalse(config["enable_authoring"])
            self.assertFalse(config["auto_commit_suggestions"])
            self.assertFalse(config["create_improvement_prs"])
            self.assertEqual(
                config["improvement_branch_pattern"],
                "vesper-improvements-{timestamp}",
            )

    def test_create_branch_success(self):
        """Test successful branch creation."""
        mock_repo = Mock()
        mock_base_ref = Mock()
        mock_base_ref.object.sha = "abc123"
        mock_new_ref = Mock()
        mock_repo.get_git_ref.side_effect = [Exception(), mock_base_ref, mock_new_ref]

        result = create_branch(mock_repo, "main", "feature-branch")
        mock_repo.create_git_ref.assert_called_once()
        self.assertEqual(result, mock_new_ref)

    def test_apply_suggestions_to_pr(self):
        """Test applying suggestions to PR."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_pr.number = 123
        mock_pr.head.ref = "feature-branch"
        mock_pr.head.sha = "def456"

        mock_ref = Mock()
        mock_repo.get_git_ref.return_value = mock_ref

        suggestions = [
            {
                "path": "test.py",
                "start_line": 1,
                "end_line": 1,
                "op": "replace",
                "suggestion": "new content",
            }
        ]

        # Mock file content
        mock_file = Mock()
        mock_file.decoded_content.decode.return_value = "old content"
        mock_repo.get_contents.return_value = mock_file

        apply_suggestions_to_pr(mock_repo, mock_pr, suggestions)

        # Should create commit with changes
        self.assertTrue(mock_repo.create_git_commit.called)

    def test_apply_suggestions_single_line(self):
        """Test applying a single-line suggestion and verify content transformation."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_pr.number = 123
        mock_pr.head.ref = "feature-branch"
        mock_pr.head.sha = "def456"

        mock_ref = Mock()
        mock_repo.get_git_ref.return_value = mock_ref

        suggestions = [
            {
                "path": "test.py",
                "start_line": 1,
                "end_line": 1,
                "op": "replace",
                "suggestion": "new line content",
            }
        ]

        # Mock file content with multiple lines
        mock_file = Mock()
        mock_file.decoded_content.decode.return_value = "line 1\nline 2\nline 3"
        mock_repo.get_contents.return_value = mock_file

        apply_suggestions_to_pr(mock_repo, mock_pr, suggestions)

        # Verify commit was created
        self.assertTrue(mock_repo.create_git_commit.called)

        # To verify content, check that create_git_blob was called with the transformed content
        # The transformed content should be "new line content\nline 2\nline 3"
        expected_content = "new line content\nline 2\nline 3"
        mock_repo.create_git_blob.assert_called_with(expected_content, "utf-8")

    def test_apply_suggestions_multi_line(self):
        """Test applying a multi-line suggestion."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_pr.number = 123
        mock_pr.head.ref = "feature-branch"
        mock_pr.head.sha = "def456"

        mock_ref = Mock()
        mock_repo.get_git_ref.return_value = mock_ref

        suggestions = [
            {
                "path": "test.py",
                "start_line": 2,
                "end_line": 2,
                "op": "replace",
                "suggestion": "new line 1\nnew line 2\nnew line 3",
            }
        ]

        mock_file = Mock()
        mock_file.decoded_content.decode.return_value = "line 1\nline 2\nline 3"
        mock_repo.get_contents.return_value = mock_file

        apply_suggestions_to_pr(mock_repo, mock_pr, suggestions)

        self.assertTrue(mock_repo.create_git_commit.called)
        # Expected: "line 1\nnew line 1\nnew line 2\nnew line 3\nline 3"
        expected_content = "line 1\nnew line 1\nnew line 2\nnew line 3\nline 3"
        mock_repo.create_git_blob.assert_called_with(expected_content, "utf-8")

    def test_apply_suggestions_out_of_bounds(self):
        """Test applying a suggestion with out-of-bounds line number."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_pr.number = 123
        mock_pr.head.ref = "feature-branch"
        mock_pr.head.sha = "def456"

        mock_ref = Mock()
        mock_repo.get_git_ref.return_value = mock_ref

        suggestions = [
            {
                "path": "test.py",
                "start_line": 10,
                "end_line": 10,
                "op": "replace",
                "suggestion": "new content",
            }
        ]

        mock_file = Mock()
        mock_file.decoded_content.decode.return_value = "line 1\nline 2\nline 3"
        mock_repo.get_contents.return_value = mock_file

        apply_suggestions_to_pr(mock_repo, mock_pr, suggestions)

        # Should not create commit since suggestion is skipped
        self.assertFalse(mock_repo.create_git_commit.called)

    def test_apply_suggestions_deletes_line(self):
        """Delete operations remove the targeted line."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_pr.number = 123
        mock_pr.head.ref = "feature-branch"
        mock_pr.head.sha = "def456"

        mock_ref = Mock()
        mock_repo.get_git_ref.return_value = mock_ref

        suggestions = [
            {
                "path": "test.py",
                "start_line": 2,
                "end_line": 2,
                "op": "delete",
                "suggestion": None,
            }
        ]

        mock_file = Mock()
        mock_file.decoded_content.decode.return_value = "line 1\nline 2\nline 3"
        mock_repo.get_contents.return_value = mock_file

        apply_suggestions_to_pr(mock_repo, mock_pr, suggestions)

        self.assertTrue(mock_repo.create_git_commit.called)
        expected_content = "line 1\nline 3"
        mock_repo.create_git_blob.assert_called_with(expected_content, "utf-8")


if __name__ == "__main__":
    unittest.main()
