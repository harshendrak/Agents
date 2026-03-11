import os 
import ollama
import json
import requests

def run_commands(cmd:str):
    result =os.popen(cmd).read()
    return result


available_tools ={

    "run_commands": run_commands

}

SYSTEM_PROMPT = """ You are an expert AI Assistant in resolving user queries using Chain of Thought.
You work on START, PLAN , OUTPUT steps. 
Once you think enough PLAN has been done, finally you can give an OUTPUT.
You can also call a tool if required from the list of available tools.
For every tool call wait for the observe steps which is the output from the called tool.

Rules:
- Strictly follow the given JSON format.
- Only run one step at a time.
- The sequence of steps is START (where user gives an input), PLAN(that can be multiple times)
 and finally OUTPUT(which is going to be displayed to the user).

 Output JSON Format:
 { "steps":"START"|"PLAN"|"OUTPUT"|"TOOL","content":"string","tool":"string","input":{"parameter_name":"parameter_value"}}

Availabe Tools:
 run_command(cmd:str): Takes linux command and returns the output.

Example Tool Call with multiple arguments :
PLAN:{"steps":"TOOL",tool":"write_file","input":{"filepath":"hello.txt","content":"Hello World"}}

Example 1:
START: Hey, can you solve 2+3*5/10
PLAN:{"steps":"PLAN","content":"Seems like the user is intrested in maths problem"}
PLAN:{"steps":"PLAN","content":"Looking at the problem, we should solve this using BODMAS method."}
PLAN:{"steps":"PLAN","content":"first we should multiply 3*5 which is 15 "}
PLAN:{"steps":"PLAN","content":"Now the equation is 2 + 15/10"}
PLAN:{"steps":"PLAN","content":"we must perform divide that is 15/10 which is 1.5"}
PLAN:{"steps":"PLAN","content":"now the equation is 2+1.5"}
PLAN:{"steps":"PLAN","content":"now finaaly perform the addition which is 3.5"}
PLAN:{"steps":"OUTPUT","content":"3.5"}

Example 2:
START: What is the weather of Delhi ?
PLAN:{"steps":"PLAN","content":"Seems like the user is intrested in weather information about the city delhi in India."}
PLAN:{"steps":"PLAN","content":"Let's see if we have any available tool from the list of available tools."}
PLAN:{"steps":"TOOL","tool":"get_weather","input":"delhi"}
OBSERVE:{"steps":"OBSERVE","tool":"get_weather","output":"The temp of delhi is cloudy with 20 C."}
PLAN:{"steps":"PLAN","content":"Great, I got the weather info about delhi."}
OUTPUT:{"steps":"OUTPUT","content":"The current weather in delhi is 20 C with some cloudy sky."}



"""

user_input = input("Hey I can write code for you : ")

message_history = [
    {"role":"system","content":SYSTEM_PROMPT},
    {"role":"user","content":user_input}
]

print("\nGetting things ready\n")


while True:
    response = ollama.chat(
        model="qwen3-coder-next:cloud",
        messages=message_history,
        format="json"
    )



    raw_results = response['message']['content']

    message_history.append({"role":"assiastant","content":raw_results})

    try:
        parsed_results=json.loads(raw_results)
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON",raw_results)
        break


    if isinstance(parsed_results,list):
        if len(parsed_results) > 0:
            parsed_results = parsed_results[0]

        else :
            continue



    step = parsed_results.get("steps")

    if step == "START":
        print("🔥", parsed_results.get("content"))
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
        observation = json.dumps({
            "steps": "OBSERVE",
            "tool": tool_to_call,
            "input": tool_input,
            "output": str(tool_response) # Ensure the output is a string
        })
        
        message_history.append({"role": "user", "content": observation})
        continue
        
        # Execute the tool safely
        if tool_to_call in available_tools:
            tool_response = available_tools[tool_to_call](tool_input)
        else:
            tool_response = f"Tool {tool_to_call} not found."
            
        # Feed the tool output back to the model as a "user" observation
        observation = json.dumps({
            "steps": "OBSERVE",
            "tool": tool_to_call,
            "input": tool_input,
            "output": tool_response
        })
        
        message_history.append({"role": "user", "content": observation})
        continue

    elif step == "PLAN":
        print("🧠", parsed_results.get("content"))
        continue

    elif step == "OUTPUT":
        print("\n🤖 Final Output:", parsed_results.get("content"))
        break
        
    else:
        print("❓ Unknown step format:", raw_results)
        break



