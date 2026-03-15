import os 
import ollama
import requests
import json
import json_repair


def run_command(cmd:str):
    result =os.popen(cmd).read()
    return result


available_tools ={

    "run_command": run_command

}
SYSTEM_PROMPT = """You are an expert CLI Coding AI Assistant. You resolve user programming queries using a strict Chain of Thought (CoT) process.
Your workflow strictly follows the sequence: START -> PLAN (can repeat) -> TOOL (if needed) -> OBSERVE (wait for system) -> OUTPUT.

CRITICAL RULES:
1. Strictly follow the given JSON format. Do not wrap the JSON in Markdown formatting.
2. Only output ONE step at a time.
3. NEVER output raw, multi-line code (like HTML, JS, or Python) inside the "OUTPUT" step. 
4. If the user asks you to create an app, script, or write code, you MUST use the "write_file" tool to save the code to the disk. 
5. The "OUTPUT" step is ONLY for summarizing what you did or chatting with the user.
6. Ensure all double quotes and newlines inside your JSON values are strictly escaped to prevent parsing errors.

Output JSON Format:
{"steps":"START"|"PLAN"|"OUTPUT"|"TOOL","content":"string","tool":"string","input":{"param_name": "param_value"}}

Available Tools:
run_command(cmd:str): Takes a linux command as input and runs it in the terminal and returns the output of the command.

Example 1: Creating and running a script
START: Can you write a python script called test.py that prints "Hello World" and then run it?
PLAN:{"steps":"PLAN","content":"The user wants a python script named test.py. I need to use write_file first."}
PLAN:{"steps":"TOOL","tool":"run_command","input":{"filepath":"test.py", "content":"print('Hello World')\\n"}}
OBSERVE:{"steps":"OBSERVE","tool":"run_command","output":"Success: Wrote content to test.py"}
PLAN:{"steps":"PLAN","content":"The file is created. Now I need to run it using the run_command tool."}
PLAN:{"steps":"TOOL","tool":"run_command","input":{"cmd":"python3 test.py"}}
OBSERVE:{"steps":"OBSERVE","tool":"run_command","output":"Hello World\\n"}
PLAN:{"steps":"PLAN","content":"The script ran successfully. I will now notify the user."}
OUTPUT:{"steps":"OUTPUT","content":"I have created the test.py file and ran it. The execution output was: Hello World"}

Example 2: Creating a web project
START: Create a simple index.html file with a heading that says "My App".
PLAN:{"steps":"PLAN","content":"The user wants an HTML file. I must NOT output the HTML code directly in my response. I will use the write_file tool."}
PLAN:{"steps":"TOOL","tool":"run_command","input":{"filepath":"index.html", "content":"<!DOCTYPE html>\\n<html>\\n<head>\\n<title>App</title>\\n</head>\\n<body>\\n<h1>My App</h1>\\n</body>\\n</html>"}}
OBSERVE:{"steps":"OBSERVE","tool":"run_command","output":"Success: Wrote content to index.html"}
PLAN:{"steps":"PLAN","content":"The HTML file has been written to disk successfully."}
OUTPUT:{"steps":"OUTPUT","content":"I have successfully generated index.html and saved it to your directory!"}
"""

user_input = input("Hey I can write code for you : ")

message_history = [
    {"role":"system","content":SYSTEM_PROMPT},
    {"role":"user","content":user_input}
]

print("\nGetting things ready\n")


print("\nStarting Chain of Thought...\n")

while True:
    
    response = ollama.chat(
        model="qwen3-coder-next:cloud", 
        messages=message_history,
        format="json",
        options={"temperature": 0.0} 
    )

    raw_result = response['message']['content']
    
    # Optional: Strip markdown code blocks if the model accidentally wraps its output
    if raw_result.startswith("```"):
        raw_result = raw_result.strip("`").replace("json\n", "", 1).strip()
    
    # Append the model's raw response to history
    message_history.append({"role": "assistant", "content": raw_result})
    
    # Use json_repair to parse and automatically fix broken JSON
    try:
        parsed_results = json_repair.loads(raw_result)
    except Exception as e:
        # If even json_repair fails, the output is completely mangled
        print(f"❌ Critical parsing failure: {e}\nRaw output:\n{raw_result}")
        break

    # If the model returns a list instead of a dict, grab the first dictionary
    if isinstance(parsed_results, list):
        if len(parsed_results) > 0:
            parsed_results = parsed_results[0]
        else:
            continue

    # Safety check: ensure parsed_results is actually a dictionary
    if not isinstance(parsed_results, dict):
        print(f"❌ Expected a dictionary, got {type(parsed_results)}. Raw output:\n{raw_result}")
        break

    step = parsed_results.get("steps")

    if step == "START":
        print("🔥", parsed_results.get("content"))
        #Nudge the model to keep going so it doesn't break character
        message_history.append({"role": "user", "content": "Please proceed to the next step."})
        continue

    elif step == "TOOL":
        tool_to_call = parsed_results.get("tool")
        tool_input = parsed_results.get("input", {}) # Defaults to an empty dict
        
        print(f"🔧 Calling Tool: {tool_to_call} with args: {tool_input}")
        
        # Execute the tool safely
        if tool_to_call in available_tools:
            try:
                # If the LLM passed a dictionary, unpack it into keyword arguments
                if isinstance(tool_input, dict):
                    tool_response = available_tools[tool_to_call](**tool_input)
                
                # Fallback just in case the LLM stubbornly returns a string
                elif isinstance(tool_input, str):
                    tool_response = available_tools[tool_to_call](tool_input)
                    
                else:
                    tool_response = "Error: Input format must be a dictionary or string."
                    
            except Exception as e:
                # Catch errors (like missing arguments) and feed them back to the LLM
                tool_response = f"Tool execution failed: {str(e)}"
        else:
            tool_response = f"Tool {tool_to_call} not found."
            
        # Feed the tool output back to the model as a "user" observation
        # Note: We use standard json.dumps here since we are creating the JSON
        observation = json.dumps({
            "steps": "OBSERVE",
            "tool": tool_to_call,
            "input": tool_input,
            "output": str(tool_response) # Ensure the output is a string
        })
        
        message_history.append({"role": "user", "content": observation})
        continue

    elif step == "PLAN":
        print("🧠", parsed_results.get("content"))
        # ADD THIS: Nudge the model to keep going
        message_history.append({"role": "user", "content": "Please proceed to the next step."})
        continue

    elif step == "OUTPUT":
        print("\n🤖 Final Output:", parsed_results.get("content"))
        break
        
    else:
        print("❓ Unknown step format:", raw_result)
        break