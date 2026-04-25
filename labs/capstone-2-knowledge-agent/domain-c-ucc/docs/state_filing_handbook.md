# State UCC Filing Handbook — Procedures and Requirements

**Document Version:** 2024.1
**Last Updated:** February 1, 2024
**Audience:** Filing officers, paralegals, compliance analysts

---

## 1. Overview of the Filing Process

Filing a UCC financing statement is the primary method for perfecting a
security interest in personal property collateral. This handbook covers
the procedures, requirements, and variations across state filing offices.

### 1.1 Where to File

The general rule for determining the correct filing office:

**For registered organizations (corporations, LLCs, LPs):**
- File in the state where the organization is **organized** (state of
  incorporation or formation), NOT the state where the organization does
  business or where the collateral is located
- File with the **Secretary of State** (or equivalent office)

**For individuals:**
- File in the state of the individual's **principal residence**
- File with the Secretary of State

**Exceptions (file locally):**
- Fixtures: file with the county recorder where the real property is located
- Timber to be cut: file with the county recorder where the timber is located
- Minerals and as-extracted collateral: file with the county recorder where
  the wellhead or minehead is located

### 1.2 Filing Methods

Most states accept filings through multiple channels:

| Method | Processing Time | Fee Notes |
|--------|----------------|-----------|
| Online (e-filing) | Same-day or next-day | Standard fee; often required for bulk filers |
| Mail | 3-10 business days | Standard fee + potential return mail delays |
| In-person (walk-in) | Same-day | May have an expedited service surcharge |
| Fax | 1-3 business days | Not accepted in all states |
| XML bulk filing | Same-day batch processing | Available for high-volume filers via direct API |

### 1.3 Standard Filing Fees (2024)

Filing fees vary by state. Below is a representative sample:

| State | UCC-1 Filing | UCC-3 Amendment | UCC-3 Continuation | Search Fee |
|-------|-------------|----------------|--------------------|-----------|
| California | $20 | $20 | $20 | $10 per debtor name |
| Delaware | $50 | $50 | $50 | $25 per debtor name |
| Florida | $10 | $10 | $10 | $5 per debtor name |
| Illinois | $10 | $10 | $10 | $10 per debtor name |
| New York | $40 | $40 | $40 | $25 per debtor name |
| Texas | $15 | $15 | $15 | $10 per debtor name |
| Nevada | $20 | $20 | $20 | $15 per debtor name |
| Wyoming | $15 | $15 | $15 | $10 per debtor name |

Note: County fixture filings may have different fee schedules. Contact the
county recorder's office for specific fees.

## 2. UCC-1 Financing Statement

### 2.1 Required Fields

The UCC-1 form (UCC1 national form, revised 04/20/2011) requires:

**Box 1 — Debtor Information:**
- 1a: Organization's name OR individual's last name, first name
- 1b: Mailing address (street, city, state, ZIP)
- 1c: (If organization) State of organization and organization ID number
- 1d: (If organization) Type of organization
- Alternative: 1a-1d for additional debtors (use addendum UCC1Ad for 3+ debtors)

**Box 2 — Additional Debtor(s):**
- Same format as Box 1 for a second debtor

**Box 3 — Secured Party Information:**
- 3a: Organization's name OR individual's last name, first name
- 3b: Mailing address
- Additional secured parties: use addendum UCC1Ap

