"""Deep Knowledge Tracing with PyTorch LSTM — dormant until DKT_ACTIVE=True.

Requires torch. Install: pip install torch

Input: one-hot encoding of (question_id × bloom_level × correctness)
Output: P(correct) for each skill per student
"""

from app.config import settings


class DKTModel:
    def __init__(self, n_skills: int, hidden_size: int = 128):
        self.n_skills = n_skills
        self.hidden_size = hidden_size
        self._model = None

    def predict(self, student_id: str) -> dict[str, float]:
        if not settings.DKT_ACTIVE:
            return {}
        return {}
