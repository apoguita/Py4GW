import os
from importlib import util
from Py4GWCoreLib import ConsoleLog

# maps/
#   └── <Region>/
#         └── <run>.py

MAPS_DIR = os.path.join(os.path.dirname(__file__), "maps")

def get_regions():
    """
    Return list of region folder names under maps/.
    """
    try:
        dirs = [
            d for d in os.listdir(MAPS_DIR)
            if os.path.isdir(os.path.join(MAPS_DIR, d))
        ]
    except Exception as e:
        ConsoleLog("map_loader", f"get_regions error: {e}")
        return []
    return sorted(dirs)


def get_runs(region):
    """
    Given a region name, return list of run script names (without .py)
    inside maps/<region>/
    """
    region_dir = os.path.join(MAPS_DIR, region)
    if not os.path.isdir(region_dir):
        ConsoleLog("map_loader", f"get_runs: no region dir for '{region}'")
        return []

    try:
        scripts = [
            f for f in os.listdir(region_dir)
            if f.endswith(".py") and f != "__init__.py"
        ]
    except Exception as e:
        ConsoleLog("map_loader", f"get_runs error in '{region}': {e}")
        return []

    runs = [os.path.splitext(f)[0] for f in scripts]
    return sorted(runs)


def load_map_data(region, run):
    """
    Import maps/<region>/<run>.py (with fallback for missing leading underscore),
    then extract:
      <run>              -> explorable path list
      <run>_outpost_path -> outpost path list
      <run>_ids          -> dict of IDs

    Returns: {
      "outpost_path": [...],
      "segments":    [...],
      "ids":             {...}
    }
    """
    region_dir = os.path.join(MAPS_DIR, region)
    # try exact
    filepath = os.path.join(region_dir, f"{run}.py")
    # fallback if run missing leading underscore
    if not os.path.isfile(filepath) and not run.startswith("_"):
        alt_run = f"_{run}"
        alt_path = os.path.join(region_dir, f"{alt_run}.py")
        if os.path.isfile(alt_path):
            run = alt_run
            filepath = alt_path

    if not os.path.isfile(filepath):
        raise FileNotFoundError(filepath)

    spec = util.spec_from_file_location(f"maps.{region}.{run}", filepath)
    if not spec or not spec.loader:
        raise ImportError(f"Could not load spec for {filepath}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # use run as prefix to match variables inside module
    base = run.lower()
    data = {
        "outpost_path": getattr(module, f"{base}_outpost_path", []),
        "segments":     getattr(module, f"{base}_segments", []),
        "ids":          getattr(module, f"{base}_ids", {}),
    }
    return data