**Box 4 — Collateral Description:**
- Free-text field describing the collateral
- May use UCC Article 9 collateral types (e.g., "All Accounts, General
  Intangibles, and Proceeds thereof")
- May reference an attached exhibit ("See Exhibit A attached hereto and
  incorporated by reference")
- "All Assets" or "All personal property" is permissible

**Box 5 — Check boxes (if applicable):**
- 5a: Lien covered by this filing is a manufactured-home transaction
- 5b: Lien covered by this filing is a public-finance transaction
- 5c: Fixture filing (requires real property description)

**Box 6 — Optional Filer Reference Data:**
- Internal reference number or code for the filer's records

### 2.2 Common Filing Errors

The following errors are grounds for rejection by the filing office:

| Error | Consequence |
|-------|------------|
| Missing debtor name | Rejection — filing not accepted |
| Missing secured party name | Rejection |
| Missing secured party address | Rejection |
| Illegible filing | Rejection |
| Insufficient fee | Rejection (filing held pending fee payment in some states) |
| Missing debtor address | Filing accepted but missing address noted |
| Wrong form version | May be rejected in some states |

The following errors do NOT result in rejection but may affect the filing's
effectiveness:

| Error | Risk |
|-------|------|
| Incorrect debtor name | Filing may be "seriously misleading" and ineffective against third parties |
| Incorrect collateral description | Security interest may not cover intended collateral |
| Missing organization type/ID | Filing accepted; may trigger informational request from filing office |
| Typographical errors in addresses | Filing accepted; may cause issues with notice delivery |

### 2.3 Debtor Name Best Practices

1. **For organizations:** Always obtain and verify the exact legal name from
   the state of organization's business entity database (e.g., Delaware
   Division of Corporations, California Secretary of State bizfile)
2. **For individuals:** Obtain a copy of the debtor's current driver's license;
   use the name exactly as it appears
3. **Run a pre-filing search** to verify the debtor name will be indexed
   correctly by the filing office's standard search logic
4. **Avoid:** Trade names, DBA names, former names, shortened names, nicknames
5. **Include the entity suffix** exactly as it appears in the public record
   (e.g., "LLC" not "L.L.C." if the state record shows "LLC")

## 3. UCC-3 Amendment Form

### 3.1 Amendment Types

The UCC-3 form is used for all post-filing actions:

**Continuation (Section 3.3):**
- Extends the filing for another 5 years from the current lapse date
- Must be filed within the 6-month window before lapse (i.e., between month 54
  and month 60 of the filing's life)
- Filing a continuation too early (before the 6-month window) is ineffective
- Filing a continuation after lapse is ineffective; a new UCC-1 must be filed

**Amendment (Section 3.4):**
- Changes to the debtor name, secured party name, or collateral description
- Adding or removing debtors requires debtor authorization
- Adding collateral requires debtor authorization
- Deleting collateral does not require debtor authorization

**Assignment (Section 3.5):**
- Transfers the secured party's interest to an assignee
- Used in loan sales, participations, and securitizations
- The assignee becomes the new secured party of record
- Does not require debtor authorization (but debtor should be notified)

**Termination (Section 3.6):**
- Ends the filing; filed when the secured obligation has been satisfied
- Secured party MUST file a termination within:
  - 20 days of debtor's written demand (for non-consumer transactions)
  - 30 days of satisfaction of the secured obligation (for consumer transactions)
- Failure to terminate: debtor may recover $500 statutory damages plus actual damages

### 3.2 Continuation Timeline

```
Year 0          Year 4.5         Year 5
  |                |               |
  |  Filing        |  Window       |  Lapse
  |  Effective     |  Opens        |  Date
  |                |               |
  |                |<-- 6 months ->|
  |                | FILE HERE     |
```

If a continuation is filed during the window, the new lapse date is 5 years
from the **original** lapse date (not from the date of the continuation filing).

### 3.3 Authorization Requirements

| Action | Debtor Auth Required? | Notes |
|--------|----------------------|-------|
| Continuation | No | Secured party files unilaterally |
| Add debtor | Yes | New debtor must authorize |
| Delete debtor | No | Secured party may file |
| Change debtor name | Yes | If debtor's name has legally changed |
| Add collateral | Yes | Debtor must authorize expansion |
| Delete collateral | No | Secured party may release collateral |
| Assignment | No | Secured party transfers interest |
| Termination | N/A | Secured party's obligation to file |

## 4. Searching the UCC Filing System

### 4.1 Search Methods

| Method | Description | Typical Cost |
|--------|-------------|-------------|
| Online portal | Most states offer real-time online search | $5-$25 per name |
| Certified search | Official search certificate from filing office | $15-$50 per name |
| Bulk data download | Full filing database (monthly or quarterly) | $500-$5,000+ per state |
| Third-party providers | Commercial search services (CSC, CT Corp, Cogency Global) | $25-$75 per name |

### 4.2 Search Tips

1. **Search the correct state:** For organizations, search the state of
   organization. For individuals, search the state of principal residence.
2. **Search by exact legal name:** Use the debtor's legal name, not trade names
3. **Run variations:** If unsure of the exact name, run searches with and
   without common entity suffixes
4. **Check the details:** When reviewing search results, verify:
   - The debtor name matches your target entity
   - The filing has not lapsed (check lapse date)
   - No termination has been filed
   - The collateral description covers the assets in question
5. **Review amendments:** Check all UCC-3 amendments associated with the
   original filing for name changes, collateral changes, or assignments

### 4.3 Interpreting Search Results

A UCC search may reveal:

| Finding | Interpretation |
|---------|---------------|
| No filings found | No perfected security interests (but could be filing in wrong state) |
| Active filing covering "all assets" | Blanket lien — most assets are pledged as collateral |
| Multiple active filings | Multiple creditors with security interests; priority determined by filing date |
| Terminated filing | Previously existing security interest that has been released |
| Lapsed filing | Filing expired; security interest is no longer perfected (but may still be enforceable against debtor) |
| Filing with specific collateral | Security interest limited to described collateral only |

## 5. State-Specific Variations

While Article 9 is largely uniform, some states have notable variations:

### 5.1 Louisiana

Louisiana has NOT adopted Article 9. Instead, Louisiana uses its own Civil Code
provisions for secured transactions (Chapter 9 of Title 10 of the Louisiana
Revised Statutes). However, Louisiana participates in the central filing system
and accepts UCC-1 filings for transactions governed by other states' laws.

### 5.2 Filing Office Variations

| State | Filing Office Name | Notable Differences |
|-------|-------------------|-------------------|
| California | Secretary of State, UCC Division | Requires debtor organizational ID; online portal: bizfileOnline.sos.ca.gov |
| Delaware | Division of Corporations, UCC | Premium expedited service (1-hour turnaround for $1,000); most popular state for entity formation |
| New York | Department of State, UCC Section | County filings handled by county clerks; dual filing may be required for certain collateral |
| Texas | Secretary of State, Statutory Filings | Two-page maximum for collateral description without additional page fee |
| Florida | Department of State, Division of Corporations | Filings indexed within 24 hours; real-time online search |

### 5.3 Individual Debtor Name Rules by State

States are split on which rule they follow for individual debtor names:

| Approach | States | Rule |
|----------|--------|------|
| Only-if (driver's license) | ~30 states (including CA, FL, TX, VA) | Must use driver's license name if debtor has one |
| Safe-harbor (either) | ~20 states (including NY, IL, OH, PA) | Filing effective if it uses DL name OR individual legal name |

## 6. Electronic Filing Standards

### 6.1 IACA XML Standard

The International Association of Commercial Administrators (IACA) has
established XML standards for electronic UCC filings:

- XML schema version: IACA UCC XML v2.0
- Supports: UCC-1, UCC-3, Information Statements
- Character encoding: UTF-8
- Maximum collateral description length: 10,000 characters (varies by state)
- File attachment support: PDF only, maximum 10 pages

### 6.2 Bulk Filing Programs

States offering bulk filing programs:

| State | Program | Minimum Volume | Format |
|-------|---------|---------------|--------|
| Delaware | Direct Filing | 50+ filings/month | IACA XML |
| California | Batch Filing | 25+ filings/month | IACA XML or CSV |
| New York | E-Filing | 10+ filings/month | IACA XML |
| Texas | SOSDirect Batch | No minimum | IACA XML |

### 6.3 Data Quality Standards

For bulk filers, the following data quality standards apply:

- Rejection rate must be below 5% per batch
- Debtor name accuracy: 99%+ match to public organic records
- Address standardization: USPS CASS-certified formatting
- Collateral description: no truncation; full description must be included
