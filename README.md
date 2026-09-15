# Multi-Agent Research & Content System

A Python pipeline that uses four specialized AI agents — **Planner**, **Researcher**, **Writer**, and **Reviewer** — to take any research topic, break it into sub-tasks, gather information, write a structured Markdown report, and iteratively refine it until approved.

---

## How It Works

```
User Topic ? Planner ? Researcher ? Writer ? Reviewer
                                        ?         |
                                        +-revise--+ (up to MAX_REVISIONS)
```

| Agent | Role |
|---|---|
| **Planner** | Breaks the topic into focused sub-tasks |
| **Researcher** | Gathers content for each sub-task |
| **Writer** | Produces an initial Markdown draft |
| **Reviewer** | Approves the draft or requests revisions |

The **Orchestrator** coordinates all agents — no agent calls another directly.

---

## Project Structure

```
multi_agent_system/
+-- main.py              # CLI entry point
+-- orchestrator.py      # Pipeline coordinator
+-- config.py            # Central configuration
+-- exceptions.py        # Custom exceptions
+-- agents/
¦   +-- base_agent.py    # Abstract base class
¦   +-- planner.py
¦   +-- researcher.py
¦   +-- writer.py
¦   +-- reviewer.py
+-- models/
¦   +-- subtask.py
¦   +-- draft.py
¦   +-- review.py
¦   +-- log_entry.py
+-- prompts/
    +-- planner_prompt.py
    +-- researcher_prompt.py
    +-- writer_prompt.py
    +-- reviewer_prompt.py
```

---

## Setup

**Requirements:** Python 3.10+

```bash
# Clone the repo
git clone https://github.com/Devreeeeee/Multi-Agent-System.git
cd Multi-Agent-System

# (Optional) create a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install anthropic      # only needed for real LLM mode
```

---

## Usage

### Mock mode (no API key needed)
```bash
python -m multi_agent_system.main --topic "Quantum Computing" --mock
```

### Real mode (Anthropic Claude)
```bash
export ANTHROPIC_API_KEY="your-key-here"   # or set in your environment
python -m multi_agent_system.main --topic "Quantum Computing"
```

### Interactive mode
```bash
python -m multi_agent_system.main
# prompts: Enter your research topic:
```

### Force a revision round (mock demo)
```bash
python -m multi_agent_system.main --topic "AI Ethics" --mock --force-revision
```

Output reports are saved as Markdown files in the `output/` directory.

---

## Configuration

Edit [`config.py`](config.py) to adjust behaviour:

| Setting | Default | Description |
|---|---|---|
| `MOCK_MODE` | `True` | Use stub responses (no API key required) |
| `ANTHROPIC_MODEL` | `claude-3-haiku-20240307` | Model used in real mode |
| `MAX_REVISIONS` | `2` | Max revision rounds before forced acceptance |
| `TOPIC_MAX_LENGTH` | `300` | Maximum topic character length |
| `TOPIC_MIN_LENGTH` | `5` | Minimum topic character length |

---

## License

MIT
