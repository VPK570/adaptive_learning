"""Learning path generation — prerequisite DAG + ZPD candidate selection."""

from app.db import get_db


class TopicPrerequisiteGraph:
    async def get_graph(self, course_code: str) -> dict[str, set[str]]:
        db = await get_db()
        rows = await db.query(
            "SELECT * FROM topic_prerequisite WHERE course_code = $cc AND prereq_type IN ['hard', 'sequential']",
            {"cc": course_code},
        )
        graph: dict[str, set[str]] = {}
        for row in rows or []:
            to_topic = row.get("topic_to", "")
            from_topic = row.get("topic_from", "")
            graph.setdefault(to_topic, set()).add(from_topic)
            graph.setdefault(from_topic, set())
        return graph

    async def get_zpd_candidates(self, student_id: str, course_code: str, mastery_threshold: float = 0.7) -> list[dict]:
        from app.knowledge_state import KnowledgeStateManager
        ksm = KnowledgeStateManager()
        states = await ksm.get_student_course_states(student_id, course_code)

        topic_mastery: dict[str, float] = {}
        for s in states:
            tid = s.get("topic_id", "")
            m = s.get("mastery_score", 0.0)
            if tid:
                topic_mastery[tid] = max(topic_mastery.get(tid, 0.0), m)

        graph = await self.get_graph(course_code)
        all_topics = set(graph.keys()) | {t for deps in graph.values() for t in deps}

        candidates = []
        for topic in all_topics:
            prereqs = graph.get(topic, set())
            if not prereqs:
                if topic_mastery.get(topic, 0.0) < mastery_threshold:
                    candidates.append(topic)
                continue

            prereq_mastery = [topic_mastery.get(p, 0.0) for p in prereqs]
            readiness = min(prereq_mastery) if prereq_mastery else 0.0
            mastery = topic_mastery.get(topic, 0.0)

            if readiness >= mastery_threshold and mastery < mastery_threshold:
                gap = mastery_threshold - mastery
                centrality = len(prereqs) + sum(1 for t, d in graph.items() if topic in d)
                candidates.append((topic, gap * centrality))

        candidates.sort(key=lambda x: -x[1] if isinstance(x, tuple) else 0.0)
        return [{"topic_id": c[0], "priority": round(c[1], 3)} if isinstance(c, tuple) else {"topic_id": c, "priority": 1.0} for c in candidates[:5]]

    async def add_prerequisite(self, course_code: str, topic_from: str, topic_to: str, prereq_type: str = "hard"):
        db = await get_db()
        await db.query(
            "CREATE topic_prerequisite CONTENT { course_code: $cc, topic_from: $f, topic_to: $t, prereq_type: $type }",
            {"cc": course_code, "f": topic_from, "t": topic_to, "type": prereq_type},
        )

    async def get_prerequisites(self, course_code: str, topic_id: str) -> list[str]:
        db = await get_db()
        rows = await db.query(
            "SELECT topic_from FROM topic_prerequisite WHERE course_code = $cc AND topic_to = $tid AND prereq_type IN ['hard', 'sequential']",
            {"cc": course_code, "tid": topic_id},
        )
        return [r["topic_from"] for r in (rows or []) if r.get("topic_from")]
