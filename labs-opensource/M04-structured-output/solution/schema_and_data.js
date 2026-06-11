/**
 * M04 Lab: Schema and Test Data (shared helper — identical to starter version)
 */

import { z } from "zod";

export const ContactInfo = z.object({
  name: z.string(),
  email: z.string().email(),
  phone: z.string().optional(),
  company: z.string().optional(),
  role: z.string().optional(),
});

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

export const TEST_SIGNATURES = [
  "Best, Jane Smith | jane@acme.com | Acme Corp",
  "John Doe, Senior Engineer at MegaTech\njohn.doe@megatech.io | (555) 234-5678",
  "Cheers,\nDr. Maria García-López, Head of Research\nBioGen International\nmgarcia@biogen.int",
  "— Alex K. | Product @ StartupXYZ | alex@startupxyz.co | they/them",
  'Thanks!\nRobert "Bob" Williams III\nChief Financial Officer\nGlobal Finance Partners LLC\nrwilliams@gfp.com\n+1 (212) 555-0199',
];
