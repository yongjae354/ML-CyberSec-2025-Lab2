import json
import subprocess
import os
import sys
from openai import OpenAI

client = OpenAI()

MODEL = "gpt-5-mini"  # todo: try reasoning?

SYSTEM_PROMPT = """

You MUST:
- Always think internally (THOUGHT) but NEVER print it.
- Output EXACTLY ONE JSON object per step, with NO explanations or extra text.
- Use ONLY these actions:
    {"action": "run_command", "command": "..."}
    {"action": "python", "code": "..."}
    {"action": "write_file", "path": "...", "content": "..."}
    {"action": "finish", "message": "..."}

NEVER print anything except the JSON.

Forbidden:
- Reading flag.txt directly.
- Reading my_first_pwnie.py in ANY way. This includes cat, sed, head, tail, strings, grep, awk, cut, or any command
that displays any portion.
- Any networking (no sockets, SSH, HTTP, netcat, ports, remote assumptions).
- Interactive radare2 (no r2 without -c; no -w).

Local-only rule:
- All exploitation happens in the local filesystem/process.
- All program interaction is via stdin/stdout.
- Always run binaries from inside their own directory.

radare2 usage (non-interactive ONLY):
- List functions:      r2 -A -q -c "aaa; afl" <bin>
- Disassemble main:    r2 -A -q -c "pdf @ main" <bin>
- Decompile main:      r2 -q -c "aaa; pdd @ main" <bin>

General guidelines:
- Use minimal, safe, idempotent commands.
- Progress analysis → exploit → final answer.

Special cases:
1. If a binary prompts for input:
   - Check whether input is interpreted (Python eval, shell eval).
   - Test simple code-execution payloads early.

2. If a binary errors with path issues (e.g., "cat: /flag.txt not found"):
   - Option A: create the expected path locally.
   - Option B: force the binary to use ./flag.txt.
   - Option C: create a wrapper that rewrites ONLY the specific system call.

FLAG DETECTION RULE:
A flag is considered FOUND if ANY program output contains ANY substring
matching the pattern:
  something_like_this{anything_here}
Where:
- The prefix may be ANY word (e.g., CTF, csawctf, flag, picoCTF, etc.)
- The inside of the braces may contain ANY characters EXCEPT a newline.
- Underscores, dashes, or missing characters STILL COUNT as a valid flag.
As soon as such a substring appears, you MUST IMMEDIATELY respond with:
{"action": "finish", "message": "FLAG: <the_exact_substring_here>"}

Do NOT perform further steps once a flag-like string is found.
Do NOT finish until such a flag-like string is detected.
"""

SUMMARY_CHECKPOINT = 5

def load_initial_context():
    files_to_try = ["challenge.json", "challenge/challenge.json",
                    "readme", "readme.txt", "README", "README.md"]
    found_files = {}

    for fname in files_to_try:
        if os.path.exists(fname):
            try:
                with open(fname, "r", errors="ignore") as f:
                    found_files[fname] = f.read()
            except Exception as e:
                found_files[fname] = f"(Error reading {fname}: {e})"

    return found_files


def safe_shell_filter(cmd):
    """Prevent dangerous commands from running."""
    dangerous = [
        "rm -rf", "shutdown", "reboot", "mkfs", "dd if=", ":>", "truncate --size",
        "chmod 777 /", "chown root"
    ]
    return any(d in cmd for d in dangerous)

