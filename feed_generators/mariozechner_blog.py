import re
from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

from utils import fetch_page, save_rss_feed, setup_feed_links, setup_logging, sort_posts_for_feed, stable_fallback_date

logger = setup_logging()

FEED_NAME = "mariozechner"
BLOG_URL = "https://mariozechner.at"


def parse_date(date_str):
    try:
        date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return date.replace(tzinfo=pytz.UTC)
    except ValueError as e:
        logger.warning(f"Could not parse date: {date_str} - {e!s}")
        return None


def parse_blog_page(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    blog_posts = []

    for link in soup.find_all("a", href=re.compile(r"^/posts/")):
        href = link.get("href", "")
        full_url = f"{BLOG_URL}{href}"

        spans = link.find_all("span")
        if len(spans) < 2:
            continue

        date_str = spans[0].get_text(strip=True)
        title = spans[1].get_text(strip=True)
        pub_date = parse_date(date_str) or stable_fallback_date(full_url)

        blog_posts.append({
            "title": title,
            "link": full_url,
            "description": title,
            "date": pub_date,
        })
        logger.info(f"Parsed: {title}")

    return sort_posts_for_feed(blog_posts)


def generate_rss_feed(blog_posts):
    fg = FeedGenerator()
    fg.title("Mario Zechner")
    fg.description("Blog by Mario Zechner - developer, coach, speaker")
    fg.language("en")
    fg.author({"name": "Mario Zechner"})
    setup_feed_links(fg, blog_url=BLOG_URL, feed_name=FEED_NAME)

    for post in blog_posts:
        fe = fg.add_entry()
        fe.title(post["title"])
        fe.description(post["description"])
        fe.link(href=post["link"])
        fe.published(post["date"])
        fe.id(post["link"])

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
