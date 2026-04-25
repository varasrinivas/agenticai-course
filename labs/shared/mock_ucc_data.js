/**
 * Shared mock UCC filing data used across multiple labs (M04+).
 * This file is COMPLETE — do not modify it.
 *
 * Usage:
 *   import { MOCK_FILINGS, getFilingByNumber, searchFilings } from '../shared/mock_ucc_data.js';
 */

export const MOCK_FILINGS = [
  {
    filing_number: "UCC-2024-NY-0012847",
    type: "UCC-1",
    state: "New York",
    filing_date: "2024-03-15",
    expiration_date: "2029-03-15",
    status: "Active",
    debtor: {
      name: "Greenfield Logistics LLC",
      address: "450 West 33rd Street, Suite 800, New York, NY 10001",
      org_type: "LLC",
      jurisdiction: "New York"
    },
    secured_party: {
      name: "Atlantic Capital Partners",
      address: "1 Chase Manhattan Plaza, Floor 45, New York, NY 10005"
    },
    collateral_description: "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor.",
    filing_office: "NY Department of State",
    document_number: "DOC-NY-2024-88291"
  },
  {
    filing_number: "UCC-2024-CA-0098231",
    type: "UCC-1",
    state: "California",
    filing_date: "2024-01-22",
    expiration_date: "2029-01-22",
    status: "Active",
    debtor: {
      name: "Pacific Ridge Technologies Inc",
      address: "2800 Sand Hill Road, Menlo Park, CA 94025",
      org_type: "Corporation",
      jurisdiction: "Delaware"
    },
    secured_party: {
      name: "Silicon Valley Bank (a division of First Citizens BancShares)",
      address: "3003 Tasman Drive, Santa Clara, CA 95054"
    },
    collateral_description: "All assets of the Debtor including but not limited to: intellectual property, patents, trademarks, accounts, deposit accounts, investment property, and all proceeds thereof.",
    filing_office: "CA Secretary of State",
    document_number: "DOC-CA-2024-44019"
  },
  {
    filing_number: "UCC-2023-TX-0187634",
    type: "UCC-1",
    state: "Texas",
    filing_date: "2023-09-10",
    expiration_date: "2028-09-10",
    status: "Active",
    debtor: {
      name: "Lone Star Energy Solutions LP",
      address: "1200 Smith Street, Suite 3000, Houston, TX 77002",
      org_type: "Limited Partnership",
      jurisdiction: "Texas"
    },
    secured_party: {
      name: "Wells Fargo Equipment Finance",
      address: "301 South College Street, Charlotte, NC 28202"
    },
    collateral_description: 'Specific equipment: (3) Caterpillar 349F L hydraulic excavators, serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; (1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124.',
    filing_office: "TX Secretary of State",
    document_number: "DOC-TX-2023-71092"
  },
  {
    filing_number: "UCC-2024-FL-0054219",
    type: "UCC-3",
    state: "Florida",
    filing_date: "2024-06-01",
    expiration_date: "2027-11-18",
    status: "Amendment",
    debtor: {
      name: "Sunshine Medical Group PA",
      address: "4500 Biscayne Boulevard, Miami, FL 33137",
      org_type: "Professional Association",
      jurisdiction: "Florida"
    },
    secured_party: {
      name: "TD Bank N.A.",
      address: "1701 Route 70 East, Cherry Hill, NJ 08034"
    },
    collateral_description: "Amendment to add: medical equipment including (2) Siemens MAGNETOM Vida 3T MRI systems and (1) GE Revolution CT scanner. Original collateral description unchanged.",
    filing_office: "FL Secured Transaction Registry",
    document_number: "DOC-FL-2024-22817",
    original_filing: "UCC-2022-FL-0031456"
  },
  {
    filing_number: "UCC-2022-DE-0002914",
    type: "UCC-1",
    state: "Delaware",
    filing_date: "2022-04-30",
    expiration_date: "2027-04-30",
    status: "Active",
    debtor: {
      name: "Nextera Holdings Corp",
      address: "1209 Orange Street, Wilmington, DE 19801",
      org_type: "Corporation",
      jurisdiction: "Delaware"
    },
    secured_party: {
      name: "JPMorgan Chase Bank N.A.",
      address: "383 Madison Avenue, New York, NY 10179"
    },
    collateral_description: "All assets of the Debtor, whether now owned or hereafter acquired, including without limitation all accounts, chattel paper, commercial tort claims, deposit accounts, documents, equipment, fixtures, general intangibles, goods, instruments, inventory, investment property, letter-of-credit rights, letters of credit, money, oil, gas, and other minerals, and all proceeds and products thereof.",
    filing_office: "DE Division of Corporations",
    document_number: "DOC-DE-2022-09381"
  },
  {
    filing_number: "UCC-2024-IL-0076543",
    type: "UCC-1",
    state: "Illinois",
    filing_date: "2024-02-14",
    expiration_date: "2029-02-14",
    status: "Active",
    debtor: {
      name: "Midwest Agricultural Cooperative",
      address: "200 W Adams St, Suite 1500, Chicago, IL 60606",
      org_type: "Cooperative",
      jurisdiction: "Illinois"
    },
    secured_party: {
      name: "Farm Credit Services of America",
      address: "5015 S 118th St, Omaha, NE 68137"
    },
    collateral_description: "All farm products, including but not limited to crops (corn, soybeans, wheat), livestock, and farm equipment. All accounts and proceeds arising from the sale of farm products.",
    filing_office: "IL Secretary of State",
    document_number: "DOC-IL-2024-33901"
  },
  {
    filing_number: "UCC-2023-NY-0145678",
    type: "UCC-3",
    state: "New York",
    filing_date: "2023-12-01",
    expiration_date: null,
    status: "Terminated",
    debtor: {
      name: "Harbor Shipping International Inc",
      address: "One World Trade Center, Floor 72, New York, NY 10007",
      org_type: "Corporation",
      jurisdiction: "New York"
    },
    secured_party: {
      name: "Citibank N.A.",
      address: "388 Greenwich Street, New York, NY 10013"
    },
    collateral_description: "TERMINATION — This filing terminates the effectiveness of the original filing UCC-2019-NY-0089012.",
    filing_office: "NY Department of State",
    document_number: "DOC-NY-2023-99102",
    original_filing: "UCC-2019-NY-0089012"
  },
  {
    filing_number: "UCC-2024-GA-0034521",
    type: "UCC-1",
    state: "Georgia",
    filing_date: "2024-04-20",
    expiration_date: "2029-04-20",
    status: "Active",
    debtor: {
      name: "Peachtree Ventures LLC",
      address: "3344 Peachtree Road NE, Suite 1200, Atlanta, GA 30326",
      org_type: "LLC",
      jurisdiction: "Georgia"
    },
    secured_party: {
      name: "Truist Financial Corporation",
      address: "214 N Tryon Street, Charlotte, NC 28202"
    },
    collateral_description: "All inventory held at debtor's warehouse locations in Fulton, DeKalb, and Gwinnett counties, Georgia. All accounts receivable generated from wholesale distribution operations.",
    filing_office: "GA Superior Court Clerks' Cooperative Authority",
    document_number: "DOC-GA-2024-18723"
  }
];

