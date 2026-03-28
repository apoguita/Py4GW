# PyDialog.pyi - Stub file for the PyDialog module

from typing import List, Optional


class DialogInfo:
    dialog_id: int
    flags: int
    frame_type: int
    event_handler: int
    content_id: int
    property_id: int
    content: str
    agent_id: int

    def __init__(self) -> None: ...


class ActiveDialogInfo:
    dialog_id: int
    context_dialog_id: int
    agent_id: int
    dialog_id_authoritative: bool
    message: str

    def __init__(self) -> None: ...


class DialogButtonInfo:
    dialog_id: int
    button_icon: int
    message: str
    message_decoded: str
    message_decode_pending: bool

    def __init__(self) -> None: ...


class DialogTextDecodedInfo:
    dialog_id: int
    text: str
    pending: bool

    def __init__(self) -> None: ...


class DialogEventLog:
    tick: int
    message_id: int
    incoming: bool
    is_frame_message: bool
    frame_id: int
    w_bytes: List[int]
    l_bytes: List[int]

    def __init__(self) -> None: ...


class DialogCallbackJournalEntry:
    tick: int
    message_id: int
    incoming: bool
    dialog_id: int
    context_dialog_id: int
    agent_id: int
    map_id: int
    model_id: int
    dialog_id_authoritative: bool
    context_dialog_id_inferred: bool
    npc_uid: str
    event_type: str
    text: str

    def __init__(self) -> None: ...


class PyDialog:
    def __init__(self) -> None: ...

    @staticmethod
    def is_dialog_available(dialog_id: int) -> bool: ...
    @staticmethod
    def get_dialog_info(dialog_id: int) -> DialogInfo: ...
    @staticmethod
    def get_last_selected_dialog_id() -> int: ...
    @staticmethod
    def get_active_dialog() -> ActiveDialogInfo: ...
    @staticmethod
    def get_active_dialog_buttons() -> List[DialogButtonInfo]: ...
    @staticmethod
    def is_dialog_active() -> bool: ...
    @staticmethod
    def is_dialog_displayed(dialog_id: int) -> bool: ...
    @staticmethod
    def enumerate_available_dialogs() -> List[DialogInfo]: ...
    @staticmethod
    def get_dialog_text_decoded(dialog_id: int) -> str: ...
    @staticmethod
    def is_dialog_text_decode_pending(dialog_id: int) -> bool: ...
    @staticmethod
    def get_dialog_text_decode_status() -> List[DialogTextDecodedInfo]: ...
    @staticmethod
    def get_dialog_event_logs() -> List[DialogEventLog]: ...
    @staticmethod
    def get_dialog_event_logs_received() -> List[DialogEventLog]: ...
    @staticmethod
    def get_dialog_event_logs_sent() -> List[DialogEventLog]: ...
    @staticmethod
    def clear_dialog_event_logs() -> None: ...
    @staticmethod
    def clear_dialog_event_logs_received() -> None: ...
    @staticmethod
    def clear_dialog_event_logs_sent() -> None: ...
    @staticmethod
    def get_dialog_callback_journal() -> List[DialogCallbackJournalEntry]: ...
    @staticmethod
    def get_dialog_callback_journal_received() -> List[DialogCallbackJournalEntry]: ...
    @staticmethod
    def get_dialog_callback_journal_sent() -> List[DialogCallbackJournalEntry]: ...
    @staticmethod
    def clear_dialog_callback_journal() -> None: ...
    @staticmethod
    def clear_dialog_callback_journal_received() -> None: ...
    @staticmethod
    def clear_dialog_callback_journal_sent() -> None: ...
    @staticmethod
    def clear_dialog_callback_journal_filtered(
        npc_uid: Optional[str] = ...,
        incoming: Optional[bool] = ...,
        message_id: Optional[int] = ...,
        event_type: Optional[str] = ...,
    ) -> None: ...
    @staticmethod
    def clear_cache() -> None: ...
    @staticmethod
    def initialize() -> None: ...
    @staticmethod
    def terminate() -> None: ...
