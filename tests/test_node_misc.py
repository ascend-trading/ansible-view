from ansible_view.models.node import Node
from ansible_view.parser.yaml_parser import get_line_number


def test_execution_label_none_when_no_index():
    node = Node(name="t", node_type="task")
    assert node.execution_label() is None


def test_execution_label_with_index():
    node = Node(name="t", node_type="task", execution_index=[2, 3])
    assert node.execution_label() == "2.3"


def test_get_line_number_non_dict_returns_none():
    assert get_line_number("a string") is None
    assert get_line_number(42) is None
    assert get_line_number(None) is None


def test_get_line_number_dict_with_line():
    assert get_line_number({"__line__": 10}) == 10


def test_node_load_children_exception_produces_error_child():
    node = Node(name="t", node_type="task")

    def bad_loader():
        raise RuntimeError("loader exploded")

    node.set_child_loader(bad_loader)
    node.load_children()
    assert isinstance(node.children, list)
    assert node.children
    assert node.children[0].node_type == "error"


def test_has_lazy_children_true_before_load():
    node = Node(name="t", node_type="task")
    node.set_child_loader(lambda: [])
    assert node.has_lazy_children() is True


def test_has_lazy_children_false_after_load():
    node = Node(name="t", node_type="task")
    node.set_child_loader(lambda: [])
    node.load_children()
    assert node.has_lazy_children() is False
