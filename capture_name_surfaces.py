from __future__ import annotations

from collections import defaultdict
from typing import Any
from typing import Iterable

import Py4GW
import PyImGui

from Py4GWCoreLib.Context import GWContext
from Py4GWCoreLib.PacketSniffer import SNIFFER as PACKET_SNIFFER


MODULE_NAME = 'Name Surface Capture'

SCENARIOS: dict[str, dict[str, Any]] = {
    'guild': {
        'label': 'Guild',
        'focus': 'guild roster, guild table, and load-time name-bearing packets',
        'instructions': 'Guild surfaces populate during map load. Start capture before travel, travel, wait for load completion, then dump the load-time replay window.',
        'interesting_stoc': {
            0x0031,  # CHARACTER_UPDATE_NAME
            0x0118,  # GUILD_PLAYER_ROLE
            0x0120,  # GUILD_ALLIANCE_INFO
            0x0121,  # GUILD_GENERAL_INFO
            0x0127,  # GUILD_PLAYER_INFO
            0x0128,  # GUILD_PLAYER_REMOVE
            0x012A,  # GUILD_PLAYER_CHANGE_COMPLETE
            0x012B,  # GUILD_CHANGE_PLAYER_CONTEXT
            0x012C,  # GUILD_CHANGE_PLAYER_STATUS
            0x012D,  # GUILD_CHANGE_PLAYER_TYPE
            0x017D,  # INSTANCE_LOAD_PLAYER_NAME
        },
        'interesting_ctos': set(),
        'after_label': 'guild_load_complete',
    },
    'friends': {
        'label': 'Friends',
        'focus': 'friends table and load-time name-bearing packets',
        'instructions': 'Friends surfaces populate during map load. Start capture before travel, travel, wait for load completion, then dump the load-time replay window.',
        'interesting_stoc': {
            0x000E,  # FRIENDLIST_MESSAGE
            0x0031,  # CHARACTER_UPDATE_NAME
            0x005D,  # CHAT_MESSAGE_CORE
            0x005E,  # CHAT_MESSAGE_SERVER
            0x0060,  # CHAT_MESSAGE_GLOBAL
            0x0061,  # CHAT_MESSAGE_LOCAL
            0x017D,  # INSTANCE_LOAD_PLAYER_NAME
        },
        'interesting_ctos': set(),
        'after_label': 'friends_load_complete',
    },
    'call_target': {
        'label': 'Call Target',
        'focus': 'manual target-call action and resulting visible announcement packets',
        'instructions': 'Call target is interaction-time. Travel if needed for fresh name replay, then baseline after load and capture one manual call-target action.',
        'interesting_stoc': {
            0x0034,  # AGENT_PINGED
            0x005D,  # CHAT_MESSAGE_CORE
            0x005E,  # CHAT_MESSAGE_SERVER
            0x0060,  # CHAT_MESSAGE_GLOBAL
            0x0061,  # CHAT_MESSAGE_LOCAL
            0x017D,  # INSTANCE_LOAD_PLAYER_NAME
        },
        'interesting_ctos': {
            0x0039,  # INTERACT_LIVING (observed during manual call-target tests on this build)
        },
        'after_label': 'after_call_target',
    },
}

SCENARIO_KEYS = ('guild',)
_selected_scenario = 'guild'
_probe_name = ''


class ObservedNameRecord:
    __slots__ = ('player_number', 'agent_id', 'real_name', 'display_name', 'aliased')

    def __init__(self, player_number: int, agent_id: int, real_name: str, display_name: str, aliased: bool) -> None:
        self.player_number = player_number
        self.agent_id = agent_id
        self.real_name = real_name
        self.display_name = display_name
        self.aliased = aliased


class PacketRecord:
    __slots__ = ('direction', 'tick', 'header', 'size', 'raw')

    def __init__(self, direction: str, tick: int, header: int, size: int, raw: bytes) -> None:
        self.direction = direction
        self.tick = tick
        self.header = header
        self.size = size
        self.raw = raw


class CaptureMarker:
    __slots__ = ('tick', 'label', 'stoc_index', 'ctos_index')

    def __init__(self, tick: int, label: str, stoc_index: int, ctos_index: int) -> None:
        self.tick = tick
        self.label = label
        self.stoc_index = stoc_index
        self.ctos_index = ctos_index


