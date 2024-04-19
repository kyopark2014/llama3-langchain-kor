import json
import boto3
import os
import time
import datetime
import PyPDF2
import csv
import sys
import re
import traceback

from botocore.config import Config
from io import BytesIO
from urllib import parse
from typing import Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import BedrockChat
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.memory import ConversationBufferWindowMemory
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain_community.llms import SagemakerEndpoint
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain

s3 = boto3.client('s3')
s3_bucket = os.environ.get('s3_bucket') # bucket name
s3_prefix = os.environ.get('s3_prefix')
callLogTableName = os.environ.get('callLogTableName')
bedrock_region = os.environ.get('bedrock_region', 'us-west-2')
path = os.environ.get('path')
doc_prefix = s3_prefix+'/'
endpoint_name = os.environ.get('endpoint_name')

aws_region = boto3.Session().region_name

# websocket
connection_url = os.environ.get('connection_url')
ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=connection_url)
print('connection_url: ', connection_url)

class ContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"
    
    def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
        input_str = json.dumps(
        {
            "inputs": prompt, 
            "parameters": model_kwargs}
        )
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        print('response_json: ', response_json)
        return response_json["generated_text"]

content_handler = ContentHandler()

def initiate_LLM():
    sagemaker_client = boto3.client(
        service_name="sagemaker-runtime",
        region_name=aws_region,
    )
    parameters = {
        "max_new_tokens": 1024, 
        "top_p": 0.9, 
        "temperature": 0.1,
        "stop": "<|eot_id|>"
    } 

    llm = SagemakerEndpoint(
        endpoint_name = endpoint_name, 
        region_name = "us-west-2", 
        model_kwargs = parameters,
        client = sagemaker_client,
        endpoint_kwargs={"CustomAttributes": "accept_eula=true"},
        content_handler = content_handler
    )    
    return llm

llm = initiate_LLM()

map_chain = dict() 
MSG_LENGTH = 100

# load documents from s3 for pdf and txt
def load_document(file_type, s3_file_name):
    s3r = boto3.resource("s3")
    doc = s3r.Object(s3_bucket, s3_prefix+'/'+s3_file_name)
    
    if file_type == 'pdf':
        contents = doc.get()['Body'].read()
        reader = PyPDF2.PdfReader(BytesIO(contents))
        
        raw_text = []
        for page in reader.pages:
            raw_text.append(page.extract_text())
        contents = '\n'.join(raw_text)    
        
    elif file_type == 'txt':        
        contents = doc.get()['Body'].read().decode('utf-8')
        
    print('contents: ', contents)
    new_contents = str(contents).replace("\n"," ") 
    print('length: ', len(new_contents))

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function = len,
    ) 

    texts = text_splitter.split_text(new_contents) 
    print('texts[0]: ', texts[0])
    
    return texts

# load csv documents from s3
def load_csv_document(s3_file_name):
    s3r = boto3.resource("s3")
    doc = s3r.Object(s3_bucket, s3_prefix+'/'+s3_file_name)

    lines = doc.get()['Body'].read().decode('utf-8').split('\n')   # read csv per line
    print('lins: ', len(lines))
        
    columns = lines[0].split(',')  # get columns
    #columns = ["Category", "Information"]  
    #columns_to_metadata = ["type","Source"]
    print('columns: ', columns)
    
    docs = []
    n = 0
    for row in csv.DictReader(lines, delimiter=',',quotechar='"'):
        # print('row: ', row)
        #to_metadata = {col: row[col] for col in columns_to_metadata if col in row}
        values = {k: row[k] for k in columns if k in row}
        content = "\n".join(f"{k.strip()}: {v.strip()}" for k, v in values.items())
        doc = Document(
            page_content=content,
            metadata={
                'name': s3_file_name,
                'row': n+1,
            }
            #metadata=to_metadata
        )
        docs.append(doc)
        n = n+1
    print('docs[0]: ', docs[0])

    return docs

def get_summary(texts):        
    prompt_template = """\n\nUser: 다음 텍스트를 요약해서 500자 이내의 한국어로 설명하세오.

    {text}
        
    Assistant:"""        
    
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT)
    
    docs = [
        Document(
            page_content=t
        ) for t in texts[:3]
    ]
    summary = chain.run(docs)
    print('summary: ', summary)

    if summary == '':  # error notification
        summary = 'Fail to summarize the document. Try agan...'
        return summary
    else:
        # return summary[1:len(summary)-1]   
        return summary
    
def load_chat_history(userId, allowTime):
    dynamodb_client = boto3.client('dynamodb')
    print('loading history.')

    try: 
        response = dynamodb_client.query(
            TableName=callLogTableName,
            KeyConditionExpression='user_id = :userId AND request_time > :allowTime',
            ExpressionAttributeValues={
                ':userId': {'S': userId},
                ':allowTime': {'S': allowTime}
            }
        )
        print('query result: ', response['Items'])
    except Exception:
        err_msg = traceback.format_exc()
        print('error message: ', err_msg)                    
        raise Exception ("Not able to request to DynamoDB")

    for item in response['Items']:
        text = item['body']['S']
        msg = item['msg']['S']
        type = item['type']['S']

        if type == 'text':
            memory_chain.chat_memory.add_user_message(text)
            if len(msg) > MSG_LENGTH:
                memory_chain.chat_memory.add_ai_message(msg[:MSG_LENGTH])                          
            else:
                memory_chain.chat_memory.add_ai_message(msg)            

