"""
M02 Lab — Step 1: Token Counter
=================================
Count tokens in different text types to understand tokenization.
"""
import tiktoken

SAMPLE_TEXTS = {
    "Short sentence": "The quick brown fox jumps over the lazy dog.",
    "Paragraph": (
        "Uniform Commercial Code filings, commonly known as UCC filings, "
        "are legal forms that creditors file to establish their interest in "
        "a debtor's personal property or assets used as collateral for a loan. "
        "These filings serve as public notice that a lender has a security "
        "interest in the specified assets, which helps establish priority "
        "among creditors in case of default or bankruptcy."
    ),
    "Code snippet": '''def search_filings(debtor_name: str) -> list[dict]:
    """Search UCC filings by debtor name."""
    results = []
    for filing in ALL_FILINGS:
        if debtor_name.lower() in filing["debtor"]["name"].lower():
            results.append(filing)
    return results''',
    "JSON blob": '{"filing_number":"UCC-2024-NY-0012847","type":"UCC-1","state":"New York","debtor":{"name":"Greenfield Logistics LLC","org_type":"LLC"},"status":"Active"}',
}

def count_tokens(text: str) -> int:
    """Count tokens using tiktoken cl100k_base encoding."""
    # TODO: Create a tiktoken encoding with model "cl100k_base"
    # Encode the text and return the number of tokens (length of the encoded list)
    pass

if __name__ == "__main__":
    print("=== Token Counter ===\n")
    print(f"{'Text Type':<20} | {'Characters':>10} | {'Tokens':>6} | {'Ratio':>5}")
    print("-" * 20 + "-|-" + "-" * 10 + "-|-" + "-" * 6 + "-|-" + "-" * 5)
    for name, text in SAMPLE_TEXTS.items():
        try:
            tokens = count_tokens(text)
            ratio = len(text) / tokens if tokens else 0
            print(f"{name:<20} | {len(text):>10} | {tokens:>6} | {ratio:>5.1f}")
        except Exception as e:
            print(f"{name:<20} | [ERROR] {e}")
    print("\nKey insight: Code and structured data use MORE tokens per character than prose.")