class SurfaceCapture:
    def __init__(
        self,
        module_name: str,
        interesting_stoc: Iterable[int] | None = (),
        interesting_ctos: Iterable[int] | None = (),
    ) -> None:
        self.module_name = module_name
        self.interesting_stoc = None if interesting_stoc is None else set(int(value) for value in interesting_stoc)
        self.interesting_ctos = None if interesting_ctos is None else set(int(value) for value in interesting_ctos)
        self._scenario_key = 'guild'
        self._scenario_label = 'Guild'
        self._scenario_focus = 'guild roster, guild table, and load-time name-bearing packets'
        self._capturing = False
        self._status = 'Idle'
        self._stoc_packets: list[PacketRecord] = []
        self._ctos_packets: list[PacketRecord] = []
        self._markers: list[CaptureMarker] = []
        self._baseline_stoc_index = 0
        self._baseline_ctos_index = 0

    def configure(
        self,
        interesting_stoc: Iterable[int] | None,
        interesting_ctos: Iterable[int] | None,
        scenario_key: str,
        scenario_label: str,
        scenario_focus: str,
    ) -> None:
        self.interesting_stoc = None if interesting_stoc is None else set(int(value) for value in interesting_stoc)
        self.interesting_ctos = None if interesting_ctos is None else set(int(value) for value in interesting_ctos)
        self._scenario_key = scenario_key
        self._scenario_label = scenario_label
        self._scenario_focus = scenario_focus

    @property
    def capturing(self) -> bool:
        return self._capturing

    @property
    def status(self) -> str:
        return self._status

    @property
    def stoc_count(self) -> int:
        return len(self._stoc_packets)

    @property
    def ctos_count(self) -> int:
        return len(self._ctos_packets)

    @property
    def markers(self) -> list[CaptureMarker]:
        return list(self._markers)

    def start(self) -> bool:
        self._stoc_packets.clear()
        self._ctos_packets.clear()
        self._markers.clear()
        self._baseline_stoc_index = 0
        self._baseline_ctos_index = 0
        PACKET_SNIFFER.clear_logs()

        started = PACKET_SNIFFER.initialize()
        if not started:
            self._status = 'Start failed: unified PacketSniffer initialization returned False'
            self._log(self._status, Py4GW.Console.MessageType.Error)
            PACKET_SNIFFER.terminate()
            return False

        self._capturing = True
        self._status = 'Capturing'
        self.reset_baseline('capture_start')
        self._log(
            f'Capture started. focus={self._scenario_focus} stoc_filter={self._format_header_filter(self.interesting_stoc)} '
            f'ctos_filter={self._format_header_filter(self.interesting_ctos)}',
            Py4GW.Console.MessageType.Success,
        )
        return True

    def stop(self) -> None:
        self.drain()
        PACKET_SNIFFER.terminate()
        self._capturing = False
        self._status = f'Stopped. StoC={len(self._stoc_packets)} CToS={len(self._ctos_packets)}'
        self._log(self._status, Py4GW.Console.MessageType.Info)

    def drain(self) -> None:
        logs = PACKET_SNIFFER.get_logs()
        for entry in logs:
            packet = PacketRecord(
                direction=entry.direction,
                tick=int(entry.tick),
                header=int(entry.header),
                size=int(entry.size),
                raw=bytes(entry.data),
            )
            if entry.direction == 'StoC':
                self._stoc_packets.append(packet)
            else:
                self._ctos_packets.append(packet)
        if logs:
            PACKET_SNIFFER.clear_logs()

    def mark(self, label: str) -> None:
        self.drain()
        marker = CaptureMarker(
            tick=int(Py4GW.Game.get_tick_count64()),
            label=label,
            stoc_index=len(self._stoc_packets),
            ctos_index=len(self._ctos_packets),
        )
        self._markers.append(marker)
        self._log(
            f"Marker '{label}' at StoC={marker.stoc_index} CToS={marker.ctos_index}",
            Py4GW.Console.MessageType.Notice,
        )

    def reset_baseline(self, label: str = 'baseline') -> None:
        self.drain()
        self._baseline_stoc_index = len(self._stoc_packets)
        self._baseline_ctos_index = len(self._ctos_packets)
        self._markers.clear()
        self._log(
            f"Baseline '{label}' set at StoC={self._baseline_stoc_index} CToS={self._baseline_ctos_index}",
            Py4GW.Console.MessageType.Notice,
        )

    def dump_summary(self) -> None:
        self._log(
            f'Capture summary: focus={self._scenario_focus} StoC={len(self._stoc_packets)} CToS={len(self._ctos_packets)} '
            f'markers={len(self._markers)} baseline=({self._baseline_stoc_index},{self._baseline_ctos_index})',
            Py4GW.Console.MessageType.Info,
        )
        for marker in self._markers:
            self._log(
                f"[marker] {marker.label} tick={marker.tick} stoc_index={marker.stoc_index} ctos_index={marker.ctos_index}",
                Py4GW.Console.MessageType.Info,
            )

    def dump_interesting(self) -> None:
        self.dump_summary()
        for index, packet in enumerate(self._stoc_packets):
            if self.interesting_stoc is not None and packet.header not in self.interesting_stoc:
                continue
            self._log_packet(index, packet)
        for index, packet in enumerate(self._ctos_packets):
            if self.interesting_ctos is not None and packet.header not in self.interesting_ctos:
                continue
            self._log_packet(index, packet)

    def dump_since_baseline(self) -> None:
        self.dump_summary()
        for index in range(self._baseline_stoc_index, len(self._stoc_packets)):
            packet = self._stoc_packets[index]
            if self.interesting_stoc is not None and packet.header not in self.interesting_stoc:
                continue
            self._log_packet(index, packet)
        for index in range(self._baseline_ctos_index, len(self._ctos_packets)):
            packet = self._ctos_packets[index]
            if self.interesting_ctos is not None and packet.header not in self.interesting_ctos:
                continue
            self._log_packet(index, packet)

    def dump_between_last_two_markers(self) -> None:
        self.dump_summary()
        if len(self._markers) < 2:
            self._log('Need at least two markers to dump a phase window.', Py4GW.Console.MessageType.Warning)
            return
        start_marker = self._markers[-2]
        end_marker = self._markers[-1]
        for index in range(start_marker.stoc_index, min(end_marker.stoc_index, len(self._stoc_packets))):
            packet = self._stoc_packets[index]
            if self.interesting_stoc is not None and packet.header not in self.interesting_stoc:
                continue
            self._log_packet(index, packet)
        for index in range(start_marker.ctos_index, min(end_marker.ctos_index, len(self._ctos_packets))):
            packet = self._ctos_packets[index]
            if self.interesting_ctos is not None and packet.header not in self.interesting_ctos:
                continue
            self._log_packet(index, packet)

    def dump_recent(self, stoc_count: int = 40, ctos_count: int = 20) -> None:
        self.dump_summary()
        for index, packet in enumerate(self._stoc_packets[-max(0, stoc_count):], start=max(0, len(self._stoc_packets) - stoc_count)):
            self._log_packet(index, packet)
        for index, packet in enumerate(self._ctos_packets[-max(0, ctos_count):], start=max(0, len(self._ctos_packets) - ctos_count)):
            self._log_packet(index, packet)

    def dump_header_summary_since_baseline(self) -> None:
        self.dump_summary()
        self._dump_header_summary(
            'StoC',
            self._stoc_packets[self._baseline_stoc_index:],
            self.interesting_stoc,
        )
        self._dump_header_summary(
            'CToS',
            self._ctos_packets[self._baseline_ctos_index:],
            self.interesting_ctos,
        )

    def dump_header_summary_between_last_two_markers(self) -> None:
        self.dump_summary()
        if len(self._markers) == 1:
            self._log(
                'Using baseline -> latest marker as the phase window.',
                Py4GW.Console.MessageType.Notice,
            )
            end_marker = self._markers[-1]
            self._dump_header_summary(
                'StoC',
                self._stoc_packets[self._baseline_stoc_index:end_marker.stoc_index],
                self.interesting_stoc,
            )
            self._dump_header_summary(
                'CToS',
                self._ctos_packets[self._baseline_ctos_index:end_marker.ctos_index],
                self.interesting_ctos,
            )
            return
        if len(self._markers) < 2:
            self._log(
                'No complete phase markers found. Falling back to summary since baseline.',
                Py4GW.Console.MessageType.Warning,
            )
            self.dump_header_summary_since_baseline()
            return
        start_marker = self._markers[-2]
        end_marker = self._markers[-1]
        self._dump_header_summary(
            'StoC',
            self._stoc_packets[start_marker.stoc_index:end_marker.stoc_index],
            self.interesting_stoc,
        )
        self._dump_header_summary(
            'CToS',
            self._ctos_packets[start_marker.ctos_index:end_marker.ctos_index],
            self.interesting_ctos,
        )

    def dump_unique_payloads_since_baseline(self, max_per_header: int = 4) -> None:
        self.dump_summary()
        self._dump_unique_payloads(
            'StoC',
            self._stoc_packets[self._baseline_stoc_index:],
            self.interesting_stoc,
            max_per_header=max_per_header,
        )
        self._dump_unique_payloads(
            'CToS',
            self._ctos_packets[self._baseline_ctos_index:],
            self.interesting_ctos,
            max_per_header=max_per_header,
        )

    def dump_unique_payloads_between_last_two_markers(self, max_per_header: int = 4) -> None:
        self.dump_summary()
        if len(self._markers) == 1:
            self._log(
                'Using baseline -> latest marker as the phase window.',
                Py4GW.Console.MessageType.Notice,
            )
            end_marker = self._markers[-1]
            self._dump_unique_payloads(
                'StoC',
                self._stoc_packets[self._baseline_stoc_index:end_marker.stoc_index],
                self.interesting_stoc,
                max_per_header=max_per_header,
            )
            self._dump_unique_payloads(
                'CToS',
                self._ctos_packets[self._baseline_ctos_index:end_marker.ctos_index],
                self.interesting_ctos,
                max_per_header=max_per_header,
            )
            return
        if len(self._markers) < 2:
            self._log(
                'No complete phase markers found. Falling back to payload grouping since baseline.',
                Py4GW.Console.MessageType.Warning,
            )
            self.dump_unique_payloads_since_baseline(max_per_header=max_per_header)
            return
        start_marker = self._markers[-2]
        end_marker = self._markers[-1]
        self._dump_unique_payloads(
            'StoC',
            self._stoc_packets[start_marker.stoc_index:end_marker.stoc_index],
            self.interesting_stoc,
            max_per_header=max_per_header,
        )
        self._dump_unique_payloads(
            'CToS',
            self._ctos_packets[start_marker.ctos_index:end_marker.ctos_index],
            self.interesting_ctos,
            max_per_header=max_per_header,
        )

    def dump_window_around_last_marker(self, before: int = 10, after: int = 20) -> None:
        self.dump_summary()
        if not self._markers:
            self._log(
                'No markers recorded. Falling back to recent filtered packets since baseline.',
                Py4GW.Console.MessageType.Warning,
            )
            self.dump_since_baseline()
            return
        marker = self._markers[-1]
        if len(self._markers) == 1:
            self._log(
                'Using baseline -> latest marker packet window.',
                Py4GW.Console.MessageType.Notice,
            )
            for index in range(self._baseline_stoc_index, min(marker.stoc_index, len(self._stoc_packets))):
                packet = self._stoc_packets[index]
                if self.interesting_stoc is not None and packet.header not in self.interesting_stoc:
                    continue
                self._log_packet(index, packet)
            for index in range(self._baseline_ctos_index, min(marker.ctos_index, len(self._ctos_packets))):
                packet = self._ctos_packets[index]
                if self.interesting_ctos is not None and packet.header not in self.interesting_ctos:
                    continue
                self._log_packet(index, packet)
            if self._scenario_key == 'guild':
                self.dump_guild_runtime_snapshot()
            return
        self._dump_window('StoC', self._stoc_packets, marker.stoc_index, before, after)
        self._dump_window('CToS', self._ctos_packets, marker.ctos_index, before, after)
        if self._scenario_key == 'guild':
            self.dump_guild_runtime_snapshot()

    def dump_guild_runtime_snapshot(self) -> None:
        if self._scenario_key != 'guild':
            return
        guild_ctx = GWContext.Guild.GetContext()
        if not guild_ctx:
            self._log('Guild runtime snapshot: GuildContext is unavailable.', Py4GW.Console.MessageType.Warning)
            return
        self._log(
            f'Guild runtime snapshot: player_name={guild_ctx.player_name_str!r} '
            f'player_guild_index={int(guild_ctx.player_guild_index)} '
            f'player_guild_rank={int(guild_ctx.player_guild_rank)}',
            Py4GW.Console.MessageType.Notice,
        )
        guilds = guild_ctx.guild_array or []
        self._log(f'Guild runtime snapshot: guild_count={len(guilds)}', Py4GW.Console.MessageType.Notice)
        for index, guild in enumerate(guilds):
            self._log(
                f"[guild {index}] index={int(guild.index)} features=0x{int(guild.features):08X} "
                f"name={guild.name_str!r} tag={guild.tag_str!r}",
                Py4GW.Console.MessageType.Info,
            )
        roster = guild_ctx.player_roster or []
        self._log(f'Guild runtime snapshot: roster_count={len(roster)}', Py4GW.Console.MessageType.Notice)
        for index, member in enumerate(roster):
            self._log(
                f"[roster {index}] name_ptr={member.name_str!r} invited_name={member.invited_name_str!r} "
                f"current_name={member.current_name_str!r} inviter_name={member.inviter_name_str!r} "
                f"promoter_name={member.promoter_name_str!r} offline={int(member.offline)} "
                f"status={int(member.status)} member_type={int(member.member_type)}",
                Py4GW.Console.MessageType.Info,
            )

    def _dump_window(self, direction: str, packets: list[PacketRecord], center: int, before: int, after: int) -> None:
        start = max(0, center - max(0, before))
        end = min(len(packets), center + max(0, after))
        for index in range(start, end):
            self._log_packet(index, packets[index], direction_override=direction)

    def _dump_header_summary(
        self,
        direction: str,
        packets: list[PacketRecord],
        interesting_headers: set[int] | None,
    ) -> None:
        all_grouped: dict[int, list[PacketRecord]] = defaultdict(list)
        grouped: dict[int, list[PacketRecord]] = defaultdict(list)
        for packet in packets:
            all_grouped[packet.header].append(packet)
            if interesting_headers is not None and packet.header not in interesting_headers:
                continue
            grouped[packet.header].append(packet)
        if not grouped:
            self._log(f'[{direction}] No packets matched the current filter.', Py4GW.Console.MessageType.Warning)
            self._log_missing_focus_diagnosis(direction, all_grouped)
            self._log_unfiltered_header_summary(direction, all_grouped)
            return
        self._log(
            f'[{direction}] analyzing {self._scenario_label.lower()} focus={self._scenario_focus} '
            f'headers={self._format_header_filter(interesting_headers)}',
            Py4GW.Console.MessageType.Notice,
        )
        self._log_present_focus_diagnosis(direction, grouped)
        for header, header_packets in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
            sizes = sorted({packet.size for packet in header_packets})
            unique_payloads = len({packet.raw for packet in header_packets})
            sample = header_packets[0]
            name = PACKET_SNIFFER.get_packet_name(direction, header)
            self._log(
                f'[{direction}] summary {name} header=0x{header:04X} count={len(header_packets)} '
                f'unique_payloads={unique_payloads} sizes={sizes} first_tick={header_packets[0].tick} '
                f'last_tick={header_packets[-1].tick} sample={self._short_hex(sample.raw)}',
                Py4GW.Console.MessageType.Info,
            )

    def _dump_unique_payloads(
        self,
        direction: str,
        packets: list[PacketRecord],
        interesting_headers: set[int] | None,
        max_per_header: int,
    ) -> None:
        all_headers: dict[int, dict[bytes, list[PacketRecord]]] = defaultdict(lambda: defaultdict(list))
        headers: dict[int, dict[bytes, list[PacketRecord]]] = defaultdict(lambda: defaultdict(list))
        for packet in packets:
            all_headers[packet.header][packet.raw].append(packet)
            if interesting_headers is not None and packet.header not in interesting_headers:
                continue
            headers[packet.header][packet.raw].append(packet)
        if not headers:
            self._log(f'[{direction}] No packets matched the current filter.', Py4GW.Console.MessageType.Warning)
            flattened_groups: dict[int, list[PacketRecord]] = defaultdict(list)
            for header, payload_groups in all_headers.items():
                for packet_group in payload_groups.values():
                    flattened_groups[header].extend(packet_group)
            self._log_missing_focus_diagnosis(direction, flattened_groups)
            self._log_unfiltered_payload_groups(direction, all_headers, max_headers=6)
            return
        self._log(
            f'[{direction}] grouping payloads for {self._scenario_label.lower()} focus={self._scenario_focus} '
            f'headers={self._format_header_filter(interesting_headers)}',
            Py4GW.Console.MessageType.Notice,
        )
        for header in sorted(headers):
            payload_groups = headers[header]
            name = PACKET_SNIFFER.get_packet_name(direction, header)
            self._log(
                f'[{direction}] unique payloads {name} header=0x{header:04X} groups={len(payload_groups)}',
                Py4GW.Console.MessageType.Notice,
            )
            ranked_groups = sorted(payload_groups.items(), key=lambda item: (-len(item[1]), item[0]))
            omitted = max(0, len(ranked_groups) - max_per_header)
            for raw, group_packets in ranked_groups[:max_per_header]:
                sample = group_packets[0]
                decoded = PACKET_SNIFFER.decode_packet(direction, sample.header, sample.size, sample.raw)
                self._log(
                    f'[{direction}]   group count={len(group_packets)} size={sample.size} '
                    f'ticks={group_packets[0].tick}->{group_packets[-1].tick} '
                    f'decoded={decoded} raw={self._hex_dump(raw)}',
                    Py4GW.Console.MessageType.Info,
                )
            if omitted:
                self._log(
                    f'[{direction}]   ... omitted_groups={omitted}',
                    Py4GW.Console.MessageType.Info,
                )

    def _log_unfiltered_header_summary(
        self,
        direction: str,
        grouped: dict[int, list[PacketRecord]],
        max_headers: int = 8,
    ) -> None:
        if not grouped:
            self._log(f'[{direction}] No packets were captured in this window.', Py4GW.Console.MessageType.Warning)
            return
        self._log(
            f'[{direction}] unfiltered fallback summary for {self._scenario_label.lower()} '
            f'(showing top {max_headers} headers seen in this window)',
            Py4GW.Console.MessageType.Notice,
        )
        for header, header_packets in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))[:max_headers]:
            name = PACKET_SNIFFER.get_packet_name(direction, header)
            sizes = sorted({packet.size for packet in header_packets})
            self._log(
                f'[{direction}] fallback {name} header=0x{header:04X} count={len(header_packets)} sizes={sizes} '
                f'sample={self._short_hex(header_packets[0].raw)}',
                Py4GW.Console.MessageType.Info,
            )

    def _log_unfiltered_payload_groups(
        self,
        direction: str,
        grouped: dict[int, dict[bytes, list[PacketRecord]]],
        max_headers: int = 6,
    ) -> None:
        if not grouped:
            self._log(f'[{direction}] No packets were captured in this window.', Py4GW.Console.MessageType.Warning)
            return
        self._log(
            f'[{direction}] unfiltered fallback payload groups for {self._scenario_label.lower()} '
            f'(showing top {max_headers} headers seen in this window)',
            Py4GW.Console.MessageType.Notice,
        )
        ranked_headers = sorted(grouped.items(), key=lambda item: (-sum(len(v) for v in item[1].values()), item[0]))
        for header, payload_groups in ranked_headers[:max_headers]:
            name = PACKET_SNIFFER.get_packet_name(direction, header)
            self._log(
                f'[{direction}] fallback groups {name} header=0x{header:04X} groups={len(payload_groups)}',
                Py4GW.Console.MessageType.Info,
            )
            best_raw, best_packets = sorted(payload_groups.items(), key=lambda item: (-len(item[1]), item[0]))[0]
            sample = best_packets[0]
            decoded = PACKET_SNIFFER.decode_packet(direction, sample.header, sample.size, sample.raw)
            self._log(
                f'[{direction}]   sample count={len(best_packets)} size={sample.size} decoded={decoded} raw={self._hex_dump(best_raw)}',
                Py4GW.Console.MessageType.Info,
            )

    def _log_missing_focus_diagnosis(
        self,
        direction: str,
        grouped: dict[int, list[PacketRecord]],
    ) -> None:
        if direction != 'StoC':
            return
        if self._scenario_key == 'guild':
            seen_headers = set(grouped)
            noise_headers = {0x001E, 0x0020, 0x0021, 0x0025, 0x0029, 0x002B, 0x005D, 0x0061}
            if seen_headers and seen_headers.issubset(noise_headers):
                self._log(
                    'Guild diagnosis: this window did not include guild load-time replay. '
                    'Only tick/movement/chat noise was captured, so guild roster/table packets were not observed. '
                    'Start capture before travel and keep it running through arrival/load completion.',
                    Py4GW.Console.MessageType.Warning,
                )
        elif self._scenario_key == 'call_target':
            self._log(
                'Call-target diagnosis: the current StoC focus headers were not observed in this window. '
                'If the action definitely happened, the announcement path may use different opcodes on this build.',
                Py4GW.Console.MessageType.Warning,
            )

    def _log_present_focus_diagnosis(
        self,
        direction: str,
        grouped: dict[int, list[PacketRecord]],
    ) -> None:
        if direction != 'StoC':
            return
        seen_headers = set(grouped)
        if self._scenario_key == 'guild':
            identity_headers = {0x0118, 0x0120, 0x0121}
            roster_headers = {0x0127, 0x0128, 0x012A, 0x012B, 0x012C, 0x012D}
            load_headers = {0x0031, 0x017D}
            if seen_headers & identity_headers and not (seen_headers & roster_headers):
                extras = []
                if seen_headers & load_headers:
                    extras.append('general load-name replay also present')
                extra_text = f" ({', '.join(extras)})" if extras else ''
                self._log(
                    'Guild diagnosis: guild identity traffic is present, but guild roster member packets were not observed'
                    f'{extra_text}. This window looks like guild-table/bootstrap data, not full member-table population.',
                    Py4GW.Console.MessageType.Warning,
                )

    def _log_packet(self, index: int, packet: PacketRecord, direction_override: str | None = None) -> None:
        direction = direction_override or packet.direction
        name = PACKET_SNIFFER.get_packet_name(direction, packet.header)
        decoded = PACKET_SNIFFER.decode_packet(direction, packet.header, packet.size, packet.raw)
        self._log(
            f'[{direction} #{index}] {name} tick={packet.tick} size={packet.size} copied={len(packet.raw)} decoded={decoded} raw={self._hex_dump(packet.raw)}',
            Py4GW.Console.MessageType.Info,
        )

    @staticmethod
    def _hex_dump(raw: bytes) -> str:
        return raw.hex(' ')

    @staticmethod
    def _short_hex(raw: bytes, limit: int = 24) -> str:
        if len(raw) <= limit:
            return raw.hex(' ')
        return raw[:limit].hex(' ') + ' ...'

    def _log(self, message: str, message_type: object) -> None:
        Py4GW.Console.Log(
            self.module_name,
            f'[scenario={self._scenario_key}:{self._scenario_label}] {message}',
            message_type,
        )

    @staticmethod
    def _format_header_filter(headers: set[int] | None) -> str:
        if headers is None:
            return 'all'
        if not headers:
            return 'none'
        return ','.join(f'0x{header:04X}' for header in sorted(headers))


