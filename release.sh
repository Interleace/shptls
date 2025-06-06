#!/bin/bash
# This project uses GitHub Actions for deploying for Windows
# After running this script and pushing the changes we're attatching
# a version as a tag, after fetching the latest repo's release version
# and incrementing. Than the action is triggered, binary created and
# a new release is automatically deployed.
#
# Run always this script when sending changes to GitHub
#
set -e

# Letztes Git-Tag holen
last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v1.4.7")

# Version zerlegen
version="${last_tag#v}"
IFS='.' read -r major minor patch <<< "$version"

# Patch erhöhen
patch=$((patch + 1))
new_tag="v$major.$minor.$patch"

# Versionsinfo
echo "Altes Tag: $last_tag"
echo "Neues Tag: $new_tag"

# Git-Aktionen
git add .
git commit -m "Release $new_tag"
git tag "$new_tag"
#git push origin HEAD
#git push origin "$new_tag"
#git push
git push origin "$new_tag"

echo "✅ Release $new_tag veröffentlicht und gepusht!"
