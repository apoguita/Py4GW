from Py4GWCoreLib import *
from Py4GWCoreLib.IniManager import IniManager

MODULE_NAME = "Icon Explorer"
MODULE_ICON = "Textures/Module_Icons/Explorer Search.png"
INI_PATH = "Widgets/IconExplorer"
INI_FILENAME = "IconExplorer.ini"

INI_KEY = ""
initialized = False

filter_text = ""
favorites_only = False
grid_columns = 4
sort_mode = 1  # 0 = A-Z, 1 = favorites first
favorites: set[str] = set()

ICON_ENTRIES: list[tuple[str, str]] = []
ICON_NAME_SET: set[str] = set()


def _build_icon_index():
    global ICON_ENTRIES, ICON_NAME_SET
    entries: list[tuple[str, str]] = []
    for name in dir(IconsFontAwesome5):
        if not name.startswith("ICON_"):
            continue
        value = getattr(IconsFontAwesome5, name)
        if isinstance(value, str):
            entries.append((name, value))
    entries.sort(key=lambda x: x[0])
    ICON_ENTRIES = entries
    ICON_NAME_SET = {name for name, _ in entries}


def _add_config_vars():
    IniManager().add_str(INI_KEY, "favorites", "Favorites", "favorites", default="")
    IniManager().add_bool(INI_KEY, "favorites_only", "View", "favorites_only", default=False)
    IniManager().add_int(INI_KEY, "grid_columns", "View", "grid_columns", default=4)
    IniManager().add_int(INI_KEY, "sort_mode", "View", "sort_mode", default=1)


def _load_settings():
    global favorites_only, grid_columns, sort_mode, favorites
    favorites_only = IniManager().getBool(INI_KEY, "favorites_only", False, section="View")
    grid_columns = max(2, min(8, IniManager().getInt(INI_KEY, "grid_columns", 4, section="View")))
    sort_mode = IniManager().getInt(INI_KEY, "sort_mode", 1, section="View")

    raw = IniManager().getStr(INI_KEY, "favorites", "", section="Favorites")
    parsed = {x.strip() for x in raw.split(",") if x.strip()}
    favorites = {name for name in parsed if name in ICON_NAME_SET}


def _save_setting(name: str, value, section: str):
    IniManager().set(INI_KEY, name, value, section=section)
    IniManager().save_vars(INI_KEY)


def _save_favorites():
    _save_setting("favorites", ",".join(sorted(favorites)), "Favorites")


def _toggle_favorite(icon_name: str):
    if icon_name in favorites:
        favorites.remove(icon_name)
    else:
        favorites.add(icon_name)
    _save_favorites()


def _matches(icon_name: str, icon_value: str) -> bool:
    q = filter_text.strip().lower()
    if not q:
        return True
    if q in icon_name.lower():
        return True
    try:
        return q in f"{ord(icon_value):04X}".lower()
    except Exception:
        return False


def _get_visible_icons() -> list[tuple[str, str]]:
    items = [
        (name, value)
        for name, value in ICON_ENTRIES
        if _matches(name, value) and (not favorites_only or name in favorites)
    ]
    if sort_mode == 1:
        items.sort(key=lambda x: (0 if x[0] in favorites else 1, x[0]))
    else:
        items.sort(key=lambda x: x[0])
    return items


def DrawWindow(title: str = "FontAwesome Icon Explorer"):
    global filter_text, favorites_only, grid_columns, sort_mode

    if ImGui.Begin(INI_KEY, title):
        PyImGui.text("Filter:")
        PyImGui.same_line(0, -1)
        filter_text = PyImGui.input_text("##IconFilter", filter_text)

        if PyImGui.button("Clear"):
            filter_text = ""
        PyImGui.same_line(0, 10)

        new_fav_only = PyImGui.checkbox("Favorites only", favorites_only)
        if new_fav_only != favorites_only:
            favorites_only = new_fav_only
            _save_setting("favorites_only", favorites_only, "View")

        PyImGui.same_line(0, 20)
        new_sort_mode = PyImGui.radio_button("Favorites first", sort_mode, 1)
        PyImGui.same_line(0, -1)
        new_sort_mode = PyImGui.radio_button("A-Z", new_sort_mode, 0)
        if new_sort_mode != sort_mode:
            sort_mode = new_sort_mode
            _save_setting("sort_mode", sort_mode, "View")

        PyImGui.same_line(0, 20)
        new_columns = PyImGui.slider_int("Columns", grid_columns, 2, 8)
        if new_columns != grid_columns:
            grid_columns = max(2, min(8, new_columns))
            _save_setting("grid_columns", grid_columns, "View")

        PyImGui.same_line(0, 12)
        if PyImGui.button("Clear Favorites"):
            favorites.clear()
            _save_favorites()

        visible = _get_visible_icons()
        PyImGui.text(f"Showing {len(visible)} icons | Favorites {len(favorites)}")

        table_flags = (
            PyImGui.TableFlags.RowBg
            | PyImGui.TableFlags.BordersInnerV
            | PyImGui.TableFlags.SizingStretchSame
        )

        if PyImGui.begin_table("IconTable", grid_columns, table_flags):
            col = 0
            for name, value in visible:
                if col == 0:
                    PyImGui.table_next_row(0, 30)
                PyImGui.table_set_column_index(col)

                is_fav = name in favorites
                fav_glyph = IconsFontAwesome5.ICON_STAR if is_fav else IconsFontAwesome5.ICON_PLUS
                if PyImGui.small_button(f"{fav_glyph}##fav_{name}"):
                    _toggle_favorite(name)

                PyImGui.same_line(0, 6)
                PyImGui.text(f"{value} {name}")

                if PyImGui.is_item_hovered():
                    PyImGui.begin_tooltip()
                    PyImGui.text(name)
                    PyImGui.text(f"U+{ord(value):04X}")
                    PyImGui.text("Click star/plus to toggle favorite")
                    PyImGui.end_tooltip()

                col += 1
                if col >= grid_columns:
                    col = 0

            PyImGui.end_table()

    ImGui.End(INI_KEY)


def tooltip():
    PyImGui.begin_tooltip()

    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Icon Explorer", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    PyImGui.text("Single-window FontAwesome icon browser.")
    PyImGui.text("Favorites are saved to INI and can be filtered.")

    PyImGui.end_tooltip()


def main():
    global INI_KEY, initialized

    if not initialized:
        if not Routines.Checks.Map.MapValid():
            return

        _build_icon_index()

        INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
        if not INI_KEY:
            return

        _add_config_vars()
        IniManager().load_once(INI_KEY)
        _load_settings()
        initialized = True

    DrawWindow()


if __name__ == "__main__":
    main()
