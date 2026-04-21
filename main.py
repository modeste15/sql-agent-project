#!/usr/bin/env python3

import os 
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

api_key = os.getenv("MISTRAL_KEY")
model = "mistral-small-2506"
client = Mistral(api_key=api_key)
temperature = 0.4
system_prompt = "You are a helpful assistant that answers questions in a concise and accurate manner."


class Conversation : 
    def __init__ (self, client, model) :
        self.client = client
        self.model = model
        self.temperature = temperature
        self.conversation_history = [{"role": "system", "content": system_prompt}]

    def new_message (self, message: str) :
        self.conversation_history.append({"role": "user", "content": message})
        chat_response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=self.conversation_history
        )
        return chat_response.choices[0].message.content



def main () :

    response = client.chat.completions.create(
        model=model,
        temperature=0.4,
        messages=[
            {
                "role": "user",
                "content": "What is the capital of France ?"
            }
        ]
    )

    

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()