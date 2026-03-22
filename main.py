import os 
import ollama
import requests
import json
import json_repair



def generate_ui(prompt: str, filepath: str = "index.html"):
    print(f"\n🎨 [Stitch Tool] Generating UI: {prompt}...\n")
    
    # Strict system prompt to ensure we only get code back
    ui_system_prompt = """You are an expert frontend developer and UI designer. 
    Your job is to generate a complete, single-file HTML document using Tailwind CSS (via CDN) and vanilla JavaScript.
    Follow the user's design prompt exactly.
    CRITICAL: Output ONLY the raw HTML code. Do NOT wrap it in markdown blockquotes (```html). Do NOT provide any explanations."""
    
    try:
        # We spin up a specialized sub-task just for writing the UI
        response = ollama.chat(
            model="qwen3-coder-next:cloud", # Or your preferred coding model
            messages=[
                {"role": "system", "content": ui_system_prompt},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.3} # Slight creativity for design
        )
        
        html_content = response['message']['content']
        
        # Fallback to strip markdown if the model disobeys the prompt
        if html_content.startswith("```"):
             html_content = html_content.strip("`").replace("html\n", "", 1).strip()
             
        # Reuse your existing write_file function to save it
        return write_file(filepath, html_content)
        
    except Exception as e:
        return f"Error generating UI: {e}"

def run_command(cmd:str):
    result =os.popen(cmd).read()
    return result

def write_file(filepath: str, content: str):
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Wrote content to {filepath}"
    except Exception as e:
        return f"Error writing file: {e}"
    
def search_wikipedia(query: str):
    # Format the query for the Wikipedia URL
    formatted_query = query.replace(' ', '_')
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_query}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("extract", "No summary found on this page.")
        else:
            return f"No Wikipedia page found exactly matching '{query}'."
    except Exception as e:
        return f"Error searching Wikipedia: {e}"
    

def get_weather(city: str):
    url = f"https://wttr.in/{city.lower()}?format=%C+%t"  
    response = requests.get(url)  
    if response.status_code == 200:
        return f"The weather in {city} is: {response.text}"
    return "Something went wrong"
    

def read_file(filepath: str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Truncate if it's massive so we don't blow up the context window
            return content[:2000] + "\n...[truncated]" if len(content) > 2000 else content
    except Exception as e:
        return f"Error reading file: {e}"

available_tools ={

    "run_command": run_command,
    "read_file": read_file,           
    "write_file": write_file,
    "get_weather":get_weather,
    "search_wikipedia":search_wikipedia,
    "generate_ui": generate_ui

}
SYSTEM_PROMPT = """You are an expert CLI Coding AI Assistant. You resolve user programming queries using a strict Chain of Thought (CoT) process.
Your workflow strictly follows the sequence: START -> PLAN (can repeat) -> TOOL (if needed) -> OBSERVE (wait for system) -> OUTPUT.

RULES:
1. Strictly follow the given JSON format. Do not wrap the JSON in Markdown formatting.
2. Only output ONE step at a time.
3. NEVER output raw, multi-line code (like HTML, JS, or Python) inside the "OUTPUT" step. 
4. If the user asks you to create an app, script, or write code, you MUST use the "write_file" tool to save the code to the disk. 
5. The "OUTPUT" step is ONLY for summarizing what you did or chatting with the user.
6. Ensure all double quotes and newlines inside your JSON values are strictly escaped to prevent parsing errors.
7. NEVER generate an "OBSERVE" step yourself. You must generate a "TOOL" step and wait for the system to return the observation.
Output JSON Format:
{"steps":"START"|"PLAN"|"OUTPUT"|"TOOL","content":"string","tool":"string","input":{"param_name": "param_value"}}

Available Tools:
get_weather(city:str) : Takes the city name and returns the weather.
run_command(cmd:str): Executes a bash/linux command and returns the output.
read_file(filepath:str): Reads the text content of a local file.
write_file(filepath:str, content:str): Creates or overwrites a file with the given content. 
search_wikipedia(query:str): Takes a search term and returns a Wikipedia summary.
generate_ui(prompt:str, filepath:str): Acts as an expert UI designer. Pass a description of the UI (prompt) and the desired filename (filepath), and it will generate and save a complete HTML/Tailwind web page.

Example 1: Creating and running a script
START: Can you write a python script called test.py that prints "Hello World" and then run it?
PLAN:{"steps":"PLAN","content":"The user wants a python script named test.py. I need to use write_file first."}
PLAN:{"steps":"TOOL","tool":"write_file","input":{"filepath":"test.py", "content":"print('Hello World')\\n"}}
OBSERVE:{"steps":"OBSERVE","tool":"write_file","output":"Success: Wrote content to test.py"}
PLAN:{"steps":"PLAN","content":"The file is created. Now I need to run it using the run_command tool."}
PLAN:{"steps":"TOOL","tool":"run_command","input":{"cmd":"python3 test.py"}}
OBSERVE:{"steps":"OBSERVE","tool":"run_command","output":"Hello World\\n"}
PLAN:{"steps":"PLAN","content":"The script ran successfully. I will now notify the user."}
OUTPUT:{"steps":"OUTPUT","content":"I have created the test.py file and ran it. The execution output was: Hello World"}

Example 2: Creating a web project
START: Create a simple index.html file with a heading that says "My App".
PLAN:{"steps":"PLAN","content":"The user wants an HTML file. I must NOT output the HTML code directly in my response. I will use the write_file tool."}
PLAN:{"steps":"TOOL","tool":"write_file","input":{"filepath":"index.html", "content":"<!DOCTYPE html>\\n<html>\\n<head>\\n<title>App</title>\\n</head>\\n<body>\\n<h1>My App</h1>\\n</body>\\n</html>"}}
OBSERVE:{"steps":"OBSERVE","tool":"write_file","output":"Success: Wrote content to index.html"}
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
    
    elif step == "OBSERVE":
        print("⚠️ Agent hallucinated an observation. Correcting...")
        # Tell the LLM it made a mistake and force it to use the TOOL step
        message_history.append({
            "role": "user", 
            "content": "Error: You are not allowed to generate 'OBSERVE' steps. You must output a 'TOOL' step with the correct tool and input to actually execute the action."
        })
        continue


    elif step == "OUTPUT":
        print("\n🤖 Final Output:", parsed_results.get("content"))
        break
        
    else:
        print("❓ Unknown step format:", raw_result)
        break