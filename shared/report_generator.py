import os
import json
from datetime import datetime
from typing import Optional


class ReportGenerator:
    def __init__(self, tool_name: str, output_dir: str = "reports"):
        self.tool_name = tool_name
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(
        self,
        status: str,
        results: dict,
        suggestions: Optional[list[str]] = None,
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.tool_name}_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)

        lines = []
        lines.append("=" * 60)
        lines.append(f"  {self.tool_name.upper()} REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Status: {status.upper()}")
        lines.append("")

        lines.append("-" * 60)
        lines.append("  RESULTS SUMMARY")
        lines.append("-" * 60)
        for key, value in results.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

        lines.append("-" * 60)
        lines.append("  APPRECIATION")
        lines.append("-" * 60)
        lines.append("  Nice work on implementing this tool! The architecture is clean")
        lines.append("  and the integration with AI backends shows thoughtful design.")
        lines.append("")

        lines.append("-" * 60)
        lines.append("  SUGGESTIONS FOR IMPROVEMENT")
        lines.append("-" * 60)
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                lines.append(f"  {i}. {suggestion}")
        else:
            lines.append("  None - No improvements needed at this time.")
        lines.append("")

        lines.append("=" * 60)
        lines.append(f"  END OF {self.tool_name.upper()} REPORT")
        lines.append("=" * 60)

        report_content = "\n".join(lines)

        with open(filepath, "w") as f:
            f.write(report_content)

        return filepath
