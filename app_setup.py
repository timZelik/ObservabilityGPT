import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts.prompt import PromptTemplate


def set_openai_env_vars():
    """
    Set environment variables for OpenAI API.
    """
    os.environ["OPENAI_API_TYPE"] = "azure"
    os.environ["OPENAI_API_VERSION"] = "2022-12-01"
    os.environ["OPENAI_API_BASE"] = "https://dv3llm01.openai.azure.com/"
    os.environ["OPENAI_API_KEY"] = ""  # paste openai key into double quotes


def initialize_embeddings():
    """
    Initialize OpenAI embeddings with a specific deployment and model.

    Returns
    -------
    OpenAIEmbeddings
        An instance of OpenAIEmbeddings.
    """
    embeddings = OpenAIEmbeddings(
        deployment="ada-embeddings",
        chunk_size="1",
        model="text-embedding-ada-002"
    )

    return embeddings


def initialize_prompt_template():
    """
    Initialize a PromptTemplate with a specific template.

    Returns
    -------
    PromptTemplate
        An instance of PromptTemplate.
    """
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
    qa_prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["request"]
    )

    return qa_prompt
