import json
import os
from typing import Dict, List, Optional, Tuple

import numpy as np


class FaceMatcher:
    """
    High-performance vector matching using Cosine Similarity.
    Pre-normalizes embeddings so similarity calculation reduces to an optimal dot product.
    Supports local JSON storage for Phase 1 and mirrors pgvector behavior in Phase 2.
    """

    def __init__(self, db_path: str = "data/embeddings.json", threshold: float = 0.50):
        self.db_path = db_path
        self.threshold = threshold
        self.students: Dict[str, dict] = {}
        self.load_database()

    def load_database(self) -> int:
        """Loads and normalizes student face embeddings from local storage."""
        if not os.path.exists(self.db_path):
            self.students = {}
            return 0

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.students = {}
                for sid, record in data.items():
                    embedding = np.array(record["embedding"], dtype=np.float32)
                    norm = np.linalg.norm(embedding)
                    if norm > 1e-6:
                        embedding = embedding / norm
                    self.students[sid] = {
                        "student_id": record.get("student_id", sid),
                        "name": record.get("name", "Unknown"),
                        "department": record.get("department", "CS"),
                        "embedding": embedding,
                        "created_at": record.get("created_at", ""),
                    }
            return len(self.students)
        except Exception as e:
            print(f"[Matcher] Error loading embeddings from {self.db_path}: {e}")
            self.students = {}
            return 0

    def save_student(
        self,
        student_id: str,
        name: str,
        department: str,
        embedding: np.ndarray,
    ) -> bool:
        """
        Saves a student with their 512-D L2-normalized embedding to data/embeddings.json.
        """
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)

        # L2-normalize before saving
        emb = np.array(embedding, dtype=np.float32)
        norm = np.linalg.norm(emb)
        if norm > 1e-6:
            emb = emb / norm

        # Read existing
        existing = {}
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}

        existing[student_id] = {
            "student_id": student_id,
            "name": name,
            "department": department,
            "embedding": emb.tolist(),
            "model": "ArcFace_buffalo_sc_512d",
        }

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        # Reload cache
        self.load_database()
        return True

    def match(
        self, query_embedding: np.ndarray
    ) -> Tuple[Optional[str], Optional[str], float, bool]:
        """
        Finds the closest registered student to the query embedding.
        Returns:
            (student_id, student_name, similarity_score, is_match)
        """
        if not self.students:
            return None, None, 0.0, False

        q = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm > 1e-6:
            q = q / q_norm

        best_id = None
        best_name = None
        best_similarity = -1.0

        for sid, record in self.students.items():
            stored_emb = record["embedding"]
            # Cosine similarity of two unit vectors is simply their dot product
            sim = float(np.dot(q, stored_emb))
            if sim > best_similarity:
                best_similarity = sim
                best_id = sid
                best_name = record["name"]

        is_match = best_similarity >= self.threshold
        return best_id, best_name, max(0.0, best_similarity), is_match
