from dotenv import load_dotenv
load_dotenv()

import asyncio
from app.curriculum import CurriculumManager

async def main():
    curriculum = CurriculumManager()
    in_scope = await curriculum.check_topic_in_curriculum('BACHY106', 'computational chemistry')
    print(f"In scope: {in_scope}")

if __name__ == "__main__":
    asyncio.run(main())