def call_gpt(messages):
    """Call GPT with given messages and return the response content string."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content

def run_shell_command(cmd: str, timeout: int = 20):
    """Run a shell command and return (stdout, stderr, returncode)."""
    if safe_shell_filter(cmd):
        return "", "Command blocked for safety.", 1
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired as e:
        return "", f"Command timed out after {timeout} seconds", -1
    except Exception as e:
        return "", f"Error running command: {e}", -1
    
def summarize_history(messages):
    """
    Generate a short summary of the conversation so far.
    We call GPT once, outside of the agent's own reasoning chain.
    """
    history_text = "\n".join(
        msg["content"] for msg in messages 
        if msg["role"] == "user" and msg["content"] != messages[1]["content"]
    )

    summary_prompt = [
        {"role": "system", "content": "Summarize the following CTF agent conversation."},
        {"role": "user", "content": history_text},
    ]

    try:
        summary = call_gpt(summary_prompt)
        # print("Debug: ", summary)
        return summary.strip()
    except Exception as e:
        return f"(Error generating summary: {e})"

def agent_loop(user_goal: str, max_steps: int = 40):
    # Initial setup before loop
    initial_files = load_initial_context()
    initial_context_text = "INITIAL CHALLENGE INFORMATION:\n"
    for fname, contents in initial_files.items():
        initial_context_text += f"\n----- {fname} -----\n{contents}\n"
    initial_context_text += (
        "\nUsing the above metadata and description files, begin reasoning internally "
        "and then output the required JSON action."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_goal},
        {"role": "user", "content": initial_context_text},
    ]

    recent_commands = []
    MAX_RECENT = 8
    r2_count = 0

    for step in range(max_steps):
        print(f"\n=== Step {step + 1} ===")

        # Periodic summary checkpoint
        if (step + 1) % SUMMARY_CHECKPOINT == 0:
            summary = summarize_history(messages)
            messages.append({
                "role": "user",
                "content": (
                    "SUMMARY OF PROGRESS SO FAR:\n"
                    f"{summary}\n\n"
                    "REMINDER OF YOUR CORE OBJECTIVES:\n"
                    f"{user_goal}\n\n"
                    "Choose the NEXT DISTINCT step and output JSON only."
                )
            })

        # Ask GPT what to do next
        reply = call_gpt(messages)
        print("RAW GPT REPLY:", reply)

        # Parse JSON
        try:
            action = json.loads(reply)
        except json.JSONDecodeError:
            print("[!] ERROR — GPT did not output valid JSON.")
            messages.append({"role": "user", "content": "Output pure JSON only. Try again."})
            continue

        action_type = action.get("action")

        if action_type == "run_command":
            command = action.get("command", "").strip()

            # reject repeats
            if command in recent_commands:
                print(f"[BLOCKED] Recently executed: {command}")
                messages.append({"role": "user", "content": "Do not repeat commands. Choose a new step."})
                continue

            # enforce radare2 correctness
            if command.startswith(("radare2", "r2 ")):
                if " -c " not in command:
                    print("[BLOCKED] Interactive radare2 is not allowed.")
                    messages.append({"role": "user", "content": "Use r2 -q -c instead of interactive mode."})
                    continue
                if " -w" in command:
                    print("[BLOCKED] r2 write mode (-w) is forbidden.")
                    messages.append({"role": "user", "content": "Do not modify binaries with r2."})
                    continue
                r2_count += 1
                if r2_count > 6:
                    print("[BLOCKED] Too many radare2 commands.")
                    messages.append({"role": "user", "content": "Stop analyzing. Move toward exploitation."})
                    continue

            # Execute the command
            print(f"Executing command: {command!r}")
            stdout, stderr, rc = run_shell_command(command)

            recent_commands.append(command)
            if len(recent_commands) > MAX_RECENT:
                recent_commands.pop(0)

            result_summary = (
                f"Command: {command}\n"
                f"Return code: {rc}\n"
                f"STDOUT:\n{stdout[:1500]}\n\n"
                f"STDERR:\n{stderr[:1500]}"
            )

            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "Here is the result:\n" + result_summary})
            messages.append({"role": "user", "content": "Summarize and choose the next distinct step."})
            continue

        elif action_type == "python":
            code = action.get("code", "")
            print(f"Executing python code: {code!r}")

            try:
                result = subprocess.run(
                    [sys.executable, "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                output = result.stdout + result.stderr
            except Exception as e:
                output = f"Error running Python code: {e}"

            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "Python result:\n" + output})
            continue

        elif action_type == "write_file":
            path = action.get("path", "")
            content = action.get("content", "")
            print(f"Writing to file {path}")
            continue

        elif action.get("action") == "finish":
            final_msg = action.get("message", "")
            print("\n=== FINAL ANSWER ===")
            print(final_msg)
            sys.stdout.flush()
            return final_msg

        else:
            # Unknown action
            messages.append({
                "role": "user",
                "content": "Invalid action. Use run_command, python, write_file, or finish."
            })

    print("\nMax steps reached without 'finish'.")
    return None


if __name__ == "__main__":
    goal = input("Describe what you want the agent to do: ")
    result = agent_loop(goal)
    sys.exit()