def getAllowTime():
    d = datetime.datetime.now() - datetime.timedelta(days = 2)
    timeStr = str(d)[0:19]
    print('allow time: ',timeStr)

    return timeStr

def isTyping(connectionId, requestId):    
    msg_proceeding = {
        'request_id': requestId,
        'msg': 'Proceeding...',
        'status': 'istyping'
    }
    #print('result: ', json.dumps(result))
    sendMessage(connectionId, msg_proceeding)
        
def readStreamMsg(connectionId, requestId, stream):
    msg = ""
    if stream:
        for event in stream:
            #print('event: ', event)
            msg = msg + event

            result = {
                'request_id': requestId,
                'msg': msg,
                'status': 'proceeding'
            }
            #print('result: ', json.dumps(result))
            sendMessage(connectionId, result)
    # print('msg: ', msg)
    return msg
    
def sendMessage(id, body):
    try:
        ws_client.post_to_connection( 
            ConnectionId=id, 
            Data=json.dumps(body)
        )
    except Exception:
        err_msg = traceback.format_exc()
        print('err_msg: ', err_msg)
        raise Exception ("Not able to send a message")

def sendResultMessage(connectionId, requestId, msg):    
    result = {
        'request_id': requestId,
        'msg': msg,
        'status': 'completed'
    }
    #print('debug: ', json.dumps(debugMsg))
    sendMessage(connectionId, result)
        
def sendErrorMessage(connectionId, requestId, msg):
    errorMsg = {
        'request_id': requestId,
        'msg': msg,
        'status': 'error'
    }
    print('error: ', json.dumps(errorMsg))
    sendMessage(connectionId, errorMsg)    

def get_summary(texts):    
    prompt_template = """\n\nUser: 다음 텍스트를 요약해서 500자 이내의 한국어로 설명하세오.

    {text}
        
    Assistant:"""
    
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT)

    docs = [
        Document(
            page_content=t
        ) for t in texts[:3]
    ]
    summary = chain.run(docs)
    print('summary: ', summary)

    if summary == '':  # error notification
        summary = 'Fail to summarize the document. Try agan...'
        return summary
    else:
        # return summary[1:len(summary)-1]   
        return summary

def load_chatHistory(userId, allowTime, chat_memory):
    dynamodb_client = boto3.client('dynamodb')

    response = dynamodb_client.query(
        TableName=callLogTableName,
        KeyConditionExpression='user_id = :userId AND request_time > :allowTime',
        ExpressionAttributeValues={
            ':userId': {'S': userId},
            ':allowTime': {'S': allowTime}
        }
    )
    print('query result: ', response['Items'])

    for item in response['Items']:
        text = item['body']['S']
        msg = item['msg']['S']
        type = item['type']['S']

        if type == 'text':
            print('text: ', text)
            print('msg: ', msg)        

            chat_memory.save_context({"input": text}, {"output": msg})    

def RAG(context, query):
    prompt_template = """Use the following pieces of context to answer the question at the end.

    {context}

    Question: {question}
    Answer:"""   
    
    PROMPT = PromptTemplate(
        template=prompt_template, 
        input_variables=["context", "question"]
    )
                
    chain = load_qa_chain(
        llm=llm,                    
        prompt=PROMPT,
    )
    
    msg = chain({"input_documents": context, "question": query}, return_only_outputs=True)
                
    msg = chain.run(query)
    print('msg: ', msg)
    
    return msg

from langchain.chains.llm import LLMChain
def general_conversation2(query):
    prompt_template = """
    <|begin_of_text|>
        <|start_header_id|>system<|end_header_id|>\n\nAlways answer without emojis in Korean<|eot_id|>
        <|start_header_id|>user<|end_header_id|>\n\n"{text}"<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>\n\n"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, 
        input_variables=["text"]
    )
    
    
                
    llm_chain = LLMChain(llm=llm, prompt=PROMPT)
    
    msg = llm_chain({"text": query}, return_only_outputs=True)
    
    return msg['text']


def general_conversation(query):
    prompt_template = """
    <|begin_of_text|>
        <|start_header_id|>system<|end_header_id|>\n\nAlways answer without emojis in Korean<|eot_id|>
        <|start_header_id|>user<|end_header_id|>\n\n"
        History: {chat_history}
        
        Question: {question}
        
        Answer:"<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>\n\n"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, 
        input_variables=["chat_history", "question"]
    )
    
    history = memory_chain.load_memory_variables({})["chat_history"]
    print('memory_chain: ', history)
    
    llm_chain = LLMChain(llm=llm, prompt=PROMPT)
    
    msg = llm_chain({"question": query, "chat_history": history}, return_only_outputs=True)
    
    return msg['text']

