# Collateral Classification Guide — UCC Article 9

**Document Version:** 2024.1
**Last Updated:** January 20, 2024
**Audience:** Credit analysts, underwriters, data engineers, legal staff

---

## 1. Purpose

This guide provides detailed classification rules for UCC Article 9 collateral
types. Proper classification of collateral is essential for:

- Drafting accurate security agreements and financing statements
- Determining the correct method of perfection
- Establishing priority among competing security interests
- Building data models for UCC filing analytics

## 2. The Collateral Classification Tree

Article 9 organizes all personal property into a hierarchy of types. The same
physical item may be classified differently depending on how it is used.

### 2.1 Goods (Tangible Property)

"Goods" are all things that are movable at the time the security interest
attaches. Goods are further classified into four mutually exclusive subtypes
based on the debtor's use:

**Equipment:**
- Definition: Goods used or bought for use primarily in a business (including
  farming or a profession), and that are not inventory, farm products, or
  consumer goods
- Examples: Manufacturing machinery, delivery trucks, office computers and
  furniture, medical devices, construction equipment
- Key test: Is the debtor using the goods in its business operations?
- Perfection: Filing UCC-1 or possession
- Notes: Equipment is the "residual" category for business goods — if goods
  don't fit the other three categories, they are equipment

**Inventory:**
- Definition: Goods held for sale or lease, goods furnished or to be furnished
  under a service contract, raw materials, work in process, and materials used
  or consumed in a business
- Examples: Retail merchandise, wholesale goods, raw steel at a manufacturer,
  partially assembled products, packaging materials
- Key test: Are the goods held for sale, lease, or consumption in the business?
- Perfection: Filing UCC-1
- Notes: Inventory is constantly changing (sold, replaced); proceeds of
  inventory are automatically covered by the security interest

**Farm Products:**
- Definition: Goods (other than standing timber) that are in possession of a
  debtor engaged in farming operations and are: crops, livestock, supplies
  used in farming, or products of crops or livestock in their unmanufactured
  state
- Examples: Wheat in a silo, cattle on a feedlot, milk in a bulk tank, eggs,
  unginned cotton, baled hay
- Key test: Is the debtor a farmer, and are the goods used in farming?
- Perfection: Filing UCC-1
- Special rules: Federal Food Security Act (FSA) provides additional
  protections for buyers of farm products

**Consumer Goods:**
- Definition: Goods used or bought for use primarily for personal, family, or
  household purposes
- Examples: Home appliances, personal vehicles (when used for personal
  transportation), furniture, electronics
- Key test: Is the debtor using the goods for personal/household purposes?
- Perfection: Filing UCC-1, possession, or automatic perfection (PMSI)
- Special rules: PMSI in consumer goods is automatically perfected upon
  attachment (no filing required)

### 2.2 Classification Depends on the Debtor

The same physical item can be different collateral types depending on who
the debtor is and how they use it:

| Item | Debtor | Use | Classification |
|------|--------|-----|---------------|
| John Deere tractor | Farm operating company | Farming | Farm Products (supplies) |
| John Deere tractor | Construction company | Business operations | Equipment |
| John Deere tractor | Tractor dealership | Held for sale | Inventory |
| John Deere tractor | Individual homeowner | Personal use (hobby farm) | Consumer Goods |
| Laptop computer | Software company | Business operations | Equipment |
| Laptop computer | Electronics retailer | Held for sale | Inventory |
| Laptop computer | Individual | Personal use | Consumer Goods |

## 3. Intangible Property

### 3.1 Accounts

- **Definition:** A right to payment for goods sold or leased, services
  rendered, insurance policies issued, secondary obligations incurred, energy
  provided, use of a vessel, use of intellectual property, or arising out of
  the use of a credit or charge card
- **Key characteristic:** The right to payment must arise from one of the
  listed transactions
- **NOT accounts:** Rights to payment evidenced by chattel paper or an
  instrument, or rights arising from tort claims
- **Perfection:** Filing UCC-1
- **Subtype — Health-care-insurance receivable:** A right to payment under a
  health-care-insurance policy (special notification rules apply)

### 3.2 General Intangibles

- **Definition:** Personal property (including things in action) that does not
  fit any other Article 9 category
- **Examples:** Intellectual property (patents, trademarks, copyrights),
  software, goodwill, tax refund claims, literary rights, contractual rights
  not constituting accounts or chattel paper
- **Perfection:** Filing UCC-1
- **Subtype — Payment intangible:** A general intangible under which the
  account debtor's principal obligation is a monetary obligation
- **Special rule:** Security interest in a payment intangible is automatically
  perfected upon attachment if acquired by sale

### 3.3 Chattel Paper

- **Definition:** A record or records that evidence both: (1) a monetary
  obligation AND (2) a security interest in or lease of specific goods
- **Tangible chattel paper:** Inscribed on tangible medium (paper)
- **Electronic chattel paper:** Stored in electronic medium with a single
  authoritative copy
