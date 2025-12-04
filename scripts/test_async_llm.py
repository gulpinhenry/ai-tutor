import asyncio
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils import get_llm

async def test_provider(provider):
    print(f"\n--- Testing Provider: {provider} ---")
    llm = get_llm(provider=provider)
    if not llm:
        print(f"Could not initialize {provider}.")
        return

    prompts = ["Hello", "Hi there", "Greetings", "Good morning", "Hey"]
    print(f"Sending {len(prompts)} async requests...")
    
    start_time = time.time()
    
    async def invoke(prompt):
        try:
            return await llm.ainvoke(prompt)
        except Exception as e:
            return f"Error: {e}"

    tasks = [invoke(p) for p in prompts]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Completed in {duration:.2f} seconds.")
    for i, res in enumerate(results):
        content = res.content if hasattr(res, 'content') else res
        print(f"[{i+1}] {content[:50]}...")

async def main():
    await test_provider('ollama')
    await test_provider('openrouter')

if __name__ == "__main__":
    asyncio.run(main())
