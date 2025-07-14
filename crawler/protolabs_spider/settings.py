BOT_NAME = "protolabs_spider"
SPIDER_MODULES = ["protolabs_spider.spiders"]
NEWSPIDER_MODULE = "protolabs_spider.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 2
USER_AGENT = "ProtolabsRAGCrawler/1.0 (+https://github.com)"

ITEM_PIPELINES = {
    "protolabs_spider.pipelines.EnsureDataDirPipeline": 0,
}

FEEDS = {
    "../data/pages.jsonl": {
        "format": "jsonlines",
        "overwrite": False,
    }
}
