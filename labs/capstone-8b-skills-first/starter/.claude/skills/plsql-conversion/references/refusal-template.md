# Writing a refusal

TODO: define the output shape for a refusal, then write a full worked example.

Start with the test a refusal has to pass. Something like: could a database engineer who
was not here act on this without re-reading the original PL/SQL? Sharpen that into a list
of required sections.

The worked example matters more than the template. Use the real refusal in this lab --
run the scanner over `legacy-oracle/03_packages.sql` with --refuse-only to find it.

Two things the example must do that a generic template will not teach:
  - state the failure mode concretely. Not 'may not work' -- say what goes wrong, when,
    and why nobody notices.
  - trace the callers. The reviewer needs the blast radius, not just the blocker.
    grep for the procedure name across `legacy-oracle/` and `app/`.
