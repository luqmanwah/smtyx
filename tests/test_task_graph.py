import unittest
from smtyx import TaskGraph, TaskNode


class TestTaskGraph(unittest.TestCase):
    def test_dependencies(self):
        graph = TaskGraph()
        graph.add(TaskNode("read", "READ", "DOCUMENT"))
        graph.add(TaskNode("verify", "VERIFY", "FINDING", depends_on=["read"]))
        self.assertTrue(graph.validate()["valid"])
        self.assertEqual([n.node_id for n in graph.ready()], ["read"])
        self.assertEqual([n.node_id for n in graph.ready(["read"])], ["verify"])

    def test_cycle_detection(self):
        graph = TaskGraph()
        graph.add(TaskNode("a", "READ", "DOCUMENT", depends_on=["b"]))
        graph.add(TaskNode("b", "VERIFY", "DOCUMENT", depends_on=["a"]))
        self.assertFalse(graph.validate()["valid"])


if __name__ == "__main__": unittest.main()
