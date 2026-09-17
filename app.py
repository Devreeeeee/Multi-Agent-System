"""
Flask web UI for the Multi-Agent Research & Content System.

Run (from inside the multi_agent_system folder):
    pip install flask markdown
    python app.py
Then open http://localhost:5000 in your browser.
"""
from __future__ import annotations

import sys
import os
import json
import time
import threading

# Make sure the package root is on sys.path so both
# "python app.py" (from inside the folder) and
# "python -m multi_agent_system.app" (from parent) work.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import markdown as md

from flask import Flask, Response, render_template, request, stream_with_context

import multi_agent_system.config as config
from multi_agent_system.exceptions import (
    EmptyTopicError,
    PipelineAbortedError,
    TopicTooLongError,
)
from multi_agent_system.orchestrator import Orchestrator, PipelineResult
from multi_agent_system.agents.base_agent import BaseAgent
from multi_agent_system.models.log_entry import IntermediateLog

app = Flask(__name__)

# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse(event: str, data: object) -> str:
    """Format a single SSE message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# Instrumented orchestrator that emits SSE events
# ---------------------------------------------------------------------------

def _run_pipeline_streaming(topic: str, mock: bool, force_revision: bool):
    """
    Generator that runs the full pipeline and yields SSE strings so the
    browser can update the progress stepper in real time.
    No backend logic is changed — we only wrap the existing agents.
    """
    config.MOCK_MODE = mock
    start = time.time()

    def elapsed() -> float:
        return round(time.time() - start, 1)

    # ── Validate topic early so we can report the error over SSE ───────────
    topic_clean = topic.strip()
    if len(topic_clean) < config.TOPIC_MIN_LENGTH:
        yield _sse("error", {"message": f"Topic must be at least {config.TOPIC_MIN_LENGTH} characters."})
        return
    if len(topic_clean) > config.TOPIC_MAX_LENGTH:
        yield _sse("error", {"message": f"Topic must be at most {config.TOPIC_MAX_LENGTH} characters."})
        return

    # ── Patch force-revision if requested ───────────────────────────────────
    if mock and force_revision:
        from multi_agent_system.agents import reviewer as rev_module
        _original = rev_module.ReviewerAgent.run  # type: ignore[attr-defined]

        def _patched(self, draft, revision_count):  # noqa: ANN001
            if revision_count == 0:
                from multi_agent_system.models.review import ReviewDecision
                return ReviewDecision(
                    approved=False,
                    feedback="Please expand the introduction section.",
                    revision_number=revision_count,
                )
            return _original(self, draft, revision_count)

        rev_module.ReviewerAgent.run = _patched  # type: ignore[attr-defined]

    # Agent-name → stepper index mapping
    AGENT_STEP = {
        "PlannerAgent":     0,
        "ResearcherAgent":  1,
        "WriterAgent":      2,
        "ReviewerAgent":    3,
    }

    logs: list[IntermediateLog] = []

    # Monkey-patch BaseAgent._log so every log entry fires an SSE event
    _original_log = BaseAgent._log  # type: ignore[attr-defined]

    def _patched_log(self, input_summary: str, output_summary: str) -> None:
        _original_log(self, input_summary=input_summary, output_summary=output_summary)
        entry = self._logs[-1]
        step_idx = AGENT_STEP.get(type(self).__name__, -1)
        logs.append(entry)
        yield_queue.append(_sse("agent_done", {
            "agent": entry.agent_name,
            "step":  step_idx,
            "in":    entry.input_summary,
            "out":   entry.output_summary,
            "time":  entry.timestamp.strftime("%H:%M:%S"),
            "elapsed": elapsed(),
        }))

    yield_queue: list[str] = []
    BaseAgent._log = _patched_log  # type: ignore[attr-defined]

    # ── Step 0: start ────────────────────────────────────────────────────────
    yield _sse("start", {"topic": topic_clean, "elapsed": elapsed()})
    yield _sse("step_active", {"step": 0, "elapsed": elapsed()})

    orchestrator = Orchestrator()

    result: PipelineResult | None = None
    error_msg: str | None = None

    def _run():
        nonlocal result, error_msg
        try:
            result = orchestrator.run(topic_clean)
        except (EmptyTopicError, TopicTooLongError, PipelineAbortedError) as exc:
            error_msg = str(exc)
        except Exception as exc:  # noqa: BLE001
            error_msg = f"Unexpected error: {exc}"

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    sent: set[int] = set()
    last_step = -1

    while thread.is_alive() or yield_queue:
        # Drain any queued SSE events from the patched _log
        while yield_queue:
            msg = yield_queue.pop(0)
            # Parse the step from the message to advance the stepper
            try:
                data = json.loads(msg.split("data: ", 1)[1].strip())
                step = data.get("step", -1)
                if step >= 0 and step != last_step:
                    if last_step >= 0:
                        yield _sse("step_complete", {"step": last_step, "elapsed": elapsed()})
                    last_step = step
                    if step not in sent:
                        sent.add(step)
                        yield _sse("step_active", {"step": step + 1 if step < 3 else step, "elapsed": elapsed()})
            except Exception:  # noqa: BLE001
                pass
            yield msg

        # Heartbeat so the connection stays alive
        yield _sse("heartbeat", {"elapsed": elapsed()})
        time.sleep(0.25)

    # Restore original _log
    BaseAgent._log = _original_log  # type: ignore[attr-defined]

    if error_msg:
        yield _sse("error", {"message": error_msg})
        return

    # Mark all steps complete
    for i in range(4):
        yield _sse("step_complete", {"step": i, "elapsed": elapsed()})

    # ── Build result payload ─────────────────────────────────────────────────
    html_report = md.markdown(
        result.final_draft.content,
        extensions=["fenced_code", "tables"],
    )

    approved = result.approved_by_reviewer
    yield _sse("done", {
        "topic":          result.topic,
        "approved":       approved,
        "revision_count": result.revision_count,
        "html_report":    html_report,
        "raw_report":     result.final_draft.content,
        "subtasks": [
            {"id": st.id, "description": st.description, "status": st.status}
            for st in result.subtasks
        ],
        "logs": [
            {
                "agent":   e.agent_name,
                "time":    e.timestamp.strftime("%H:%M:%S"),
                "input":   e.input_summary,
                "output":  e.output_summary,
            }
            for e in result.logs
        ],
        "elapsed": elapsed(),
    })


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run")
def run_pipeline():
    topic          = request.args.get("topic", "")
    mock           = request.args.get("mock", "true").lower() == "true"
    force_revision = request.args.get("force_revision", "false").lower() == "true"

    return Response(
        stream_with_context(_run_pipeline_streaming(topic, mock, force_revision)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":  "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    # threaded=True is required for SSE + background thread to work
    app.run(debug=True, port=5000, threaded=True)
