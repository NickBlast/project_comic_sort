"""
JSON reporting for dry-run.

Generates detailed JSON reports of simulation results.
"""

import json
import time
from pathlib import Path
from typing import List
from dataclasses import asdict

from src.core.simulator import MigrationAction

def generate_json_report(actions: List[MigrationAction], output_path: Path):
    """
    Generate a JSON report of the simulation.
    """
    report = {
        "timestamp": time.time(),
        "summary": {
            "total": len(actions),
            "copy": sum(1 for a in actions if a.status == "COPY"),
            "skip": sum(1 for a in actions if a.status == "SKIP"),
            "conflict": sum(1 for a in actions if a.status == "CONFLICT"),
            "error": sum(1 for a in actions if a.status == "ERROR")
        },
        "actions": [asdict(a) for a in actions]
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
