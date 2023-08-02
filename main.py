import prompts
from azure_openai import initialize_azure_openai
from app_setup import set_openai_env_vars, initialize_embeddings, initialize_prompt_template

def main():
    """
    Main function to run the application.
    """
    # Set environment variables
    set_openai_env_vars()

    # Initialize Azure OpenAI
    llm = initialize_azure_openai()

    # Initialize OpenAI embeddings
    embeddings = initialize_embeddings()

    # Initialize prompt template
    qa_prompt = initialize_prompt_template()

    # Print the answer from prompts
    print(prompts.response.get('answer'))

if __name__ == "__main__":
    main()
