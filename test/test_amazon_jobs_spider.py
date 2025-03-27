import pytest
from scrapy.http import Request, HtmlResponse
from amazon_jobs_scrapy.amazon_jobs_scrapy.spiders.amazon_jobs import AmazonJobsSpider
from scrapy_playwright.page import PageMethod
from unittest.mock import AsyncMock, MagicMock, patch

class TestAmazonJobsSpider:

    @pytest.fixture
    def spider(self):
        return AmazonJobsSpider()

    def create_response(self, request, body_content):
        """Helper para crear respuestas con contenido personalizado"""
        return HtmlResponse(
            url=request.url,
            request=request,
            body=body_content.encode('utf-8'),
            encoding='utf-8'
        )

    @pytest.mark.asyncio
    async def test_parse_job_extraction(self, spider, mock_response, mock_playwright_page):
        # Configurar HTML de prueba creando una nueva respuesta
        test_html = """
        <html>
            <ul class="jobs-module_root">
                <li></li>
                <div role="button">
                    <h3><a href="/job/123">Software Engineer</a></h3>
                    <div class="metadata-wrapper">
                        <div><div class="metadatum-module_text">Seattle, WA</div></div>
                        <div><div class="metadatum-module_text">Updated 2 days ago</div></div>
                    </div>
                    <div><div><div>Short description</div></div></div>
                </div>
            </ul>
        </html>
        """
        response = self.create_response(mock_response.request, test_html)

        # Configurar mock para la nueva pestaña
        new_tab = AsyncMock()
        mock_playwright_page.context.new_page.return_value = new_tab
        new_tab.locator.return_value.text_content.side_effect = [
            "JOB123",  # job_id
            "Full description text",  # full_description
            "Basic qualifications text",  # basic_qual
            "Preferred qualifications text"  # preferred_qual
        ]

        # Ejecutar parse
        results = []
        async for item in spider.parse(response):
            results.append(item)

        # Verificaciones
        assert len(results) == 1
        assert results[0]["title"] == "Software Engineer"
        assert "Seattle, WA" in results[0]["location"]
        assert "2 days ago" in results[0]["updated"]
        assert "Short description" in str(results[0]["short_description"])
        assert results[0]["job_id"] == "JOB123"
        assert results[0]["full_description"] == "Full description text"

        # Verificar que se abrió y cerró la nueva pestaña
        mock_playwright_page.context.new_page.assert_called_once()
        new_tab.goto.assert_called_once_with("https://www.amazon.jobs/job/123")
        new_tab.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_pagination(self, spider, mock_response, mock_playwright_page):
        # Configurar HTML de prueba con botón de paginación
        test_html = """
        <html>
            <button data-test-id="next-page"></button>
            <div role="button">
                <h3><a href="/job/123">Job 1</a></h3>
                <div class="metadata-wrapper"></div>
                <div><div><div>Description</div></div></div>
            </div>
        </html>
        """
        response = self.create_response(mock_response.request, test_html)

        # Configurar mock para paginación
        mock_playwright_page.locator.return_value.is_visible.return_value = True
        mock_playwright_page.content.return_value = "<html><div role='button'><h3><a href='/job/456'>Job 2</a></h3></div></html>"

        # Mock para la nueva pestaña de detalles
        new_tab = AsyncMock()
        mock_playwright_page.context.new_page.return_value = new_tab
        new_tab.locator.return_value.text_content.return_value = "Mocked content"

        # Ejecutar parse
        results = []
        async for item in spider.parse(response):
            results.append(item)

        # Verificaciones
        assert len(results) > 0
        mock_playwright_page.locator.assert_called_with("//button[@data-test-id='next-page']")
        mock_playwright_page.wait_for_function.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_no_jobs(self, spider, mock_response, mock_playwright_page):
        # Configurar HTML sin trabajos
        test_html = "<html><body>No jobs found</body></html>"
        response = self.create_response(mock_response.request, test_html)

        results = []
        async for item in spider.parse(response):
            results.append(item)

        assert len(results) == 0
        mock_playwright_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_details_extraction(self, spider, mock_response, mock_playwright_page):
        # Configurar HTML de prueba
        test_html = """
        <html>
            <div role="button">
                <h3><a href="/job/123">Detailed Job</a></h3>
                <div class="metadata-wrapper"></div>
                <div><div><div>Details</div></div></div>
            </div>
        </html>
        """
        response = self.create_response(mock_response.request, test_html)

        # Configurar mock para la nueva pestaña con detalles específicos
        new_tab = AsyncMock()
        mock_playwright_page.context.new_page.return_value = new_tab
        
        # Configurar diferentes respuestas para diferentes locators
        def text_content_side_effect(*args, **kwargs):
            locator = args[0]
            if "DESCRIPTION" in locator:
                return "Job description text"
            elif "PREFERRED QUALIFICATIONS" in locator:
                return "Preferred qualifications text"
            return "Default text"
        
        new_tab.locator.return_value.text_content.side_effect = text_content_side_effect

        # Ejecutar parse
        results = []
        async for item in spider.parse(response):
            results.append(item)

        # Verificaciones específicas de campos de detalles
        assert results[0]["full_description"] == "Job description text"
        assert results[0]["preferred_qual"] == "Preferred qualifications text"