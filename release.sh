#!/bin/bash

DATE=$(date +%Y.%m.%d)
VERSION="v${DATE}-v0.1"

echo "🔖 Releasing version: $VERSION"

# Add changelog (you must update CHANGELOG.md manually first)
git add CHANGELOG.md
git commit -m "Update changelog for version $VERSION"

# Tag it
git tag -a $VERSION -m "Release $VERSION"
git push origin main
git push origin $VERSION

echo "✅ Released and pushed $VERSION"