def _module() -> Any:
    import PyNameObfuscator  # type: ignore[import-not-found]

    return PyNameObfuscator


def get_alias_map() -> dict[str, str]:
    module = _module()
    raw = module.get_aliases()
    if isinstance(raw, dict):
        return {str(key): str(value) for key, value in raw.items()}
    if isinstance(raw, list):
        out: dict[str, str] = {}
        for pair in raw:
            if isinstance(pair, tuple) and len(pair) == 2:
                out[str(pair[0])] = str(pair[1])
        return out
    return {}


def get_observed_records() -> list[ObservedNameRecord]:
    module = _module()
    players = module.get_observed_players()
    out: list[ObservedNameRecord] = []
    for player in players:
        out.append(
            ObservedNameRecord(
                player_number=int(getattr(player, 'player_number', 0)),
                agent_id=int(getattr(player, 'agent_id', 0)),
                real_name=str(getattr(player, 'real_name', '')),
                display_name=str(getattr(player, 'display_name', '')),
                aliased=bool(getattr(player, 'aliased', False)),
            )
        )
    return out


def get_real_name(display_name: str) -> str | None:
    for record in reversed(get_observed_records()):
        if record.display_name == display_name:
            return record.real_name
    alias_map = get_alias_map()
    for real_name, fake_name in alias_map.items():
        if fake_name == display_name:
            return real_name
    return None


