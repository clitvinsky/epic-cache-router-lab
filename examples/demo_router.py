"""Run a small public-safe cache-routing demo."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epic_cache_router_lab.evals import load_prior_panels, load_requests
from epic_cache_router_lab.router import CacheRouter


def main() -> int:
    prior = load_prior_panels(ROOT / "fixtures" / "prior_panels.json")
    requests = load_requests(ROOT / "fixtures" / "requests.json")
    router = CacheRouter(prior)

    for request in requests:
        decision = router.route(request)
        print(json.dumps(decision.to_dict(), indent=2))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

