from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class ContentCategory(Enum):
    TELENOVELA = "telenovela"
    NEWS = "news"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    GENERAL = "general"

class BroadcastRegion(Enum):
    NATIONAL = "national"
    INTERNATIONAL = "international"
    REGIONAL = "regional"

class Article:
    def __init__(self, id: str, title: str, content: str, category: ContentCategory, region: BroadcastRegion, author: str):
        self.id = id
        self.title = title
        self.content = content
        self.category = category
        self.region = region
        self.author = author
        self.published_at: Optional[datetime] = None
        self.views = 0
        self.translations: Dict[str, str] = {}

    def publish(self):
        self.published_at = datetime.now()

    def add_translation(self, language: str, translated_content: str):
        self.translations[language] = translated_content

    def increment_views(self):
        self.views += 1

class NewsSystem:
    def __init__(self):
        self.articles: Dict[str, Article] = {}

    def create_article(self, id: str, title: str, content: str, category: ContentCategory, region: BroadcastRegion, author: str) -> Article:
        if id in self.articles:
            raise ValueError(f"Article with id {id} already exists")

        article = Article(id, title, content, category, region, author)
        self.articles[id] = article
        return article

    def get_article(self, id: str) -> Optional[Article]:
        return self.articles.get(id)

    def publish_article(self, id: str):
        article = self.get_article(id)
        if article:
            article.publish()
        else:
            raise ValueError(f"Article {id} not found")

    def get_articles_by_category(self, category: ContentCategory) -> List[Article]:
        return [a for a in self.articles.values() if a.category == category]

    def get_articles_by_region(self, region: BroadcastRegion) -> List[Article]:
        return [a for a in self.articles.values() if a.region == region]

    def get_international_broadcasts(self) -> List[Article]:
        """Returns articles configured for international broadcasting (must have translations)"""
        return [a for a in self.articles.values() if a.region == BroadcastRegion.INTERNATIONAL and len(a.translations) > 0]
