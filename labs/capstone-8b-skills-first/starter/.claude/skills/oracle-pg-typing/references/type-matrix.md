# The full Oracle -> PostgreSQL 16 type matrix

TODO: build the matrix. Group by family: numeric, character, date/time, binary/LOB, oddities.
Each row needs Oracle type, PostgreSQL type, a confidence (C / D / M), and a one-line WHY.
The WHY column is the point. A matrix without it is a lookup table the agent follows
mechanically, and mechanical output is what this course is trying to avoid.

Keep this file and `scripts/check_mapping.py` in agreement, and say in the header which one
wins if they ever disagree. Pick the one that can be unit-tested.
