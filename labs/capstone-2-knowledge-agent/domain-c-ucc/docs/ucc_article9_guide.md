# UCC Article 9 — Secured Transactions: A Plain-English Guide

**Document Version:** 2024.1
**Last Updated:** January 15, 2024
**Audience:** Filing officers, legal staff, data analysts, compliance teams

---

## 1. What Is Article 9?

Article 9 of the Uniform Commercial Code (UCC) is the body of law governing
secured transactions — deals where a borrower pledges personal property as
collateral to secure a loan or other obligation. Article 9 has been adopted
(with some state-specific variations) in all 50 U.S. states, the District of
Columbia, and the U.S. territories.

The core idea is simple: when a lender makes a loan and the borrower puts up
assets as collateral, Article 9 tells everyone — the lender, the borrower,
other creditors, and the public — what rules apply.

### 1.1 Why Article 9 Matters

- **For lenders:** It establishes how to create and protect (perfect) a
  security interest so the lender has priority over other creditors if the
  borrower defaults.
- **For borrowers:** It defines the borrower's rights and obligations with
  respect to the collateral.
- **For third parties:** It provides a public notice system (the UCC filing
  system) so anyone can check whether assets are already pledged as collateral.
- **For data analysts:** UCC filings are a rich source of business intelligence
  — they reveal credit relationships, asset bases, and financial health signals.

### 1.2 Key Terminology

| Term | Definition |
|------|-----------|
| Secured Party | The lender or creditor who holds the security interest |
| Debtor | The borrower or party who owns the collateral and grants the security interest |
| Collateral | The property pledged to secure the obligation |
| Security Interest | The legal right of the secured party in the collateral |
| Security Agreement | The contract between debtor and secured party that creates the security interest |
| Financing Statement (UCC-1) | The public filing that perfects the security interest and provides notice to third parties |
| Perfection | The legal process that makes a security interest enforceable against third parties |
| Priority | The ranking among competing security interests in the same collateral |
| Default | The debtor's failure to perform under the security agreement |
| Attachment | The point at which a security interest becomes enforceable against the debtor |

## 2. Creating a Security Interest (Attachment)

A security interest "attaches" to collateral — meaning it becomes enforceable
against the debtor — when three conditions are met:

1. **Value has been given** — The secured party has provided something of
   value to the debtor (usually a loan, line of credit, or goods on credit).

2. **The debtor has rights in the collateral** — The debtor owns or has
   sufficient rights in the property to grant a security interest.

3. **A security agreement exists** — Either:
   - A written (or electronic) security agreement authenticated by the debtor
     that describes the collateral, OR
   - The secured party has possession or control of the collateral (a "pledge").

### 2.1 The Security Agreement

The security agreement must contain:

- **Identification of the parties** (debtor and secured party)
- **Description of the collateral** — must "reasonably identify" the collateral
  (see Section 4 on collateral descriptions)
- **Granting clause** — language by which the debtor grants the security interest
- **Authentication** — the debtor's signature (wet or electronic)

A security agreement may also contain:

- Description of the secured obligation (the loan or duty being secured)
- Default provisions (what constitutes a default)
- Remedies upon default
- Representations and warranties
- After-acquired property clause (extending the security interest to property
  the debtor acquires in the future)
- Proceeds clause (extending the security interest to proceeds from the
  disposition of collateral)

## 3. Perfection

Perfection is the process that gives a security interest priority over other
creditors and makes it effective against third parties (including a bankruptcy
trustee). Without perfection, a security interest may be enforceable against
the debtor but can be defeated by other creditors.

### 3.1 Methods of Perfection

| Method | When Used | Duration |
|--------|-----------|----------|
| Filing a UCC-1 Financing Statement | Most personal property | 5 years (renewable) |
| Possession | Tangible collateral (goods, instruments, money) | While in possession |
| Control | Deposit accounts, electronic chattel paper, investment property, letter-of-credit rights | While control is maintained |
| Automatic Perfection | Purchase-money security interest (PMSI) in consumer goods | Automatic upon attachment |

### 3.2 Filing a UCC-1 Financing Statement

The most common method of perfection is filing a UCC-1 Financing Statement
with the appropriate state filing office.

**Required information on a UCC-1:**

- Debtor's legal name (individual or organization) — this is CRITICAL; an
  error in the debtor's name can render the filing ineffective (see Section 5)
- Debtor's mailing address
- Secured party's name and mailing address
- Collateral description (may use broad categories or specific descriptions)

**Filing office:**

- For most collateral: file with the Secretary of State in the state where
  the debtor is located (organized, for entities; principal residence, for
  individuals)
- For fixtures, timber, minerals, and as-extracted collateral: file with the
  county recorder in the county where the real property is located

### 3.3 Duration and Continuation

