from ansible_view.execution.execution_graph_builder import assign_execution_indices
from ansible_view.models.node import Node


def test_execution_indices_nested():
    play = Node(name="play", node_type="play")
    task1 = Node(name="task1", node_type="task")
    section = Node(name="tasks", node_type="section")
    task2 = Node(name="task2", node_type="task")
    task3 = Node(name="task3", node_type="task")
    section.children = [task2, task3]
    role = Node(name="web", node_type="role")
    role_task = Node(name="install", node_type="task")
    role.children = [role_task]
    play.children = [task1, section, role]

    assign_execution_indices(play.children, eager=True)

    assert task1.execution_label() == "1"
    assert task2.execution_label() == "2"
    assert task3.execution_label() == "3"
    assert role.execution_label() == "4"
    assert role_task.execution_label() == "4.1"
