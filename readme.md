# 🤖 CLI Coding AI Agent

A terminal-based AI coding assistant powered by a local LLM (via [Ollama](https://ollama.com/)) that uses a **Chain of Thought (CoT)** reasoning loop to plan, execute tools, and deliver results — step by step.

---

## ✨ Features

- 🧠 **Chain of Thought reasoning** — the agent thinks before it acts, planning each step explicitly
- 🔧 **Tool use** — can run shell commands, read/write files, search Wikipedia, and fetch live weather
- 🔁 **Agentic loop** — automatically retries and continues until a final answer is reached
- 🛠️ **Local LLM** — runs entirely on your machine via Ollama (no API keys required)
- 🩹 **Fault-tolerant JSON parsing** — uses `json_repair` to gracefully handle malformed model output

---

## 🛠️ Available Tools

| Tool | Description |
|---|---|
| `run_command(cmd)` | Executes a bash/shell command and returns its output |
| `read_file(filepath)` | Reads content from a local file (truncated at 2000 chars) |
| `write_file(filepath, content)` | Creates or overwrites a file with the given content |
| `get_weather(city)` | Fetches current weather for a city using wttr.in |
| `search_wikipedia(query)` | Returns a Wikipedia summary for a given search term |

---

## 📋 Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com/) installed and running locally
- A compatible model pulled in Ollama (default: `qwen3-coder-next:cloud`)

---

## 📦 Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/cli-coding-agent.git
cd cli-coding-agent
```

**2. Install Python dependencies**
```bash
pip install ollama requests json_repair
```

**3. Pull the model in Ollama**
```bash
ollama pull qwen3-coder-next:cloud
```

> You can swap this for any Ollama-compatible model. Update the `model` field in the `ollama.chat()` call inside `agent.py`.

---

## 🚀 Usage

```bash
python agent.py
```

You'll be prompted to enter a task:

```
Hey I can write code for you : Write a Python script that prints the Fibonacci sequence up to 10 terms and save it as fib.py, then run it.
```

The agent will then reason through the task step by step, calling tools as needed and printing its thought process to the terminal.

---

## 🔄 How It Works

The agent follows a strict **CoT state machine**:

```
START → PLAN → TOOL → OBSERVE → PLAN → ... → OUTPUT
```

| Step | Description |
|---|---|
| `START` | Receives the user's request |
| `PLAN` | Agent thinks about what to do next |
| `TOOL` | Agent calls a tool with specific arguments |
| `OBSERVE` | Tool output is fed back to the agent |
| `OUTPUT` | Agent delivers the final answer and stops |

All communication between the loop and the LLM is done via structured JSON, enforcing predictable, parseable output at every step.

---

## 💬 Example Session

```
Hey I can write code for you : Create a Python script called hello.py that prints "Hello, World!" and run it.

Starting Chain of Thought...

🧠 The user wants a Python script. I'll use write_file to create it first.
🔧 Calling Tool: write_file with args: {'filepath': 'hello.py', 'content': "print('Hello, World!')\n"}
🧠 File created. Now I'll run it with run_command.
🔧 Calling Tool: run_command with args: {'cmd': 'python3 hello.py'}
🧠 Script ran successfully. Ready to report back.

🤖 Final Output: I created hello.py and ran it. The output was: Hello, World!
```

---

## ⚙️ Configuration

You can customize the agent by editing `agent.py`:

- **Model**: Change the `model` field in `ollama.chat()` to use a different Ollama model
- **Temperature**: Adjust `"temperature"` in `options` (default: `0.0` for deterministic output)
- **Tools**: Add new functions to `available_tools` and describe them in `SYSTEM_PROMPT`
- **Context window**: Adjust the truncation limit in `read_file` (default: 2000 characters)

---

## ⚠️ Known Limitations

- The agent runs in a single session — there is no memory between separate runs
- `read_file` truncates files longer than 2000 characters to protect context window size
- The model must return valid JSON at every step; `json_repair` handles most edge cases but very garbled output will cause the loop to stop
- Shell commands via `run_command` are executed directly — use caution with untrusted input

---

## 📄 License

MIT License. Feel free to use, modify, and distribute.