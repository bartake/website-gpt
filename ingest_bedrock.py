"""
Ingest crawled pages into Amazon Bedrock Knowledge Base.
1. Converts pages.jsonl to .txt files (one per page)
2. Uploads to S3
3. Starts ingestion job to sync KB with S3

Prerequisites:
- Bedrock Knowledge Base created (Console: Bedrock > Knowledge bases > Create)
- S3 data source connected to the KB
- AWS credentials configured
"""
import json
import os
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from config_bedrock import (
    BEDROCK_KNOWLEDGE_BASE_ID,
    BEDROCK_DATA_SOURCE_ID,
    BEDROCK_S3_BUCKET,
    BEDROCK_S3_PREFIX,
    BEDROCK_REGION,
)

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
PAGES_FILE = DATA_DIR / "pages.jsonl"


def main():
    if not PAGES_FILE.exists():
        print(f"Error: {PAGES_FILE} not found. Run the crawler first:")
        print("  cd crawler && scrapy crawl my_company")
        return 1

    if not BEDROCK_KNOWLEDGE_BASE_ID or not BEDROCK_DATA_SOURCE_ID:
        print("Error: Set BEDROCK_KNOWLEDGE_BASE_ID and BEDROCK_DATA_SOURCE_ID")
        print("  In config_bedrock.py or as environment variables")
        return 1

    if not BEDROCK_S3_BUCKET:
        print("Error: Set BEDROCK_S3_BUCKET (S3 bucket for document storage)")
        return 1

    print(f"Loading pages from {PAGES_FILE}...")
    pages = []
    with open(PAGES_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pages.append(json.loads(line))

    if not pages:
        print("No pages to ingest.")
        return 1

    s3 = boto3.client("s3", region_name=BEDROCK_REGION)

    print(f"Uploading {len(pages)} documents to s3://{BEDROCK_S3_BUCKET}/{BEDROCK_S3_PREFIX}...")
    for i, doc in enumerate(pages):
        url = doc.get("url", "")
        title = doc.get("title", "")
        text = doc.get("text", "")
        content = f"Title: {title}\nURL: {url}\n\n{text}"
        key = f"{BEDROCK_S3_PREFIX.rstrip('/')}/page_{i:05d}.txt"
        try:
            s3.put_object(
                Bucket=BEDROCK_S3_BUCKET,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/plain",
            )
        except ClientError as e:
            print(f"  Error uploading {key}: {e}")
            return 1
        if (i + 1) % 20 == 0:
            print(f"  Uploaded {i + 1}/{len(pages)}")

    print(f"  Uploaded {len(pages)} documents.")

    client = boto3.client("bedrock-agent", region_name=BEDROCK_REGION)
    print("Starting ingestion job...")
    try:
        response = client.start_ingestion_job(
            knowledgeBaseId=BEDROCK_KNOWLEDGE_BASE_ID,
            dataSourceId=BEDROCK_DATA_SOURCE_ID,
        )
        job_id = response["ingestionJob"]["ingestionJobId"]
        print(f"  Ingestion job started: {job_id}")
        print("  Polling for completion (this may take several minutes)...")

        while True:
            job = client.get_ingestion_job(
                knowledgeBaseId=BEDROCK_KNOWLEDGE_BASE_ID,
                dataSourceId=BEDROCK_DATA_SOURCE_ID,
                ingestionJobId=job_id,
            )["ingestionJob"]
            status = job["status"]
            if status == "COMPLETE":
                stats = job.get("statistics", {})
                print(f"  Done. Indexed: {stats.get('numberOfDocumentsIndexed', 'N/A')}")
                break
            if status == "FAILED":
                reasons = job.get("failureReasons", [])
                print(f"  Ingestion failed: {reasons}")
                return 1
            print(f"  Status: {status}")
            time.sleep(10)

    except ClientError as e:
        err = e.response.get("Error", {})
        print(f"Error: {err.get('Code')} - {err.get('Message')}")
        return 1

    print("\nIngestion complete. You can now run:")
    print("  python rag_bedrock.py 'What services does My Company offer?'")
    return 0


if __name__ == "__main__":
    exit(main())
