import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils import get_llm

def main():
    print("Verifying LLM connection...")
    llm = get_llm()
    if not llm:
        print("Could not initialize LLM client.")
        return

    try:
        response = llm.invoke("Hello, are you ready to be a tutor?")
        print(f"Response from LLM: {response.content}")
        print("SUCCESS: LLM connection verified.")
    except Exception as e:
        print(f"ERROR: Could not connect to LLM. Details: {e}")
        print("Ensure Ollama is running and the model 'qwen2.5' is pulled.")

if __name__ == "__main__":
    main()
