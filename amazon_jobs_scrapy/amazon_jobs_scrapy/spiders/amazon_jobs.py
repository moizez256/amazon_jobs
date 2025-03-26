import scrapy
from scrapy_playwright.page import PageMethod
#from playwright.async_api import Page

class AmazonJobsSpider(scrapy.Spider):
    name = "amazon_jobs"
    allowed_domains = ["www.amazon.jobs"]
    start_urls = ["https://www.amazon.jobs/content/en/job-categories/software-development"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, meta=dict(
                playwright = True,
                playwright_include_page = True,
                playwright_context = "default",
                playwright_page_methods = [
                    PageMethod("wait_for_selector", "//ul[contains(@class, 'jobs-module_root')]/li[10]"),
                    #PageMethod("wait_for_selector", "//button[@data-test-id='next-page']"),
                    #PageMethod("wait_for_timeout", 45 * 1000),
                ],
                errback=self.errback,
            ))

    async def parse(self, response):
        page = response.meta["playwright_page"]
        #await page.close()
        headers = response.xpath("//div[@role=\"button\"]//h3")
        metadata = response.xpath("//div[@role=\"button\"]//div[contains(@class, \"metadata-wrapper\")]")
        bodies = response.xpath(".//div[@role=\"button\"]/div/div[2]/div")
        for header, metadatum, body in zip(headers, metadata, bodies):
            yield {
                "title": header.xpath("./a/text()").get(),
                "url": response.urljoin(header.xpath("./a/@href").get()),
                "location": metadatum.xpath("./div[1]/div[2][contains(@class, \"metadatum-module_text\")]//text()").get(),
                "updated": metadatum.xpath("./div[last()]/div[2][contains(@class, \"metadatum-module_text\")]//text()").get(),
                "description_snippet": body.xpath("./text()").getall(),
            }

        next_button = await page.query_selector("//button[@data-test-id='next-page']")
        if await next_button.is_visible():
            self.logger.info("Paginación encontrada. Pasando a la siguiente página sin recargar...")
            
            await next_button.click()
            await page.wait_for_selector("//div[@role='button']", state="visible")

            new_html = await page.content()
            new_response = response.replace(body=new_html, encoding="utf-8")

            async for item in self.parse(new_response):
                yield item

        await page.close()

        # next_button = response.xpath("//button[@data-test-id='next-page']")
        # if next_button:
        #     self.logger.info("Paginación encontrada. Pasando a la siguiente página...")
        #     yield scrapy.Request(
        #         url=response.url,
        #         dont_filter=True,
        #         meta={
        #             "playwright": True,
        #             "playwright_include_page": True,
        #             "playwright_context": "default",
        #             "playwright_page_methods": [
        #                 PageMethod("wait_for_selector", "//button[@data-test-id='next-page']", state="visible"),
        #                 PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
        #                 #PageMethod("click", "//button[@data-test-id='next-page']"),
        #                 PageMethod("evaluate", "document.querySelector('[data-test-id=\"next-page\"]').click()"),
        #                 PageMethod("wait_for_selector", "//ul[contains(@class, 'jobs-module_root')]/li[10]"),
        #                 #PageMethod("wait_for_timeout", 45 * 1000),
        #             ],
        #             "errback": self.errback,
        #         },
        #         callback=self.parse,  # Vuelve a ejecutar parse con la nueva página
        #     )

        
        
    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
