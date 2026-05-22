# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

"""
Vesper Apply Module
Handles user-approved application of code suggestions, committed as Vesper.
"""

import logging

# Flask imported conditionally for webhook mode
flask_available = False
try:
    from flask import jsonify

    flask_available = True
except ImportError:
    pass

# Assuming these are imported from vesper
# from vesper.vesper import setup_environment_webhook, get_pr_details_webhook, analyze_with_gemini, parse_code_suggestions, apply_suggestions_to_pr


def handle_apply_comment(installation_id, repo_name, pr_number, commenter_login=None):
    """
    Handle /apply comment on PR: re-analyze and apply suggestions as Vesper.
    """
    if not flask_available:
        logging.error("Flask not available for webhook mode")
        return {"error": "Flask not installed"}, 500

    try:
        from vesper.vesper import (
            analyze_with_gemini,
            apply_suggestions_to_pr,
            build_pr_details_from_pr,
            format_notice,
            get_commenter_permission,
            load_config,
            parse_code_suggestions,
            setup_environment_webhook,
        )

        g, installation_token, client = setup_environment_webhook(installation_id)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        config = load_config()

        if not config.get("enable_authoring", False):
            pr.create_issue_comment(
                format_notice(
                    "Authoring disabled",
                    "The `/apply` command is disabled unless `enable_authoring` is turned on.",
                )
            )
            return jsonify({"status": "forbidden"}), 403

        permission = get_commenter_permission(repo, commenter_login)
        if permission not in {"admin", "write"}:
            pr.create_issue_comment(
                format_notice(
                    "Insufficient permissions",
                    "You need write/admin permissions to use `/apply`.",
                )
            )
            logging.warning(
                f"User {commenter_login or '<unknown>'} lacks permission ({permission}) for /apply on PR #{pr_number}"
            )
            return jsonify({"status": "forbidden"}), 403

        pr_details = build_pr_details_from_pr(pr, installation_token=installation_token)
        analysis = analyze_with_gemini(client, pr_details)
        suggestions = parse_code_suggestions(analysis)

        if suggestions:
            apply_suggestions_to_pr(repo, pr, suggestions)
            # Post confirmation comment
            pr.create_issue_comment("Vesper: Applied\n\n🙂 Applied code suggestions from Vesper analysis.")
            logging.info(f"Applied suggestions to PR #{pr_number} via /apply")
        else:
            # No suggestions
            pr.create_issue_comment("Vesper: No suggestions\n\n😴 No code suggestions were found to apply.")
        return jsonify({"status": "applied"})
    except Exception as e:
        logging.error(f"Error handling apply comment: {str(e)}")
        return jsonify({"error": "Apply failed"}), 500
