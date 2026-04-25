# Shared Utilities

Files in this directory are used across multiple labs. They are **complete** — do not modify them.

## Files

| File | Purpose | Used By |
|------|---------|---------|
| `mock_ucc_data.py` | 11 realistic UCC filings (8 normal + 3 edge cases) with search functions | M04+ (Python) |
| `mock_ucc_data.js` | Same data and search functions for Node.js | M04+ (Node.js) |
| `test_helpers.py` | Response validation, mock objects, output formatting, cost tracking | All labs (Python) |

## Mock UCC Data

The UCC filing dataset simulates Domain C (Public Records / UCC Data Engineering) scenarios:

- **8 standard filings**: NY, CA, TX, FL, DE, IL, NY (terminated), GA
- **3 edge cases**: Missing debtor name (NV), duplicate filing number (NY), expired/lapsed filing (OH)
- Filing types: UCC-1 (original) and UCC-3 (amendment/termination)
- Statuses: Active, Amendment, Terminated, Lapsed

### Python Usage

```python
from shared.mock_ucc_data import MOCK_FILINGS, get_filing_by_number, search_filings

# Look up a specific filing
filing = get_filing_by_number("UCC-2024-NY-0012847")

# Search by criteria
texas_filings = search_filings(state="Texas")
active_llcs = search_filings(status="Active", debtor_name="LLC")
```

### Node.js Usage

```javascript
import { MOCK_FILINGS, getFilingByNumber, searchFilings } from '../shared/mock_ucc_data.js';

const filing = getFilingByNumber("UCC-2024-NY-0012847");
const texasFilings = searchFilings({ state: "Texas" });
```

## Test Helpers

Utilities for validating Claude API responses and formatting lab output:

```python
from shared.test_helpers import (
    load_env,              # Load .env from labs root
    assert_valid_response, # Validate Claude response structure
    get_text_content,      # Extract text from response
    get_tool_use_blocks,   # Extract tool_use blocks from response
    mock_claude_response,  # Create mock response (no API call)
    print_separator,       # Visual output separator
    format_tokens,         # Format token count with cost estimate
)
```

## Import Notes

Run scripts from the `labs/` root directory so shared imports resolve correctly:

```bash
# From labs/ root
python -m M05-function-calling.starter.agent

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```
