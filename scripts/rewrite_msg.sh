#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# Read the commit message from stdin
MSG=$(cat)

# Get first line
FIRST_LINE=$(echo "$MSG" | head -n1)

# Make lowercase
FIRST_LINE=$(echo "$FIRST_LINE" | tr '[:upper:]' '[:lower:]')

# Truncate to 60 chars
FIRST_LINE=$(echo "$FIRST_LINE" | cut -c1-60)

# Replace first line in MSG
lines=()
while IFS= read -r line; do
  lines+=("$line")
done <<< "$MSG"
lines[0]="$FIRST_LINE"
for line in "${lines[@]}"; do
  echo "$line"
done
