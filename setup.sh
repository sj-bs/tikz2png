#!/usr/bin/env bash

set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

install_pipx() {
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3-pipx
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python-pipx
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S python-pipx
    else
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    fi
}

echo "🔍 Checking dependencies..."

if ! command -v pipx >/dev/null 2>&1; then
    echo "📦 pipx is required but not installed"
    read -p "Would you like to install pipx? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing pipx..."
        install_pipx || {
            echo "❌ Error: Failed to install pipx"
            exit 1
        }
    else
        echo "❌ pipx is required for installation. Exiting."
        exit 1
    fi
fi

echo "🔍 Checking for existing installation..."
if pipx list | grep -q "tikz2png"; then
    echo "🔄 Upgrading tikz2png..."
    pipx upgrade --editable . || {
        echo "❌ Error: Upgrade failed"
        exit 1
    }
else
    echo "🚀 Installing tikz2png..."
    pipx install --editable . || {
        echo "❌ Error: Installation failed"
        exit 1
    }
fi

echo "✨ Success! You can now use 'tikz2png' from anywhere on your system"