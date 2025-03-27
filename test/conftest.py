import pytest
from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy_playwright.page import PageMethod
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_playwright_page():
    page = AsyncMock()
    page.context.new_page.return_value = AsyncMock()
    page.content.return_value = "<html></html>"
    return page

@pytest.fixture
def mock_response(mock_playwright_page):
    url = "https://www.amazon.jobs/content/en/job-categories/software-development?country%5B%5D=US"
    request = Request(url=url, meta={
        "playwright": True,
        "playwright_page": mock_playwright_page,
        "playwright_include_page": True,
        "playwright_context": "default",
    })
    return HtmlResponse(url=url, request=request, body=b"", encoding="utf-8")