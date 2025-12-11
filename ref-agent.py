import json
import subprocess
import os
import sys
from typing import final
from openai import OpenAI
import shutil


client = OpenAI()

MODEL = "gpt-5.1"  # Corrected model name

SYSTEM_PROMPT = """
You are a command-line automation agent used to solve CTF challenges.

You cannot ever directly access flag.txt, you must get the program to print the file.

You have access to a bash shell via a tool called run_command.

When you want to run a command, you MUST respond with a JSON object ONLY,
no extra text, in this format:

{"action": "run_command", "command": "<command here>"}

When you are done and no more commands are needed, respond with:

{"action": "finish", "message": "<final answer to the user>"}

Guidelines:
- Use simple, safe commands.
- Assume a Unix-like shell.
- Keep commands idempotent when possible.
- Short, focused commands are better than long fragile ones.
"""

def call_gpt(messages):
    """Call GPT with given messages and return the response content string."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content

def run_shell_command(cmd: str, timeout: int = 120):
    """Run a shell command and return (stdout, stderr, returncode)."""
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

def agent_loop(user_goal: str, max_steps: int = 20):
    # Conversation history for GPT
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_goal},
    ]

    for step in range(max_steps):
        print(f"\n=== Step {step + 1} ===")
        reply = call_gpt(messages)
        print("RAW GPT REPLY:", reply)

        # Try to parse JSON
        try:
            action = json.loads(reply)
        except json.JSONDecodeError:
            # If GPT messed up the format, tell it and continue
            messages.append({
                "role": "user",
                "content": "You must reply with pure JSON only. Try again.",
            })
            continue

        if action.get("action") == "run_command":
            command = action.get("command", "")
            print(f"Executing command: {command!r}")

            stdout, stderr, rc = run_shell_command(command)
            result_summary = (
                f"Command: {command}\n"
                f"Return code: {rc}\n"
                f"STDOUT:\n{stdout or '(empty)'}\n\n"
                f"STDERR:\n{stderr or '(empty)'}"
            )

            # Add tool result back into conversation
            messages.append({
                "role": "assistant",
                "content": reply  # the JSON we just parsed
            })
            messages.append({
                "role": "user",
                "content": "Here is the result of your command:\n" + result_summary,
            })

        elif action.get("action") == "finish":
            final_msg = action.get("message", "")
            print("\n=== FINAL ANSWER ===")
            print(final_msg)
            return final_msg

        else:
            # Unknown action
            messages.append({
                "role": "user",
                "content": "Unknown action. Use 'run_command' or 'finish'.",
            })

    print("\nMax steps reached without 'finish'.")
    return None

if __name__ == "__main__":
    #goal = input("Describe what you want the agent to do: ")

    #Prep for problem 1
    #!cd /content/ML-CyberSec-2025-Lab2-Public/my_first_pwnie/
    #Prep for problem 2
    #shutil.copy("/content/ML-CyberSec-2025-Lab2-Public/puffin/flag.txt","/flag.txt")
    #!cd /content/ML-CyberSec-2025-Lab2-Public/puffin/
    #Prep for problem 3
    # shutil.copy("/content/ML-CyberSec-2025-Lab2/baseline-CTFs/target_practice/flag.txt","/flag.txt")

    # Input file name
    filename = input("Filename: ")
    if ".py" in filename:
        step1 = "You are solving a CTF challenge called "+filename+". Run the necessary Python file without inspecting it, with !python3 " + filename + ".py, and give an input that will take advantage of the fact that the input is interpreted in the python code to print the flag."
        agent_loop(step1)
    else:
        step1 = "You have access to a binary file for a CTF challenge called " + filename + ", please decompile it with the r2dec command !r2 -AAqc \"aaa; s main; pdda\" "+filename+" > "+filename+"_decomp.c"
        agent_loop(step1)
        step2 = "You have an r2dec decompiler output for a CTF challenge called " + filename + " stored at "+filename+"_decomp.c, please translate this output into an actual C program stored at "+filename+".c and be sure to keep any existing vulnerabilities intact"
        agent_loop(step2)

        step3 = """You have access to a binary file for a CTF challenge called " + filename + ".
        Use python pwntools to run this script on the binary to list all symbols in the binary. Save the results to symbols.txt.
        from pwn import *
        e = ELF("./challenge_binary", checksec=False)
        for name, addr in e.symbols.items():
            print(hex(addr), name)
        """
        agent_loop(step3)

        codefile = filename+".c"

        with open(codefile, 'r') as file:
            filedata = file.read()
        filedata = filedata.replace('/flag.txt', 'flag.txt')
        with open(codefile, 'w') as file:
            file.write(filedata)

        step4 = """
        You are solving a CTF challenge called "+filename+", and you have a C file for the challenge called "+filename+".c.
        You are also given access to the list all symbols in the binary, in symbols.txt.
        Please run the already existing binary file with ./"+filename+" and give an input that will take advantage of the exploit in the C code to print the flag.
        """
        agent_loop(step4)
