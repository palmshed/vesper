# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

"""
Unit tests for Vesper /apply handler.
Run with: python -m pytest test/test_vesper_apply.py
"""

import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

# Ensure repo root is importable so `vesper.*` package imports work.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestVesperApply(unittest.TestCase):
    def test_handle_apply_comment_no_suggestions_does_not_crash(self):
        from vesper import vesper_apply

        # Fake `vesper.vesper` module that `handle_apply_comment` imports at runtime.
        fake_vesper_mod = types.SimpleNamespace()

        g = Mock()
        repo = Mock()
        pr = Mock()
        g.get_repo.return_value = repo
        repo.get_pull.return_value = pr

        fake_vesper_mod.setup_environment_webhook = Mock(return_value=(g, "token", Mock()))
        fake_vesper_mod.load_config = Mock(return_value={"enable_authoring": True})
        fake_vesper_mod.format_notice = Mock(side_effect=lambda title, details: f"{title}: {details}")
        fake_vesper_mod.get_commenter_permission = Mock(return_value="write")
        fake_vesper_mod.build_pr_details_from_pr = Mock(return_value={"number": 1})
        fake_vesper_mod.analyze_with_gemini = Mock(return_value="analysis text")
        fake_vesper_mod.parse_code_suggestions = Mock(return_value=[])
        fake_vesper_mod.apply_suggestions_to_pr = Mock()

        with (
            patch.object(vesper_apply, "flask_available", True),
            patch.object(vesper_apply, "jsonify", lambda obj: obj),
            patch.dict(sys.modules, {"vesper.vesper": fake_vesper_mod}),
        ):
            result = vesper_apply.handle_apply_comment(123, "o/r", 1, commenter_login="alice")

        pr.create_issue_comment.assert_called_once_with("No code suggestions found to apply.")
        fake_vesper_mod.apply_suggestions_to_pr.assert_not_called()
        self.assertEqual(result, {"status": "applied"})

    def test_handle_apply_comment_with_suggestions_applies_and_comments(self):
        from vesper import vesper_apply

        fake_vesper_mod = types.SimpleNamespace()

        g = Mock()
        repo = Mock()
        pr = Mock()
        g.get_repo.return_value = repo
        repo.get_pull.return_value = pr

        fake_vesper_mod.setup_environment_webhook = Mock(return_value=(g, "token", Mock()))
        fake_vesper_mod.load_config = Mock(return_value={"enable_authoring": True})
        fake_vesper_mod.format_notice = Mock(side_effect=lambda title, details: f"{title}: {details}")
        fake_vesper_mod.get_commenter_permission = Mock(return_value="write")
        fake_vesper_mod.build_pr_details_from_pr = Mock(return_value={"number": 1})
        fake_vesper_mod.analyze_with_gemini = Mock(return_value="analysis text")
        fake_vesper_mod.parse_code_suggestions = Mock(return_value=[("a.txt", "1", "change")])
        fake_vesper_mod.apply_suggestions_to_pr = Mock()

        with (
            patch.object(vesper_apply, "flask_available", True),
            patch.object(vesper_apply, "jsonify", lambda obj: obj),
            patch.dict(sys.modules, {"vesper.vesper": fake_vesper_mod}),
        ):
            result = vesper_apply.handle_apply_comment(123, "o/r", 1, commenter_login="alice")

        fake_vesper_mod.apply_suggestions_to_pr.assert_called_once_with(repo, pr, [("a.txt", "1", "change")])
        pr.create_issue_comment.assert_called_once_with("Applied code suggestions from Vesper analysis.")
        self.assertEqual(result, {"status": "applied"})

    def test_handle_apply_comment_rejects_when_authoring_disabled(self):
        from vesper import vesper_apply

        fake_vesper_mod = types.SimpleNamespace()

        g = Mock()
        repo = Mock()
        pr = Mock()
        g.get_repo.return_value = repo
        repo.get_pull.return_value = pr

        fake_vesper_mod.setup_environment_webhook = Mock(return_value=(g, "token", Mock()))
        fake_vesper_mod.load_config = Mock(return_value={"enable_authoring": False})
        fake_vesper_mod.format_notice = Mock(side_effect=lambda title, details: f"{title}: {details}")
        fake_vesper_mod.get_commenter_permission = Mock(return_value="write")
        fake_vesper_mod.build_pr_details_from_pr = Mock()
        fake_vesper_mod.analyze_with_gemini = Mock()
        fake_vesper_mod.parse_code_suggestions = Mock()
        fake_vesper_mod.apply_suggestions_to_pr = Mock()

        with (
            patch.object(vesper_apply, "flask_available", True),
            patch.object(vesper_apply, "jsonify", lambda obj: obj),
            patch.dict(sys.modules, {"vesper.vesper": fake_vesper_mod}),
        ):
            payload, status = vesper_apply.handle_apply_comment(123, "o/r", 1, commenter_login="alice")

        self.assertEqual(status, 403)
        self.assertEqual(payload, {"status": "forbidden"})
        pr.create_issue_comment.assert_called_once()
        fake_vesper_mod.analyze_with_gemini.assert_not_called()
        fake_vesper_mod.apply_suggestions_to_pr.assert_not_called()

    def test_handle_apply_comment_rejects_without_write_permission(self):
        from vesper import vesper_apply

        fake_vesper_mod = types.SimpleNamespace()

        g = Mock()
        repo = Mock()
        pr = Mock()
        g.get_repo.return_value = repo
        repo.get_pull.return_value = pr

        fake_vesper_mod.setup_environment_webhook = Mock(return_value=(g, "token", Mock()))
        fake_vesper_mod.load_config = Mock(return_value={"enable_authoring": True})
        fake_vesper_mod.format_notice = Mock(side_effect=lambda title, details: f"{title}: {details}")
        fake_vesper_mod.get_commenter_permission = Mock(return_value="read")
        fake_vesper_mod.build_pr_details_from_pr = Mock()
        fake_vesper_mod.analyze_with_gemini = Mock()
        fake_vesper_mod.parse_code_suggestions = Mock()
        fake_vesper_mod.apply_suggestions_to_pr = Mock()

        with (
            patch.object(vesper_apply, "flask_available", True),
            patch.object(vesper_apply, "jsonify", lambda obj: obj),
            patch.dict(sys.modules, {"vesper.vesper": fake_vesper_mod}),
        ):
            payload, status = vesper_apply.handle_apply_comment(123, "o/r", 1, commenter_login="alice")

        self.assertEqual(status, 403)
        self.assertEqual(payload, {"status": "forbidden"})
        pr.create_issue_comment.assert_called_once()
        fake_vesper_mod.analyze_with_gemini.assert_not_called()
        fake_vesper_mod.apply_suggestions_to_pr.assert_not_called()

    def test_handle_apply_comment_rejects_non_collaborator_lookup_failure(self):
        from vesper import vesper_apply

        fake_vesper_mod = types.SimpleNamespace()

        g = Mock()
        repo = Mock()
        pr = Mock()
        g.get_repo.return_value = repo
        repo.get_pull.return_value = pr

        fake_vesper_mod.setup_environment_webhook = Mock(return_value=(g, "token", Mock()))
        fake_vesper_mod.load_config = Mock(return_value={"enable_authoring": True})
        fake_vesper_mod.format_notice = Mock(side_effect=lambda title, details: f"{title}: {details}")
        fake_vesper_mod.get_commenter_permission = Mock(return_value=None)
        fake_vesper_mod.build_pr_details_from_pr = Mock()
        fake_vesper_mod.analyze_with_gemini = Mock()
        fake_vesper_mod.parse_code_suggestions = Mock()
        fake_vesper_mod.apply_suggestions_to_pr = Mock()

        with (
            patch.object(vesper_apply, "flask_available", True),
            patch.object(vesper_apply, "jsonify", lambda obj: obj),
            patch.dict(sys.modules, {"vesper.vesper": fake_vesper_mod}),
        ):
            payload, status = vesper_apply.handle_apply_comment(123, "o/r", 1, commenter_login="external-user")

        self.assertEqual(status, 403)
        self.assertEqual(payload, {"status": "forbidden"})
        pr.create_issue_comment.assert_called_once()
        fake_vesper_mod.analyze_with_gemini.assert_not_called()
        fake_vesper_mod.apply_suggestions_to_pr.assert_not_called()
