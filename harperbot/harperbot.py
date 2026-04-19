#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 friday_gemini_ai
"""
GitHub PR Bot that analyzes pull requests using Google's Gemini API.
Supports both CLI and webhook modes.
"""

import argparse
import hashlib
import hmac
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone

import google.genai as genai
import requests
import yaml
from dotenv import load_dotenv
from github import Auth, Github
from github.GithubException import GithubException
from google.genai import errors as genai_errors
from google.genai import types

PAUSE_LABEL = "harperbot:paused"
QUOTA_COOLDOWN_SECONDS = int(os.getenv("HARPERBOT_QUOTA_COOLDOWN_SECONDS", "1800"))
QUOTA_UNTIL_MARKER_RE = re.compile(r"harperbot-quota-until:\s*(\d+)")

try:
    from .rag import fetch_rag_context
except ImportError:
    from rag import fetch_rag_context
ENABLE_RANGE_COMMENTS = os.getenv("HARPERBOT_ENABLE_RANGE_COMMENTS", "0").strip().lower() in {"1", "true", "yes", "on"}

try:
    from .harperbot_apply import handle_apply_comment
except ImportError:
    from harperbot_apply import handle_apply_comment

# Flask imported conditionally for webhook mode
flask_available = False
try:
    from flask import Flask, jsonify, request

    flask_available = True
    app = Flask(__name__)

    @app.route("/webhook", methods=["POST"])
    def webhook():
        return webhook_handler()

except ImportError:
    # Allow non-Flask environments (CLI/tests) to import and call helpers that
    # return JSON-ish payloads.
    def jsonify(payload):  # type: ignore[no-redef]
        return payload

    request = None  # type: ignore[assignment]


def fetch_pr_diff(diff_url: str, token: str | None) -> str:
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        response = requests.get(diff_url, headers=headers, timeout=20)
    except requests.RequestException as e:
        logging.warning(f"Failed to fetch PR diff: {str(e)}")
        return ""

    if response.status_code != 200:
        snippet = (response.text or "").strip().replace("\n", " ")
        if len(snippet) > 200:
            snippet = snippet[:200] + "…"
        logging.warning(f"Failed to fetch PR diff (HTTP {response.status_code}): {snippet}")
        return ""

    return response.text or ""


def get_build_string() -> str:
    """Best-effort build identifier for notices (useful in Vercel)."""
    sha = (
        os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("VERCEL_GITHUB_COMMIT_SHA") or os.getenv("GITHUB_SHA") or ""
    ).strip()
    ref = (os.getenv("VERCEL_GIT_COMMIT_REF") or os.getenv("GITHUB_REF_NAME") or "").strip()
    if sha:
        short = sha[:7]
        return f"Build: `{short}`" + (f" ({ref})" if ref else "")
    if ref:
        return f"Build: ({ref})"
    return ""


def find_diff_position(diff, file_path, line_number):
    """
    Find the position in the diff hunk for a given file and line number.

    Parses the unified diff to locate the hunk containing the specified line,
    then calculates the position within that hunk for inline comments.
    """
    lines = diff.split("\n")
    i = 0
    while i < len(lines):
        # Look for the diff header for the specific file
        if lines[i].startswith("diff --git") and f"b/{file_path}" in lines[i]:
            i += 1  # Skip the header
            # Process hunks for this file
            while i < len(lines):
                if lines[i].startswith("@@"):
                    # Parse hunk header to get starting line in new file
                    match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", lines[i])
                    if match:
                        hunk_start = int(match.group(1))
                        i += 1  # Move to hunk content
                        # Collect all lines in this hunk
                        hunk_lines = []
                        while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("diff --git"):
                            hunk_lines.append(lines[i])
                            i += 1
                        # Find the position of the target line in the hunk
                        # Simulate line numbers in the new file
                        current_line = hunk_start
                        position = 1
                        for line in hunk_lines:
                            if line.startswith("+"):
                                if current_line == line_number:
                                    return position
                                current_line += 1
                            elif line.startswith("-"):
                                # Removed line, no change to current_line
                                pass
                            else:
                                # Context line
                                current_line += 1
                            position += 1
                elif lines[i].startswith("diff --git"):
                    break
                else:
                    i += 1
        else:
            i += 1
    return None  # Line not found in any hunk


