# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

from vesper.vesper import app

# Export the Flask app for Vercel as 'app' (required for WSGI compatibility)
# Changed from 'handler = app' to 'app = app' because Vercel expects WSGI apps
# to be exported as 'app' for proper issubclass() checking and WSGI handling
app = app
