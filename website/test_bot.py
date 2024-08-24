import os
import openai
from dotenv import find_dotenv, load_dotenv
import pandas as pd
from langchain_openai import ChatOpenAI
import json


from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader




openai.api_key  = os.environ['OPENAI_API_KEY']

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

from langchain_core.tools import tool


def csv_search(question:str):
    import pandas as pd
    from langchain_experimental.agents.agent_toolkits import create_csv_agent
    agent = create_csv_agent(llm=llm, path ='website/keyboards.csv', verbose = True, allow_dangerous_code=True)
    return agent.invoke(question)







def text_search(question:str):
    """Answer question based on text document.
    """
    # This is a long document we can split up.

    loader = TextLoader('website/all.txt')
    document= loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=0, length_function=len
    )
    docs = text_splitter.split_documents(document)

    from langchain_openai import OpenAIEmbeddings
    embedding = OpenAIEmbeddings()

    from langchain_community.vectorstores import FAISS

    library = FAISS.from_documents(docs, embedding)
    from langchain.prompts import PromptTemplate

    template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum. Keep the answer as concise as possible. Always say "thanks for asking!" at the end of the answer. 
    {context}
    Question: {question}
    Helpful Answer:"""

    QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"],template=template,)

    answer = library.similarity_search(question, k=2, llm=llm, chain_type_kwargs={"prompt": QA_CHAIN_PROMPT, "query": question})
    
    return json.dumps({"answer": answer[0].page_content})





'''
from langchain_community.agent_toolkits import GmailToolkit

toolkit = GmailToolkit()

from langchain_community.tools.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)

# Can review scopes here https://developers.google.com/gmail/api/auth/scopes
# For instance, readonly scope is 'https://www.googleapis.com/auth/gmail.readonly'
credentials = get_gmail_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/"],
    client_secrets_file="credentials.json",
)
api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)


from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI


def gmail_message(question):
    instructions = """You are an assistant in company called ephomaker. Your job is to send email to marcol.krystof@gmail.com
                      You are provided with user sententenc and you have to extract user e-mail and user question and send it.
                      Make sure you send user email and question. Send email"""
    base_prompt = hub.pull("langchain-ai/openai-functions-template")
    prompt = base_prompt.partial(instructions=instructions)

    llm = ChatOpenAI(temperature=0)

    agent = create_openai_functions_agent(llm, toolkit.get_tools(), prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=toolkit.get_tools(),
        # This is set to False to prevent information about my email showing up on the screen
        # Normally, it is helpful to have it set to True however.
        verbose=False,
    )


    answer = agent_executor.invoke(
        {
            "input": question
        }
    )
    return answer['output']

'''