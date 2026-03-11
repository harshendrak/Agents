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