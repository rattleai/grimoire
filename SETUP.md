# Fast Setup Guide

A step-by-step guide to get Rattle AI Workspace running on your computer.
No programming experience required.

---

## What You Will Need

Before you start, make sure you have the following:

1. **A computer** running Windows, macOS, or Linux
2. **An internet connection**
3. **A Rattle API key** (provided by your Rattle administrator)
4. **An AI provider key** (optional — only needed for AI commands)

---

## Step 1: Install Python

Rattle AI Workspace requires **Python 3.10 or newer**.

### Check if Python is already installed

Open a terminal (see below) and type:

```
python3 --version
```

If you see something like `Python 3.12.4`, you are good — skip to **Step 2**.

If you get an error like `command not found`, install Python first:

### How to open a terminal

| Operating System | How to Open |
|---|---|
| **Windows** | Press `Win + R`, type `cmd`, press Enter. Or search for "Command Prompt" in the Start menu. |
| **macOS** | Press `Cmd + Space`, type `Terminal`, press Enter. |
| **Linux** | Press `Ctrl + Alt + T`, or find "Terminal" in your applications menu. |

### Install Python

| Operating System | Instructions |
|---|---|
| **Windows** | Go to https://www.python.org/downloads/ and click the big yellow "Download Python" button. **Important:** During installation, check the box that says "Add Python to PATH". |
| **macOS** | Go to https://www.python.org/downloads/ and download the macOS installer. Run it and follow the prompts. |
| **Linux** | Run: `sudo apt update && sudo apt install python3 python3-pip python3-venv` (Ubuntu/Debian) or `sudo dnf install python3 python3-pip` (Fedora). |

After installing, close and reopen your terminal, then verify:

```
python3 --version
```

> **Windows note:** On Windows, you may need to use `python` instead of `python3`
> throughout this guide. Try both and use whichever works.

---

## Step 2: Download Rattle AI Workspace

### Option A: Download as ZIP (easiest)

1. Go to https://github.com/rattleai/grimoire
2. Click the green **"Code"** button
3. Click **"Download ZIP"**
4. Extract the ZIP file to a folder you can find easily (e.g., your Desktop or Documents)

### Option B: Clone with Git (if you have Git installed)

```
git clone https://github.com/rattleai/grimoire.git
```

### Navigate into the folder

In your terminal, navigate to the folder you just downloaded:

```
cd rattle_api
```

> **Tip:** On Windows, you can type `cd ` (with a space) and then drag the
> folder from File Explorer into the terminal window to paste the path.

---

## Step 3: Create a Virtual Environment

A virtual environment keeps Rattle's dependencies separate from other Python
projects on your computer. This is a one-time setup.

```
python3 -m venv .venv
```

Now activate it:

| Operating System | Command |
|---|---|
| **macOS / Linux** | `source .venv/bin/activate` |
| **Windows (Command Prompt)** | `.venv\Scripts\activate` |
| **Windows (PowerShell)** | `.venv\Scripts\Activate.ps1` |

After activation, your terminal prompt will show `(.venv)` at the beginning.
This means the virtual environment is active.

> **Important:** You need to activate the virtual environment every time you open
> a new terminal window before using Rattle. Just run the activate command again.

---

## Step 4: Install Rattle AI Workspace

Run this single command to install everything:

```
pip install -e ".[all-ai]"
```

Wait for the installation to finish. You will see a success message at the end.
This installs Rattle together with all supported AI providers (OpenAI, Anthropic)
so you can switch between them freely without reinstalling anything.

---

## Step 5: Configure Your API Keys

### 5a: Create your configuration file

```
cp .env.example .env
```

> **Windows (Command Prompt):** Use `copy .env.example .env` instead.

### 5b: Edit the configuration file

Open the `.env` file in any text editor:

| Operating System | Command |
|---|---|
| **Windows** | `notepad .env` |
| **macOS** | `open -e .env` |
| **Linux** | `nano .env` or `xdg-open .env` |

### 5c: Add your Rattle API key

Find this line in the file:

```
RATTLE_API_KEY_ACME=your-api-key-here
```

Replace `your-api-key-here` with the API key you received from your Rattle
administrator. Replace `ACME` with your tenant name (in UPPERCASE):

```
RATTLE_API_KEY_MYCOMPANY=abc123-your-real-key-here
```

> **What is a tenant?** A tenant is your company or workspace name in Rattle.
> The part after `RATTLE_API_KEY_` becomes the name you use on the command line.
> For example, `RATTLE_API_KEY_MYCOMPANY=...` means you will use `mycompany`
> as the tenant name in commands.

### 5d: Add your AI provider key (if using AI features)

Find the AI provider section and fill in the key for your chosen provider:

**For OpenAI:**
```
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
```

**For Anthropic:**
```
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

**For Ollama (free, runs locally — no API key needed):**
```
AI_PROVIDER=ollama
```

### 5e: Save and close the file

---

## Step 6: Verify the Setup

Test that everything works by running the connection test. Replace `mycompany`
with the tenant name you configured in Step 5c:

```
rattle mycompany test-connection
```

If the setup is correct, you will see:

```
Connection OK for tenant 'mycompany'
```

### Troubleshooting

| Problem | Solution |
|---|---|
| `command not found: rattle` | Make sure your virtual environment is activated (Step 3). |
| `Unknown tenant 'mycompany'` | Check that `RATTLE_API_KEY_MYCOMPANY=...` is in your `.env` file and the key is correct. |
| `Connection FAILED` | Verify your API key is correct and you have internet access. |

---

## Step 7: Run Your First AI Command

Once the connection test passes, try an AI-powered command:

```bash
# Generate product descriptions in German
rattle mycompany ai-describe --limit 3 --language de

# Classify products into categories
rattle mycompany ai-classify --limit 5

# Ask a question about your product data
rattle mycompany ai-analyse --question "Which products have no description?"

# See which AI providers are available
rattle mycompany ai-providers
```

---

## Quick Reference

### Commands you will use often

| What you want to do | Command |
|---|---|
| Test the connection | `rattle <tenant> test-connection` |
| Generate product descriptions | `rattle <tenant> ai-describe --limit 5` |
| Classify products | `rattle <tenant> ai-classify --limit 10` |
| Transform data formats | `rattle <tenant> ai-transform datanorm rattle data.json` |
| Analyse product data | `rattle <tenant> ai-analyse --question "your question"` |
| List available AI providers | `rattle <tenant> ai-providers` |
| List local source files | `rattle <tenant> list-sources` |

Replace `<tenant>` with your tenant name (e.g., `mycompany`).

### Starting a new terminal session

Every time you open a new terminal, you need to:

1. Navigate to the project folder: `cd path/to/rattle_api`
2. Activate the virtual environment:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`

Then you can run `rattle` commands as normal.

---

## Getting Help

- Run `rattle --help` to see all available commands
- Run `rattle <tenant> <command> --help` to see options for a specific command
- Report issues at https://github.com/rattleai/grimoire/issues
