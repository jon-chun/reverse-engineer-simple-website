from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class PathNode:
    name: str
    children: dict[str, PathNode]


def build_path_tree(urls: Iterable[str]) -> PathNode:
    root = PathNode(name="/", children={})
    for u in sorted(set(urls)):
        path = urlparse(u).path.strip("/")
        parts = [p for p in path.split("/") if p] or [""]
        node = root
        for part in parts:
            if part not in node.children:
                node.children[part] = PathNode(name=part, children={})
            node = node.children[part]
    return root


def render_tree_md(node: PathNode, *, indent: int = 0) -> list[str]:
    lines: list[str] = []
    if indent > 0:
        prefix = "  " * (indent - 1) + "- "
        name = node.name if node.name else "(root)"
        lines.append(f"{prefix}`{name}`")
    for child in sorted(node.children.values(), key=lambda n: n.name):
        lines.extend(render_tree_md(child, indent=indent + 1))
    return lines
