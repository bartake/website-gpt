# Amazon Bedrock Knowledge Base + LLM Setup

This guide walks through configuring the Protolabs RAG pipeline to use **Amazon Bedrock Knowledge Base** (vector store) and **Bedrock LLM** instead of Chroma + Ollama.

## Prerequisites

- AWS account with Bedrock access
- Bedrock model access enabled (enable in Console: Bedrock > Model access)
- AWS credentials configured (`aws configure` or environment variables)

## Step 1: Create Knowledge Base

1. Go to **AWS Console** → **Amazon Bedrock** → **Knowledge bases**
2. Click **Create knowledge base**
3. **Quick create** (recommended): Uses default settings; creates OpenSearch Serverless + S3 automatically
   - Give it a name (e.g. `protolabs-kb`)
   - Note the **Knowledge base ID** and **Data source ID** from the summary
   - Note the **S3 URI** for the data source (e.g. `s3://your-bucket-name/`)
4. Or **Custom create**: Configure vector store (OpenSearch, Aurora, Pinecone) and S3 data source manually

## Step 2: Configure Environment

Set these in `config_bedrock.py` or as environment variables:

```bash
export BEDROCK_KNOWLEDGE_BASE_ID="XXXXXXXXXX"
export BEDROCK_DATA_SOURCE_ID="YYYYYYYYYY"
export BEDROCK_S3_BUCKET="your-bucket-name"
export BEDROCK_S3_PREFIX="protolabs-docs/"
export BEDROCK_MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
export AWS_REGION="us-east-1"
```

- **BEDROCK_S3_BUCKET**: The S3 bucket connected to your KB data source (from Step 1)
- **BEDROCK_MODEL_ID**: Any Bedrock model, e.g.:
  - `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - `meta.llama3-70b-instruct-v1:0`
  - `anthropic.claude-3-haiku-20240307-v1:0`

## Step 3: Run Crawler (if not already done)

```bash
python run_crawl.py
```

Creates `data/pages.jsonl`.

## Step 4: Ingest into Bedrock Knowledge Base

```bash
python ingest_bedrock.py
```

This will:
1. Convert each page in `pages.jsonl` to a .txt file
2. Upload to S3
3. Start an ingestion job to index documents in the Knowledge Base
4. Poll until ingestion completes (typically 5–15 minutes)

## Step 5: Query

```bash
python rag_bedrock.py "What CNC machining tolerances does Protolabs offer?"
python rag_bedrock.py "What materials are available for injection molding?"
python rag_bedrock.py "PEEK tensile strength" --retrieve-only
```

## IAM Permissions Required

Your AWS credentials need:

- `bedrock:Retrieve` (for retrieve_and_generate)
- `bedrock:RetrieveAndGenerate` (for RAG)
- `bedrock:InvokeModel` (for generation)
- `bedrock-agent:StartIngestionJob`
- `bedrock-agent:GetIngestionJob`
- `s3:PutObject` on the data bucket
- `bedrock:GetKnowledgeBase` (optional, for validation)

## Cost Notes

- **Knowledge Base**: OpenSearch Serverless has hourly costs
- **Embeddings**: Amazon Titan embeddings (used by KB) are charged per 1K tokens
- **LLM**: Per model (e.g. Claude 3.5 Sonnet, Llama 3)
- **S3**: Storage and requests

See [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) for details.
