#!/usr/bin/env python3
"""Fail if a build script contains a character that ends its own quoting.

Every rebuild stage runs its work as the body of

    docker run ... bash -exc 'LONG SCRIPT'

so a single quote anywhere inside closes the string and the shell reparses
whatever follows. It is silent: the job dies within seconds on a syntax error
that names nothing recognisable.

Three apostrophes in one comment -- AlmaLinux's, Red Hat's, Fedora's -- failed
all 36 stage 0 jobs at once. The existing comments avoid this by writing
"Fedora own noopenh264" and "this job own diagnostic", which reads like a typo
rather than a constraint, so nothing stopped the next person reintroducing it.
This does.
"""
import sys
from pathlib import Path

workflow = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "rebuild-rpms.yml"
lines = workflow.read_text().splitlines()

offenders = []
start = None
for number, line in enumerate(lines, start=1):
    if "bash -exc '" in line:
        start = number
    elif start is not None and line.strip() == "'":
        for offset, body in enumerate(lines[start:number - 1], start=start + 1):
            if "'" in body:
                offenders.append((offset, body.strip()))
        start = None

if offenders:
    print("A single quote inside a bash -exc script closes it. These lines do that:",
          file=sys.stderr)
    for number, text in offenders:
        print(f"  {workflow.name}:{number}: {text}", file=sys.stderr)
    print("\nRephrase to avoid the apostrophe, as the surrounding comments do.",
          file=sys.stderr)
    raise SystemExit(1)

print(f"checked {workflow.name}: no build script contains a quote that would close it")
