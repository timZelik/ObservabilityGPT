# using the index created above we are connecting to llm using langchain and asking question
from langchain.prompts.prompt import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import AzureOpenAI
import prompts
import os
import time
from os import getcwd, listdir
from os.path import isfile, join

from langchain.document_loaders import BSHTMLLoader, DirectoryLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import AzureOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import UnstructuredURLLoader
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.memory import ConversationBufferMemory
from azure_openai import initialize_azure_openai
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2022-12-01"
os.environ["OPENAI_API_BASE"] = "https://dv3llm01.openai.azure.com/"
os.environ["OPENAI_API_KEY"] = "" #paste openai key into double quotes
def langchain_qa(query):
    llm = initialize_azure_openai()


    prompt_template = """
        You are an AI assistant with expertise in Azure Application Insights and Kusto Query Language (KQL).
        You have access to all the application insights within the BlockWorks Online Azure DevOps project. Your goal is 
        to assist users in retrieving the data they need by generating the appropriate Kusto queries based on their requests.
    
        You are also aware that the data you have access to is extensive and may contain many different tables and fields.
        Therefore, you are careful to generate queries that are as specific as possible to the user's request, to avoid returning unnecessary or irrelevant data.
        
         If you know the answer Please return the answer in a string with Kusto Query followed by colon (:) and answer.
      example: Kusto Query: answer
       
        If you don't know the answer, reply the answer in string with Kusto Query followed by colon (:) and unknown 
        and comma separated by reason followed by colon (:) attempt to ask clarifying questions still to the user, but 
        do not hallucinate and make up a Kusto query that is wrong or does not exist. 
        example: Kusto Query: unknown, reason: reason for not knowing the answer
    
      If you need more information to generate the query, please specify what additional information you need.
      
    Here is the user's request: {request}
    
        Based on this request, please generate the Kusto query that will retrieve the requested data. If you need more 
        information to generate the query, please specify what additional information you need.
                    """
    # Fill in the user's request in the prompt template
    filled_prompt = prompt_template.format(request=query)

    # Use the Langchain model to generate a response
    response = llm.generate([filled_prompt])  # Note the list around filled_prompt

    # Extract the generated text from the response
    generated_text = response.generations[0][0].text


    return {'answer': generated_text}