def setup_environment():
    """Load environment variables and configure the Gemini API."""
    load_dotenv()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Get GitHub token and API key from environment
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_api_key = os.getenv("HARPERBOT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not github_token or not gemini_api_key:
        logging.error(
            "Missing required environment variables. Ensure GITHUB_TOKEN and GEMINI_API_KEY (or HARPERBOT_GEMINI_API_KEY) are set."
        )
        sys.exit(1)

    # Create Gemini client
    client = genai.Client(api_key=gemini_api_key)
    return github_token, client


def get_pr_details(github_token, repo_name, pr_number):
    """Fetch PR details from GitHub."""
    g = Github(auth=Auth.Token(github_token))
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Get PR details
    files_changed = [f.filename for f in pr.get_files()]
    diff_url = pr.diff_url

    # Get diff content
    diff_content = fetch_pr_diff(diff_url, github_token)

    return {
        "title": pr.title,
        "body": pr.body or "",
        "author": pr.user.login,
        "files_changed": files_changed,
        "diff": diff_content,
        "base": pr.base.ref,
        "head": pr.head.ref,
        "head_sha": pr.head.sha,
        "number": pr_number,
    }


def load_config():
    """
    Load configuration from config.yaml with defaults.

    Supports customization of analysis focus, model, limits, and AI prompt.
    Users can modify config.yaml to change bot behavior without code changes.
    """
    default_prompt = """**Files Changed** ({num_files}):
{files_list}

```diff
{diff_content}
```

{focus_instruction}

Provide a concise code review analysis in this format:

## Summary
[Brief overview of changes and purpose]

### Scores
- Code Quality: [score]/10
- Maintainability: [score]/10
- Security: [score]/10

### Strengths
- [Key positives]
- [What's working well]

### Areas Needing Attention
- [Potential issues or improvements]
- [Be specific and constructive]

### Recommendations
- [Specific suggestions for code, docs, or tests]

### Code Suggestions
- [Provide specific code changes as diff blocks]
- [Use ```diff format for each suggestion]

### Next Steps
- [Actionable items for the author]"""

    default_config = {
        "focus": "all",
        "model": "gemini-2.5-flash",
        "max_diff_length": 4000,
        "temperature": 0.2,
        "max_output_tokens": 8192,
        # When enabled, a manual `/analyze` will post a new PR review even if one already exists
        # for the current head SHA. This can create extra reviews; prefer `/analyze --force-review`
        # for one-off reruns.
        "force_review_on_analyze": False,
        "enable_authoring": False,
        "auto_commit_suggestions": False,
        "create_improvement_prs": False,
        "improvement_branch_pattern": "harperbot-improvements-{timestamp}",
        "prompt": default_prompt,
        "safety_settings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    }

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                user_config = yaml.safe_load(f) or {}
                return {**default_config, **user_config}
            except yaml.YAMLError as e:
                logging.error(f"Error loading config.yaml: {e}")
                return default_config
    return default_config


def analyze_with_gemini(client, pr_details):
    """Analyze the PR using Gemini API."""
    try:
        config = load_config()
        model_name = config.get("model", "gemini-2.5-flash")
        focus = config.get("focus", "all")
        max_diff = config.get("max_diff_length", 4000)
        temperature = config.get("temperature", 0.2)
        max_output_tokens = config.get("max_output_tokens", 8192)
        safety_settings = config.get("safety_settings", [])

        # Auto-select model based on PR complexity
        diff_length = len(pr_details["diff"])
        num_files = len(pr_details["files_changed"])
        if diff_length > 10000 or num_files > 10:
            model_name = "gemini-2.5-flash"  # More powerful model for complex PRs
        # For simple PRs, use the configured model (default gemini-2.5-flash)

        # Use client for selected model

        # Prepare the prompt based on focus
        focus_instructions = {
            "security": "Focus primarily on security concerns, authentication, data handling, and potential vulnerabilities.",
            "performance": "Focus primarily on performance optimizations, efficiency, and potential bottlenecks.",
            "quality": "Focus primarily on code quality, maintainability, readability, and best practices.",
        }
        focus_instruction = focus_instructions.get(focus, "")

        # Use configurable prompt template
        prompt_template = config["prompt"]
        files_list = ", ".join(pr_details["files_changed"])
        diff_content = pr_details["diff"][:max_diff]
        formatted_prompt = prompt_template.format(
            # Preferred placeholders (used by the built-in default prompt)
            num_files=len(pr_details["files_changed"]),
            files_list=files_list,
            diff_content=diff_content,
            # Backward-compatible placeholders (used by harperbot/config.yaml)
            files=files_list,
            diff=diff_content,
            focus_instruction=focus_instruction,
        )

        # Fetch RAG context for current information
        rag_context = fetch_rag_context(pr_details, config)
        if rag_context:
            formatted_prompt = f"{rag_context}\n\n{formatted_prompt}"

        # Generate content with retries for transient failures (5xx, network).
        generate_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            top_k=40,
            max_output_tokens=max_output_tokens,
            safety_settings=safety_settings,
        )

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=formatted_prompt,
                    config=generate_config,
                )
                break
            except genai_errors.ServerError:
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise
            except Exception as e:
                # Retry common transient network failures surfaced as generic exceptions.
                transient_markers = (
                    "timeout",
                    "timed out",
                    "temporarily unavailable",
                    "connection reset",
                    "connection aborted",
                    "connection refused",
                    "name or service not known",
                    "dns",
                )
                if attempt < 2 and any(m in str(e).lower() for m in transient_markers):
                    time.sleep(2**attempt)
                    continue
                raise

        # Handle different response formats
        def extract_text(resp):
            """
            Extract text from Gemini API response object.

            Attempts to extract text from various possible response structures:
            - Direct text attribute
            - Candidates with content parts
            - Direct parts array

            Args:
                resp: The response object from Gemini API

            Returns:
                str: Sanitized extracted text, or None if extraction fails
            """
            try:
                # Try the standard text accessor first
                if getattr(resp, "text", None):
                    text = resp.text.strip()
                    logging.debug(f"Extracted text from direct response.text (length: {len(text)})")
                    # Check if text ends abruptly (might indicate incomplete response)
                    if len(text) > 50 and not text.endswith((".", "!", "?", "\n", "```")):
                        logging.warning(f"Response text appears incomplete - ends with: '{text[-50:]}'")
                    return sanitize_text(text)

                # Try candidates structure (most common for Gemini API)
                candidates = getattr(resp, "candidates", None)
                if candidates:
                    logging.debug(f"Found {len(candidates)} candidates")
                    for i, candidate in enumerate(candidates):
                        content = getattr(candidate, "content", None)
                        if content and getattr(content, "parts", None):
                            parts = [getattr(part, "text", "") for part in content.parts if getattr(part, "text", None)]
                            if parts:
                                text = "\n".join(parts).strip()
                                logging.debug(f"Extracted text from candidate {i} (length: {len(text)})")
                                # Check if text ends abruptly
                                if len(text) > 50 and not text.endswith((".", "!", "?", "\n", "```")):
                                    logging.warning(
                                        f"Response text from candidate {i} appears incomplete - ends with: '{text[-50:]}'"
                                    )
                                return sanitize_text(text)

                # Try direct parts access as fallback
                parts = getattr(resp, "parts", None)
                if parts:
                    parts = [getattr(part, "text", "") for part in parts if getattr(part, "text", None)]
                    if parts:
                        text = "\n".join(parts).strip()
                        logging.debug(f"Extracted text from direct response.parts (length: {len(text)})")
                        # Check if text ends abruptly
                        if len(text) > 50 and not text.endswith((".", "!", "?", "\n", "```")):
                            logging.warning(f"Response text from direct parts appears incomplete - ends with: '{text[-50:]}'")
                        return sanitize_text(text)

                logging.warning("No text found in any response structure")
            except Exception as extract_error:
                logging.error(f"Error during text extraction: {str(extract_error)}")
                return None

            return None

        def sanitize_text(text):
            """Comprehensive sanitization of extracted text for security."""
            if not text:
                return text
            # Remove potentially dangerous patterns
            text = re.sub(r"</?script[^>]*>", "", text, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "", text)  # Remove all HTML tags
            text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
            text = re.sub(r"on\w+\s*=", "", text, flags=re.IGNORECASE)  # Remove event handlers
            # Keep the character cap aligned with the configured token budget.
            max_sanitized_chars = max(20000, max_output_tokens * 4)
            if len(text) > max_sanitized_chars:
                logging.warning(
                    "Sanitized Gemini response exceeded %s chars; truncating to fit downstream limits",
                    max_sanitized_chars,
                )
                text = text[:max_sanitized_chars] + "... (truncated for length)"
            return text.strip()

        try:
            text = extract_text(response)
            if text:
                # Additional check for potentially incomplete responses
                if len(text) < 100 and not any(
                    indicator in text.lower() for indicator in ["analysis", "review", "summary", "changes"]
                ):
                    logging.warning(f"Response seems too short and may be incomplete (length: {len(text)}): {text[:200]}")
                return text

            # Check for finish reasons that indicate truncation or issues
            candidates = getattr(response, "candidates", None)
            if candidates:
                for candidate in candidates:
                    finish_reason = getattr(candidate, "finish_reason", None)
                    if finish_reason:
                        finish_str = str(finish_reason).upper()
                        if "MAX" in finish_str and "TOKEN" in finish_str:
                            logging.warning(f"Analysis truncated due to token limit (finish_reason: {finish_reason})")
                            return "Analysis truncated due to token limit. The code changes are too extensive for a complete analysis. Please review manually or split into smaller PRs."
                        elif "SAFETY" in finish_str:
                            logging.warning(f"Analysis blocked due to safety filters (finish_reason: {finish_reason})")
                            return "Analysis blocked due to content safety filters. Please ensure the PR content complies with usage policies."
                        elif "STOP" in finish_str:
                            logging.info(f"Analysis completed normally (finish_reason: {finish_reason})")
                        else:
                            logging.warning(f"Unexpected finish_reason: {finish_reason}")

            # If we get here, no text found - log and return safe message
            logging.warning(f"No text extracted from response. Response type: {type(response)}")
            return "Unable to generate analysis due to an unexpected response format. Please try again or review the code manually."

        except Exception as e:
            # Log the error and return safe info
            logging.error(f"Error processing Gemini response: {str(e)}")
            return f"Error processing response: {str(e)}\n\nResponse type: {type(response)}"

    except Exception as e:
        context = (
            f" (PR: {pr_details.get('title', 'Unknown')}, Model: {model_name}, Diff length: {len(pr_details.get('diff', ''))})"
        )

        # Prefer structured API errors when available (google-genai).
        if isinstance(e, genai_errors.ClientError):
            code = getattr(e, "code", None)
            status = getattr(e, "status", None)
            message = getattr(e, "message", None)
            lower_message = (message or str(e)).lower()

            if code == 429 or "quota" in lower_message or "rate limit" in lower_message or "billing" in lower_message:
                logging.exception(f"API quota/rate limit error{context}: {str(e)}")
                return f"Error generating analysis: API quota exceeded{context}. Please check your billing or try again later."

            if (
                code in (401, 403)
                or "api key" in lower_message
                or "authentication" in lower_message
                or "unauthorized" in lower_message
            ):
                logging.exception(f"API authentication error{context}: {str(e)}")
                return (
                    "Error generating analysis: Invalid API key or authentication failed"
                    f"{context}. Please check your GEMINI_API_KEY or HARPERBOT_GEMINI_API_KEY."
                )

            if code == 404 or "model" in lower_message or "not found" in lower_message:
                logging.exception(f"Model error{context}: {str(e)}")
                return f"Error generating analysis: Requested model not available{context}. Please try again later."

            logging.exception(f"API client error{context}: {str(e)}")
            details = f" (HTTP {code} {status})" if code else ""
            return f"Error generating analysis: API request failed{details}{context}. Please try again later."

        if isinstance(e, genai_errors.ServerError):
            code = getattr(e, "code", None)
            status = getattr(e, "status", None)
            details = f" (HTTP {code} {status})" if code else ""
            logging.exception(f"API server error{context}: {str(e)}")
            return f"Error generating analysis: API unavailable{details}{context}. Please try again later."

        error_msg = str(e).lower()
        if "quota" in error_msg or "rate limit" in error_msg or "billing" in error_msg:
            logging.error(f"API quota/rate limit error{context}: {str(e)}")
            return f"Error generating analysis: API quota exceeded{context}. Please check your billing or try again later."
        elif "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
            logging.error(f"API authentication error{context}: {str(e)}")
            return (
                "Error generating analysis: Invalid API key or authentication failed"
                f"{context}. Please check your GEMINI_API_KEY or HARPERBOT_GEMINI_API_KEY."
            )
        elif "model" in error_msg or "not found" in error_msg:
            logging.error(f"Model error{context}: {str(e)}")
            return f"Error generating analysis: Requested model not available{context}. Please try again later."
        else:
            logging.error(f"Unexpected API error{context}: {str(e)}")
            error_type = type(e).__name__
            return f"Error generating analysis: API unavailable ({error_type}){context}. Please try again later."


