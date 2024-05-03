import streamlit as st
import os
import pymongo
import json
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from openai import OpenAI

uri = "mongodb+srv://rishiraij:5MQ06RORfLYOHkji@100x-assessment.ptowryu.mongodb.net/?retryWrites=true&w=majority&appName=100x-Assessment"

sample_out = """[
    {"$group": { "_id": "$example_key", "count": { "$sum": 1 } }},
    {"$sort": { "count": -1 }},
    {"$limit": 1}
]"""

prompt = prompt = """You will generate a MongoDB aggregation pipeline to help answer a user question based on a given MongoDB collection. 

Please ensure that each pipeline stage specification object contains exactly one field. 
You may have a pipeline with multiple stages, but the key and value of each stage must be encapsulated in curly brackets. 
As an example, a correctly formatted sample output may look like this:
{sample_out}

Please include only the JSON output without any formatting.


A sample document in the collection looks as follows:
{sample_document}

The question is: {query}

Return a JSON formatted aggregation pipeline that can be passed directly to the aggregate call."""

def get_response(query, collection):

    sample_document = str(collection.find_one())
    llm = OpenAI()
    messages = [
            {"role": "system", "content": prompt.format(sample_document = sample_document, query = query, sample_out = sample_out)},
            {"role": "user", "content": query}
    ]
    response = llm.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        temperature=0.0
    )
    llm_out = response.choices[0].message.content
    try:
        aggregated = collection.aggregate(json.loads(llm_out))
    except Exception as e:
        error = str(e)
        messages.append({"role": "system", "content": f"The attempt to run the following aggregation pipeline: \n'{llm_out}'\n returned the following error: {error}. \nPlease fix the error and try again."})
        retry = llm.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
            temperature=0.2
        )
        llm_out = retry.choices[0].message.content
        try:
            aggregated = collection.aggregate(json.loads(llm_out))
        except Exception as e:
            return("Sorry, we are unable to provide the information you requested.")
    aggregated_response = '\n'.join([str(w) for w in aggregated])
    messages.append({"role": "system", "content": f"The aggregation pipeline for the user query '{query}' returned the following JSON object: {aggregated_response}. \nPlease answer the original query in one sentence based on the returned JSON object."})
    natural_language_response = llm.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages
    )
    return(natural_language_response.choices[0].message.content)


def getMongoDB():
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.custom_examples
    collection = db.example_member_info
    return client, db, collection

def upload_mongodb(file_name):
    client, db, collection = getMongoDB()
    collection.delete_many({})
    f = file_name.read()
    json_contents = json.loads(f)
    collection.insert_many(json_contents)
    return client, db, collection


st.title("Chat with your JSON data!")
st.write("This is a tool to interact with JSON data using natural language")

if 'uploaded' not in st.session_state or st.session_state.uploaded == False:
    file_holder, upload_holder = st.empty(), st.empty()
    json_file = file_holder.file_uploader("Upload a JSON data file", type=["json"])
    upload_button = upload_holder.button("Upload")

    if json_file is not None and upload_button:
        try:
            client, db, collection = upload_mongodb(json_file)
            file_holder.empty()
            upload_holder.empty()
            st.session_state.uploaded = True
        except:
            st.error("Unable to upload JSON file.")
            st.session_state.uploaded = False

if 'uploaded' in st.session_state and st.session_state.uploaded:
    query = st.text_area("Please enter your question below:")
    submit_button = st.button("Submit")
    client, db, collection = getMongoDB()
    if query is not None and submit_button:
        st.write(get_response(query, collection))
    finish_button = st.button("Finish")
    if finish_button:
        st.session_state.uploaded = False
        st.experimental_rerun()
