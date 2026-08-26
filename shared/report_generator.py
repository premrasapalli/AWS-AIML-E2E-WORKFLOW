import os
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
        implemented_correctly: list[str],
        improvements_needed: Optional[list[str]] = None,
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
        lines.append("  WHAT IS IMPLEMENTED CORRECTLY")
        lines.append("-" * 60)
        if implemented_correctly:
            for item in implemented_correctly:
                lines.append(f"  - {item}")
        else:
            lines.append("  None")
        lines.append("")

        lines.append("-" * 60)
        lines.append("  IMPROVEMENTS NEEDED")
        lines.append("-" * 60)
        if improvements_needed:
            for i, item in enumerate(improvements_needed, 1):
                lines.append(f"  {i}. {item}")
        else:
            lines.append("  None - No improvements needed")
        lines.append("")

        lines.append("=" * 60)
        lines.append(f"  END OF {self.tool_name.upper()} REPORT")
        lines.append("=" * 60)

        report_content = "\n".join(lines)

        with open(filepath, "w") as f:
            f.write(report_content)

        return filepath