def parse_diff_for_suggestions(diff_text):
    """Parse a diff block into structured suggestion operations.

    Supports two common formats:

    1) Standard unified diff headers:
       --- a/path
       +++ b/path
       @@ -old +new @@

    2) The simplified format HarperBot asks the model to emit:
       path
       @@ -old +new @@
       - old
       + new

    Returns a list of dicts:
      - path: str
      - start_line: int (1-based, against the *current* file the patch applies to)
      - end_line: int (inclusive; equals start_line for inserts)
      - op: "replace" | "insert" | "delete"
      - suggestion: str | None (replacement text for replace/insert)
    """
    lines = diff_text.strip().split("\n")
    if not lines:
        return None

    file_path = None
    start_idx = 0
    if lines[0].startswith("--- a/"):
        file_path = lines[0][6:]
        start_idx = 0
    else:
        candidate = lines[0].strip()
        if candidate and not candidate.startswith("@@") and not candidate.startswith(("+", "-", "diff --git")):
            file_path = candidate
            start_idx = 1

    if not file_path:
        return None

    suggestions = []
    in_hunk = False
    old_line = 0
    pending_plus_lines = []
    pending_anchor_line_num = None
    pending_minus_line_num = None
    pending_minus_count = 0

    def flush_pending():
        nonlocal pending_plus_lines, pending_anchor_line_num, pending_minus_line_num, pending_minus_count
        if pending_plus_lines and pending_anchor_line_num is not None:
            # Treat (- then +) as a replacement at the first removed line.
            # If there are no '-' lines, this is an insertion anchored at the current old_line.
            if pending_minus_count:
                op = "replace"
                start_line_num = pending_minus_line_num
                end_line_num = pending_minus_line_num + pending_minus_count - 1
            else:
                op = "insert"
                start_line_num = pending_anchor_line_num
                end_line_num = pending_anchor_line_num
            suggestions.append(
                {
                    "path": file_path,
                    "start_line": start_line_num,
                    "end_line": end_line_num,
                    "op": op,
                    "suggestion": "\n".join(pending_plus_lines),
                }
            )
            pending_plus_lines = []
            pending_anchor_line_num = None
            pending_minus_line_num = None
            pending_minus_count = 0
            return

        if pending_minus_count and pending_minus_line_num is not None:
            suggestions.append(
                {
                    "path": file_path,
                    "start_line": pending_minus_line_num,
                    "end_line": pending_minus_line_num + pending_minus_count - 1,
                    "op": "delete",
                    "suggestion": None,
                }
            )
        pending_minus_line_num = None
        pending_minus_count = 0

    for line in lines[start_idx:]:
        if line.startswith("@@"):
            flush_pending()
            match = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if not match:
                in_hunk = False
                continue
            in_hunk = True
            old_line = int(match.group(1))
            continue

        if not in_hunk:
            continue

        if line.startswith("+"):
            if pending_anchor_line_num is None:
                pending_anchor_line_num = pending_minus_line_num if pending_minus_line_num is not None else old_line
            pending_plus_lines.append(line[1:])
            continue

        if line.startswith("-"):
            if pending_minus_line_num is None:
                pending_minus_line_num = old_line
            pending_minus_count += 1
            old_line += 1
            continue

        # Context line (or an unprefixed line treated as context)
        flush_pending()
        old_line += 1

    flush_pending()
    return suggestions or None


