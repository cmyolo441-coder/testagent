#!/usr/bin/env bash
# Install the Cline-cloud GitHub Actions workflow into this repository.
# Requires a git remote + a token that may write workflow files (the Actions
# tab / repo owner). Run from the repository root:
#   bash cloud/install-workflow.sh
set -euo pipefail

src="$(dirname "$0")/cline-cloud.workflow.yml"
dst=".github/workflows/cline-cloud.yml"

mkdir -p .github/workflows
cp "$src" "$dst"
chmod +x cloud/run-cline-cloud.sh 2>/dev/null || true

echo "Installed $dst"
echo "Next steps:"
echo "  1) gh secret set GWARDEN_API_KEY --body '<your GWAR key>'"
echo "  2) git add $dst cloud && git commit -m 'ci: add Cline cloud agent' && git push"
echo "  3) gh workflow run cline-cloud.yml -f task='<task>' -f branch=main"
