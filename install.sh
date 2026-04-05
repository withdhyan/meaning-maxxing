#!/usr/bin/env bash
#
# Install the value-extraction skill into Hermes Agent.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/withdhyan/meaning-maxxing/main/install.sh | bash
#
# Or from a local clone:
#   ./install.sh
#

set -euo pipefail

SKILL_NAME="value-extraction"
HERMES_SKILLS="${HOME}/.hermes/skills"
TARGET="${HERMES_SKILLS}/${SKILL_NAME}"
REPO_URL="https://github.com/withdhyan/meaning-maxxing.git"

echo "Installing ${SKILL_NAME} skill for Hermes Agent..."

# Check if Hermes is installed
if [ ! -d "${HOME}/.hermes" ]; then
    echo "Warning: ~/.hermes not found. Creating it — install Hermes Agent first"
    echo "for the skill to be active: https://github.com/NousResearch/hermes-agent"
fi

mkdir -p "${HERMES_SKILLS}"

# Determine source: local clone or remote
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "${SCRIPT_DIR}/skill" ]; then
    # Running from a local clone
    SOURCE="${SCRIPT_DIR}/skill"
    echo "Installing from local clone: ${SOURCE}"
else
    # Clone from remote
    TMPDIR=$(mktemp -d)
    trap "rm -rf ${TMPDIR}" EXIT
    echo "Cloning from ${REPO_URL}..."
    git clone --depth 1 --quiet "${REPO_URL}" "${TMPDIR}/meaning-maxxing"
    SOURCE="${TMPDIR}/meaning-maxxing/skill"
fi

# Remove old installation if present
if [ -d "${TARGET}" ]; then
    echo "Removing previous installation..."
    rm -rf "${TARGET}"
fi

# Copy skill into Hermes skills directory
cp -r "${SOURCE}" "${TARGET}"

# Create the values storage directory
mkdir -p "${HOME}/.hermes/values"

echo ""
echo "Installed to: ${TARGET}"
echo "Values stored in: ~/.hermes/values/values.json"
echo ""
echo "The skill is now available in Hermes. Start a conversation and"
echo "the agent will begin noticing what matters to you."
echo ""
echo "Commands:"
echo "  /skills              — verify the skill appears"
echo "  values show          — view your captured values"