def format_comment(analysis, sha=None):
    """Format the analysis with proper markdown and emojis."""
    sha_marker = f"\n<!-- harperbot-sha: {sha} -->" if sha else ""
    return f"""<details>
<summary>HarperBot</summary>

{analysis}

{sha_marker}
</details>
"""


def parse_code_suggestions(analysis):
    """
    Parse code suggestions from analysis text.

    Extracts diff blocks and parses them into structured operations.
    """
    diff_blocks = []
    start_pos = 0
    while True:
        start_pos = analysis.find("```diff\n", start_pos)
        if start_pos == -1:
            break
        end_pos = analysis.find("\n```", start_pos + 8)
        if end_pos == -1:
            break
        diff_text = analysis[start_pos + 8 : end_pos]
        diff_blocks.append(diff_text)
        start_pos = end_pos + 4
    suggestions: list[dict] = []
    for diff_text in diff_blocks:
        parsed = parse_diff_for_suggestions(diff_text)
        if not parsed:
            continue
        suggestions.extend(parsed)
    return suggestions


def create_branch(repo, base_branch, new_branch_name):
    """
    Create a new branch from the base branch.

    Args:
        repo: GitHub repository object
        base_branch: Name of the base branch (e.g., 'main')
        new_branch_name: Name for the new branch

    Returns:
        The created branch reference
    """
    try:
        # Check if branch already exists
        try:
            existing_ref = repo.get_git_ref(f"heads/{new_branch_name}")
            logging.warning(f"Branch '{new_branch_name}' already exists, using existing")
            return existing_ref
        except Exception:
            pass  # Branch doesn't exist, create it

        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=base_ref.object.sha)
        logging.info(f"Created branch '{new_branch_name}' from '{base_branch}'")
        return repo.get_git_ref(f"heads/{new_branch_name}")
    except Exception as e:
        logging.error(f"Error creating branch '{new_branch_name}': {str(e)}")
        raise


def create_commit_with_changes(repo, branch_ref, changes, commit_message):
    """
    Create a commit with the given file changes.

    Args:
        repo: GitHub repository object
        branch_ref: Branch reference to commit to
        changes: Dict of {file_path: new_content}
        commit_message: Commit message

    Returns:
        The created commit
    """
    try:
        # Get the current tree
        current_commit = repo.get_git_commit(branch_ref.object.sha)
        current_tree = repo.get_git_tree(current_commit.sha)

        # Create blobs for new/updated files
        new_blobs = []
        for file_path, content in changes.items():
            blob = repo.create_git_blob(content, "utf-8")
            new_blobs.append({"path": file_path, "mode": "100644", "type": "blob", "sha": blob.sha})  # Regular file

        # Create new tree
        tree = repo.create_git_tree(new_blobs, base_tree=current_tree)
        author = {
            "name": "HarperBot",
            "email": "236089746+harper-bot-glitch@users.noreply.github.com",
        }
        commit = repo.create_git_commit(commit_message, tree, [current_commit], author=author)
        branch_ref.edit(commit.sha)
        logging.info(f"Created commit with {len(changes)} file changes")
        return commit
    except Exception as e:
        logging.error(f"Error creating commit: {str(e)}")
        raise


def create_improvement_pr(repo, head_branch, base_branch, title, body):
    """
    Create a pull request with improvements.

    Args:
        repo: GitHub repository object
        head_branch: Branch with improvements
        base_branch: Target branch
        title: PR title
        body: PR description

    Returns:
        The created pull request
    """
    try:
        pr = repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
        logging.info(f"Created improvement PR #{pr.number}: {title}")
        return pr
    except Exception as e:
        logging.error(f"Error creating PR: {str(e)}")
        raise


def apply_suggestions_to_pr(repo, pr, suggestions):
    """
    Apply code suggestions directly to the PR branch.

    Args:
        repo: GitHub repository object
        pr: Pull request object
        suggestions: List of suggestion operation dicts from parse_code_suggestions()
    """
    try:
        from collections import defaultdict

        # Get PR head branch
        head_ref = repo.get_git_ref(f"heads/{pr.head.ref}")

        # Group suggestions by file
        suggestion_groups = defaultdict(list)
        for sugg in suggestions or []:
            file_path = sugg.get("path")
            start_line = sugg.get("start_line")
            end_line = sugg.get("end_line")
            op = sugg.get("op")
            suggestion_text = sugg.get("suggestion")

            if not file_path or not isinstance(start_line, int) or not isinstance(end_line, int) or not op:
                continue
            suggestion_groups[file_path].append((start_line, end_line, op, suggestion_text))

        # Apply suggestions per file
        changes = {}
        for file_path, suggs in suggestion_groups.items():
            # Get current file content
            try:
                file_content = repo.get_contents(file_path, ref=pr.head.sha)
                current_content = file_content.decoded_content.decode("utf-8")
            except Exception:
                # File doesn't exist, create it
                current_content = ""

            lines = current_content.split("\n")

            # Sort suggestions by line number
            suggs.sort(key=lambda x: (x[0], x[1]))

            offset = 0
            applied = False
            for start_line, end_line, op, suggestion_text in suggs:
                adjusted_start = start_line - 1 + offset  # 0-based
                adjusted_end = end_line - 1 + offset

                if op == "insert":
                    # Insertion is anchored at a single line; insert before it (or at end if beyond).
                    insert_at = max(0, min(adjusted_start, len(lines)))
                    new_lines = (suggestion_text or "").split("\n")
                    lines = lines[:insert_at] + new_lines + lines[insert_at:]
                    offset += len(new_lines)
                    applied = True
                    continue

                if (
                    not (0 <= adjusted_start < len(lines))
                    or not (0 <= adjusted_end < len(lines))
                    or adjusted_end < adjusted_start
                ):
                    logging.warning(
                        f"Suggestion for {file_path}:{start_line}-{end_line} is out of bounds "
                        f"(adjusted {adjusted_start}-{adjusted_end}), skipping"
                    )
                    continue

                if op == "delete":
                    old_len = adjusted_end - adjusted_start + 1
                    lines = lines[:adjusted_start] + lines[adjusted_end + 1 :]
                    offset -= old_len
                    applied = True
                    continue

                # replace
                new_lines = (suggestion_text or "").split("\n")
                old_len = adjusted_end - adjusted_start + 1
                lines = lines[:adjusted_start] + new_lines + lines[adjusted_end + 1 :]
                offset += len(new_lines) - old_len
                applied = True

            if applied:
                changes[file_path] = "\n".join(lines)

        if changes:
            create_commit_with_changes(
                repo,
                head_ref,
                changes,
                "Apply code suggestions from HarperBot analysis",
            )
            logging.info(f"Applied {len(suggestion_groups)} file changes to PR #{pr.number}")
    except Exception as e:
        logging.error(f"Error applying suggestions to PR: {str(e)}")


