from __future__ import annotations

from scrapy.http import Response

from ...models import DiscussionPost
from .common import abs_url, join_text, normalize_whitespace


def extract_discussion_posts(
    response: Response,
    *,
    roundtable_id: str,
    thread_title_sel: str,
    posts_sel: str,
    post_id_sel: str,
    author_sel: str,
    posted_at_sel: str,
    content_sel: str,
    permalink_sel: str,
) -> list[DiscussionPost]:
    thread_title = normalize_whitespace(join_text(response.css(thread_title_sel).getall()))
    out: list[DiscussionPost] = []

    posts = response.css(posts_sel)
    idx = 0
    for post in posts:
        idx += 1
        post_id = post.css(post_id_sel).get()
        if post_id and "<" in post_id:
            post_id = None

        author = normalize_whitespace(join_text(post.css(author_sel).getall()))
        posted_at = normalize_whitespace(join_text(post.css(posted_at_sel).getall()))
        content = normalize_whitespace(join_text(post.css(content_sel).getall()))

        permalink = post.css(permalink_sel).get() if permalink_sel else None
        permalink = abs_url(str(response.url), permalink) if permalink else str(response.url)

        discussion_id = post_id or f"{roundtable_id}-{idx}"

        if not content:
            continue

        out.append(
            DiscussionPost(
                discussion_id=discussion_id,
                roundtable_id=roundtable_id,
                thread_title=thread_title or None,
                post_id=post_id or None,
                author_name=author or None,
                posted_at=posted_at or None,
                content_text=content,
                permalink=permalink,
            )
        )

    return out