- **Examples:** Auto loan contracts (the document that says "you owe $X and
  we have a lien on the car"), equipment lease agreements
- **Perfection:** Filing, possession (tangible), or control (electronic)
- **Priority note:** A purchaser of chattel paper who takes possession (or
  control of electronic chattel paper) in good faith has priority over a
  security interest perfected only by filing

### 3.4 Instruments

- **Definition:** Negotiable instruments (Article 3) or other writings that
  evidence a right to payment of money, are transferable by delivery, and are
  of the type ordinarily transferred by delivery
- **Examples:** Promissory notes, checks, certificates of deposit, drafts
- **NOT instruments:** Documents governed by Article 7 (documents of title) or
  investment property governed by Article 8
- **Perfection:** Filing (but only for 20-day temporary perfection for some
  instruments) or possession (the preferred method)

### 3.5 Deposit Accounts

- **Definition:** Demand, time, savings, passbook, or similar accounts
  maintained at a bank
- **Examples:** Checking accounts, savings accounts, money market accounts, CDs
- **NOT deposit accounts:** Accounts evidenced by an instrument (e.g., a
  negotiable CD is an instrument, not a deposit account)
- **Perfection:** Control ONLY (filing is not effective for deposit accounts)
- **Control methods:** (1) The secured party IS the bank, (2) deposit account
  control agreement among debtor, bank, and secured party, or (3) the secured
  party becomes the bank's customer on the account

### 3.6 Investment Property

- **Definition:** Securities (certificated and uncertificated), security
  entitlements, securities accounts, commodity contracts, and commodity accounts
- **Examples:** Stock certificates, brokerage account holdings, futures contracts
- **Perfection:** Filing, control, or delivery (of certificated securities)
- **Priority:** Control has priority over filing

### 3.7 Letter-of-Credit Rights

- **Definition:** A right to payment or performance under a letter of credit
- **Perfection:** Control ONLY
- **Control:** Requires the issuer or nominated person to consent to assignment
  of proceeds

## 4. Special Collateral Types

### 4.1 Documents of Title

- **Definition:** Warehouse receipts, bills of lading, and other documents
  treated as documents of title under Article 7
- **Perfection:** Filing or possession
- **Tangible vs. electronic:** Different possession/control rules apply

### 4.2 Money

- **Definition:** A medium of exchange authorized or adopted by a government
- **Perfection:** Possession ONLY (cannot perfect by filing)
- **Example:** Cash in a safe

### 4.3 Fixtures

- **Definition:** Goods that become so related to particular real property that
  an interest in them arises under real property law
- **Perfection:** Fixture filing (filed in the real property records of the
  county where the real property is located)
- **Special form:** The financing statement must contain a real property
  description sufficient to identify the real property, and must indicate that
  it covers fixtures
- **Priority:** Complex priority rules involving real property mortgagees

### 4.4 Proceeds

- **Definition:** Whatever is received upon the sale, lease, license, exchange,
  or other disposition of collateral; also insurance payable by reason of loss
  or damage to collateral
- **Automatic coverage:** A security interest in collateral automatically
  extends to identifiable proceeds
- **Perfection of proceeds:** Automatically perfected for 20 days; remains
  perfected thereafter if the original collateral was perfected by filing and
  the proceeds are of the type that would be covered by filing in the same
  office, OR the proceeds are identifiable cash proceeds
- **Tracing:** The secured party bears the burden of tracing proceeds to the
  original collateral

## 5. Collateral Description Patterns for Data Analytics

### 5.1 Common Collateral Description Templates

When analyzing UCC filing data, these are the most common collateral description
patterns encountered:

| Pattern | Frequency | Interpretation |
|---------|-----------|---------------|
| "All assets" / "All personal property" | ~35% | Blanket lien — covers everything |
| "All accounts and general intangibles" | ~15% | Receivables financing or factoring |
| "All inventory" | ~10% | Inventory line of credit (floor plan, revolving) |
| "All equipment" | ~10% | Equipment financing or leasing |
| Specific asset descriptions (serial numbers) | ~20% | Equipment loans, vehicle financing |
| "All accounts, inventory, equipment, and general intangibles" | ~10% | Asset-based lending (ABL) facility |

### 5.2 Red Flags in Collateral Analysis

When performing due diligence on UCC filings, watch for these red flags:

| Red Flag | Risk | Action |
|----------|------|--------|
| Multiple "all assets" filings | Debtor may be over-leveraged | Review priority dates; subordination agreements |
| Filing close to lapse date | May indicate distressed refinancing | Verify continuation filed; check for lapse gaps |
| Numerous amendments in short period | Potential collateral shifting | Review amendment details for collateral deletions |
| Filing by non-traditional lender | Alternative lending (MCA, factoring) | Review terms carefully; may include UCC as a precautionary filing |
| Terminated filing followed by new filing from different lender | Refinancing or lender change | Verify clean handoff; no priority gaps |
| IRS or state tax liens | Government priority | Tax liens may prime UCC filings depending on timing and collateral type |

### 5.3 Lien Position Analysis

To determine a lender's lien position:

1. **Search all filings** against the debtor in the correct state
2. **Filter out** terminated filings, lapsed filings, and filings by the
   debtor as secured party (reverse filings)
3. **Sort by file date** (earliest first)
4. **Check for PMSI** filings — these may have super-priority regardless of
   file date
5. **Review assignments** — the current secured party may differ from the
   original filer
6. **Check for subordination agreements** — a senior lender may have
   subordinated its interest (not reflected in the UCC filing itself)
7. **Check federal tax liens** — IRS liens filed before a UCC filing may
   have priority for certain collateral types
