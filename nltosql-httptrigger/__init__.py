## ------------------------------------------------ Libraries
import logging
import azure.functions as func
import json
import datetime
import os
import textwrap
from sqlalchemy import text

import pyodbc

import openai
import pandas as pd
import numpy as np

# ------------------------------------------------ Setup
def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    

# Load config values
with open(r'nltosql-httptrigger/config.json') as config_file:
    config_details = json.load(config_file)
    
# Setting up the deployment name
deployment_name = config_details['DEPLOYMENT_NAME']

# This is set to `azure`
openai.api_type = "azure"

# The API key for your Azure OpenAI resource.
openai.api_key = config_details["OPENAI_API_KEY"]

# The base URL for your Azure OpenAI resource. e.g. "https://<your resource name>.openai.azure.com"
openai.api_base = config_details['OPENAI_API_BASE']

# Currently Chat Completion API have the following versions available: 2023-07-01-preview
openai.api_version = config_details['OPENAI_API_VERSION']


# ------------------------------------------------ Main Function

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Initiating Python HTTP trigger function to process a request.')

    server = config_details['SERVER']
    database = config_details['DATABASE']
    username = config_details['USERNAME']
    password = config_details['PASSWORD']   
    driver= '{ODBC Driver 18 for SQL Server}'
    finaloutput = "\n"

    #user_input = req.params.get('user_input')
    #logging.info(str(user_input))
    
    user_input_bytes = req.get_body()
    user_input = user_input_bytes.decode('utf-8')
    contents = json.loads(user_input)
    user_input_test = contents['user_input']
    logging.info("User input: " + str(user_input_test))

    #user_input = 'What is the total amount?'
    query_string = f'''\n
    
    Below is the schema of the table dbo.sales_data:
    sale_id INT PRIMARY KEY,
    region VARCHAR(50),
    product_name VARCHAR(100),
    sale_date DATE,
    amount DECIMAL(10, 2)\n\n
    
    Return only the SQL query and no other explanation.

    ### A SQL query to answer the question: {user_input} for the table Sales is:\n
    '''
    logging.info(query_string)

    system_msg = 'You are a SQL coder who writes meaningful SQL queries to run on databases.'

    logging.info('Calling OpenAI API to process user input.')

    response = openai.ChatCompletion.create(
        deployment_id = deployment_name,
        messages=[{"role": "system", "content": system_msg},{"role": "user", "content": query_string}],
        temperature=0 
    )   
    # answer to return
    sql_query = response["choices"][0]["message"]["content"]

    logging.info('Query to run: ' + sql_query)

    logging.info(pyodbc.drivers())

    connection_string = textwrap.dedent('''
    DRIVER={driver};
    SERVER=tcp:{server};
    PORT=1433;
    DATABASE={database};
    UID={username};
    PWD={password};
    Encrypt=yes;
    trustServerCertificate=no;
    connection timeout=30;
    '''.format(
        driver=driver,
        server=server,
        database=database,
        username=username,
        password=password
        ).replace("'", "")
    )

    logging.info('Connecting to the database.')
    try:
        conn: pyodbc.Connection = pyodbc.connect(connection_string)
    except:
        TimeoutError
        conn: pyodbc.Connection = pyodbc.connect(connection_string)

    logging.info('Connection to the database established.')

    #create cursor object
    cursor_object: pyodbc.Cursor = conn.cursor()

    # Execute the query
    cursor_object.execute(sql_query)

    # Fetchall the rows
    records = list(cursor_object.fetchall())

    # Clean up the recordset
    records = [tuple(record) for record in records]

    '''
    logging.info('Running the SQL query on the database.')
    with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
          with conn.cursor() as cursor:
              cursor.execute(answer)
              row = cursor.fetchone()
              result = str(row[0])
              #while row:
                #finaloutput = finaloutput + (str(row[0]) + " " + str(row[1]) + "\n")
                #row = cursor.fetchone()
    '''    
    logging.info('Returning the response.')

    return func.HttpResponse(
        body = json.dumps(f"Answer: {records}", default=default),
        status_code=200
    )
