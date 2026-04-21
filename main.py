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
    def __init__ (self) :
        self.client = client
        self.model = model
        self.temperature = temperature
        self.conversation_history = [{"role": "system", "content": system_prompt}]

    def new_message (self, message: str) :
        self.conversation_history.append({"role": "user", "content": message})

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