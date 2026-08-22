# `NUMBER(p,s)` — picking the right PostgreSQL width

Load this when a column is a `NUMBER` and you are deciding between an integer type and
`numeric`. This is the single most common place a migration quietly loses data.

## The decision

```
NUMBER(p, s)
   |
   +-- s > 0  ------------------> numeric(p,s)      exact decimal. Money, rates, ratios.
   |
   +-- s < 0  ------------------> numeric  + MANUAL REVIEW
   |                              Negative scale rounds LEFT of the decimal point.
   |                              NUMBER(5,-2) stores 12345 as 12300.
   |                              PostgreSQL cannot express this. The rounding has
   |                              to move into the application, and someone has to
   |                              decide that deliberately.
   |
   +-- s = 0 or absent
   |     |
   |     +-- p <= 4   -----------> smallint          2 bytes, +/- 32767
   |     +-- p <= 9   -----------> integer           4 bytes, +/- 2.1e9
   |     +-- p <= 18  -----------> bigint            8 bytes, +/- 9.2e18
   |     +-- p >  18  -----------> numeric(p)        beyond bigint
   |
   +-- no precision at all -----> numeric  + CHECK THE DATA
                                  A bare NUMBER may carry a scale. See below.
```

## Why bare `NUMBER` is the dangerous one

`NUMBER` with no precision or scale accepts up to 38 significant digits **and any scale**. It is
Oracle's "I did not decide" type, and legacy schemas are full of it.

Mapping it to `integer` because every sampled row happens to be a whole number is how a
migration loses `1.5` from a column that is whole-numbered in 19,000 rows and fractional in six.

Two ways to settle it, in order of trustworthiness:

```sql
-- 1. Does any row actually carry a fraction?
SELECT COUNT(*) FROM meridian.state_sos_source
 WHERE records_expected != TRUNC(records_expected);

-- 2. What is the widest value present?
SELECT MAX(LENGTH(TRIM(TO_CHAR(ABS(records_expected))))) FROM meridian.state_sos_source;
```

A zero from query 1 **still does not license `integer`** unless you also know the column cannot
receive a fractional value in future. If the application writes to it, `numeric` is the answer.
Widening later is a migration; narrowing later is a data loss incident.

In this schema, `STATE_SOS_SOURCE.RECORDS_EXPECTED` is exactly this case — declared bare, and
the checker returns `check_data` for it.

## The overflow that does not error

Oracle `NUMBER(38)` holds values PostgreSQL `bigint` cannot. If you map it to `bigint` and a
value exceeds 9.2 × 10¹⁸, the **load fails loudly** — which is the good outcome.

The bad outcome is `NUMBER(19)` mapped to `bigint`: 19 digits *usually* fit, and the rows that
do not are rejected one at a time in a batch load, so the failure looks like a handful of bad
rows rather than a mapping error. Anything above `p = 18` goes to `numeric`.