def getResponse(connectionId, jsonBody):
    print('jsonBody: ', jsonBody)
    
    userId  = jsonBody['user_id']
    print('userId: ', userId)
    requestId  = jsonBody['request_id']
    print('requestId: ', requestId)
    requestTime  = jsonBody['request_time']
    print('requestTime: ', requestTime)
    type  = jsonBody['type']
    print('type: ', type)
    body = jsonBody['body']
    print('body: ', body)
    convType = jsonBody['convType']
    print('convType: ', convType)
    
    global llm, memory_chain, map_chain
    global enableConversationMode  # debug

    # create memory
    if userId in map_chain:  
        memory_chain = map_chain[userId]
        print('memory_chain exist. reuse it!')
    else: 
        memory_chain = ConversationBufferWindowMemory(memory_key="chat_history", output_key='answer', return_messages=True, k=3)
        map_chain[userId] = memory_chain
        print('memory_chain does not exist. create new one!')

        allowTime = getAllowTime()
        load_chat_history(userId, allowTime)
    
    start = int(time.time())    

    msg = ""
    if type == 'text':
        text = body
        print('query: ', text)

        querySize = len(text)
        textCount = len(text.split())
        print(f"query size: {querySize}, words: {textCount}")

        if text == 'clearMemory':
            memory_chain.clear()
            map_chain[userId] = memory_chain
                    
            print('initiate the chat memory!')
            msg  = "The chat memory was intialized in this session."
        else:            
            if convType == "normal":
                msg = general_conversation(text)                
                print('msg: ', msg)         
            
            memory_chain.chat_memory.add_user_message(text)
            memory_chain.chat_memory.add_ai_message(msg)
                                        
    elif type == 'document':
        isTyping(connectionId, requestId)
            
        object = body
        file_type = object[object.rfind('.')+1:len(object)]            
        print('file_type: ', file_type)
            
        if file_type == 'csv':
            docs = load_csv_document(path, doc_prefix, object)
            contexts = []
            for doc in docs:
                contexts.append(doc.page_content)
            print('contexts: ', contexts)

            msg = get_summary(contexts)
                        
        elif file_type == 'pdf' or file_type == 'txt' or file_type == 'md' or file_type == 'pptx' or file_type == 'docx':
            texts = load_document(file_type, object)

            docs = []
            for i in range(len(texts)):
                docs.append(
                    Document(
                        page_content=texts[i],
                        metadata={
                            'name': object,
                            # 'page':i+1,
                            'uri': path+doc_prefix+parse.quote(object)
                        }
                    )
                )
            print('docs[0]: ', docs[0])    
            print('docs size: ', len(docs))

            contexts = []
            for doc in docs:
                contexts.append(doc.page_content)
            print('contexts: ', contexts)

            msg = get_summary(contexts)
            
            memory_chain.chat_memory.add_user_message(text)
            memory_chain.chat_memory.add_ai_message(msg)
                
    elapsed_time = int(time.time()) - start
    print("total run time(sec): ", elapsed_time)        
    print('msg: ', msg)

    item = {
        'user_id': {'S':userId},
        'request_id': {'S':requestId},
        'request_time': {'S':requestTime},
        'type': {'S':type},
        'body': {'S':body},
        'msg': {'S':msg}
    }

    dynamo_client = boto3.client('dynamodb')
    try:
        resp =  dynamo_client.put_item(TableName=callLogTableName, Item=item)
    except Exception:
        err_msg = traceback.format_exc()
        print('error message: ', err_msg)
        raise Exception ("Not able to write into dynamodb")               
    #print('resp, ', resp)

    return msg

def lambda_handler(event, context):
    # print('event: ', event)    
    msg = ""
    if event['requestContext']: 
        connectionId = event['requestContext']['connectionId']        
        routeKey = event['requestContext']['routeKey']
        
        if routeKey == '$connect':
            print('connected!')
        elif routeKey == '$disconnect':
            print('disconnected!')
        else:
            body = event.get("body", "")
            #print("data[0:8]: ", body[0:8])
            if body[0:8] == "__ping__":
                # print("keep alive!")                
                sendMessage(connectionId, "__pong__")
            else:
                print('connectionId: ', connectionId)
                print('routeKey: ', routeKey)
        
                jsonBody = json.loads(body)
                print('request body: ', json.dumps(jsonBody))

                requestId  = jsonBody['request_id']
                try:
                    msg = getResponse(connectionId, jsonBody)
                    print('result msg: ', msg)
                    
                    sendResultMessage(connectionId, requestId, msg)  
                                        
                except Exception:
                    err_msg = traceback.format_exc()
                    print('err_msg: ', err_msg)

                    sendErrorMessage(connectionId, requestId, err_msg)    
                    raise Exception ("Not able to send a message")

    return {
        'statusCode': 200
    }