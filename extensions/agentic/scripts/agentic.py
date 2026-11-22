#!/usr/bin/env python3
"""Launcher: python .specify/extensions/agentic/scripts/agentic.py <command> ..."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agentic_kit.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
