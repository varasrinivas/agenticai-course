# Check UCC Filing

Review the filing with number: $ARGUMENTS

## Steps
1. Validate the filing number format matches `UCC-YYYY-ST-NNNNNNN`
2. Search the codebase for any references to this filing number
3. Check `data/filings/` for the filing record
4. If found, report: status, debtor, secured party, expiration date
5. If not found, suggest checking the state filing office directly
6. Flag any compliance issues (expired, missing amendments, etc.)