def create_improvement_pr_from_analysis(repo, pr_details, analysis, config):
    """
    Create an improvement PR with additional suggestions beyond the original PR.

    Args:
        repo: GitHub repository object
        pr_details: PR details dict
        analysis: Full analysis text
        config: Configuration dict
    """
    try:
        import time

        timestamp = str(int(time.time()))

        # Generate branch name
        branch_pattern = config.get("improvement_branch_pattern", "harperbot-improvements-{timestamp}")
        branch_name = branch_pattern.replace("{timestamp}", timestamp).replace("{pr_number}", str(pr_details["number"]))

        # Create branch from main/master
        base_branch = pr_details.get("base", "main")
        branch_ref = create_branch(repo, base_branch, branch_name)

        # Create an initial empty commit to allow PR creation
        create_commit_with_changes(repo, branch_ref, {}, "Initial commit for HarperBot improvements")

        # For now, create an empty improvement PR (could be extended to include actual improvements)
        title = f"HarperBot Improvements for PR #{pr_details['number']}"
        body = f"""## HarperBot Improvement Suggestions

This PR contains additional improvements suggested by HarperBot analysis of PR #{pr_details["number"]}.

### Analysis Summary
{analysis[:1000]}...

---
*Generated by HarperBot*"""

        create_improvement_pr(repo, branch_name, base_branch, title, body)

    except Exception as e:
        logging.error(f"Error creating improvement PR: {str(e)}")


def update_main_comment(analysis):
    """
    Update the main comment by replacing the code suggestions section.
    """
    start_pos = analysis.find("### Code Suggestions\n")
    if start_pos == -1:
        return analysis
    end_pos = analysis.find("###", start_pos + 21)
    if end_pos == -1:
        end_pos = len(analysis)
    return analysis[:start_pos] + "### Code Suggestions\n- Suggestions posted as inline comments below.\n" + analysis[end_pos:]


def post_inline_suggestions(pr, pr_details, suggestions, g, repo, *, force_review: bool = False):
    """
    Post inline code suggestions as a pull request review.
    """
    try:
        head_sha = pr_details["head_sha"]

        # Check if we already posted a review for this exact commit
        # We'll look for reviews that include the harperbot marker.
        for review in pr.get_reviews():
            if f"harperbot-sha: {head_sha}" in (review.body or ""):
                if not force_review:
                    logging.info(f"Skipping inline suggestions for SHA {head_sha}: Review already exists")
                    return
                logging.info(f"Existing review found for SHA {head_sha}; force-posting a new review")
                break

        commit = repo.get_commit(head_sha)
        review_comments = []
        for sugg in suggestions or []:
            file_path = sugg.get("path")
            start_line = sugg.get("start_line")
            end_line = sugg.get("end_line")
            op = sugg.get("op")
            suggestion_text = sugg.get("suggestion")

            if not file_path or not isinstance(start_line, int) or not isinstance(end_line, int):
                logging.warning(f"Invalid suggestion payload for inline comment: {sugg!r}. Skipping.")
                continue

            if op == "delete":
                body = "Suggested deletion."
            else:
                body = f"```suggestion\n{suggestion_text or ''}\n```"

            comment = {"path": file_path, "body": body}
            if ENABLE_RANGE_COMMENTS and end_line > start_line:
                comment.update(
                    {
                        "start_line": start_line,
                        "start_side": "RIGHT",
                        "line": end_line,
                        "side": "RIGHT",
                    }
                )
            else:
                comment.update({"line": start_line, "side": "RIGHT"})
            review_comments.append(comment)

        review_body = f"HarperBot Analysis for {head_sha}\n<!-- harperbot-sha: {head_sha} -->"

        if not review_comments:
            # Still create a review so it shows up in the PR review timeline.
            pr.create_review(commit=commit, body=review_body, event="COMMENT")
            logging.info("Posted a review without inline suggestions")
            return

        try:
            pr.create_review(
                commit=commit,
                body=review_body,
                comments=review_comments,
                event="COMMENT",
            )
            logging.info(f"Posted {len(review_comments)} inline suggestions as a review")
        except Exception as e:
            # Fallback to legacy `position` field if the API rejects line-based comments.
            logging.warning(f"Line-based review comments failed, retrying with diff positions: {str(e)}")
            position_comments = []
            for sugg in suggestions or []:
                file_path = sugg.get("path")
                start_line = sugg.get("start_line")
                op = sugg.get("op")
                suggestion_text = sugg.get("suggestion")
                if not file_path or not isinstance(start_line, int):
                    continue

                position = find_diff_position(pr_details.get("diff", ""), file_path, start_line)
                if position is None:
                    continue
                body = "Suggested deletion." if op == "delete" else f"```suggestion\n{suggestion_text or ''}\n```"
                position_comments.append({"path": file_path, "position": position, "body": body})

            if position_comments:
                pr.create_review(
                    commit=commit,
                    body=review_body,
                    comments=position_comments,
                    event="COMMENT",
                )
                logging.info(f"Posted {len(position_comments)} inline suggestions as a review (position fallback)")
            else:
                pr.create_review(commit=commit, body=review_body, event="COMMENT")
                logging.info("Posted a review without inline suggestions (fallback)")
    except Exception as e:
        logging.error(f"Error posting review with suggestions: {str(e)}")
        # Don't fail the whole process for review posting errors


def verify_webhook_signature(payload, signature, secret):
    """
    Verify GitHub webhook signature for security.

    Uses HMAC-SHA256 to ensure the webhook payload hasn't been tampered with.
    This prevents malicious requests from triggering analysis.

    Args:
        payload: Raw request body bytes
        signature: GitHub signature header (sha256=...)
        secret: Webhook secret configured in GitHub App

    Returns:
        bool: True if signature is valid
    """
    if not signature or not secret:
        return False

    # Verify signature contains "=" and has valid format
    if "=" not in signature:
        return False

    parts = signature.split("=", 1)
    if len(parts) != 2:
        return False

    sha_name, sig = parts
    if sha_name != "sha256" or not sig:
        return False

    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), sig)


