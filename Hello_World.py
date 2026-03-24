from dataclasses import dataclass
from typing import Callable

import PyImGui

from Py4GWCoreLib import IconsFontAwesome5, Py4GW
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager


MODULE_NAME = "Widget Catalog Help"
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 620
TOPICS_PANE_WIDTH = 250.0
INI_PATH = "Widgets/WidgetCatalog"
INI_FILENAME = "WidgetCatalogHelp.ini"
INI_KEY = ""
INI_INIT = False
WINDOW_VISIBLE = True
WINDOW_VISIBILITY_INITIALIZED = False


@dataclass(frozen=True)
class HelpTopic:
    topic_id: str
    title: str
    summary: str
    render: Callable[[], None]


def _draw_topic_overview() -> None:
    PyImGui.spacing()
    ImGui.push_font("Bold", 40)
    PyImGui.text_wrapped("Welcome to Py4GW")
    ImGui.pop_font()
    
    PyImGui.spacing()
    PyImGui.text_wrapped(
        "Py4GW is a community toolkit for Guild Wars players. It brings together helpful windows, smart tools, automation, and everyday quality-of-life features in one place."
    )

    PyImGui.spacing()
    PyImGui.text_wrapped(
        "Some parts are there to give you better information. Some help you manage the game more comfortably. Some handle repetitive tasks for you. All of it is meant to make the game easier to navigate and more enjoyable to live in."
    )

    PyImGui.spacing()
    PyImGui.text_wrapped(
        "The goal of Py4GW is not just to add features. It is to give players a shared place where useful systems feel consistent, approachable, and worth relying on, whether you are here for convenience, customization, automation, or exploration."
    )
    
    show_on_startup = not IniManager().getBool(INI_KEY, "show_on_startup", default=True, section="Configuration")
    updated_show_on_startup = not PyImGui.checkbox("Show this Screen on startup", not show_on_startup)
    if updated_show_on_startup != show_on_startup:
        IniManager().set(
            INI_KEY,
            "show_on_startup",
            not updated_show_on_startup,
            section="Configuration",
        )
        IniManager().save_vars(INI_KEY)


def _draw_topic_navigation() -> None:
    PyImGui.text_wrapped("This split layout mirrors the help experience we want inside the Widget Catalog.")
    PyImGui.spacing()
    PyImGui.bullet_text("Use the left pane to choose a topic.")
    PyImGui.bullet_text("Use the right pane to render the selected topic with any mix of text, tables, icons, buttons, or previews.")
    PyImGui.bullet_text("This callback-based structure lets each topic evolve into its own custom layout.")


def _draw_topic_planned_topics() -> None:
    PyImGui.text_wrapped("These are good candidates for the next help chapters.")
    PyImGui.spacing()
    PyImGui.bullet_text("Favorites and how they are stored.")
    PyImGui.bullet_text("Reloading widgets and understanding when a refresh is needed.")
    PyImGui.bullet_text("Pausing optional or non-system widgets.")
    PyImGui.bullet_text("Catalog settings, floating button behavior, and layout customization.")
    PyImGui.bullet_text("Differences between the catalog UI and the advanced widget manager.")


TOPICS: tuple[HelpTopic, ...] = (
    HelpTopic(
        topic_id="overview",
        title="Overview",
        summary="Py4GW's introduction.",
        render=_draw_topic_overview,
    ),
    HelpTopic(
        topic_id="navigation",
        title="Navigation",
        summary="How users move through topics and folders.",
        render=_draw_topic_navigation,
    ),
    HelpTopic(
        topic_id="planned_topics",
        title="Planned Topics",
        summary="What we can document next.",
        render=_draw_topic_planned_topics,
    ),
)


selected_topic_id = TOPICS[0].topic_id


def _get_selected_topic() -> HelpTopic:
    for topic in TOPICS:
        if topic.topic_id == selected_topic_id:
            return topic
    return TOPICS[0]


def _draw_topics_pane() -> None:
    global selected_topic_id

    if PyImGui.begin_child("##help_topics", (TOPICS_PANE_WIDTH, 0.0), True):
        PyImGui.text(f"{IconsFontAwesome5.ICON_LIST} Topics")
        PyImGui.separator()

        for topic in TOPICS:
            if PyImGui.selectable(
                f"{topic.title}##{topic.topic_id}",
                topic.topic_id == selected_topic_id,
                PyImGui.SelectableFlags.NoFlag,
                (0.0, 0.0),
            ):
                selected_topic_id = topic.topic_id
            if PyImGui.is_item_hovered():
                PyImGui.show_tooltip(topic.summary)

    PyImGui.end_child()


def _draw_content_pane() -> None:
    topic = _get_selected_topic()

    if PyImGui.begin_child("##help_content", (0.0, 0.0), True):
        PyImGui.text(f"{IconsFontAwesome5.ICON_BOOK} {topic.title}")
        PyImGui.separator()
        topic.render()

    PyImGui.end_child()


def _draw_help_window() -> None:
    global WINDOW_VISIBLE

    expanded, WINDOW_VISIBLE = ImGui.BeginWithClose(
        ini_key=INI_KEY,
        name=MODULE_NAME,
        p_open=WINDOW_VISIBLE,
        flags=PyImGui.WindowFlags.NoCollapse,
    )

    if expanded:
        if PyImGui.begin_table(
            "##help_layout",
            2,
            PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.Resizable,
        ):
            PyImGui.table_setup_column("Topics", PyImGui.TableColumnFlags.WidthFixed, TOPICS_PANE_WIDTH)
            PyImGui.table_setup_column("Content", PyImGui.TableColumnFlags.WidthStretch, 0.0)

            PyImGui.table_next_column()
            _draw_topics_pane()

            PyImGui.table_next_column()
            _draw_content_pane()

            PyImGui.end_table()

    ImGui.End(INI_KEY)


def _ensure_ini() -> bool:
    global INI_KEY, INI_INIT
    if INI_INIT:
        return True

    if not INI_PATH:
        return False

    INI_KEY = IniManager().ensure_global_key(INI_PATH, INI_FILENAME)
    if not INI_KEY:
        return False

    IniManager().add_bool(INI_KEY, "init", "Window config", "init", default=True)
    IniManager().add_bool(INI_KEY, "show_on_startup", "Configuration", "show_on_startup", default=True)
    IniManager().load_once(INI_KEY)
    node = IniManager()._get_node(INI_KEY)
    if node is not None and not node.ini_handler.has_key("Configuration", "show_on_startup"):
        IniManager().set(INI_KEY, "show_on_startup", True, section="Configuration")
    IniManager().set(INI_KEY, "init", True)
    IniManager().save_vars(INI_KEY)
    INI_INIT = True
    return True


def _apply_initial_visibility() -> None:
    global WINDOW_VISIBLE, WINDOW_VISIBILITY_INITIALIZED
    if WINDOW_VISIBILITY_INITIALIZED:
        return

    WINDOW_VISIBLE = IniManager().getBool(INI_KEY, "show_on_startup", default=True, section="Configuration")
    WINDOW_VISIBILITY_INITIALIZED = True


def main():
    try:
        if not _ensure_ini():
            return
        _apply_initial_visibility()
        _draw_help_window()
    except Exception as exc:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()
