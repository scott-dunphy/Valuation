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
    st.write("API Call URL")
    st.write(url)
    r = requests.get(url)
    return json.dumps(r.json())


def run_conversation(prompt):
    # Initialize conversation history in session state if not present
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
      
    messages = st.session_state.conversation_history + [{"role": "user", "content": f"{prompt}"},
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
                        "description": "Annual market rent growth (e.g. 0.03). The input must be in decimal form so convert 3% to 0.03" ,
                    },
                  "year_1_expense_ratio": {
                        "type": "number",
                        "description": "Ratio of expenses to revenue" ,
                    },
                  "expense_growth_per_year": {
                        "type": "number",
                        "description": "Growth rate for the apartment building's expenses (e.g. 0.03). The input must be in decimal form so convert 3% to 0.03" ,
                    },
                  "capex_per_unit": {
                        "type": "number",
                        "description": "Assumed capital expenditures in $ per unit for the building" ,
                    },
                  "exit_cap_rate": {
                        "type": "number",
                        "description": "Exit capitalization rate used to determine the terminal value of the property in the cash flow. The input must be in decimal form so convert 3% to 0.03" ,
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
            rent_growth_per_year=function_args.get("rent_growth_per_year"),
            year_1_expense_ratio=function_args.get("year_1_expense_ratio"),
            expense_growth_per_year=function_args.get("expense_growth_per_year"),
            capex_per_unit=function_args.get("capex_per_unit"),
            exit_cap_rate=function_args.get("exit_cap_rate"),
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
                )  

        st.session_state.conversation_history += [
          response_message,
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            }
        ]
        return second_response.choices[0].message.content
  
st.set_page_config(page_title='Multifamily AI IRR')
st.title('Multifamily AI IRR')

query_input = st.text_input("Enter your query: ")
if query_input:
  query_input += ". Don't be verbose. If the user asks for cash flows put them in a table formatted as dollars with no decimals. Be sure to include revenue, expense, net operating income, capex, and net cash flow."
  url = ''
  irr = run_conversation(query_input)
  
  write_value = irr
else:
  write_value = ""

st.write(write_value)

# HTML code for the table
html_table = """
<p>
<br><br>
Example Prompt:<br>
Calculate the IRR and cash flows for an Investment with the Following Inputs:<br><br>
Unit Count: 20<br>
Purchase Price: $1,000,000<br>
Market Rent per Unit: $1,200<br>
Rent Growth per Year: 3%<br>
Year 1 Expense Ratio: 50%<br>
Expense Growth per Year: 2%<br>
CapEx Per Unit: $500<br>
Exit Cap Rate: 5%<br>
</p>
<h3>API Function Parameters</h3><br>
<table border="1">
    <tr>
        <th>Parameter</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>unit_count</td>
        <td>Number of units in the apartment.</td>
        <td>20</td>
    </tr>
    <tr>
        <td>purchase_price</td>
        <td>Total price for acquiring the property.</td>
        <td>1,000,000</td>
    </tr>
    <tr>
        <td>market_rent_per_unit</td>
        <td>Average expected rent per unit.</td>
        <td>1,200</td>
    </tr>
    <tr>
        <td>rent_growth_per_year</td>
        <td>Annual rent growth rate.</td>
        <td>3%</td>
    </tr>
    <tr>
        <td>year_1_expense_ratio</td>
        <td>Ratio of expenses to revenue in the first year.</td>
        <td>50%</td>
    </tr>
    <tr>
        <td>expense_growth_per_year</td>
        <td>Annual growth rate of expenses.</td>
        <td>2%</td>
    </tr>
    <tr>
        <td>capex_per_unit</td>
        <td>Annual capital expenditure per unit.</td>
        <td>500</td>
    </tr>
    <tr>
        <td>exit_cap_rate</td>
        <td>Cap rate for estimating the property's sale value.</td>
        <td>5%</td>
    </tr>
</table>


"""

# Display HTML table in Streamlit app
st.markdown(html_table, unsafe_allow_html=True)




    


