This repository is built to deploy a lightweight NL to SQL chatbot implementation.

Language - Python

Azure services used - 
1. Azure SQL - to store data in a relational DB
2. Azure OpenAI - LLM model for answering questions
3. Azure functions - HTTP based orchestration layer between user inputs, openai completions and running SQL query on Azure SQL

Additionally this is deployed with a frontend django app (hosted on Azure web app) or logic can be easily integrated as an API.

Pending - ci/cd deployments using actions (ongoing), architecture diagram, django app code
