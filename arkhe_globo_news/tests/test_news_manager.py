import pytest
from arkhe_globo_news.src.news_manager import NewsSystem, ContentCategory, BroadcastRegion

def test_create_and_retrieve_article():
    system = NewsSystem()
    article = system.create_article(
        "1", "Breaking News", "Content here", ContentCategory.NEWS, BroadcastRegion.NATIONAL, "John Doe"
    )

    assert article.id == "1"
    assert article.category == ContentCategory.NEWS

    retrieved = system.get_article("1")
    assert retrieved is not None
    assert retrieved.title == "Breaking News"

def test_telenovela_category():
    system = NewsSystem()
    system.create_article("1", "Vale Tudo Recap", "Details...", ContentCategory.TELENOVELA, BroadcastRegion.NATIONAL, "Maria")
    system.create_article("2", "News Update", "Details...", ContentCategory.NEWS, BroadcastRegion.NATIONAL, "Joao")

    telenovelas = system.get_articles_by_category(ContentCategory.TELENOVELA)
    assert len(telenovelas) == 1
    assert telenovelas[0].id == "1"

def test_international_broadcasting():
    system = NewsSystem()
    article = system.create_article("1", "Global Update", "Portuguese content", ContentCategory.NEWS, BroadcastRegion.INTERNATIONAL, "Carlos")

    # Initially no translations, shouldn't be in international broadcast list
    assert len(system.get_international_broadcasts()) == 0

    # Add translation
    article.add_translation("en", "English content")

    # Should now be broadcastable
    int_broadcasts = system.get_international_broadcasts()
    assert len(int_broadcasts) == 1
    assert "en" in int_broadcasts[0].translations
