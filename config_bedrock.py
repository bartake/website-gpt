"""
Bedrock Knowledge Base and LLM configuration.
Set via environment variables or override below.
"""
import os

# Knowledge Base (create via AWS Console: Bedrock > Knowledge bases > Create)
BEDROCK_KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID", "")
BEDROCK_DATA_SOURCE_ID = os.getenv("BEDROCK_DATA_SOURCE_ID", "")

# S3 bucket for document ingestion (must be in same region as KB)
BEDROCK_S3_BUCKET = os.getenv("BEDROCK_S3_BUCKET", "")
BEDROCK_S3_PREFIX = os.getenv("BEDROCK_S3_PREFIX", "my-company-docs/")

# Bedrock LLM for generation (retrieve_and_generate uses this)
# Examples: anthropic.claude-3-5-sonnet-20241022-v2:0, meta.llama3-70b-instruct-v1:0
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

# AWS Region
BEDROCK_REGION = os.getenv("AWS_REGION", os.getenv("BEDROCK_REGION", "us-east-1"))
