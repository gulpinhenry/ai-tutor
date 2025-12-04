import os
from langchain_openai import ChatOpenAI

def get_llm(model_name="qwen2.5:0.5b", provider=None):
    def get_ollama():
        print(f"Connecting to local Ollama with model: {model_name}...")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        try:
            llm = ChatOpenAI(
                base_url=f"{ollama_base_url}/v1",
                api_key="ollama",
                model=model_name,
                temperature=0,
                max_retries=1,
                request_timeout=120
            )
            llm.invoke("test")
            print("Connected to Ollama successfully.")
            return llm
        except Exception as e:
            print(f"Failed to connect to Ollama: {e}")
            return None

    def get_openrouter():
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        fallback_model = "qwen/qwen-2.5-7b-instruct"
        
        if api_key:
            print(f"Connecting to OpenRouter with model: {fallback_model}")
            return ChatOpenAI(
                base_url=base_url,
                api_key=api_key,
                model=fallback_model,
                temperature=0,
            )
        print("No OpenRouter API key found.")
        return None

    if provider == 'ollama':
        return get_ollama()
    elif provider == 'openrouter':
        return get_openrouter()
    else:
        llm = get_ollama()
        if llm:
            return llm
        
        print("Falling back to OpenRouter...")
        return get_openrouter()
