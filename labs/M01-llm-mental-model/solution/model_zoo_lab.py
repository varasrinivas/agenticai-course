"""
M01 Bonus Lab — Model Zoo: Generative vs. Multimodal (SOLUTION)
================================================================
"""
import base64
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


def generative_call(question: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=128,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text


def multimodal_call(image_path: Path, question: str) -> str:
    """Send a local image as base64 rather than pointing the API at a URL.

    The URL form is fragile in a way that is easy to miss until it bites: the
    API fetches the image itself, so it depends on a third-party host still
    serving that exact path to Anthropic's fetcher. The Wikimedia URL this lab
    used stopped working ("Unable to download the file"), and a Google-hosted
    replacement came back "This URL is disallowed". Reading bytes off disk has
    neither failure mode, and is what production code tends to do anyway.
    """
    data = base64.standard_b64encode(image_path.read_bytes()).decode()
    response = client.messages.create(
        model=MODEL,
        max_tokens=128,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64",
                                                 "media_type": "image/png",
                                                 "data": data}},
                    {"type": "text", "text": question},
                ],
            }
        ],
    )
    return response.content[0].text


if __name__ == "__main__":
    print("=" * 60)
    print("PART 1: GENERATIVE MODEL (text → text)")
    print("=" * 60)
    answer = generative_call("What is the Eiffel Tower? One sentence.")
    print(f"Claude: {answer}\n")

    print("=" * 60)
    print("PART 2: MULTIMODAL MODEL (image + text → text)")
    print("=" * 60)
    # Shipped with the lab, so this works offline-of-the-web and cannot rot.
    # The picture is a red circle, a blue square and a green triangle, which
    # makes the answer easy to check by eye — the point of the exercise is that
    # you can verify the model actually saw the image.
    IMAGE = Path(__file__).resolve().parents[1] / "assets" / "shapes.png"
    description = multimodal_call(IMAGE, "Describe this image in one sentence.")
    print(f"Claude sees: {description}\n")

    print("=" * 60)
    print("CONCEPTUAL: EMBEDDING & RERANKER MODELS")
    print("=" * 60)
    print(
        "An EMBEDDING model (e.g., Voyage-3) would NOT describe the image.\n"
        "Instead it would output ~1024 numbers — a dense vector capturing\n"
        "meaning — so you could search a million images by comparing vectors.\n"
        "\n"
        "A RERANKER model (e.g., Cohere Rerank) takes a query + a list of\n"
        "candidate passages and outputs a relevance score for each one.\n"
        "It is too slow to scan millions of items but very accurate at the\n"
        "final scoring step (typically top-20 → top-5).\n"
        "\n"
        "You will call both in the RAG track:\n"
        "  → M09: embed documents, build a vector index, run semantic search\n"
        "  → M10: add a reranker stage to improve precision"
    )
