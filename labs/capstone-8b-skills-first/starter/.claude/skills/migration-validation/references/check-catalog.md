# The six checks, with queries

TODO: one section per check, in run order, each with the Oracle-side and PostgreSQL-side
query and two headings: what it CATCHES and what it MISSES.

The MISSES half is the reason this file exists. Checks 1 and 2 come back green on a
migration that is badly broken; if that is not obvious from your write-up, a reader will
stop at the first two greens.

Things to work out and state explicitly:
  - the hash functions differ between the engines. What does that mean for how check 2 can
    legitimately be used?
  - check 4 has no Oracle counterpart. Say why, and what shape the assertion takes instead.
  - check 6 is the only one that sees DATE truncation. Explain why every aggregate misses
    it -- the reason is about WHEN the truncation happens relative to the checksum.
  - how the 20 rows for check 6 should be chosen, and why random sampling is not good
    enough on a 7,418-row table with ~1,400 affected rows.

Close with why the order matters and what to do when a check fails partway through.