def setup_environment_webhook(installation_id):
    """
    Setup environment for webhook mode using GitHub App authentication.

    Generates an installation token for the specific repository installation.
    This provides secure, scoped access without storing long-lived tokens.
    """
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    gemini_api_key = os.getenv("HARPERBOT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    app_id = os.getenv("HARPER_BOT_APP_ID")
    private_key = os.getenv("HARPER_BOT_PRIVATE_KEY")

    if not gemini_api_key or not app_id or not private_key:
        logging.error(
            "Missing required environment variables for webhook mode (HARPERBOT_GEMINI_API_KEY or GEMINI_API_KEY, HARPER_BOT_APP_ID, HARPER_BOT_PRIVATE_KEY)"
        )
        raise ValueError("Missing required environment variables")

    client = genai.Client(api_key=gemini_api_key)

    # Generate installation-specific token
    auth = Auth.AppAuth(app_id, private_key)
    installation_auth = auth.get_installation_auth(installation_id)
    g = Github(auth=installation_auth)
    return g, installation_auth.token, client


def build_pr_details_from_pr(pr, installation_token: str | None = None):
    """Build normalized PR details from an existing pull request object."""
    files_changed = [f.filename for f in pr.get_files()]

    # Get diff content using diff_url
    diff_content = fetch_pr_diff(pr.diff_url, installation_token)

    return {
        "title": pr.title,
        "body": pr.body or "",
        "author": pr.user.login,
        "files_changed": files_changed,
        "diff": diff_content,
        "base": pr.base.ref,
        "head": pr.head.ref,
        "head_sha": pr.head.sha,
        "number": pr.number,
    }


def get_pr_details_webhook(g, repo_name, pr_number, installation_token: str | None = None):
    """Fetch PR details using GitHub App authentication."""
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return build_pr_details_from_pr(pr, installation_token=installation_token)


def is_harperbot_comment(comment):
    """Identify HarperBot comments by the known summary marker."""
    return "<summary>HarperBot</summary>" in (comment.body or "")


def post_comment_webhook(
    github_token: str,
    repo_name: str,
    pr_details: dict,
    analysis: str,
    *,
    manual: bool = False,
    force_review: bool = False,
):
    """
    Post analysis comment and inline suggestions using GitHub App auth.

    Updates the existing main comment with the analysis summary if it exists,
    otherwise creates a new one. Posts code suggestions as inline review comments.
    """
    try:
        g = Github(auth=Auth.Token(github_token))
        config = load_config()
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_details["number"])

        suggestions = parse_code_suggestions(analysis)
        main_comment = update_main_comment(analysis)
        formatted_comment = format_comment(main_comment, sha=pr_details.get("head_sha"))

        # Find existing HarperBot comment to update
        existing_comment = None
        for comment in pr.get_issue_comments():
            if is_harperbot_comment(comment):
                existing_comment = comment
                break

        if existing_comment:
            existing_comment.edit(formatted_comment)
            logging.info(f"Updated existing analysis comment for PR #{pr_details['number']}")
        else:
            pr.create_issue_comment(formatted_comment)
            logging.info(f"Posted new analysis comment to PR #{pr_details['number']}")

        # Post inline suggestions (as a Review)
        effective_force_review = force_review or (manual and bool(config.get("force_review_on_analyze", False)))
        post_inline_suggestions(pr, pr_details, suggestions, g, repo, force_review=effective_force_review)

        # Apply authoring features if enabled
        if config.get("enable_authoring", False):
            if config.get("auto_commit_suggestions", False) and suggestions:
                apply_suggestions_to_pr(repo, pr, suggestions)

            if config.get("create_improvement_prs", False):
                create_improvement_pr_from_analysis(repo, pr_details, analysis, config)

    except Exception as e:
        logging.error(f"Error posting comment to PR #{pr_details.get('number', 'unknown')}: {str(e)}")
        raise


def format_notice(title: str, details: str) -> str:
    # Notice comments should not include the SHA marker to avoid being treated as successful analysis
    return f"""⚠️ **HarperBot Notice: {title}**

{details}
"""


def post_notice_comment(github_token: str, repo_name: str, pr_number: int, title: str, details: str):
    g = Github(auth=Auth.Token(github_token))
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(format_notice(title, details))


