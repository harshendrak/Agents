import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
from pydantic import BaseModel, Field
from typing import Optional
import time

# 1. Load the variables from the .env file into your environment
load_dotenv()

# 2. Fetch the API key securely
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API Key not found. Please check your .env file.")

client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# ... [The rest of your code remains the same] ...
def get_weather(city:str):
    url=f"https://wttr.in/{city.lower()}?format=%C+%t"  

    response=requests.get(url)  

    if response.status_code==200:
        return f"The weather in {city} is: {response.text}"
    
    return "Something went wrong"

available_tools={
    "get_weather":get_weather
}

SYSTEM_PROMPT=""" You are an expert AI Assistant in resolving user queries using chain of thought.
You work on START,PLAN,OUTPUT steps.
You need to first PLAN and what needs to be done. The PLAN can be multiple steps.
Once you think enough PLAN has been done, finally you can give an OUTPUT.

Rules:
- Strictly Follow the given JSON format
- Only run one steps at a time.
- The sequence of steps is START (where user gives an input), PLAN(That can be multiple
times) and finally OUTPUT (which is going to be displayed to the user.)
You can also call a tool if required from the list of available tools.
For every tool call wait for the observe steps which is the output from the called tool.


Output JSON Format:
{"step":"START"|"PLAN"|"OUTPUT" |"TOOL","content":"string","tool":"string","input":"string"}

Available Tools:
get_weather(city:str) : Takes the city name as an input string and returns the weather info about the city.



Example 1:
START: Hey, can you solve 2+3*5/10
PLAN:{"step":"PLAN","content":"Seems like the user is intrested in
 maths problem"}
PLAN:{"step":"PLAN","content":"Looking at the problem, 
we should solve this using BODMAS method."}
PLAN:{"step":"PLAN","content":"Yes, the BODMAS is the correct 
thing to be done here."}
PLAN:{"step":"PLAN","content":"first we should multiply 3*5 which is 15 "}
PLAN:{"step":"PLAN","content":"Now the equation is 2 + 15/10"}
PLAN:{"step":"PLAN","content":"we must perform divide that is 15/10 which is 1.5"}
PLAN:{"step":"PLAN","content":"now the equation is 2+1.5"}
PLAN:{"step":"PLAN","content":"now finaaly perform the addition which is 3.5"}
PLAN:{"step":"PLAN","content":"Great! we've solved the problem and left with the answer which is 
3.5"}
PLAN:{"step":"OUTPUT","content":"3.5"}

Example 2:
START: What is the weather of Delhi ?
PLAN:{"step":"PLAN","content":"Seems like the user is intrested in
 weather information about the city delhi in India."}
PLAN:{"step":"PLAN","content":"Let's see if we have any available tool from the list of available tools."}
PLAN:{"step":"PLAN","content":"Great, we have the get_weather tool available."}
PLAN:{"step":"PLAN","content":"I need to call the tool get_weather for the city Delhi as input for city."}
PLAN:{"step":"TOOL","tool":"get_weather","input":"delhi"}
PLAN:{"step":"OBSERVE","tool":"get_weather","output":"The temp of delhi is cloudy with 20 C."}
PLAN:{"step":"PLAN","content":"Great, I got the weather info about delhi."}
OUTPUT:{"step":"OUTPUT","content":"The current weather in delhi is 20 C with some cloudy sky."}


"""
class MyOutputFormat(BaseModel):
    step : str = Field(...,description="The ID oof the step, plan ")
    content : Optional[str] = Field(None,description="The optional string content for content")
    tool : Optional[str]= Field(None,description="The ID of the tool to call.")
    input: Optional[str]=Field(None,description="The input params for the tool")


message_history = [
    {"role":"system","content":SYSTEM_PROMPT}

]

user_input=input("Ask for the Weather \n")
message_history.append({"role":"user","content":user_input})

while True:
    time.sleep(12)
    response = client.chat.completions.parse(
    model="gemini-2.5-flash",
    response_format=MyOutputFormat,
    messages=message_history
    )
    raw_result = response.choices[0].message.parsed
    
    # Convert the Pydantic object back to a JSON string for the message history
    message_history.append({"role": "assistant", "content": raw_result.model_dump_json()})
    
    parsed_results = raw_result
                

    if parsed_results.step== "START":
        print("🔥",parsed_results.content)
        continue

    if parsed_results.step=="TOOL":
        tool_to_call=parsed_results.tool
        tool_input=parsed_results.input
        print(f"⚙️ { tool_to_call} {tool_input}")

        tool_response = available_tools[tool_to_call](tool_input)
        print(f"⚙️ { tool_to_call} {tool_input} = {tool_response}")
        message_history.append({"role":"developer","content":json.dumps({"step":"OBSERVE","tool":tool_input,"output":tool_response})})
        continue

    if parsed_results.step=="PLAN":
        print("🧠",parsed_results.content)
        continue
    if parsed_results.step=="OUTPUT":
        print("🤖",parsed_results.content)
        break


print(response.choices[0].message.content)


