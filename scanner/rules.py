import json
from pathlib import Path

from scanner.models import AppRule, PathRule


def load_rules(rule_file: str) -> list[AppRule]:
    path = Path(rule_file)
    if not path.exists():
        raise FileNotFoundError(f"Rules fle not found: {rule_file}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    app_configs = data.get("apps", [])
    rules: list[AppRule] = []
    for config in app_configs:
        path_rules: list[PathRule] = []
        # path_rules: list[str] = []
        for path_data in config.get("paths", []):
            path_rules.append(
                PathRule(
                    path=path_data["path"],
                    category=path_data["category"],
                    description=path_data.get("description", ""),
                )
            )
        app_rule = AppRule(
            app_id=config["id"],
            app_name=config["name"],
            platforms=config.get("platforms", []),
            description=config.get("description", ""),
            paths=path_rules,
        )
        rules.append(app_rule)
    return rules
