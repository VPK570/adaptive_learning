import asyncio
from app.rag import RAGPipeline

async def main():
    rag = RAGPipeline()
    print(rag.get_course_stats('BACHY106'))

if __name__ == "__main__":
    asyncio.run(main())
