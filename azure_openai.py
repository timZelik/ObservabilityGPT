from langchain.llms import AzureOpenAI


def initialize_azure_openai():
    """
    Initialize Azure OpenAI with a specific deployment and model.

    Returns
    -------
    AzureOpenAI
        An instance of AzureOpenAI.
    """
    llm = AzureOpenAI(
        deployment_name="dv3llm01-01",
        model_name="text-embedding-ada-002",
        verbose=True,
        temperature=0,
    )

    return llm
