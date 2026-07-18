from ..GlobalCache import GLOBAL_CACHE
from ..Player import Player


class BottingTreeMessagingMixin:
    def ClearPendingMessages(self) -> int:
        account_email = Player.GetAccountEmail()
        if not account_email:
            return 0

        cleared_count = 0
        for message_index, message in GLOBAL_CACHE.ShMem.GetAllMessages():
            if message is None:
                continue
            if not getattr(message, 'Active', False):
                continue
            if getattr(message, 'ReceiverEmail', '') != account_email:
                continue
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, message_index)
            cleared_count += 1
        return cleared_count
