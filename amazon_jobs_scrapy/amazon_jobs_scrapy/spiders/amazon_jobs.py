import scrapy
from scrapy_playwright.page import PageMethod

class AmazonJobsSpider(scrapy.Spider):
    name = "amazon_jobs"
    allowed_domains = ["www.amazon.jobs"]
    start_urls = ["https://www.amazon.jobs/content/en/job-categories/software-development?country%5B%5D=US"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url,
                meta=dict(
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
        context = page.context

        headers = response.xpath("//div[@role=\"button\"]//h3")
        metadata = response.xpath("//div[@role=\"button\"]//div[contains(@class, \"metadata-wrapper\")]")
        bodies = response.xpath(".//div[@role=\"button\"]/div/div[2]/div")

        for header, metadatum, body in zip(headers, metadata, bodies):
            job_url = response.urljoin(header.xpath("./a/@href").get())

            new_tab = await context.new_page()
            await new_tab.goto(job_url)
            await new_tab.wait_for_selector("#job-detail")

            job_id = await new_tab.locator("xpath=//div[@class='details-line']/p").text_content()
            full_description = await new_tab.locator("xpath=//div[@class='content']/div/*[text() = 'DESCRIPTION']/../p").text_content()
            basic_qual = await new_tab.locator("xpath=//div[@class='content']/div/*[text() = 'DESCRIPTION']/../p").text_content()
            preferred_qual = await new_tab.locator("xpath=//div[@class='content']/div/*[text() = 'PREFERRED QUALIFICATIONS']/../p").text_content()

            yield {
                "title": header.xpath("./a/text()").get(),
                "url": response.urljoin(header.xpath("./a/@href").get()),
                "location": metadatum.xpath("./div[1]/div[2][contains(@class, \"metadatum-module_text\")]//text()").get(),
                "updated": metadatum.xpath("./div[last()]/div[2][contains(@class, \"metadatum-module_text\")]//text()").get(),
                "short_description": body.xpath("./text()").getall(),
                "job_id": job_id,
                "full_description": full_description,
                "basic_qual": basic_qual,
                "preferred_qual": preferred_qual,
            }

            await new_tab.close()

        next_button = page.locator("//button[@data-test-id='next-page']")
        if await next_button.is_visible():
            self.logger.info("Paginación encontrada. Pasando a la siguiente página sin recargar...")

            last_job_title = header.xpath("./a/text()").get()

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

        await page.close()

    # def details_parse(self, response):
    #     job = response.xpath("//div[@id='job-detail']")
    #     return {
    #         "job_id": job.xpath(".//div[@class='details-line']/p/text()").re_first(r"Job ID: (\d+)"),
    #         "full_description": job.xpath(".//div[@class='content']/div/*[text() = 'DESCRIPTION']/../p/text()").getall(),
    #         "basic_qual": job.xpath(".//div[@class='content']/div/*[text() = 'BASIC QUALIFICATIONS']/../p/text()").getall(),
    #         "preferred_qual": job.xpath(".//div[@class='content']/div/*[text() = 'PREFERRED QUALIFICATIONS']/../p/text()").getall(),
    #     }

    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