def run_analysis_for_pr(
    installation_id: int,
    repo_name: str,
    pr_number: int,
    *,
    force: bool = False,
    force_review: bool = False,
):
    """Fetch PR details, run analysis, and post comments for a PR.

    Args:
        force: If True, re-run analysis even when an analysis already exists for
            the current PR head SHA (useful for manual `/analyze` requests).
    """
    g, installation_token, client = setup_environment_webhook(installation_id)
    pr_details = get_pr_details_webhook(g, repo_name, pr_number, installation_token=installation_token)
    head_sha = pr_details.get("head_sha")

    if not force:
        try:
            repo = g.get_repo(repo_name)
            issue = repo.get_issue(number=pr_number)
            paused = any((label.name == PAUSE_LABEL) for label in issue.get_labels())
            if paused:
                logging.info(f"Skipping analysis for PR #{pr_number}: paused via label '{PAUSE_LABEL}'")
                return

            pr = repo.get_pull(pr_number)
            quota_until = get_quota_cooldown_until(pr)
            if quota_until is not None and time.time() < quota_until:
                until_iso = datetime.fromtimestamp(quota_until, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                logging.info(f"Skipping analysis for PR #{pr_number}: quota cooldown until {until_iso}")
                return
        except Exception as e:
            # Do not hard-fail analysis for label lookup issues.
            logging.warning(f"Pause label check failed for PR #{pr_number}: {str(e)}")

    # De-duplication check: Skip ONLY if analysis already exists for this EXACT commit SHA
    if not force:
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        for comment in pr.get_issue_comments():
            if f"harperbot-sha: {head_sha}" in (comment.body or ""):
                logging.info(f"Skipping analysis for PR #{pr_number}: Analysis already exists for SHA {head_sha}")
                return

    if not pr_details.get("files_changed"):
        post_notice_comment(
            installation_token,
            repo_name,
            pr_number,
            "No files changed",
            "This PR has no file changes to analyze.",
        )
        return
    if not pr_details.get("diff"):
        post_notice_comment(
            installation_token,
            repo_name,
            pr_number,
            "Empty diff",
            "HarperBot could not find a diff to analyze.",
        )
        return
    analysis = analyze_with_gemini(client, pr_details)
    if not analysis:
        post_notice_comment(
            installation_token,
            repo_name,
            pr_number,
            "No analysis output",
            "HarperBot did not receive a response from the model.",
        )
        return

    if is_quota_exceeded_message(analysis):
        quota_until = int(time.time()) + max(0, QUOTA_COOLDOWN_SECONDS)
        until_iso = datetime.fromtimestamp(quota_until, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        post_notice_comment(
            installation_token,
            repo_name,
            pr_number,
            "Gemini quota exceeded",
            (
                "HarperBot hit a Gemini quota/rate limit and will pause auto-analysis for this PR.\n\n"
                f"Auto-analysis resumes after: **{until_iso}**\n\n"
                "You can retry immediately with `/analyze`.\n\n"
                f"<!-- harperbot-quota-until: {quota_until} -->"
            ),
        )
        logging.warning(f"Quota exceeded for PR #{pr_number}; cooldown until {until_iso}")
        return

    post_comment_webhook(
        installation_token,
        repo_name,
        pr_details,
        analysis,
        manual=force,
        force_review=force_review,
    )


def handle_pr_comment_command(
    installation_id: int,
    repo_name: str,
    pr_number: int,
    comment_body: str,
    commenter_login: str,
):
    """Handle slash-commands posted as PR comments.

    Supports both PR conversation comments (issue_comment events) and inline
    "Files changed" comments (pull_request_review_comment events).
    """
    raw_command = (comment_body or "").strip()
    command_parts = raw_command.split()
    command = (command_parts[0] if command_parts else "").lower()
    command_args = {part.lower() for part in command_parts[1:]}

    if command == "/apply":
        return handle_apply_comment(installation_id, repo_name, pr_number, commenter_login=commenter_login)
    if command == "/analyze":
        logging.info(f"Processing /analyze for PR #{pr_number} in {repo_name}")
        force_review = ("--force-review" in command_args) or ("--force_review" in command_args)
        try:
            run_analysis_for_pr(
                installation_id,
                repo_name,
                pr_number,
                force=True,
                force_review=force_review,
            )
            return {"status": "ok"}, 200
        except Exception as e:
            logging.error(f"Error processing /analyze: {str(e)}")
            return {"error": "Processing failed"}, 500
    if command in {"/pause", "/resume", "/status"}:
        g, installation_token, _ = setup_environment_webhook(installation_id)
        repo = g.get_repo(repo_name)
        issue = repo.get_issue(number=pr_number)
        label_names = {label.name for label in issue.get_labels()}
        is_paused = PAUSE_LABEL in label_names

        if command == "/pause":
            if not is_paused:
                try:
                    issue.add_to_labels(PAUSE_LABEL)
                except GithubException:
                    ensure_label_exists(repo, PAUSE_LABEL)
                    issue.add_to_labels(PAUSE_LABEL)
            post_notice_comment(
                installation_token,
                repo_name,
                pr_number,
                "Paused",
                f"Auto analysis is paused for this PR.\n\nUse `/resume` to turn it back on.\n\nLabel: `{PAUSE_LABEL}`",
            )
            return {"status": "ok"}, 200

        if command == "/resume":
            if is_paused:
                try:
                    issue.remove_from_labels(PAUSE_LABEL)
                except GithubException:
                    # If the label was deleted/renamed, treat it as already resumed.
                    pass
            post_notice_comment(
                installation_token,
                repo_name,
                pr_number,
                "Resumed",
                f"Auto analysis is enabled for this PR.\n\nUse `/pause` to pause again.\n\nLabel: `{PAUSE_LABEL}`",
            )
            return {"status": "ok"}, 200

        # /status
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        quota_until = get_quota_cooldown_until(pr)
        quota_msg = ""
        if quota_until is not None and time.time() < quota_until:
            until_iso = datetime.fromtimestamp(quota_until, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            quota_msg = f"\n\nQuota cooldown active until: **{until_iso}**"

        state = "paused" if is_paused else "enabled"
        label_msg = f"Paused label present: `{PAUSE_LABEL}`" if is_paused else f"Paused label not present: `{PAUSE_LABEL}`"
        build_msg = get_build_string()
        build_line = f"\n\n{build_msg}" if build_msg else ""
        post_notice_comment(
            installation_token,
            repo_name,
            pr_number,
            "Status",
            f"Auto analysis is **{state}** for this PR.{quota_msg}\n\n{label_msg}{build_line}",
        )
        return {"status": "ok"}, 200
    if command == "/help":
        _, installation_token, _ = setup_environment_webhook(installation_id)
        help_text = """
**HarperBot Capabilities**

- Automatic analysis on PR open/reopen
- Manual analysis: `/analyze`
- Apply suggestions: `/apply`
- Pause/resume auto analysis: `/pause`, `/resume`, `/status`
- Merge commands (write/admin only): `/merge`, `/squash`, `/rebase`
""".strip()
        post_notice_comment(
            installation_token,
            repo_name,
            pr_number,
            "Help",
            help_text,
        )
        return {"status": "ok"}, 200
    if command == "/merge":
        return handle_merge_command(installation_id, repo_name, pr_number, "merge", commenter_login)
    if command == "/squash":
        return handle_merge_command(installation_id, repo_name, pr_number, "squash", commenter_login)
    if command == "/rebase":
        return handle_merge_command(installation_id, repo_name, pr_number, "rebase", commenter_login)
    return {"status": "ignored"}, 200


def is_quota_exceeded_message(analysis: str) -> bool:
    text = (analysis or "").lower()
    return "api quota exceeded" in text or "rate limit" in text or "quota" in text and "exceeded" in text


def get_quota_cooldown_until(pr) -> int | None:
    """Return a unix timestamp until which auto-analysis should be skipped."""
    latest = None
    try:
        for comment in pr.get_issue_comments():
            body = comment.body or ""
            match = QUOTA_UNTIL_MARKER_RE.search(body)
            if not match:
                continue
            try:
                value = int(match.group(1))
            except ValueError:
                continue
            if latest is None or value > latest:
                latest = value
    except Exception:
        return None
    return latest


def ensure_label_exists(repo, name: str):
    """Ensure a repository label exists (best-effort)."""
    try:
        # If it already exists, GitHub will return 422 on create; swallow it.
        repo.create_label(name=name, color="6e7681", description="HarperBot control label")
    except GithubException as e:
        status = getattr(e, "status", None)
        if status in {422, 409}:
            return
        raise


def get_commenter_permission(repo, commenter_login: str | None):
    """Best-effort collaborator permission lookup for slash-command authorization."""
    if not commenter_login:
        return None

    try:
        return repo.get_collaborator_permission(commenter_login)
    except GithubException as e:
        status = getattr(e, "status", None)
        if status in {403, 404}:
            logging.warning(f"Permission lookup failed for user {commenter_login}; treating as unprivileged (status={status})")
            return None
        raise


def handle_merge_command(
    installation_id: int,
    repo_name: str,
    pr_number: int,
    merge_method: str,
    commenter_login: str,
):
    """Handle merge/rebase commands from PR comments."""
    g, _, _ = setup_environment_webhook(installation_id)
    repo = g.get_repo(repo_name)
    permission = get_commenter_permission(repo, commenter_login)
    if permission not in {"admin", "write"}:
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(
            format_notice(
                "Insufficient permissions",
                "You need write/admin permissions to use merge commands.",
            )
        )
        logging.warning(f"User {commenter_login} lacks permission ({permission}) for {merge_method} on PR #{pr_number}")
        return jsonify({"status": "forbidden"}), 403

    pr = repo.get_pull(pr_number)
    if pr.merged:
        pr.create_issue_comment(format_notice("Already merged", "This PR is already merged."))
        return jsonify({"status": "already_merged"})

    try:
        if pr.mergeable is False:
            pr.create_issue_comment(
                format_notice(
                    "PR not mergeable",
                    "Resolve conflicts or wait for checks, then try again.",
                )
            )
            return jsonify({"status": "not_mergeable"})

        result = pr.merge(merge_method=merge_method)
        if result.merged:
            pr.create_issue_comment(f"Merged via {merge_method} by HarperBot.")
            logging.info(f"Merged PR #{pr_number} with method={merge_method}")
            return jsonify({"status": "merged"})

        pr.create_issue_comment(f"Merge failed: {result.message}")
        return jsonify({"status": "merge_failed"}), 409
    except GithubException as e:
        status = getattr(e, "status", None)
        message = ""
        documentation_url = ""
        try:
            data = getattr(e, "data", None) or {}
            message = (data.get("message") or "").strip()
            documentation_url = (data.get("documentation_url") or "").strip()
        except Exception:
            message = ""
            documentation_url = ""

        logging.error(f"Error merging PR #{pr_number}: {str(e)}")

        if status == 405:
            # Common for /rebase when the repo disallows rebase merges.
            details = message or "GitHub rejected this merge method for the PR."
            docs_line = f"\n\nDocs: {documentation_url}" if documentation_url else ""
            pr.create_issue_comment(
                format_notice(
                    "Merge method not allowed",
                    (
                        f"GitHub API rejected this request (HTTP {status}).\n\n"
                        f"{details}\n\n"
                        "Try `/merge` or `/squash`, or enable rebase merges in repository settings."
                        f"{docs_line}"
                    ),
                )
            )
            return jsonify({"status": "method_not_allowed"}), 200

        if status in {409, 422}:
            details = message or "GitHub rejected the merge request."
            pr.create_issue_comment(format_notice("Merge rejected", details))
            return jsonify({"status": "merge_rejected"}), 200

        pr.create_issue_comment(format_notice("Merge failed", "Merge failed due to an error. Check logs for details."))
        return jsonify({"error": "merge_failed"}), 500
    except Exception as e:
        logging.error(f"Error merging PR #{pr_number}: {str(e)}")
        pr.create_issue_comment(format_notice("Merge failed", "Merge failed due to an error. Check logs for details."))
        return jsonify({"error": "merge_failed"}), 500


def webhook_handler():
    """
    Handle incoming GitHub webhooks for PR events.

    Processes webhook payloads for pull request opened/reopened events.
    Verifies signature, extracts PR data, runs analysis, and posts comments.
    """
    if not flask_available:
        logging.error("Flask not available for webhook mode")
        return {"error": "Flask not installed"}, 500

    payload = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256")
    secret = os.getenv("WEBHOOK_SECRET")

    if not verify_webhook_signature(payload, signature, secret):
        logging.warning("Invalid webhook signature received")
        return jsonify({"error": "Invalid signature"}), 403

    data = request.get_json()

    event_type = data.get("action")
    has_pr = "pull_request" in data
    has_comment = "issue" in data and "comment" in data
    has_review_comment = "comment" in data and has_pr and "issue" not in data

    installation_id = data["installation"]["id"]
    repo_name = data.get("repository", {}).get("full_name") or data.get("repo", {}).get("full_name")

    if not repo_name:
        logging.warning(f"Webhook payload missing repository field: {data.keys()}")
        return jsonify({"error": "Missing repository information"}), 400

    # Inline PR review comments (Files changed tab)
    if event_type == "created" and has_review_comment:
        pr_number = data["pull_request"]["number"]
        comment_body = data["comment"]["body"]
        commenter_login = data.get("comment", {}).get("user", {}).get("login", "")
        result = handle_pr_comment_command(
            installation_id,
            repo_name,
            pr_number,
            comment_body,
            commenter_login,
        )
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], dict):
            payload, status = result
            return jsonify(payload), status
        return result

    if event_type == "created" and has_comment:
        issue = data["issue"]
        if "pull_request" not in issue:
            return jsonify({"status": "ignored"})  # Not a PR comment
        pr_number = issue["number"]
        comment_body = data["comment"]["body"]
        commenter_login = data.get("comment", {}).get("user", {}).get("login", "")
        result = handle_pr_comment_command(
            installation_id,
            repo_name,
            pr_number,
            comment_body,
            commenter_login,
        )
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], dict):
            payload, status = result
            return jsonify(payload), status
        return result

    # Only process PR events
    if event_type not in ["opened", "reopened", "synchronize"] or not has_pr:
        logging.info(f"Ignored webhook event: action={event_type}, has_pr={has_pr}")
        return jsonify({"status": "ignored"})

    pr_number = data["pull_request"]["number"]

    logging.info(f"Processing PR #{pr_number} in {repo_name}")

    try:
        run_analysis_for_pr(installation_id, repo_name, pr_number)
        logging.info(f"Successfully processed PR #{pr_number}")
        return jsonify({"status": "ok"})
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return jsonify({"error": "Processing failed"}), 500