- A UCC-1 filing is effective for **5 years** from the date of filing
- To maintain perfection beyond 5 years, a **UCC-3 Continuation Statement**
  must be filed within the 6-month window before the filing lapses (i.e.,
  between 4.5 and 5 years after the original filing)
- If the continuation is not filed, the filing lapses and the security
  interest becomes unperfected
- There is no limit on the number of continuations that can be filed

### 3.4 Amendments (UCC-3)

A UCC-3 is a multi-purpose amendment form used for:

| Action | Purpose |
|--------|---------|
| Continuation | Extend the filing for another 5 years |
| Amendment | Change the debtor name, secured party name, or collateral description |
| Assignment | Transfer the secured party's interest to another party |
| Termination | End the filing (secured party's obligation when debt is paid) |

## 4. Collateral Description Standards

### 4.1 In the Security Agreement

The collateral description in the security agreement must "reasonably identify"
the collateral. Acceptable methods include:

- Specific listing ("one 2023 Caterpillar D6 bulldozer, serial #CAT2023D6-44821")
- Category ("all equipment")
- UCC-defined type ("all accounts," "all inventory," "all general intangibles")
- Formula or procedure ("all assets listed on Exhibit A")
- **"All assets" or "all personal property"** — this is acceptable in a
  financing statement but NOT in a security agreement (a super-generic
  description is not sufficient to "reasonably identify" collateral in the
  security agreement itself)

### 4.2 In the Financing Statement (UCC-1)

The financing statement may use broader descriptions than the security
agreement:

- "All assets" or "all personal property of the debtor" — this IS acceptable
  in a financing statement
- UCC collateral type categories (equipment, inventory, accounts, etc.)
- Specific descriptions

### 4.3 UCC Collateral Types (Article 9 Categories)

| Category | Definition | Examples |
|----------|-----------|---------|
| Accounts | Right to payment for goods sold/leased or services rendered | Trade receivables, credit card receivables |
| Chattel Paper | A record evidencing both a monetary obligation and a security interest in goods | Retail installment contracts, equipment leases |
| Deposit Accounts | Demand, time, savings, or similar accounts at a bank | Checking accounts, savings accounts, CDs |
| Documents | Documents of title (warehouse receipts, bills of lading) | BOLs, warehouse receipts |
| Equipment | Goods used or bought for use in a business (not inventory or farm products) | Machinery, vehicles, office furniture, computers |
| Farm Products | Goods used in farming operations (crops, livestock, aquatic goods) | Cattle, grain, timber (uncut) |
| Fixtures | Goods that become so attached to real property that they are part of it | HVAC systems, built-in shelving |
| General Intangibles | Personal property not fitting other categories | Patents, trademarks, software, goodwill |
| Goods | All things movable at the time the security interest attaches | Equipment, inventory, consumer goods, farm products |
| Instruments | Negotiable instruments and promissory notes | Checks, promissory notes, certificates of deposit |
| Inventory | Goods held for sale/lease or furnished under service contracts | Raw materials, work-in-process, finished goods |
| Investment Property | Securities, security entitlements, commodity contracts | Stocks, bonds, mutual fund shares |
| Letter-of-Credit Rights | Rights to payment under a letter of credit | Standby letters of credit |
| Money | Legal tender (coin, currency) | Cash |
| Proceeds | Whatever is received upon the sale, exchange, or other disposition of collateral | Cash from sold inventory, insurance proceeds |
| Supporting Obligations | Letters of credit, guaranties, or other secondary obligations that support payment of an account, chattel paper, or instrument | Guaranty agreements |

## 5. The Debtor Name Rule

The debtor's name on the UCC-1 financing statement is the single most critical
piece of information. An error in the debtor name can render the entire filing
ineffective.

### 5.1 Rules for Organization Names

For a registered organization (corporation, LLC, LP, etc.):

- The debtor name on the UCC-1 must match the name on the debtor's **public
  organic record** (e.g., articles of incorporation, certificate of formation)
  as filed with the state of organization
- Trade names, assumed names, and DBA names are NOT sufficient — the legal
  entity name must be used
- The name must be the name shown on the **most recent** public organic record

### 5.2 Rules for Individual Names

For individual debtors (varies by state; two approaches):

- **Only-if-approach:** Use the name on the debtor's unexpired driver's license
  from the state where the debtor is located. If no license, use the
  individual's legal name.
- **Safe-harbor approach:** The filing is effective if it uses the individual
  name on the driver's license OR the individual's legal name (some states
  allow either).

### 5.3 Name Errors and the "Seriously Misleading" Test

A financing statement is ineffective if the debtor's name is "seriously
misleading." A name is NOT seriously misleading if a search of the filing
office's standard search logic under the correct name would disclose the filing.

In practice:
- Minor typographical errors may NOT be seriously misleading (e.g., "Smith"
  vs. "Smth") if the filing office's search logic would still return the filing
- Adding or omitting "Inc." or "LLC" can be seriously misleading
- Using a trade name instead of the legal entity name is almost always
  seriously misleading

## 6. Priority Rules

When multiple creditors claim a security interest in the same collateral,
Article 9 establishes priority rules to determine who gets paid first.

### 6.1 General Priority Rules

1. **Perfected vs. unperfected:** A perfected security interest has priority
   over an unperfected one.
2. **First to file or perfect:** Among perfected security interests, the first
   to file a financing statement or perfect by another method has priority
   (regardless of when the security interest attached).
3. **Purchase-money security interest (PMSI):** A PMSI in inventory or
   equipment has special priority (super-priority) over other security
   interests in the same collateral, if properly perfected and (for inventory)
   if proper notice is given to prior secured parties.
4. **Lien creditors:** A perfected security interest has priority over a
   judicial lien creditor; an unperfected security interest does not.
5. **Buyers in the ordinary course:** A buyer who purchases goods in the
   ordinary course of business from a seller's inventory takes free of any
   security interest created by the seller, even if the security interest is
   perfected.

### 6.2 PMSI Super-Priority

A purchase-money security interest arises when a secured party:
- Sells goods on credit and retains a security interest, OR
- Advances funds used by the debtor to acquire the collateral

PMSI priority rules:
- **PMSI in goods other than inventory:** Super-priority if perfected within
  20 days of the debtor receiving possession of the collateral
- **PMSI in inventory:** Super-priority only if (a) perfected before the
  debtor receives possession AND (b) written notification is sent to holders
  of previously filed financing statements covering the same type of inventory

## 7. Default and Remedies

### 7.1 What Constitutes Default

Default is defined by the security agreement (not by Article 9). Common
default triggers include:

- Failure to make a scheduled payment
- Breach of a covenant in the security agreement
- Insolvency or bankruptcy filing
- Material adverse change in the debtor's financial condition
- Unauthorized disposition of collateral

### 7.2 Secured Party's Remedies After Default

Upon default, the secured party may:

1. **Foreclose on the collateral:**
   - Take possession of the collateral (self-help if without breach of the peace,
     or through judicial process)
   - Dispose of the collateral by public or private sale
   - Apply the proceeds: (1) costs of repossession and sale, (2) secured debt,
     (3) junior secured parties, (4) surplus to debtor

2. **Strict foreclosure (acceptance):**
   - Accept the collateral in full or partial satisfaction of the debt
   - Requires debtor consent (no objection within 20 days of notice)
   - Not available for consumer goods if the debtor has paid 60% or more

3. **Collection from account debtors:**
   - If the collateral is accounts or chattel paper, the secured party may
     notify account debtors to pay the secured party directly

### 7.3 Debtor's Rights After Default

- Right to receive notice of disposition (at least 10 days before disposition)
- Right to redeem the collateral (pay the full debt plus costs) before
  disposition
- Right to an accounting of the secured obligation
- Right to any surplus from the disposition proceeds
- Right to sue for damages if the secured party fails to comply with Article 9
  disposition requirements (commercially reasonable manner)

## 8. The UCC Filing System: A Data Perspective

### 8.1 Filing Offices

Each state maintains a central filing office (typically the Secretary of
State's office) and county filing offices:

| Filing Type | Filing Office | Search Scope |
|-------------|---------------|-------------|
| Most personal property | Secretary of State | Statewide |
| Fixtures | County Recorder | County-specific |
| Timber/Minerals/As-extracted | County Recorder | County-specific |

### 8.2 Standard Search Logic

Filing offices use "standard search logic" to index and retrieve filings.
The IACA (International Association of Commercial Administrators) Model
Administrative Rules define standard search logic:

- Ignore noise words ("the," "a," "an")
- Ignore punctuation and accents
- Ignore spaces (for organization names in some states)
- Ignore "ending noise words" for organizations ("Inc.," "LLC," "Corp.,"
  "Ltd.," "LP," "Co.")
- Exact match on remaining characters (after applying the above rules)

### 8.3 UCC Data Fields (Summary)

A typical UCC filing record contains:

| Field | Description | Required |
|-------|-------------|----------|
| File Number | Unique identifier assigned by the filing office | Yes (auto-assigned) |
| File Date | Date the filing was accepted | Yes (auto-assigned) |
| Lapse Date | Date the filing expires (5 years from file date) | Yes (calculated) |
| Debtor Name | Legal name of the debtor (individual or organization) | Yes |
| Debtor Address | Mailing address of the debtor | Yes |
| Secured Party Name | Legal name of the secured party | Yes |
| Secured Party Address | Mailing address of the secured party | Yes |
| Collateral Description | Description of the collateral | Yes |
| Filing Type | Original, amendment, continuation, assignment, termination | Yes |
| Related File Number | For amendments: the file number of the original filing | If amendment |
