import os
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model


def get_llm_instance():
    # Ensure API key is set, can be done in config.py
    if not os.environ["GOOGLE_API_KEY"]:
        raise ValueError("GOOGLE_API_KEY not set.")
    llm = init_chat_model(
        os.environ["GOOGLE_MODEL"],
        model_provider="google_genai",
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )
    return llm

llm_instance = get_llm_instance()