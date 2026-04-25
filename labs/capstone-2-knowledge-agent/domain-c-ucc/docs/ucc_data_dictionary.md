# UCC Filing Data Dictionary

**Document Version:** 2024.1
**Last Updated:** January 25, 2024
**Audience:** Data engineers, analysts, software developers

---

## 1. Purpose

This data dictionary defines the fields, data types, and validation rules for
UCC filing data as maintained by state filing offices and consumed by
downstream data systems. It is intended for use in building data pipelines,
analytical models, and search applications that process UCC filing records.

## 2. Core Filing Record

### 2.1 Filing Header

| Field Name | Data Type | Length | Required | Description |
|------------|----------|--------|----------|-------------|
| file_number | VARCHAR | 20 | Yes | Unique filing identifier assigned by the filing office. Format varies by state (e.g., "2024-1234567" in CA, "20240112345" in DE). |
| file_date | DATE | 10 | Yes | Date the filing was accepted by the filing office. Format: YYYY-MM-DD. |
| file_time | TIME | 8 | No | Time of filing acceptance (HH:MM:SS). Not all states record time. |
| lapse_date | DATE | 10 | Yes | Date the filing expires. Calculated as file_date + 5 years for original filings. For continuations: original_lapse_date + 5 years. |
| filing_type | ENUM | 20 | Yes | Type of filing: ORIGINAL, AMENDMENT, CONTINUATION, ASSIGNMENT, TERMINATION, INFORMATION_STATEMENT. |
| original_file_number | VARCHAR | 20 | Conditional | For non-original filings: the file_number of the initial UCC-1 that this filing relates to. Required for all filing types except ORIGINAL. |
| filing_office | VARCHAR | 50 | Yes | Name of the filing office that accepted the filing (e.g., "California Secretary of State"). |
| filing_state | CHAR | 2 | Yes | Two-letter state code (e.g., "CA", "DE", "NY"). |
| status | ENUM | 15 | Yes | Current status: ACTIVE, LAPSED, TERMINATED. Derived from lapse_date and termination filings. |
| image_available | BOOLEAN | 1 | No | Whether a scanned image of the original filing is available. |
| pages | INTEGER | 3 | No | Number of pages in the filing document. |

### 2.2 Debtor Record

A filing may have one or more debtor records.

| Field Name | Data Type | Length | Required | Description |
|------------|----------|--------|----------|-------------|
| debtor_id | INTEGER | 10 | Yes | System-generated unique identifier for this debtor record. |
| file_number | VARCHAR | 20 | Yes | Foreign key to the filing header. |
| debtor_type | ENUM | 15 | Yes | INDIVIDUAL or ORGANIZATION. |
| org_name | VARCHAR | 200 | Conditional | Organization's legal name (required if debtor_type = ORGANIZATION). |
| last_name | VARCHAR | 100 | Conditional | Individual's last/family name (required if debtor_type = INDIVIDUAL). |
| first_name | VARCHAR | 50 | Conditional | Individual's first/given name (required if debtor_type = INDIVIDUAL). |
| middle_name | VARCHAR | 50 | No | Individual's middle name or initial. |
| suffix | VARCHAR | 10 | No | Name suffix (Jr., Sr., III, etc.). |
| address_line1 | VARCHAR | 100 | Yes | Mailing address line 1. |
| address_line2 | VARCHAR | 100 | No | Mailing address line 2 (suite, apt, etc.). |
| city | VARCHAR | 50 | Yes | City name. |
| state | CHAR | 2 | Yes | Two-letter state code. |
| zip_code | VARCHAR | 10 | Yes | ZIP code (5-digit or ZIP+4 format). |
| country | CHAR | 2 | No | Two-letter country code (defaults to "US"). |
| org_state | CHAR | 2 | Conditional | State of organization (required if debtor_type = ORGANIZATION). |
| org_id | VARCHAR | 30 | No | Organization identification number (e.g., state-assigned entity number). |
| org_type | VARCHAR | 30 | No | Type of organization: CORPORATION, LLC, LP, LLP, TRUST, PARTNERSHIP, OTHER. |

### 2.3 Secured Party Record

A filing may have one or more secured party records.

| Field Name | Data Type | Length | Required | Description |
|------------|----------|--------|----------|-------------|
| secured_party_id | INTEGER | 10 | Yes | System-generated unique identifier. |
| file_number | VARCHAR | 20 | Yes | Foreign key to the filing header. |
| party_type | ENUM | 15 | Yes | INDIVIDUAL or ORGANIZATION. |
| org_name | VARCHAR | 200 | Conditional | Organization's name (required if party_type = ORGANIZATION). |
| last_name | VARCHAR | 100 | Conditional | Individual's last name (required if party_type = INDIVIDUAL). |
| first_name | VARCHAR | 50 | Conditional | Individual's first name (required if party_type = INDIVIDUAL). |
| address_line1 | VARCHAR | 100 | Yes | Mailing address line 1. |
| address_line2 | VARCHAR | 100 | No | Mailing address line 2. |
| city | VARCHAR | 50 | Yes | City. |
| state | CHAR | 2 | Yes | State code. |
| zip_code | VARCHAR | 10 | Yes | ZIP code. |

