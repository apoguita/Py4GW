import json
import os
import sys
import shutil


def _load_json_safe(path: str) -> dict:
    """Load JSON from a file. On corruption, attempt recovery via raw_decode
    (handles concatenated JSON from multi-writer conflicts)."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"  WARNING: {os.path.basename(path)} is corrupted ({exc})")
        print(f"  Attempting recovery via raw_decode...")
        decoder = json.JSONDecoder()
        try:
            data, end = decoder.raw_decode(raw)
            discarded = len(raw) - end
            pct = end * 100.0 / max(1, len(raw))
            print(f"  Recovered {pct:.1f}% ({discarded} chars of trailing garbage discarded)")
            return data
        except json.JSONDecodeError:
            print(f"  ERROR: Recovery failed — file is unrecoverable")
            sys.exit(1)


def _is_agent_name_junk(name: str) -> bool:
    s = str(name or "").strip()
    return s.startswith("Agent ") and s[6:].isdigit()


def _merge_enemy_data(main_file: str, side_file: str) -> dict | None:
    main = {}
    side = {}

    if os.path.exists(main_file):
        main = _load_json_safe(main_file)
    if os.path.exists(side_file):
        side = _load_json_safe(side_file)

    if not main and not side:
        return None

    merged_enemies: dict[str, dict] = {}

    # Start with main data
    main_enemies = main.get("enemies", {})
    for key, record in main_enemies.items():
        merged_enemies[str(key)] = dict(record)

    # Merge side data field-by-field
    side_enemies = side.get("enemies", {})
    for key, side_record in side_enemies.items():
        key = str(key)
        side_record = dict(side_record)

        if key not in merged_enemies:
            merged_enemies[key] = side_record
            continue

        existing = merged_enemies[key]

        # Merge encoded_names
        for value in side_record.get("encoded_names", []):
            if value not in existing.get("encoded_names", []):
                existing["encoded_names"].append(value)

        # Merge model_ids
        for value in side_record.get("model_ids", []):
            if value not in existing.get("model_ids", []):
                existing["model_ids"].append(value)

        # Merge observed_maps
        for map_key, map_entry in side_record.get("observed_maps", {}).items():
            if str(map_key) not in existing.setdefault("observed_maps", {}):
                existing["observed_maps"][str(map_key)] = map_entry

        # Merge observed_skills
        for skill_key, skill_entry in side_record.get("observed_skills", {}).items():
            if str(skill_key) not in existing.setdefault("observed_skills", {}):
                existing["observed_skills"][str(skill_key)] = skill_entry

        # Adopt inferred professions if main doesn't have them
        if not existing.get("inferred_primary") and side_record.get("inferred_primary"):
            existing["inferred_primary"] = side_record["inferred_primary"]
        if not existing.get("inferred_secondary") and side_record.get("inferred_secondary"):
            existing["inferred_secondary"] = side_record["inferred_secondary"]

    return {
        "schema": "py4gw_enemy_tracker",
        "schema_version": 2,
        "enemies": merged_enemies,
    }


def _merge_name_data(main_file: str, side_file: str) -> dict | None:
    main = {}
    side = {}

    if os.path.exists(main_file):
        main = _load_json_safe(main_file)
    if os.path.exists(side_file):
        side = _load_json_safe(side_file)

    if not main and not side:
        return None

    language = main.get("language") or side.get("language") or "en"

    merged_names: dict[str, list[str]] = {}

    # Start with main names (strip junk)
    main_names = main.get("names", {})
    for key, names in main_names.items():
        cleaned: list[str] = []
        if isinstance(names, list):
            for name in names:
                name = str(name or "").strip()
                if name and not _is_agent_name_junk(name) and name not in cleaned:
                    cleaned.append(name)
        if cleaned:
            merged_names[str(key)] = cleaned

    # Merge side names (strip junk, deduplicate)
    side_names = side.get("names", {})
    for key, names in side_names.items():
        key = str(key)
        if key not in merged_names:
            merged_names[key] = []
        cleaned = merged_names[key]
        if isinstance(names, list):
            for name in names:
                name = str(name or "").strip()
                if name and not _is_agent_name_junk(name) and name not in cleaned:
                    cleaned.append(name)

    # Remove keys whose name list became empty after stripping
    merged_names = {k: v for k, v in merged_names.items() if v}

    return {
        "schema": "py4gw_enemy_tracker_names",
        "schema_version": 1,
        "language": language,
        "names": merged_names,
    }


def _atomic_write(path: str, payload: dict) -> None:
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))

    DATA_MAIN = os.path.join(script_dir, "EnemyTrackerData.json")
    DATA_SIDE = os.path.join(script_dir, "EnemyTrackerData (1).json")
    NAMES_MAIN = os.path.join(script_dir, "EnemyTrackerNames.en.json")
    NAMES_SIDE = os.path.join(script_dir, "EnemyTrackerNames.en (1).json")

    # Root-level stale files
    root_dir = os.path.dirname(script_dir)
    ROOT_DATA = os.path.join(root_dir, "EnemyTrackerData.json")
    ROOT_NAMES = os.path.join(root_dir, "EnemyTrackerNames.en.json")

    # WARNING banner
    print("=" * 60)
    print("WARNING: Close all Guild Wars game clients before running this script.")
    print("=" * 60)
    if "--yes" in sys.argv:
        print("(Running non-interactively with --yes)")
    else:
        try:
            input("Press Enter to continue (Ctrl+C to cancel)... ")
        except EOFError:
            print("(Non-interactive — continuing)")
            pass

    # Phase 1: Migration — copy root→EnemyData/ if target missing
    if not os.path.exists(DATA_MAIN) and os.path.exists(ROOT_DATA):
        print("Phase 1: Copying root data file to EnemyData/")
        shutil.copy2(ROOT_DATA, DATA_MAIN)
    if not os.path.exists(NAMES_MAIN) and os.path.exists(ROOT_NAMES):
        print("Phase 1: Copying root names file to EnemyData/")
        shutil.copy2(ROOT_NAMES, NAMES_MAIN)

    # Phase 2: Merge enemy data
    print("Phase 2: Merging enemy data...")
    merged_data = _merge_enemy_data(DATA_MAIN, DATA_SIDE)
    if merged_data is not None:
        _atomic_write(DATA_MAIN, merged_data)
        print(f"  Wrote {len(merged_data.get('enemies', {}))} enemy records to {DATA_MAIN}")
    else:
        print("  No enemy data to merge.")

    # Phase 3: Merge names
    print("Phase 3: Merging name data (stripping Agent NNN junk)...")
    merged_names = _merge_name_data(NAMES_MAIN, NAMES_SIDE)
    if merged_names is not None:
        _atomic_write(NAMES_MAIN, merged_names)
        print(f"  Wrote {len(merged_names.get('names', {}))} name entries to {NAMES_MAIN}")
    else:
        print("  No name data to merge.")

    # Phase 4: Delete (1) source files
    print("Phase 4: Deleting (1) source files...")
    for side_file in (DATA_SIDE, NAMES_SIDE):
        if os.path.exists(side_file):
            os.remove(side_file)
            print(f"  Deleted {side_file}")

    # Phase 5: Delete root stale copies (with safety check)
    print("Phase 5: Cleaning up root stale copies...")
    for root_file in (ROOT_DATA, ROOT_NAMES):
        if os.path.exists(root_file):
            try:
                with open(root_file, "r", encoding="utf-8") as f:
                    content = f.read()
                if "py4gw_enemy_tracker" in content:
                    os.remove(root_file)
                    print(f"  Deleted {root_file}")
                else:
                    print(f"  SKIPPED {root_file} (does not appear to be enemy tracker data)")
            except Exception:
                print(f"  SKIPPED {root_file} (could not read)")

    print("=" * 60)
    print("Cleanup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
