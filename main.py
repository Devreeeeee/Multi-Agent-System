"""
CLI entry point for the Multi-Agent Research & Content System.

Usage
-----
    # Interactive mode (prompts for topic)
    python -m multi_agent_system.main

    # Scripted mode
    python -m multi_agent_system.main --topic "Quantum Computing"

    # Mock mode (no API key / Ollama needed)
    python -m multi_agent_system.main --topic "Quantum Computing" --mock

    # Force a revision round even in mock mode
    python -m multi_agent_system.main --topic "Quantum Computing" --mock --force-revision
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path

import multi_agent_system.config as config
from multi_agent_system.exceptions import (
    EmptyTopicError,
    PipelineAbortedError,
    TopicTooLongError,
)
from multi_agent_system.orchestrator import Orchestrator, PipelineResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_SEPARATOR = "-" * 70


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def display_result(result: PipelineResult) -> None:
    """Pretty-print the full pipeline result to stdout."""
    print(f"\n{_SEPARATOR}")
    print("  MULTI-AGENT RESEARCH SYSTEM - RUN COMPLETE")
    print(_SEPARATOR)
    print(f"  Topic        : {result.topic}")
    print(f"  Revision(s)  : {result.revision_count}")
    verdict = (
        "[OK] Approved by Reviewer"
        if result.approved_by_reviewer
        else "[WARN] Accepted after reaching max revisions"
    )
    print(f"  Verdict      : {verdict}")
    print(_SEPARATOR)

    print("\n-- Agent Logs (intermediate outputs) --\n")
    for i, entry in enumerate(result.logs, start=1):
        print(f"  [{i}] {entry.agent_name} @ {entry.timestamp.strftime('%H:%M:%S')}")
        print(f"       IN  : {entry.input_summary}")
        print(f"       OUT : {entry.output_summary}")
        print()

    print("-- Sub-tasks --\n")
    for st in result.subtasks:
        status_icon = "[OK]" if st.status == "RESEARCHED" else "[--]"
        print(f"  {status_icon} [{st.id}] {st.description}  ({st.status})")
    print()

    print("-- Final Document --\n")
    print(result.final_draft.content)
    print(f"\n{_SEPARATOR}\n")


def save_output(topic: str, content: str) -> Path:
    """Save the Markdown document to the output directory and return its path."""
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitise topic → valid filename
    filename = re.sub(r"[^\w]", "_", topic.lower()).strip("_")
    filename = re.sub(r"_+", "_", filename)  # collapse multiple underscores
    filepath = output_dir / f"{filename}_result.md"

    filepath.write_text(content, encoding="utf-8")
    return filepath


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-Agent AI Research & Content System"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Research topic (prompted interactively if omitted)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Use stub LLM responses — no API key required",
    )
    parser.add_argument(
        "--force-revision",
        action="store_true",
        default=False,
        help=(
            "In mock mode: make the Reviewer start by requesting a revision "
            "(useful for demonstrating the revision loop)"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Apply mock mode BEFORE constructing the Orchestrator
    if args.mock:
        config.MOCK_MODE = True

    # Interactive topic input
    topic: str
    if args.topic:
        topic = args.topic
    else:
        try:
            topic = input("Enter your research topic: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

    # Run the pipeline
    orchestrator = Orchestrator()

    try:
        result = orchestrator.run(topic)
    except EmptyTopicError as exc:
        print(f"\n[ERROR] Invalid input: {exc}", file=sys.stderr)
        sys.exit(1)
    except TopicTooLongError as exc:
        print(f"\n[ERROR] Invalid input: {exc}", file=sys.stderr)
        sys.exit(1)
    except PipelineAbortedError as exc:
        print(f"\n[ERROR] Pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Display to terminal
    display_result(result)

    # Save to disk
    saved_path = save_output(result.topic, result.final_draft.content)
    print(f"Report saved to: {saved_path}\n")


if __name__ == "__main__":
    main()
