from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

import time

from utils import fetch_page, save_rss_feed, setup_feed_links, setup_logging, sort_posts_for_feed, stable_fallback_date

logger = setup_logging()

FEED_NAME = "humanlayer"
BLOG_URL = "https://www.humanlayer.dev/blog"
BASE_URL = "https://www.humanlayer.dev"


def parse_date(date_str):
    try:
        date = datetime.strptime(date_str.strip(), "%B %d, %Y")
        return date.replace(tzinfo=pytz.UTC)
    except ValueError as e:
        logger.warning(f"Could not parse date: {date_str} - {e!s}")
        return None


def parse_blog_page(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    blog_posts = []

    post_links = soup.select('a.block.py-2.group[href^="/blog/"]')
    logger.info(f"Found {len(post_links)} posts")

    for link in post_links:
        href = link.get("href", "")
        if "/blog/tags/" in href:
            continue
        full_url = f"{BASE_URL}{href}"

        title_elem = link.find("h2")
        title = title_elem.get_text(strip=True) if title_elem else "Untitled"

        meta_elem = link.find("p", class_="text-sm")
        pub_date = None
        if meta_elem:
            parts = meta_elem.get_text().split("·")
            if len(parts) >= 2:
                pub_date = parse_date(parts[1])
        if pub_date is None:
            pub_date = stable_fallback_date(full_url)

        desc_paragraphs = link.find_all("p", style=True)
        description = ""
        for p in desc_paragraphs:
            if "text-secondary" in (p.get("style") or ""):
                description = p.get_text(strip=True)
                break

        blog_posts.append({
            "title": title,
            "link": full_url,
            "description": description,
            "date": pub_date,
            "content": "",
        })
        logger.info(f"Parsed: {title}")

    for post in blog_posts:
        try:
            time.sleep(1)
            page_html = fetch_page(post["link"])
            page_soup = BeautifulSoup(page_html, "html.parser")
            prose = page_soup.find("div", class_="prose")
            if prose:
                post["content"] = str(prose)
                logger.info(f"Fetched content for: {post['title']}")
        except Exception as e:
            logger.warning(f"Could not fetch content for {post['title']}: {e!s}")

    return sort_posts_for_feed(blog_posts)


def generate_rss_feed(blog_posts):
    fg = FeedGenerator()
    fg.title("HumanLayer Blog")
    fg.description("Insights on AI agents, LLM applications, and the future of human-AI collaboration.")
    fg.language("en")
    fg.author({"name": "HumanLayer"})
    setup_feed_links(fg, blog_url=BLOG_URL, feed_name=FEED_NAME)

    for post in blog_posts:
        fe = fg.add_entry()
        fe.title(post["title"])
        fe.description(post["description"])
        fe.link(href=post["link"])
        fe.published(post["date"])
        fe.id(post["link"] + "#v2")
        if post.get("content"):
            fe.content(post["content"], type="html")

    return fg


def main():
    try:
        html_content = fetch_page(BLOG_URL)
        blog_posts = parse_blog_page(html_content)
        feed = generate_rss_feed(blog_posts)
        save_rss_feed(feed, FEED_NAME)
        return True
    except Exception as e:
        logger.error(f"Failed to generate RSS feed: {e!s}")
        return False


if __name__ == "__main__":
    main()
