import scrapy
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page

class AmazonJobsSpider(scrapy.Spider):

    custom_settings = {
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 4,
    }

    name = "amazon_jobs"
    allowed_domains = ["www.amazon.jobs"]
    start_urls = ["https://www.amazon.jobs/content/en/job-categories/software-development?country%5B%5D=US"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": "default",
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "//ul[contains(@class, 'jobs-module_root')]/li[10]"),
                    ],
                    "errback": self.errback,
                },)

    async def parse(self, response):
        page = response.meta["playwright_page"]

        self.logger.info("Gathering data from jobs modules...")
        
        headers = response.xpath("//div[@role='button']//h3")
        metadata = response.xpath("//div[@role='button']//div[contains(@class, 'metadata-wrapper')]")
        bodies = response.xpath(".//div[@role='button']/div/div[2]/div")

        for header, metadatum, body in zip(headers, metadata, bodies):
            job_url = response.urljoin(header.xpath("./a/@href").get())
            job_id = header.xpath("./a/@href").re_first(r"/job/(\d+)")

            data = {
                "title": header.xpath("./a/text()").get(),
                "url": response.urljoin(header.xpath("./a/@href").get()),
                "location": metadatum.xpath("./div[1]/div[2][contains(@class, 'metadatum-module_text')]//text()").get(),
                "updated": metadatum.xpath("./div[last()]/div[2][contains(@class, 'metadatum-module_text')]//text()").get(),
                "short_description": body.xpath("./text()").getall(),
                "job_id": job_id,
            }

            self.logger.info("Opening job details in new tab...")

            yield response.follow(
                job_url,
                callback=self.parse_jobs,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": f"job-{job_id}",
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "#job-detail"),
                    ],
                    "data": data,
                    "errback": self.errback,
                },
                dont_filter=True,
            )

        next_button = page.locator("//button[@data-test-id='next-page']")
        if next_button and await next_button.is_visible():
            self.logger.info("Pagination found, moving to next 10 results...")

            last_job_title = header.xpath("./a/text()")[-1].get()

            await next_button.click()
            await page.wait_for_timeout(2 * 1000)

            await page.wait_for_function(
                """(lastTitle) => {
                    const jobLinks = document.querySelectorAll('div[role="button"] h3 a');
                    return jobLinks.length > 0 && jobLinks[jobLinks.length - 1].textContent.trim() !== lastTitle;
                }""",
                arg=last_job_title
            )

            new_html = await page.content()
            new_response = response.replace(body=new_html, encoding="utf-8")

            async for item in self.parse(new_response):
                yield item
        else:
            self.logger.info("No pagination found, ending crawl.")
            await page.close()

    async def parse_jobs(self, response):
        page: Page = response.meta["playwright_page"]
        data = response.meta.get("data", {})

        detail_data ={
            "full_description": response.xpath("//div[@class='content']/div/*[text() = 'DESCRIPTION']/following-sibling::p//text()").getall(),
            "basic_qual": response.xpath("//div[@class='content']/div/*[text() = 'DESCRIPTION']/following-sibling::p//text()").getall(),
            "preferred_qual": response.xpath("//div[@class='content']/div/*[text() = 'PREFERRED QUALIFICATIONS']/following-sibling::p//text()").getall(),
        }

        data.update(detail_data)

        await page.close()
        return data

    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        self.logger.info(
            "Handling failure in errback, request=%r, exception=%r", failure.request, failure.value)
        await page.close()
