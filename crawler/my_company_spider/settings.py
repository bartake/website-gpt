BOT_NAME = "my_company_spider"
SPIDER_MODULES = ["my_company_spider.spiders"]
NEWSPIDER_MODULE = "my_company_spider.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 2
USER_AGENT = "MyCompanyRAGCrawler/1.0 (+https://github.com)"

ITEM_PIPELINES = {
    "my_company_spider.pipelines.EnsureDataDirPipeline": 0,
}

FEEDS = {
    "../data/pages.jsonl": {
        "format": "jsonlines",
        "overwrite": False,
    }
}
