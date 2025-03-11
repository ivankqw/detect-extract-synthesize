from google.cloud import storage
import time
from typing import List
from db import Database
from doc_uploader import DocUploader
from pydantic import BaseModel
import asyncio
import uvicorn
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Response, BackgroundTasks
import io

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from vector_db import VectorDB

app_env = os.environ.get("APP_ENVIRONMENT")
app_host = os.environ.get("APP_HTTP_HOST")
app_port = int(os.environ.get("APP_HTTP_PORT"))

is_prod = os.environ.get("APP_ENVIRONMENT") == "prod"

if is_prod:
    pg_uri = os.environ.get("PGURL_PROD")
else:
    pg_uri = os.environ.get("PGURL_DEV")

qdrant_url = os.environ.get("QDRANT_URL")
qdrant_api_key = os.environ.get("QDRANT_API_KEY")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

assert pg_uri is not None, "PGURL environment variable not set"

app = FastAPI()
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm = ChatAnthropic(
    streaming=True,
    verbose=True,
    temperature=0,
    anthropic_api_key=anthropic_api_key,
    model="claude-3-opus-20240229"
)

# INIT DATABASES
db = Database(pg_uri)
try:
    db._setup()
except Exception as e:
    print(f"Error initializing database: {e}")
    raise e

vector_db = VectorDB(api_key=qdrant_api_key, url=qdrant_url)
try:
    vector_db._setup()
except Exception as e:
    print(f"Error initializing vector database: {e}")
    raise e

storage_client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
bucket = storage_client.get_bucket("fyp_pdfs")

upload_status_tracker = {}


async def process_file(doc_uploader: DocUploader):
    try:
        uid = doc_uploader.uid
        await doc_uploader.parse()
        upload_status_tracker[uid] = True
    except Exception as e:
        print(f"Error parsing file: {e}")
        upload_status_tracker[uid] = False


@app.post('/backend/upload')
async def upload(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    try:
        contents = file.file.read()
        destination_blob_name = os.path.basename(file.filename)
        curr_blob = bucket.blob(destination_blob_name)
        curr_blob.upload_from_string(contents, content_type=file.content_type)
    except asyncio.TimeoutError:
        return {"status": "error", "message": "Timeout occurred while reading the file."}
    except Exception as e:
        print(f"Error uploading file to GCS: {e}")
        return {"status": "error", "message": "Error uploading file to GCS"}

    try:
        doc_uploader = DocUploader(is_nerfed=False,
                                   storage_client=storage_client,
                                   bucket=bucket,
                                   blob=curr_blob,
                                   db=db,
                                   vector_db=vector_db)
        # Generate a unique identifier for the upload
        uid = doc_uploader.uid
        upload_status_tracker[uid] = False  # Initially set the status to False
        # Create a background task to process the file
        background_tasks.add_task(process_file, doc_uploader)
        return {"status": "success", "message": "File uploaded successfully", "uid": uid}
    except Exception as e:
        print(f"Error parsing file: {e}")
        return {"status": "error", "message": "Error parsing file"}


@app.get('/backend/upload-status/{uid}')
async def get_upload_status(uid: str):
    if uid not in upload_status_tracker:
        return {"status": "error", "message": "UID not found"}
    return {"status": "success", "message": "Upload status retrieved successfully", "is_parsed": upload_status_tracker[uid]}


@app.get('/backend/docs')
def get_docs():
    fyp_docs = db.get_all_documents()
    return {"docs": fyp_docs}


@app.get('/backend/docs-search/{query}')
def get_docs_given_query(query: str):
    print(query)
    doc_ids = vector_db.get_relevant_docs(query)
    fyp_docs = db.get_documents(doc_ids)
    print(fyp_docs)
    return {"docs": fyp_docs}


# this is to pass the pdf metadata to the frontend to render to correct pdf and correct bboxes
@app.get('/backend/docs/{doc_id}')
def get_doc(doc_id: str):
    print(f"get_doc: {doc_id}")
    try:
        fyp_doc = db.get_document(doc_id)
    except Exception as e:
        print(f"Error retrieving document: {e}")
        return {"status": "error", "message": "Error retrieving document"}

    if fyp_doc is None:
        return {"status": "error", "message": "Document not found"}

    return {"status": "success", "doc": fyp_doc}

# this is to render the whole pdf in the frontend


@app.get('/backend/getpdf/{doc_id}')
def get_pdf(doc_id: str, background_tasks: BackgroundTasks):
    print(f"get_pdf: {doc_id}")
    fyp_doc = db.get_document(doc_id)
    if fyp_doc is None:
        return {"status": "error", "message": "Document not found"}

    doc_path = fyp_doc.path
    try:
        blob = bucket.blob(doc_path)
        buffer = io.BytesIO(blob.download_as_bytes())
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return {"status": "error", "message": "Error reading PDF file"}

    background_tasks.add_task(buffer.close)
    headers = {'Content-Disposition': f'inline; filename="{doc_id}.pdf"'}
    return Response(buffer.getvalue(), headers=headers, media_type='application/pdf')


class Message(BaseModel):
    role: str
    content: str


class Messages(BaseModel):
    doc_id: str
    messages: List[Message]


@app.post('/backend/ask')
async def ask(messages: Messages):
    doc_id = messages.doc_id
    # Reverse the messages and then extract the latest human message
    reversed_messages = list(reversed(messages.messages))
    human_message_idx = next((len(reversed_messages) - i - 1 for i, message in enumerate(
        reversed_messages) if message.role == "user"), None)
    if human_message_idx is None:
        raise HTTPException(
            status_code=400, detail="No human message found in the payload")
    human_message = messages.messages[human_message_idx]
    # then call vector db to get the relevant context given the human message
    start = time.time()
    doc_name = db.get_document(doc_id).name
    context = vector_db.get_relevant_texts(doc_id, human_message.content)
    print(f"Time taken to get relevant texts: {time.time() - start}")
    print("CONTEXT:", context)
    print("QUESTION:", human_message.content)
    # modify the human message to include the context
    human_message.content = f"""
    All context are extracted from a document named {doc_name}.
    Using the provided context (refer to this as your knowledge base), answer the question in detail and provide insightful explanations. Use the context as much as possible and quote relevant parts of the context to support your answer. Also, provide the page number(s) where the relevant information is found in the context.

    Format your answer as follows:

    Page number: <page number>
    Answer: <detailed answer using the context and relevant quotes>

    Page number: <page number>
    Answer: <detailed answer using the context and relevant quotes>

    ...

    If the context is not enough to answer the question, respond with "My knowledge base is not sufficient to answer the question."

    Context:
    {context}

    Question:
    {human_message.content}
    """
    # remove the previous human message and add the modified one
    messages.messages.pop(human_message_idx)
    messages.messages.insert(human_message_idx, human_message)

    # convert the messages to the correct format
    formatted_messages = [HumanMessage(content=message.content) if message.role == "user" else AIMessage(
        content=message.content) for message in messages.messages]

    def generator(formatted_messages):
        for item in llm.stream(formatted_messages):
            yield item.content

    return StreamingResponse(
        generator(formatted_messages), media_type='text/event-stream')


if __name__ == "__main__":
    uvicorn.run("main:app", host=app_host,
                reload=True, port=app_port, workers=5, timeout_keep_alive=120)
