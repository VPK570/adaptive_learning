from collections import Counter
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query_log import QueryLog


class AnalyticsStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_query(
        self,
        question: str,
        course_code: str,
        response: str,
        cited_sources: Optional[list] = None,
    ) -> QueryLog:
        refusal_phrase = "This topic is not covered"
        out_of_scope = refusal_phrase in response

        entry = QueryLog(
            question=question,
            course_code=course_code,
            response_preview=response[:200],
            out_of_scope=out_of_scope,
            cited_sources=cited_sources or [],
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_unanswered(self, course_code: str) -> List[QueryLog]:
        result = await self.session.execute(
            select(QueryLog)
            .where(QueryLog.course_code == course_code, QueryLog.out_of_scope.is_(True))
        )
        return list(result.scalars().all())

    async def get_all_for_course(self, course_code: str) -> List[QueryLog]:
        result = await self.session.execute(
            select(QueryLog).where(QueryLog.course_code == course_code)
        )
        return list(result.scalars().all())

    async def get_coverage(self, course_code: str) -> dict:
        result = await self.session.execute(
            select(QueryLog.cited_sources).where(QueryLog.course_code == course_code)
        )
        doc_hits = {}
        for row in result.scalars().all():
            if row:
                for src in row:
                    title = src.get("source_title") if isinstance(src, dict) else str(src)
                    if title:
                        doc_hits[title] = doc_hits.get(title, 0) + 1
        return doc_hits
