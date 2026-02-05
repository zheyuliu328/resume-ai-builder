"""Verify V1.3 gap engine stemming behavior.

Checks that managing/managed do not create false gaps.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'backend'))

from gap_engine import gap_analyze


def main():
    jd = "We need someone managing distributed systems and managing incidents."
    resume = {
        "experience": [
            {
                "company": "X",
                "highlights": [
                    "Managed distributed systems at scale.",
                    "Managed incidents and improved reliability.",
                ],
            }
        ]
    }

    out = gap_analyze(jd, resume)
    gaps = set(out.get("gaps") or [])
    assert "manag" not in gaps, f"Expected stem 'manag' to match; got gaps={gaps}"
    print("OK")


if __name__ == "__main__":
    main()
