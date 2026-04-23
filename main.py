#!/usr/bin/env python3

import httpx 
import json
import os 
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

api_key = os.getenv("MISTRAL_KEY")
model = "mistral-small-2506"
client = Mistral(api_key=api_key)
temperature = 0.4
system_prompt = "You are a helpful assistant that answers questions in a concise and accurate manner."




'''
FUNCTION CALL 

'''

def get_weather (location: str) -> str :

    '''
    Get the current weather for a given location using the Open-Meteo Geocoding API.
    Parameters:
    - location (str): The name of the location to get the weather for.
    Returns:
    - str: A string containing the current weather information for the specified location.
    '''
    
    with httpx.Client() as client :
        geo_url = client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&format=json&language=en&limit=1")
        geo_data = geo_url.json()

        if not geo_data.get("results") :
            return f"Sorry, I couldn't find any weather data for {location}."

        lat, lon = geo_data["results"][0]["latitude"], geo_data["results"][0]["longitude"]

        weather_url = client.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true")

        print(f"\033[1;36m API call: https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true \033[0m")
        
        weather_data = weather_url.json().get("current_weather", {})


        return f"The current weather in {location} is {weather_data.get('temperature', 'unknown')}°C with a wind speed of {weather_data.get('windspeed', 'unknown')} km/h."



## Function list 
function_list = {
    'get_weather': get_weather    
}

tools = [
    {
        "type": "function",
        "function": {
            "name"  : "get_weather",
            "description" : "Get the current weather for a given location.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "location" : {
                        "type" : "string",
                        "description" : "The name of the location to get the weather for."
                    }
                },
                "required" : ["location"]
            }
        }
    }
]


## Conversation class

class Conversation : 
    def __init__ (self) :
        self.client = client
        self.model = model
        self.temperature = temperature
        self.conversation_history = [{"role": "system", "content": system_prompt}]

    def new_message (self, message: str) :

        self.conversation_history.append({"role": "user", "content": message})


        chat_tools = self.client.chat.complete(
            model=self.model,
            temperature=self.temperature,
            messages=self.conversation_history,
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=False
        )


        if chat_tools.choices[0].message.tool_calls :
            
            self.conversation_history.append( chat_tools.choices[0].message)

            for tool_call in chat_tools.choices[0].message.tool_calls :

                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"\033[1;36m Tool call detected: {function_name} with arguments {function_args} \033[0m")

                if function_name in function_list :
                    function_response = function_list[function_name](**function_args)

                    self.conversation_history.append({
                        "role" : "tool",
                        "name" : function_name,
                        "content" : function_response,
                        "tool_call_id" : tool_call.id
                    })


        chat_response = self.client.chat.complete(
            model=self.model,
            temperature=self.temperature,
            messages=self.conversation_history
        )

        return chat_response.choices[0].message.content

    def get_conversation_history (self) :
        return self.conversation_history


    def clear_conversation_history (self) :
        self.conversation_history = [{"role": "system", "content": system_prompt}]
        return self.conversation_history





def main () :

    print("\033[1;34m  I am a helpful assistant!  \033[0m")

    print("Ask me anything!")
    print("***********************************")

    discussion = Conversation()


    while True :
        user_imput = input("\033[1;32m User (q/quit | cls/clear |  h/history): \033[0m")

        if user_imput.lower() in ["q", "quit"] :
            print("\033[1;31m Goodbye! \033[0m")
            break
        elif user_imput.lower() in ["cls", "clear"] :
            discussion.clear_conversation_history()
            print("\033[1;33m Conversation history cleared! \033[0m")

        elif user_imput.lower() in ["h", "history"] :
            history = discussion.get_conversation_history()
            for message in history :
                role = message["role"]
                content = message["content"]
                print(f"\033[1;34m{role.capitalize()}: \033[0m{content}")

        else :
            response = discussion.new_message(user_imput)
            print(f"\033[1;35m Assistant: \033[0m{response}")



if __name__ == "__main__":
    main()