def main():
    """Main function to run the PR bot."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GitHub PR Bot with Gemini AI")
    parser.add_argument("--repo", required=True, help="GitHub repository in format: owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="Pull request number")
    args = parser.parse_args()

    # Setup environment and get PR details
    github_token, client = setup_environment()
    pr_details = get_pr_details(github_token, args.repo, args.pr)

    # Analyze PR with Gemini
    logging.info("Analyzing PR with Gemini...")
    analysis = analyze_with_gemini(client, pr_details)
    logging.debug("Analysis response received")
    logging.debug(analysis)

    # Post the comment with formatted analysis
    logging.info("Posting analysis to PR...")
    try:
        post_comment_webhook(github_token, args.repo, pr_details, analysis)
        logging.info("Analysis complete!")
    except Exception as e:
        logging.error(f"Failed to post analysis: {str(e)}")
        # Continue even if posting fails


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # CLI mode
        main()
    else:
        # Webhook mode
        if flask_available:
            print("Starting HarperBot in webhook mode...")
            # Note: Flask's development server is for testing only. For production,
            # use a WSGI server like Gunicorn: gunicorn -w 4 harperbot:app
            app.run(debug=False)
        else:
            print("Flask not installed. For webhook mode, install with: pip install flask")
            print("For CLI mode, run: python harperbot.py --repo owner/repo --pr 123")
            sys.exit(1)
