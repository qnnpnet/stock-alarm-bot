from typing import List
import feedparser
from datetime import datetime, timedelta
from dateutil import parser
from newspaper import Article
from playwright.async_api import async_playwright
from models import NewsArticle
from pathlib import Path
from utils.http import get_final_url
from utils.logger import setup_logger
from urllib.parse import quote
import traceback


class NewsService:
    def __init__(self):
        self.cache_file = "returned_news.txt"
        self.logger = setup_logger("news_service")
        self._init_cache_file()

    def _init_cache_file(self):
        try:
            Path(self.cache_file).touch(exist_ok=True)
            self.logger.info(f"Initialized cache file: {self.cache_file}")
        except Exception as e:
            self.logger.error(f"Failed to initialize cache file: {str(e)}")
            raise

    async def extract_article(self, url: str) -> tuple[str, str, str]:
        self.logger.info(f"Extracting article from URL: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(locale="ko-KR")
            page = await context.new_page()

            try:
                await page.goto(url, timeout=5000)
                await page.wait_for_load_state("networkidle", timeout=10000)
                html = await page.content()
                link = page.url

                article = Article(link)
                article.set_html(html)
                article.parse()

                self.logger.debug(f"Successfully extracted article: {article.title}")
                return article.title, article.text, link
            except Exception as e:
                self.logger.error(f"Failed to extract article: {str(e)}")
                raise
            finally:
                await browser.close()

    async def get_news(self, keyword: str) -> List[NewsArticle]:
        self.logger.info(f"Fetching news for keyword: {keyword}")
        url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            feed = feedparser.parse(url)
            three_days_ago = datetime.now() - timedelta(days=3)

            filtered_entries = [
                (datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z"), entry)
                for entry in feed.entries
                if hasattr(entry, "published")
                and datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
                >= three_days_ago
            ]

            filtered_entries.sort(key=lambda x: x[0], reverse=True)
            returned_news = self._get_returned_news()
            news_articles = []

            for _, entry in filtered_entries[:5]:
                try:
                    title, content, link = await self.extract_article(entry.link)

                    # redirect되어 최종 url이 나오면 해당 url과 returned_news를 비교
                    if link in returned_news:
                        self.logger.debug(
                            f"Skipping already processed article: {entry.title}"
                        )
                        continue

                    published = (
                        parser.parse(entry.published) + timedelta(hours=9)
                        if entry.published
                        else None
                    )

                    article = NewsArticle(
                        title=f"[{keyword}] {title}",
                        link=link,
                        content=content,
                        published=published,
                    )
                    news_articles.append(article)
                    self._add_to_returned_news(link)
                    self.logger.info(f"Successfully processed article: {title}")
                except Exception as e:
                    self.logger.error(f"Failed to process article: {str(e)}")
                    continue

            return news_articles

        except Exception as e:
            self.logger.error(
                f"Failed to fetch news: {str(e)}\n{traceback.format_exc()}"
            )
            return []

    def _get_returned_news(self) -> set:
        try:
            with open(self.cache_file, "r") as f:
                return {line.strip() for line in f}
        except Exception as e:
            self.logger.error(f"Failed to read cache file: {str(e)}")
            return set()

    def _add_to_returned_news(self, link: str):
        try:
            with open(self.cache_file, "a") as f:
                f.write(f"{link}\n")
            self.logger.debug(f"Added article to cache: {link}")
        except Exception as e:
            self.logger.error(f"Failed to add article to cache: {str(e)}")
