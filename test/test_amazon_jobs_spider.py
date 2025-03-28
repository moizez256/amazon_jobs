import pytest
from scrapy.http import HtmlResponse, Request
from scrapy.utils.test import get_crawler
from unittest.mock import AsyncMock, MagicMock, patch
from amazon_jobs_scrapy.amazon_jobs_scrapy.spiders.amazon_jobs import AmazonJobsSpider

@pytest.fixture
def spider():
    crawler = get_crawler(AmazonJobsSpider)
    return crawler.spidercls.from_crawler(crawler)

@pytest.mark.asyncio
async def test_start_requests(spider):
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert isinstance(requests[0], Request)
    assert requests[0].url == spider.start_urls[0]
    assert requests[0].meta["playwright"]
    assert requests[0].meta["playwright_include_page"]

@pytest.mark.asyncio
async def test_parse_with_jobs(spider):
    html_content = """
    <html>
        <body>
            <ul class="jobs-module_root">
                <li></li>
                <li></li>
            </ul>
            <div role="button">
                <h3><a href="/job/123">Software Engineer</a></h3>
                <div class="metadata-wrapper">
                    <div><div class="metadatum-module_text">Seattle, WA</div></div>
                    <div><div class="metadatum-module_text">Updated 01/01/2025</div></div>
                </div>
                <div><div><div>Short description</div></div></div>
            </div>
            <button data-test-id="next-page">Next</button>
        </body>
    </html>
    """
    
    request = Request(
        url=spider.start_urls[0],
        meta={
            "playwright_page": AsyncMock(),
            "playwright_include_page": True
        }
    )
    response = HtmlResponse(
        url=spider.start_urls[0],
        body=html_content.encode(),
        encoding='utf-8',
        request=request
    )

    mock_page = response.meta["playwright_page"]
    mock_page.locator.return_value = MagicMock(is_visible=AsyncMock(return_value=True))
    mock_page.content = AsyncMock(return_value=html_content)
    
    results = []
    async for item in spider.parse(response):
        if isinstance(item, Request):
            results.append(item)
        else:
            results.append(item)
    
    assert len(results) > 0
    assert any(isinstance(r, Request) for r in results)
    

    job_requests = [r for r in results if isinstance(r, Request)]
    for req in job_requests:
        assert "job-detail" in str(req.meta["playwright_page_methods"][0])
        assert req.meta["data"]["title"] == "Software Engineer"
        assert req.meta["data"]["location"] == "Seattle, WA"

@pytest.mark.asyncio
async def test_parse_jobs(spider):
    html_content = """
    <html>
        <body>
            <div id="job-detail">
                <div class="content">
                    <div>
                        <h2>DESCRIPTION</h2>
                        <p>Full description text</p>
                        <h2>BASIC QUALIFICATIONS</h2>
                        <p>Basic qualifications text</p>
                        <h2>PREFERRED QUALIFICATIONS</h2>
                        <p>Preferred qualifications text</p>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """
    
    request = Request(
        url="https://www.amazon.jobs/job/123",
        meta={
            "playwright_page": AsyncMock(),
            "playwright_include_page": True,
            "data": {
                "title": "Software Engineer",
                "url": "https://www.amazon.jobs/job/123",
                "location": "Seattle, WA",
                "updated": "Updated today",
                "short_description": ["Short description"],
                "job_id": "123"
            }
        }
    )
    response = HtmlResponse(
        url="https://www.amazon.jobs/job/123",
        body=html_content.encode(),
        encoding='utf-8',
        request=request
    )
    
    result = await spider.parse_jobs(response)
    
    assert result["title"] == "Software Engineer"
    assert "full_description" in result
    assert "basic_qual" in result
    assert "preferred_qual" in result
    assert "Full description text" in " ".join(result["full_description"])
    assert result["job_id"] == "123"
    response.meta["playwright_page"].close.assert_awaited_once()

@pytest.mark.asyncio
async def test_errback(spider):
    mock_page = AsyncMock()
    failure = MagicMock()
    failure.request = MagicMock()
    failure.request.meta = {"playwright_page": mock_page}
    
    await spider.errback(failure)
    
    mock_page.close.assert_awaited_once()

@pytest.mark.asyncio
async def test_parse_no_pagination(spider):
    html_content = """
    <html>
        <body>
            <div role="button">
                <h3><a href="/job/123">Software Engineer</a></h3>
                <div class="metadata-wrapper">
                    <div><div class="metadatum-module_text">Seattle, WA</div></div>
                    <div><div class="metadatum-module_text">Updated today</div></div>
                </div>
                <div><div><div>Short description here</div></div></div>
            </div>
        </body>
    </html>
    """
    
    request = Request(
        url=spider.start_urls[0],
        meta={
            "playwright_page": AsyncMock(),
            "playwright_include_page": True
        }
    )
    response = HtmlResponse(
        url=spider.start_urls[0],
        body=html_content.encode(),
        encoding='utf-8',
        request=request
    )
    
    mock_page = response.meta["playwright_page"]
    mock_page.locator.return_value = MagicMock(is_visible=AsyncMock(return_value=False))
    
    results = []
    async for item in spider.parse(response):
        results.append(item)
    
    mock_page.close.assert_awaited_once()