export const EDGE_CASE_FILINGS = [
  {
    filing_number: "UCC-2024-NV-0000001",
    type: "UCC-1",
    state: "Nevada",
    filing_date: "2024-05-01",
    expiration_date: "2029-05-01",
    status: "Active",
    debtor: {
      name: "",
      address: "100 N Carson St, Carson City, NV 89701",
      org_type: "LLC",
      jurisdiction: "Nevada"
    },
    secured_party: {
      name: "Quick Lend Corp",
      address: "555 E Washington Ave, Las Vegas, NV 89101"
    },
    collateral_description: "All assets.",
    filing_office: "NV Secretary of State",
    document_number: "DOC-NV-2024-00001"
  },
  {
    filing_number: "UCC-2024-NY-0012847",
    type: "UCC-1",
    state: "New York",
    filing_date: "2024-07-10",
    expiration_date: "2029-07-10",
    status: "Active",
    debtor: {
      name: "Greenfield Logistics LLC",
      address: "450 West 33rd Street, Suite 800, New York, NY 10001",
      org_type: "LLC",
      jurisdiction: "New York"
    },
    secured_party: {
      name: "Second National Bank",
      address: "200 Park Avenue, New York, NY 10166"
    },
    collateral_description: "All inventory and equipment.",
    filing_office: "NY Department of State",
    document_number: "DOC-NY-2024-92104"
  },
  {
    filing_number: "UCC-2019-OH-0299100",
    type: "UCC-1",
    state: "Ohio",
    filing_date: "2019-03-01",
    expiration_date: "2024-03-01",
    status: "Lapsed",
    debtor: {
      name: "Buckeye Manufacturing Co",
      address: "75 E State Street, Columbus, OH 43215",
      org_type: "Corporation",
      jurisdiction: "Ohio"
    },
    secured_party: {
      name: "KeyBank National Association",
      address: "127 Public Square, Cleveland, OH 44114"
    },
    collateral_description: "All equipment located at 900 Industrial Parkway, Akron, OH 44301.",
    filing_office: "OH Secretary of State",
    document_number: "DOC-OH-2019-45021"
  }
];

export const ALL_FILINGS = [...MOCK_FILINGS, ...EDGE_CASE_FILINGS];

export function getFilingByNumber(filingNumber) {
  return ALL_FILINGS.find(f => f.filing_number === filingNumber) || null;
}

export function searchFilings({ debtorName, state, status, filingType } = {}) {
  let results = ALL_FILINGS;
  if (debtorName) results = results.filter(f => f.debtor.name.toLowerCase().includes(debtorName.toLowerCase()));
  if (state) results = results.filter(f => f.state.toLowerCase() === state.toLowerCase());
  if (status) results = results.filter(f => f.status.toLowerCase() === status.toLowerCase());
  if (filingType) results = results.filter(f => f.type.toLowerCase() === filingType.toLowerCase());
  return results;
}

export function getStates() {
  return [...new Set(ALL_FILINGS.map(f => f.state))].sort();
}

export function getStats() {
  return {
    total_filings: ALL_FILINGS.length,
    active: ALL_FILINGS.filter(f => f.status === "Active").length,
    terminated: ALL_FILINGS.filter(f => f.status === "Terminated").length,
    lapsed: ALL_FILINGS.filter(f => f.status === "Lapsed").length,
    amendments: ALL_FILINGS.filter(f => f.type === "UCC-3").length,
    states: getStates(),
  };
}