### 2.4 Collateral Record

| Field Name | Data Type | Length | Required | Description |
|------------|----------|--------|----------|-------------|
| collateral_id | INTEGER | 10 | Yes | System-generated unique identifier. |
| file_number | VARCHAR | 20 | Yes | Foreign key to the filing header. |
| collateral_description | TEXT | 10000 | Yes | Free-text description of the collateral. May be very long (up to 10,000 characters in some states). |
| collateral_type_code | VARCHAR | 50 | No | Standardized collateral type code (derived by NLP/classification from description). Values: ACCOUNTS, CHATTEL_PAPER, DEPOSIT_ACCOUNTS, DOCUMENTS, EQUIPMENT, FARM_PRODUCTS, FIXTURES, GENERAL_INTANGIBLES, GOODS, INSTRUMENTS, INVENTORY, INVESTMENT_PROPERTY, LETTER_OF_CREDIT_RIGHTS, ALL_ASSETS, OTHER. |
| is_all_assets | BOOLEAN | 1 | No | True if the collateral description is a blanket "all assets" or equivalent. |
| fixture_indicator | BOOLEAN | 1 | No | True if this is a fixture filing. |
| real_property_description | TEXT | 5000 | Conditional | Real property description (required if fixture_indicator = TRUE). |

## 3. Amendment Records

### 3.1 Amendment Header

| Field Name | Data Type | Length | Required | Description |
|------------|----------|--------|----------|-------------|
| amendment_id | INTEGER | 10 | Yes | System-generated unique identifier. |
| file_number | VARCHAR | 20 | Yes | The file number of this amendment (UCC-3). |
| original_file_number | VARCHAR | 20 | Yes | The file number of the original UCC-1 being amended. |
| amendment_date | DATE | 10 | Yes | Date the amendment was filed. |
| amendment_type | ENUM | 20 | Yes | CONTINUATION, AMENDMENT, ASSIGNMENT, TERMINATION, PARTIAL_RELEASE, FULL_RELEASE. |
| amendment_description | TEXT | 5000 | No | Description of the amendment action. |

### 3.2 Amendment Actions

| Field Name | Data Type | Length | Required | Description |
|------------|----------|--------|----------|-------------|
| action_id | INTEGER | 10 | Yes | System-generated unique identifier. |
| amendment_id | INTEGER | 10 | Yes | Foreign key to the amendment header. |
| action_type | ENUM | 30 | Yes | ADD_DEBTOR, DELETE_DEBTOR, CHANGE_DEBTOR_NAME, ADD_SECURED_PARTY, DELETE_SECURED_PARTY, CHANGE_SECURED_PARTY_NAME, ADD_COLLATERAL, DELETE_COLLATERAL, CHANGE_COLLATERAL. |
| party_data | JSON | - | No | JSON object containing the party information being added, deleted, or changed. |
| collateral_data | TEXT | 10000 | No | Text of collateral being added, deleted, or changed. |

## 4. Derived Fields and Analytics

### 4.1 Calculated Fields

| Field Name | Formula | Description |
|------------|---------|-------------|
| filing_age_days | CURRENT_DATE - file_date | Number of days since the filing was recorded. |
| days_to_lapse | lapse_date - CURRENT_DATE | Number of days until the filing lapses. Negative values indicate lapsed filings. |
| is_in_continuation_window | days_to_lapse BETWEEN 0 AND 180 | True if the filing is within 6 months of lapsing (continuation should be filed). |
| has_been_continued | EXISTS(amendment WHERE amendment_type = 'CONTINUATION') | True if a continuation has been filed. |
| is_blanket_lien | is_all_assets = TRUE | True if the collateral description covers all assets. |
| secured_party_type | Classified from org_name | BANK, CREDIT_UNION, FINANCE_COMPANY, ALTERNATIVE_LENDER, GOVERNMENT, OTHER. |
| debtor_entity_type | Derived from org_type or individual indicators | CORPORATION, LLC, LP, INDIVIDUAL, TRUST, PARTNERSHIP, OTHER. |

### 4.2 Entity Resolution Fields

For matching debtors across filings:

