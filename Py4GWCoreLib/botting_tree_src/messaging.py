from ..GlobalCache import GLOBAL_CACHE
from ..GlobalCache.shared_memory_src.HeroAIOptionStruct import HeroAIOptionStruct
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

    def RestoreHeroAIOptions(self) -> bool:
        cached_data = self.headless_heroai.cached_data

        def _apply_core_options(options: HeroAIOptionStruct) -> HeroAIOptionStruct:
            options.Following = True
            options.Avoidance = True
            options.Targeting = True
            options.Combat = True
            options.Looting = self.looting_enabled
            return options

        cached_data.account_options = _apply_core_options(cached_data.account_options or HeroAIOptionStruct())
        cached_data.global_options = _apply_core_options(cached_data.global_options or HeroAIOptionStruct())

        account_email = Player.GetAccountEmail()
        if not account_email:
            return False

        shared_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email) or HeroAIOptionStruct()
        shared_options = _apply_core_options(shared_options)
        GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, shared_options)
        cached_data.account_options = shared_options
        return True

    def _heroai_options_match_runtime_policy(self) -> bool:
        expected_looting = bool(self.looting_enabled)
        cached_options = self.headless_heroai.cached_data.account_options
        if cached_options is not None:
            if not all([
                bool(cached_options.Following),
                bool(cached_options.Avoidance),
                bool(cached_options.Targeting),
                bool(cached_options.Combat),
            ]):
                return False
            if bool(cached_options.Looting) != expected_looting:
                return False

        account_email = Player.GetAccountEmail()
        if not account_email:
            return True

        shared_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if shared_options is None:
            return False

        if not all([
            bool(shared_options.Following),
            bool(shared_options.Avoidance),
            bool(shared_options.Targeting),
            bool(shared_options.Combat),
        ]):
            return False

        return bool(shared_options.Looting) == expected_looting

    def EnsureHeroAIOptionsEnabled(self) -> bool:
        if self._heroai_options_match_runtime_policy():
            return True
        return self.RestoreHeroAIOptions()
