# local-usage-scanner

`local-usage-scanner` is a read-only macOS app storage scanner.
It helps you find which desktop apps are using disk space in `caches`, `logs`, `local data` folders, and a few app-specific `media/download` locations.

## Safety

- Read-only only.
- No file deletion.
- No file moving.
- BTW: Any `safe_to_clean_hint` is only a hint, not a guarantee.

## Run

Use the bundled rules directory:

```bash
python3 main.py
```

Only scan selected apps:

```bash
python3 main.py --only slack notion wechat
```

JSON output:

```bash
python3 main.py --format json
```

Verbose output:

```bash
python3 main.py --verbose
# More detai information
```

Custom rules:

```bash
python3 main.py --rules ./rules
python3 main.py --rules ./rules/default_macos_apps_max.json
```

## Rule format

Each `app` rule supports:

- `id`
- `name`
- `platforms`
- `description`
- `user_access_paths`
- `warnings`
- `paths`

Each `path` in `paths` item supports:

- `path`
- `category`
- `description`
- `accessible_path`
- `safe_to_clean_hint`
- `warning`

## Notes

- The scanner is `read-only`, no edit/delete.
- Symbolic links are not followed.
- Missing paths are reported instead of failing the whole scan.
- Permission or filesystem errors are captured per path.
- Platform mismatch is reported as `skipped`.

## Current scope

The default macOS rules focus on common desktop apps and conservative local storage locations.
Some apps store downloads or catalog data in user-configurable folders; those may not be fully covered by the default rules.
