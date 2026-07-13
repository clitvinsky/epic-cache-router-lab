"""Show how routing decisions map to generation execution plans and cost."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epic_cache_router_lab.cost_model import summarize_costs
from epic_cache_router_lab.evals import load_prior_panels, load_requests
from epic_cache_router_lab.execution_router import plan_generation
from epic_cache_router_lab.router import CacheRouter


def main() -> int:
    prior = load_prior_panels(ROOT / "fixtures" / "prior_panels.json")
    requests = load_requests(ROOT / "fixtures" / "requests.json")
    router = CacheRouter(prior)

    plans = []
    for request in requests:
        decision = router.route(request)
        plan = plan_generation(decision)
        plans.append(plan)
        print(json.dumps(plan.to_dict(), indent=2))
        print()

    print("cost summary")
    print(json.dumps(summarize_costs(plans).to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
