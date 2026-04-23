#!/usr/bin/env python3

import httpx 
import json
import os 
from dotenv import load_dotenv
from mistralai.client import Mistral
import psycopg2
from psycopg2.extras import RealDictCursor 

load_dotenv()

api_key = os.getenv("MISTRAL_KEY")
model = "mistral-small-2506"
client = Mistral(api_key=api_key)
temperature = 0.4
system_prompt = """
    You are database assistant that can help users with their PostgreSQL database. You can answer questions about the database schema, and you can also execute SQL queries to get data from the database. 
    You have access to the following tool:
    Get always use the tool when the user asks about the database schema or when you need to execute a SQL query to get data from the database. Do not try to answer questions about the database schema without using the tool, as you do not have access to the database schema directly. Always use the tool to get the database schema and then answer the user's question based on the schema you obtained from the tool.
    - get_pg_schema : Get the PostgreSQL database schema. This tool does not take any arguments and returns a string representation of the database schema.

    Some examples of questions you can answer are:
    - What is the query for getting all users?
    - How many orders were placed in the last month?
    - What are the columns in the users table?
    - What is the data type of the email column in the users table?

    Aside from the schema you obtain from the database connection, provide an answer.
"""



def get_pg_schema () -> str :
    '''
    Get the PostgreSQL database schema as a string.
    Returns:
    - str: A string representation of the PostgreSQL database schema.
    '''

    connection = psycopg2.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB")
    )

    

    result = {}
    connection.autocommit = True

    with connection.cursor() as cur :
        cur.execute("""
            SELECT datname
            FROM pg_database
            WHERE datistemplate = false
        """)
        
        databases = [row[0] for row in cur.fetchall()]

    connection.close()

    for db in databases :
        result[db] = {}

        connection = psycopg2.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=db
        )

        with connection.cursor(cursor_factory=RealDictCursor) as cur :
            cur.execute(f"""
                    SELECT column_name, data_type, table_schema, table_name
                    FROM information_schema.columns
                    WHERE table_name not like 'pg_%' 
                    AND table_schema <> 'information_schema'
                """)

            rows = cur.fetchall()

            for r in rows :
                schema = r["table_schema"]
                table = r["table_name"]
                column = r["column_name"]
                data_type = r["data_type"]

                result[db].setdefault(schema, {})
                result[db][schema].setdefault(table, [])
                result[db][schema][table].append(column)
            
        connection.close()

    print(f"\033[1;36m Database schema obtained: {result} \033[0m")
    return result





## Function list 
function_list = {
    'get_pg_schema': get_pg_schema    
}

tools = [
    {
        "type": "function",
        "function": {
            "name"  : "get_pg_schema",
            "description" : "Get the PostgreSQL database schema.",
            "parameters" : {
                "type" : "object",
                "properties" : {},
                "required" : []
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
                if function_name in function_list:
                    function_response = function_list[function_name](**function_args)

                    # sérialisation propre
                    if isinstance(function_response, str):
                        result_content = function_response
                    else:
                        result_content = json.dumps(function_response)

                    self.conversation_history.append({
                        "role": "tool",
                        "name": function_name,
                        "content": result_content,
                        "tool_call_id": tool_call.id
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