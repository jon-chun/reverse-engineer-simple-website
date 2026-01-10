"""Unit tests for the site map builder."""
from __future__ import annotations

from revweb.crawl.map_builder import PathNode, build_path_tree, render_tree_md


class TestBuildPathTree:
    """Tests for building path tree from URLs."""

    def test_single_url(self):
        """Single URL creates simple tree."""
        urls = ["https://example.com/speakers"]
        tree = build_path_tree(urls)
        assert tree.name == "/"
        assert "speakers" in tree.children

    def test_nested_paths(self):
        """Nested paths create nested tree structure."""
        urls = ["https://example.com/speakers/john-doe"]
        tree = build_path_tree(urls)
        assert "speakers" in tree.children
        assert "john-doe" in tree.children["speakers"].children

    def test_multiple_urls(self):
        """Multiple URLs are combined in tree."""
        urls = [
            "https://example.com/speakers/john",
            "https://example.com/speakers/jane",
            "https://example.com/roundtables/test",
        ]
        tree = build_path_tree(urls)
        assert "speakers" in tree.children
        assert "roundtables" in tree.children
        speakers = tree.children["speakers"]
        assert "john" in speakers.children
        assert "jane" in speakers.children

    def test_root_url(self):
        """Root URL creates minimal tree."""
        urls = ["https://example.com/"]
        tree = build_path_tree(urls)
        assert tree.name == "/"
        # Root URL creates empty string child
        assert "" in tree.children

    def test_deduplication(self):
        """Duplicate URLs are deduplicated."""
        urls = [
            "https://example.com/page",
            "https://example.com/page",
            "https://example.com/page",
        ]
        tree = build_path_tree(urls)
        assert len(tree.children) == 1

    def test_empty_urls(self):
        """Empty URL list creates empty tree."""
        tree = build_path_tree([])
        assert tree.name == "/"
        assert len(tree.children) == 0

    def test_sorting(self):
        """URLs are sorted before processing."""
        urls = [
            "https://example.com/zebra",
            "https://example.com/apple",
        ]
        tree = build_path_tree(urls)
        # Both should exist as children
        assert "zebra" in tree.children
        assert "apple" in tree.children


class TestRenderTreeMd:
    """Tests for rendering path tree as markdown."""

    def test_single_level(self):
        """Single level tree renders correctly."""
        tree = PathNode(name="/", children={
            "speakers": PathNode(name="speakers", children={}),
        })
        lines = render_tree_md(tree)
        assert any("speakers" in line for line in lines)

    def test_nested_levels(self):
        """Nested tree renders with indentation."""
        tree = PathNode(name="/", children={
            "speakers": PathNode(name="speakers", children={
                "john": PathNode(name="john", children={}),
            }),
        })
        lines = render_tree_md(tree)
        # Check structure exists
        assert len(lines) >= 2

    def test_sorted_output(self):
        """Output is sorted alphabetically."""
        tree = PathNode(name="/", children={
            "zebra": PathNode(name="zebra", children={}),
            "apple": PathNode(name="apple", children={}),
        })
        lines = render_tree_md(tree)
        # Find positions of apple and zebra
        apple_pos = next(i for i, line in enumerate(lines) if "apple" in line)
        zebra_pos = next(i for i, line in enumerate(lines) if "zebra" in line)
        assert apple_pos < zebra_pos

    def test_empty_tree(self):
        """Empty tree renders empty output."""
        tree = PathNode(name="/", children={})
        lines = render_tree_md(tree)
        assert lines == []

    def test_markdown_format(self):
        """Output uses markdown list format."""
        tree = PathNode(name="/", children={
            "page": PathNode(name="page", children={}),
        })
        lines = render_tree_md(tree)
        assert any(line.strip().startswith("-") for line in lines)
        assert any("`" in line for line in lines)
