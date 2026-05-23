from dotenv import load_dotenv
load_dotenv()

import asyncio
from app.rag import RAGPipeline

async def main():
    rag = RAGPipeline()
    results = await rag.retrieve('computational chemistry', 'BACHY106')
    for r in results:
        print(f"Distance: {r['distance']}, Text: {r['text'][:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
