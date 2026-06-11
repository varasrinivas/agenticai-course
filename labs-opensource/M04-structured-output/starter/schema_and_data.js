/**
 * M04 Lab - Step 1: Schema and Test Data (COMPLETE — just run it)
 * ================================================================
 * Defines the ContactInfo schema and 5 test email signatures.
 * Imported by extractor.js and extractor_retry.js.
 * Run: node schema_and_data.js
 */

import { z } from "zod";

import { pathToFileURL } from "node:url";
export const ContactInfo = z.object({
  name: z.string(),
  email: z.string().email(),
  phone: z.string().optional(),
  company: z.string().optional(),
  role: z.string().optional(),
});

// The same schema in JSON Schema form — this becomes the tool's parameters
export const CONTACT_PARAMETERS = {
  type: "object",
  properties: {
    name: { type: "string", description: "Full name of the person" },
    email: { type: "string", description: "Email address" },
    phone: { type: "string", description: "Phone number, if mentioned" },
    company: { type: "string", description: "Company name, if mentioned" },
    role: { type: "string", description: "Job title or role, if mentioned" },
  },
  required: ["name", "email"],
};

// 5 test email signatures — easy to hard
export const TEST_SIGNATURES = [
  "Best, Jane Smith | jane@acme.com | Acme Corp",
  "John Doe, Senior Engineer at MegaTech\njohn.doe@megatech.io | (555) 234-5678",
  "Cheers,\nDr. Maria García-López, Head of Research\nBioGen International\nmgarcia@biogen.int",
  "— Alex K. | Product @ StartupXYZ | alex@startupxyz.co | they/them",
  'Thanks!\nRobert "Bob" Williams III\nChief Financial Officer\nGlobal Finance Partners LLC\nrwilliams@gfp.com\n+1 (212) 555-0199',
];

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log("Tool parameters (JSON Schema):");
  console.log(JSON.stringify(CONTACT_PARAMETERS, null, 2));
  console.log(`\nTest signatures: ${TEST_SIGNATURES.length}`);
  TEST_SIGNATURES.forEach((sig, i) => console.log(`\n--- Signature ${i + 1} ---\n${sig}`));
}