def get_display_name(real_name: str) -> str:
    alias_map = get_alias_map()
    return alias_map.get(real_name, real_name)


def require_real_name(name: str) -> str:
    return get_real_name(name) or name


def _dump_observed() -> None:
    rows = get_observed_records()
    print(f'[{MODULE_NAME}] observed_count={len(rows)}')
    for index, row in enumerate(rows):
        print(
            f'[{MODULE_NAME}] observed[{index}] '
            f'player_number={row.player_number} agent_id={row.agent_id} '
            f"real_name={row.real_name!r} display_name={row.display_name!r} aliased={row.aliased}"
        )


_capture = SurfaceCapture(MODULE_NAME, interesting_stoc=SCENARIOS[_selected_scenario]['interesting_stoc'], interesting_ctos=SCENARIOS[_selected_scenario]['interesting_ctos'])


def _apply_scenario(scenario_key: str) -> None:
    scenario = SCENARIOS[scenario_key]
    _capture.configure(
        interesting_stoc=scenario['interesting_stoc'],
        interesting_ctos=scenario['interesting_ctos'],
        scenario_key=scenario_key,
        scenario_label=scenario['label'],
        scenario_focus=scenario['focus'],
    )


_apply_scenario(_selected_scenario)


def draw_window() -> None:
    global _selected_scenario, _probe_name

    PyImGui.set_next_window_size((760, 360), PyImGui.ImGuiCond.FirstUseEver)
    if PyImGui.begin(MODULE_NAME):
        if _capture.capturing:
            _capture.drain()

        PyImGui.text('Focused capture tool for guild load-time packet investigation.')
        scenario = SCENARIOS[_selected_scenario]
        PyImGui.text(f"Scenario: {scenario['label']}")
        PyImGui.text_wrapped(scenario['instructions'])
        PyImGui.text_wrapped('Workflow: start capture before travel, travel into the map, wait for roster/name replay to settle, mark complete, then analyze the load window.')
        PyImGui.separator()

        if not _capture.capturing:
            if PyImGui.button('Start Capture'):
                _capture.start()
        else:
            if PyImGui.button('Stop Capture'):
                _capture.stop()

        PyImGui.same_line(0, -1)
        if PyImGui.button('Reset Baseline'):
            _capture.reset_baseline('manual_reset')

        PyImGui.same_line(0, -1)
        if PyImGui.button('Mark Complete'):
            _capture.mark(scenario['after_label'])

        if PyImGui.button('Analyze Last Phase'):
            _capture.dump_header_summary_between_last_two_markers()
            _capture.dump_unique_payloads_between_last_two_markers()
            before = 12 if _selected_scenario == 'call_target' else 10
            after = 30 if _selected_scenario == 'call_target' else 20
            _capture.dump_window_around_last_marker(before=before, after=after)

        PyImGui.separator()
        PyImGui.text(f'Status: {_capture.status}')
        PyImGui.text(f'StoC packets: {_capture.stoc_count}')
        PyImGui.text(f'CToS packets: {_capture.ctos_count}')
        PyImGui.text(f'Markers: {len(_capture.markers)}')
    PyImGui.end()


def main() -> None:
    draw_window()
