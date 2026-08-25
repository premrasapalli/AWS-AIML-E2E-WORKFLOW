import os
import re
from ..models import TerraformChange


class TerraformParser:
    def parse_diff(self, diff_output: str) -> list[TerraformChange]:
        changes = []
        current_file = None
        current_resource = None
        current_change_type = None
        before = {}
        after = {}

        for line in diff_output.split("\n"):
            file_match = re.match(r"^diff --git a/(.+\.tf) b/(.+\.tf)$", line)
            if file_match:
                current_file = file_match.group(1)
                continue

            resource_match = re.match(
                r"^([+-])\s+(resource|data|variable|output|module)\s+\"([^\"]+)\"\s+\"([^\"]+)\"",
                line,
            )
            if resource_match:
                if current_resource:
                    changes.append(
                        TerraformChange(
                            file=current_file or "unknown",
                            resource_type=current_resource["type"],
                            resource_name=current_resource["name"],
                            change_type=current_change_type or "modify",
                            before=before or None,
                            after=after or None,
                        )
                    )
                prefix = resource_match.group(1)
                current_change_type = "create" if prefix == "+" else "delete"
                current_resource = {
                    "type": resource_match.group(2),
                    "name": resource_match.group(4),
                }
                before = {}
                after = {}

        if current_resource:
            changes.append(
                TerraformChange(
                    file=current_file or "unknown",
                    resource_type=current_resource["type"],
                    resource_name=current_resource["name"],
                    change_type=current_change_type or "modify",
                    before=before or None,
                    after=after or None,
                )
            )

        return changes

    def parse_hcl(self, file_path: str) -> dict:
        resources = {}
        try:
            with open(file_path, "r") as f:
                content = f.read()
                resource_pattern = re.compile(
                    r"(resource|data|variable|output|module)\s+\"([^\"]+)\"\s+\"([^\"]+)\"\s*\{([^}]*)\}",
                    re.DOTALL,
                )
                for match in resource_pattern.finditer(content):
                    kind = match.group(1)
                    type_name = match.group(2)
                    name = match.group(3)
                    block = match.group(4)
                    key = f"{kind}.{type_name}.{name}"
                    resources[key] = {"type": type_name, "name": name, "block": block}
        except Exception:
            pass
        return resources

    def get_terraform_files(self, path: str) -> list[str]:
        tf_files = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".tf"):
                    tf_files.append(os.path.join(root, file))
        return tf_files
