from openai import OpenAI
client = OpenAI()
import json
import pandas as pd
import requests
import streamlit as st
import os
import base64
from urllib.parse import urlparse, parse_qs

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

def irr(unit_count, purchase_price, market_rent_per_unit, rent_growth_per_year, 
                 year_1_expense_ratio, expense_growth_per_year, capex_per_unit, exit_cap_rate):
    url = f"https://scott-irr.replit.app/irr?unit_count={unit_count}&purchase_price={purchase_price}&market_rent_per_unit={market_rent_per_unit}&rent_growth_per_year={rent_growth_per_year}&year_1_expense_ratio={year_1_expense_ratio}&expense_growth_per_year={expense_growth_per_year}&capex_per_unit={capex_per_unit}&exit_cap_rate={exit_cap_rate}"
    st.write(url)
    r = requests.get(url)
    
    return json.dumps(r.json())


def run_conversation(prompt, messages):
    
    # Step 1: send the conversation and available functions to GPT
    #prompt = input("What is your query?: ")
    messages = [{"role": "user", "content": f"{prompt}"},
                {"role": "system", "content": """
                 Take a deep breath and go step-by-step.
                 You are a helpful assistant creating a function call to an API.
                 """ 
                 
                 }]
    functions = [
        {
            "name": "irr",
            "description": """ 
                                Calculates the IRR of an apartment property based on entered assumptions.
                            """,
           "parameters": {
                "type": "object",
                "properties": {
                    "unit_count": {
                        "type": "number",
                        "description": "The number of units in an apartment building" ,
                    },
                  "purchase_price": {
                        "type": "number",
                        "description": "The purchase price of the apartment building" ,
                    },
                  "market_rent_per_unit": {
                        "type": "number",
                        "description": "Market rent per unit for the apartment building (e.g. $2,000)" ,
                    },
                  "rent_growth_per_year": {
                        "type": "number",
                        "description": "Annual market rent growth (e.g. 3.00%)" ,
                    },
                  "year_1_expense_ratio": {
                        "type": "number",
                        "description": "Ratio of expenses to revenue" ,
                    },
                  "expense_growth_per_year": {
                        "type": "number",
                        "description": "Growth rate for the apartment building's expenses" ,
                    },
                  "capex_per_unit": {
                        "type": "number",
                        "description": "Assumed capital expenditures in $ per unit for the building" ,
                    },
                  "exit_cap_rate": {
                        "type": "number",
                        "description": "Exit capitalization rate used to determine the terminal value of the property in the cash flow" ,
                    },

                },
                     
            },
        }
    ]
    
    
    response = client.chat.completions.create(model="gpt-4-1106-preview",
    temperature = .5,
    messages=messages,
    functions=functions,
    function_call="auto")
    response_message = response.choices[0].message

    if response_message.function_call:
        available_functions = {
            "irr": irr,
        }  
        function_name = response_message.function_call.name
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(response_message.function_call.arguments)
        #st.write(function_args)
        function_response = fuction_to_call(
            unit_count=function_args.get("unit_count"),
            purchase_price=function_args.get("purchase_price"),
            market_rent_per_unit=function_args.get("market_rent_per_unit"),
            rent_growth_per_year=function_args.get("rent_growth_per_year")/100,
            year_1_expense_ratio=function_args.get("year_1_expense_ratio")/100,
            expense_growth_per_year=function_args.get("expense_growth_per_year")/100,
            capex_per_unit=function_args.get("capex_per_unit"),
            exit_cap_rate=function_args.get("exit_cap_rate")/100,
        )

        messages.append(response_message) 
        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            }
        )
      
        second_response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
                )  # get a new response from the model where it can see the function response
        return second_response.choices[0].message.content, messages

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
  
st.set_page_config(page_title='Multifamily AI IRR')
st.title('Multifamily AI IRR')

write_value = "Enter query"


query_input = st.text_input("Enter your query: ")

url = ''
irr, messages = run_conversation(query_input, messages)

st.session_states.messages.append(messages)

write_value = irr
st.write(write_value)



    


