"""Spider that crawls the company site via sitemap and extracts content.

Replace mycompany.com in allowed_domains and start_requests with your real domain.
"""
import scrapy
import trafilatura


class MyCompanySpider(scrapy.Spider):
    name = "my_company"
    allowed_domains = ["mycompany.com", "www.mycompany.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 2,
        "ROBOTSTXT_OBEY": True,
    }

    def start_requests(self):
        yield scrapy.Request(
            "https://www.mycompany.com/sitemap/",
            callback=self.parse_sitemap_index,
        )

    def parse_sitemap_index(self, response):
        """Parse sitemap index, find URL sitemaps."""
        # Handle both sitemap index and regular sitemap
        for url in response.xpath("//*[local-name()='loc']/text()").getall():
            url = url.strip()
            if "sitemap" in url.lower():
                yield scrapy.Request(url, callback=self.parse_sitemap)
            else:
                # Direct page URL in sitemap
                if self._allowed_url(url):
                    yield scrapy.Request(url, callback=self.parse_page)

    def parse_sitemap(self, response):
        """Parse sitemap with page URLs."""
        for url in response.xpath("//*[local-name()='loc']/text()").getall():
            url = url.strip()
            if self._allowed_url(url):
                yield scrapy.Request(url, callback=self.parse_page)

    def _allowed_url(self, url):
        """Skip URLs disallowed by robots.txt (query params except wchannelid, wmediaid)."""
        if "?" in url:
            if "wchannelid" not in url and "wmediaid" not in url:
                return False
        return True

    def parse_page(self, response):
        """Extract main content from page."""
        if not response.headers.get("Content-Type", b"").startswith(b"text/html"):
            return

        text = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )

        if not text or len(text.strip()) < 50:
            return

        yield {
            "url": response.url,
            "title": response.css("title::text").get(default="").strip(),
            "text": text.strip(),
        }
