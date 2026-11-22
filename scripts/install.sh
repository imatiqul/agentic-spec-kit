#!/usr/bin/env bash
# Install agentic-spec-kit (slice 0.1) into an initialised Spec Kit project.
# Usage: scripts/install.sh <project-dir> <lite|standard|regulated> [pack]
# Bundles cannot be used yet: Spec Kit 1.4.3 resolves bundle components only through catalogs,
# and this kit has no published catalog. This script runs the same installs a bundle would.
set -euo pipefail
kit="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project="${1:?project directory}"; profile="${2:?lite, standard or regulated}"; pack="${3:-}"
case "$profile" in lite|standard|regulated) ;; *) echo "unknown profile: $profile" >&2; exit 2;; esac
cd "$project"
[ -d .specify ] || { echo "run 'specify init' in $project first" >&2; exit 2; }
specify extension add --dev "$kit/extensions/agentic" --force
[ -n "$pack" ] && specify extension add --dev "$kit/extensions/agentic-$pack" --force
[ "$profile" != lite ] && specify extension add --dev "$kit/extensions/agentic-system" --force
specify preset add --dev "$kit/presets/agentic-$profile"
specify workflow step add agentic-gate --dev "$kit/steps/agentic-gate" --force
specify workflow add --dev "$kit/workflows/agentic-sdd"
echo
echo "Installed. Next:"
echo "  python .specify/extensions/agentic/scripts/agentic.py init --profile $profile --repository <owner/name>${pack:+ --pack $pack}"
echo "  python .specify/extensions/agentic/scripts/agentic.py doctor"
