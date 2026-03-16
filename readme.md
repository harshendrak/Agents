## Agents

This folder contains small “agent” scripts that wrap an LLM and let it call a few local tools (read/write files, run commands, fetch weather, etc.) using a simple JSON step protocol.

## What’s inside

- **`coding_agent.py`**: CLI coding assistant using **Ollama**. It runs in a loop where the model returns JSON steps (`PLAN`, `TOOL`, `OBSERVE`, `OUTPUT`), and the script executes allowed tools locally.
- **`weather_agent.py`**: Weather Q&A agent using Google Gemini via the OpenAI-compatible endpoint (separate script).

## Requirements

- **Python 3.10+** recommended
- **Ollama installed and running** (for `coding_agent.py`)
- Python packages (install what you’re missing):

```bash
pip install ollama requests json-repair python-dotenv openai pydantic
```

## Run

### Coding agent (Ollama)

```bash
python coding_agent.py
```

You’ll be prompted:

- `Hey I can write code for you :`

The agent will respond step-by-step and may call tools like writing files or running commands.

### Weather agent (Gemini)

1) Create a `.env` file next to `weather_agent.py`:

```bash
GEMINI_API_KEY=your_key_here
```

2) Run:

```bash
python weather_agent.py
```

## Tools available to `coding_agent.py`

The agent can call these tools:

- **`read_file(filepath)`**: reads a local file (truncated for very large files)
- **`write_file(filepath, content)`**: creates/overwrites a file (creates directories if needed)
- **`run_command(cmd, timeout_s=30)`**: runs a shell command and returns JSON with `stdout/stderr/returncode`
- **`get_weather(city)`**: weather via `wttr.in`
- **`search_wikipedia(query)`**: summary via Wikipedia REST API

## Notes / troubleshooting

- **Windows + OneDrive**: if you see “Access is denied” errors related to `__pycache__`, it’s usually OneDrive/permissions/lock contention. Running scripts normally is fine; avoid tools that try to write `.pyc` files if your environment blocks it.
- **Network calls**: `coding_agent.py` uses timeouts + retries for weather/Wikipedia; if you’re offline, those tools will fail gracefully.
- **Safety**: `run_command` has a basic “dangerous command” blocker and a timeout, but it still executes shell commands. Don’t run the agent in folders containing sensitive files unless you trust the prompts you give it.



