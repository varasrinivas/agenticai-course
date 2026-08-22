# `NUMBER(p,s)` -- picking the right PostgreSQL width

TODO: write the decision tree for NUMBER, covering scale > 0, scale < 0, scale 0 at each
precision band, and a bare NUMBER with no precision at all.

Then explain why the bare NUMBER is the dangerous one. Include the two queries that settle
it against real data, and be honest about what a zero result does and does not license.

`STATE_SOS_SOURCE.RECORDS_EXPECTED` in this schema is exactly this case. Use it.
