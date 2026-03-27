import os


class EnsureDataDirPipeline:
    """Ensure data directory exists before writing feed."""

    def open_spider(self, spider):
        os.makedirs("../data", exist_ok=True)
