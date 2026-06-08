"""
M01 Bonus Lab — Model Zoo: Generative vs. Multimodal
=====================================================
You've already used the GENERATIVE mode (text in → text out) in the
temperature lab.  This script shows the MULTIMODAL mode: pass an image
URL alongside a text question and Claude returns a description.

No extra API key needed — both modes use the same Claude client.

HOW TO RUN
----------
1. Activate the venv you created in the main lab setup.
2. Run:  python model_zoo_lab.py
3. Confirm you see a text-only answer AND an image description.

LOOKING AHEAD
-------------
Embedding and reranker models require a separate API key (Voyage, Cohere,
or OpenAI).  You'll call them in the RAG labs:
  - M09: embedding model to index documents, cosine-similarity search
  - M10: reranker to score retrieved chunks before sending to Claude
For now, the conceptual side is covered below in the printed output.
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"   # cheapest Claude; handles both modes


# ---------------------------------------------------------------------------
# Part 1: GENERATIVE (text only) — you already know this from temperature_lab
# ---------------------------------------------------------------------------

def generative_call(question: str) -> str:
    """Standard text-in / text-out call."""
    # TODO: Call client.messages.create() with:
    #   model=MODEL, max_tokens=128
    #   messages=[{"role": "user", "content": question}]
    # Return response.content[0].text
    pass


# ---------------------------------------------------------------------------
# Part 2: MULTIMODAL (image URL + text → text)
# Claude 3+ accepts images directly via a public URL in the message content.
# ---------------------------------------------------------------------------

def multimodal_call(image_url: str, question: str) -> str:
    """
    Pass a public image URL alongside a text question.
    Claude reads the image and answers the question about it.
    """
    # TODO: Call client.messages.create() with:
    #   model=MODEL, max_tokens=128
    #   messages=[{
    #     "role": "user",
    #     "content": [
    #       {
    #         "type": "image",
    #         "source": {"type": "url", "url": image_url}
    #       },
    #       {"type": "text", "text": question}
    #     ]
    #   }]
    # Return response.content[0].text
    pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Part 1: Generative ---
    print("=" * 60)
    print("PART 1: GENERATIVE MODEL (text → text)")
    print("=" * 60)
    answer = generative_call("What is the Eiffel Tower? One sentence.")
    print(f"Claude: {answer}\n")

    # --- Part 2: Multimodal ---
    print("=" * 60)
    print("PART 2: MULTIMODAL MODEL (image + text → text)")
    print("=" * 60)
    # A stable Wikipedia public domain image of bicycles
    IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Bikesgray.jpg/320px-Bikesgray.jpg"
    description = multimodal_call(IMAGE_URL, "Describe this image in one sentence.")
    print(f"Claude sees: {description}\n")

    # --- Conceptual: what embedding & reranker models would do differently ---
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
