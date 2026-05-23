import asyncio
from app.rag import RAGPipeline

async def main():
    rag = RAGPipeline()
    print(rag.list_courses())

if __name__ == "__main__":
    asyncio.run(main())
