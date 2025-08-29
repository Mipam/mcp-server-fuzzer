import json
import os
from datetime import datetime
from typing import List, Dict


from typing import List, Dict, Any, Optional


class Reporter:
    """Generates reports for fuzzing sessions."""

    def __init__(self, output_dir: str, session_id: Optional[str] = None):
        """
        Initialize the Reporter.

        Args:
            output_dir: The directory to save reports to.
            session_id: The ID of the session. If not provided, a new one will be generated.
        """
        self.output_dir = output_dir
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results: List[Dict[str, Any]] = []
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def add_result(self, result: Dict[str, Any]) -> None:
        """Add a result to the report."""
        self.results.append(result)

    def generate_json_report(self) -> None:
        """Generate a JSON report."""
        filename = f"fuzzing_report_{self.session_id}.json"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=4)

    def generate_text_report(self) -> None:
        """Generate a text report."""
        filename = f"fuzzing_report_{self.session_id}.txt"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            for result in self.results:
                f.write(f"Target: {result.get('target')}\n")
                f.write(f"Total Runs: {result.get('total_runs')}\n")
                f.write(f"Exceptions: {result.get('exceptions')}\n")
                f.write(f"Example Exception: {result.get('example_exception')}\n")
                f.write("\n")
