import streamlit as st
import urllib,io
import pymongo
import json
from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = uri = "mongodb+srv://rishiraij:5MQ06RORfLYOHkji@100x-assessment.ptowryu.mongodb.net/?retryWrites=true&w=majority&appName=100x-Assessment"

def upload_mongodb(file_name):
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.custom_examples
    collection = db.example_member_info
    collection.delete_many({})
    f = file_name.read()
    json_contents = json.loads(f)
    collection.insert_many(json_contents)
    return client, db, collection

def close_client(client, collection):
    #TODO: Add code to clear collection
    client.close()


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

    if query is not None and submit_button:
        st.write(query)
    finish_button = st.button("Finish")
    if finish_button:
        st.session_state.uploaded = False
        st.experimental_rerun()

# close_client(client, collection)
