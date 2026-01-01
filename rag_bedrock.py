"""
RAG query using Amazon Bedrock Knowledge Base and Bedrock LLM.
Uses retrieve_and_generate API for retrieval + generation in one call.
"""
import sys
import boto3
from botocore.exceptions import ClientError

from config_bedrock import (
    BEDROCK_KNOWLEDGE_BASE_ID,
    BEDROCK_MODEL_ID,
    BEDROCK_REGION,
)


def ask_bedrock(query: str, retrieve_only: bool = False, top_k: int = 5):
    """Query Bedrock Knowledge Base and optionally generate with Bedrock LLM."""
    if not BEDROCK_KNOWLEDGE_BASE_ID:
        return (
            None,
            None,
            "Error: BEDROCK_KNOWLEDGE_BASE_ID not set. Set it in config_bedrock.py or env.",
        )

    client = boto3.client("bedrock-agent-runtime", region_name=BEDROCK_REGION)

    try:
        if retrieve_only:
            response = client.retrieve(
                knowledgeBaseId=BEDROCK_KNOWLEDGE_BASE_ID,
                retrievalQuery={"text": query},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {"numberOfResults": top_k}
                },
            )
            chunks = []
            for r in response.get("retrievalResults", []):
                text = r.get("content", {}).get("text", "")
                loc = r.get("location", {})
                if text:
                    chunks.append((text, loc))
            return chunks, None, None

        response = client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": BEDROCK_KNOWLEDGE_BASE_ID,
                    "modelArn": f"arn:aws:bedrock:{BEDROCK_REGION}::foundation-model/{BEDROCK_MODEL_ID}",
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": top_k}
                    },
                    "generationConfiguration": {
                        "inferenceConfig": {
                            "maxTokens": 1024,
                            "temperature": 0.0,
                            "topP": 1.0,
                        }
                    },
                },
            },
        )

        output = response.get("output", {})
        text = output.get("text", "")
        citations = output.get("citations", [])

        return None, text, None

    except ClientError as e:
        err = e.response.get("Error", {})
        return None, None, f"Error: {err.get('Code', 'Unknown')} - {err.get('Message', str(e))}"
    except Exception as e:
        return None, None, f"Error: {e}"


def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("Usage: python rag_bedrock.py <question> [--retrieve-only]")
        print("Example: python rag_bedrock.py 'What CNC machining tolerances does Protolabs offer?'")
        print("  --retrieve-only: show retrieved chunks only (no LLM call)")
        return 1

    args = sys.argv[1:]
    retrieve_only = "--retrieve-only" in args
    if retrieve_only:
        args.remove("--retrieve-only")
    query = " ".join(args)

    print(f"Query: {query}\n")

    chunks, answer, err = ask_bedrock(query, retrieve_only=retrieve_only)

    if err:
        print(err)
        return 1

    if retrieve_only and chunks:
        print("--- Retrieved chunks ---\n")
        for i, (text, loc) in enumerate(chunks, 1):
            print(f"[{i}] {text[:500]}...\n")
        return 0

    if answer:
        print(answer)
        return 0

    print("No response returned.")
    return 1


if __name__ == "__main__":
    exit(main())
