import unittest
from smtyx import MemoryKind, MemoryRecord, InMemoryStore, LearningLedger, LearningStage


class TestMemoryLearning(unittest.TestCase):
    def test_memory_types(self):
        store = InMemoryStore()
        store.add(MemoryRecord(MemoryKind.PROCEDURAL, {"procedure":"review document"}, verified=True))
        self.assertEqual(len(store.query(kind=MemoryKind.PROCEDURAL, verified_only=True)), 1)

    def test_learning_requires_approval(self):
        ledger = LearningLedger()
        item = ledger.observe("agent A is effective on PDFs", scope="routing")
        ledger.promote_candidate(item.candidate_id)
        ledger.verify(item.candidate_id, note="benchmark passed", confidence=.9)
        with self.assertRaises(PermissionError):
            ledger.adopt(item.candidate_id)
        adopted = ledger.adopt(item.candidate_id, human_approved=True, note="approved")
        self.assertEqual(adopted.stage, LearningStage.ADOPTED)


if __name__ == "__main__": unittest.main()