| Field Name | Description |
|------------|-------------|
| normalized_name | Debtor name after applying standard search logic (strip noise words, punctuation, entity suffixes) |
| name_key | Phonetic key (Soundex or Metaphone) for fuzzy matching |
| address_hash | Hash of standardized address for dedup |
| org_state_id_key | Composite key of org_state + org_id for exact entity matching |

### 4.3 Risk Scoring Fields

| Field Name | Description | Score Range |
|------------|-------------|------------|
| lien_count | Number of active UCC filings against the debtor | 0-N |
| blanket_lien_count | Number of active "all assets" filings | 0-N |
| recent_filing_count | Number of filings in the last 12 months | 0-N |
| tax_lien_indicator | Whether IRS or state tax liens exist | 0 or 1 |
| judgment_lien_indicator | Whether judgment liens exist | 0 or 1 |
| lien_diversity_score | Number of distinct secured parties | 0-N |
| continuation_health | Ratio of continued filings to lapsed filings | 0.0-1.0 |

## 5. Data Quality Rules

### 5.1 Validation Rules

| Rule ID | Field | Rule | Severity |
|---------|-------|------|----------|
| V001 | file_number | Must be unique within filing_state | Error |
| V002 | file_date | Must be <= CURRENT_DATE | Error |
| V003 | lapse_date | Must be file_date + 5 years (±1 day for weekends) | Warning |
| V004 | debtor_type | Must be INDIVIDUAL or ORGANIZATION | Error |
| V005 | org_name | Required if debtor_type = ORGANIZATION | Error |
| V006 | last_name + first_name | Required if debtor_type = INDIVIDUAL | Error |
| V007 | filing_type | Must be valid ENUM value | Error |
| V008 | original_file_number | Required if filing_type != ORIGINAL | Error |
| V009 | zip_code | Must match pattern: 5 digits or 5+4 digits | Warning |
| V010 | state | Must be valid 2-letter state code | Error |
| V011 | collateral_description | Must not be empty | Error |
| V012 | lapse_date | Must be > CURRENT_DATE for status = ACTIVE | Warning |

### 5.2 Common Data Quality Issues

| Issue | Frequency | Impact | Mitigation |
|-------|-----------|--------|-----------|
| Debtor name variations | ~15% of filings | Missed liens in search results | Entity resolution / fuzzy matching |
| Missing org_id | ~25% of filings | Harder to confirm entity identity | Cross-reference with state business registry |
| Truncated collateral description | ~5% of filings | Incomplete collateral coverage analysis | Flag for manual review; request full text |
| Inconsistent date formats | ~3% of filings | Incorrect lapse date calculations | Normalize to YYYY-MM-DD on ingest |
| Stale address data | ~20% of filings | Notification delivery failures | Address standardization and NCOA updates |
| Duplicate filings | ~2% of filings | Inflated lien counts | Deduplication by debtor + secured party + file date |

## 6. Standard Queries

### 6.1 Debtor Lien Search

```sql
SELECT f.file_number, f.file_date, f.lapse_date, f.status,
       d.org_name, d.last_name, d.first_name,
       sp.org_name AS secured_party_name,
       c.collateral_description
FROM filing_header f
JOIN debtor d ON f.file_number = d.file_number
JOIN secured_party sp ON f.file_number = sp.file_number
JOIN collateral c ON f.file_number = c.file_number
WHERE d.normalized_name = 'TARGET DEBTOR NAME'
  AND f.filing_state = 'DE'
  AND f.status = 'ACTIVE'
ORDER BY f.file_date ASC;
```

### 6.2 Continuation Monitoring

```sql
SELECT f.file_number, f.file_date, f.lapse_date,
       f.days_to_lapse, f.is_in_continuation_window,
       d.org_name AS debtor_name,
       sp.org_name AS secured_party_name
FROM filing_header f
JOIN debtor d ON f.file_number = d.file_number
JOIN secured_party sp ON f.file_number = sp.file_number
WHERE f.status = 'ACTIVE'
  AND f.is_in_continuation_window = TRUE
  AND f.has_been_continued = FALSE
ORDER BY f.lapse_date ASC;
```

### 6.3 Portfolio Analysis

```sql
SELECT sp.org_name AS lender_name,
       COUNT(DISTINCT f.file_number) AS filing_count,
       COUNT(DISTINCT d.normalized_name) AS debtor_count,
       SUM(CASE WHEN c.is_all_assets THEN 1 ELSE 0 END) AS blanket_lien_count,
       MIN(f.file_date) AS earliest_filing,
       MAX(f.file_date) AS latest_filing
FROM filing_header f
JOIN debtor d ON f.file_number = d.file_number
JOIN secured_party sp ON f.file_number = sp.file_number
JOIN collateral c ON f.file_number = c.file_number
WHERE f.status = 'ACTIVE'
GROUP BY sp.org_name
ORDER BY filing_count DESC;
```
