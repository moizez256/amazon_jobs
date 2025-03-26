import scrapy
from scrapy_playwright.page import PageMethod

class AmazonJobsSpider(scrapy.Spider):
    name = "amazon_jobs"
    allowed_domains = ["www.amazon.jobs"]
    start_urls = ["https://www.amazon.jobs/content/en/job-categories/software-development"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, meta=dict(
                playwright = True,
                playwright_include_page = True,
                #playwright_page_methods = PageMethod("click", "//button[contains(@class, \"footer-module_expando\")]"),
                errback=self.errback,
            ))

    async def parse(self, response):
        page = response.meta["playwright_page"]
        await page.close()
        for job in response.xpath("//div[@role=\"button\"]"):
            #await page.locator("xpath=.//button[contains(@class, \"footer-module_expando\")]").click()
            #await page.locator(job.xpath(".//button[contains(@class, \"footer-module_expando\")]/")).click()
            yield {
                "title": job.xpath(".//h3/a/text()").extract_first(),
                "location": job.xpath(".//div[contains(@class, \"metadatum-module_text\")]/text()").extract_first(),
                "url": "https://www.amazon.jobs" + job.xpath(".//h3/a/@href").extract_first(),
                #"description_snippet": job.xpath(".//div[contains(@class, \"job-card-module_content\")]/div/text()").extract_first(),
                "updated": job.xpath(".//div[contains(@class, \"metadatum-module_text\")]/text()")[1].extract(),
            }

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
