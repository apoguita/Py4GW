import sys
import argparse
import struct

from process import *
from datetime import datetime
from consts import *
from msgs import *
from hexdump import hexdump

def game_str_from_bytes(bytes):
    length = len(bytes) // 2
    codepoints = struct.unpack(f'<{length}H', bytes)
    try:
        idx = codepoints.index(0)
        return codepoints[:idx]
    except:
        return codepoints

def main(args):
    if (2 ** 32) < sys.maxsize:
        print('Use a 32 bits version of Python')
        sys.exit(1)

    proc, = GetProcesses(args.proc)
    scanner = ProcessScanner(proc)
    smsg_addr = scanner.find(b'\x50\x8B\x41\x08\xFF\xD0\x83\xC4\x08', 4)
    cmsg_addr = scanner.find(b'\xF7\xD8\xC7\x47\x54\x01\x00\x00\x00\x1B\xC0\x25', -0xBF)

    tmp = scanner.find(b'\x50\x6A\x0F\x6A\x00\xFF\x35', +7)
    base_addr, = proc.read(tmp)
    print(f'base_addr = 0x{base_addr:08X}')

    def get_game_ctx():
        tmp, = proc.read(base_addr)
        return proc.read(tmp + 24)[0]

    def get_agent_summary_info(agent_id):
        ctx = get_game_ctx()
        print(f'game ctx 0x{ctx:08X}')
        agent_ctx, = proc.read(ctx + 8)
        print(f'agent ctx 0x{agent_ctx:08X}')
        buf, cap, len, param = proc.read(agent_ctx + 0x98, 'IIII')
        print(f'buf = 0x{buf:08X}, cap = {cap}, len = {len}')
        return proc.read(buf + (12 * agent_id) + 8)[0]

    running = True
    def signal_handler(sig, frame):
        global running
        running = False

    @Hook.stdcall(LPVOID, DWORD, LPVOID)
    def on_send_packet(ctx, size, packet):
        header, = proc.read(packet, 'I')
        if header in game_cmsg_names:
            name = game_cmsg_names[header]
        else:
            name = "unknown"
        # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'SendPacket: {header}, 0x{header:X}, {name}')

        if header == 69:
            x, y, unk = proc.read(packet + 4, 'ffI')
            print(f'x = {x}, y = {y}, unk = {unk}')

    @Hook.rawcall
    def on_recv_packet(ctx):
        packet, = proc.read(ctx.Esp, 'I')
        header, = proc.read(packet, 'I')
        if header in game_smsg_names:
            name = game_smsg_names[header]
        else:
            name = "unknown"

        if name in ('GAME_SMSG_AGENT_MOVEMENT_TICK', 'GAME_SMSG_AGENT_UPDATE_DIRECTION', 'GAME_SMSG_AGENT_MOVE_TO_POINT', 'GAME_SMSG_AGENT_UPDATE_SPEED', 'GAME_SMSG_AGENT_UPDATE_ROTATION', 'GAME_SMSG_AGENT_ATTR_UPDATE_INT', 'GAME_SMSG_WORLD_SIMULATION_TICK'):
            return

        # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        print(f'RecvPacket ({ctx.Esi:X}): {header}, 0x{header:X}, {name}')

        if name == 'GAME_SMSG_AGENT_UPDATE_DIRECTION':
            # print(f'{now} RecvPacket ({ctx.Esi:X}): {header}, 0x{header:X}, {name}')
            agent_id, x, y, rotation = proc.read(packet + 4, 'IffI')
            print(f'>> agent_id = {agent_id}, x = {x}, y = {y}, rotation = {rotation}')

        if name == 'GAME_SMSG_AGENT_MOVE_TO_POINT':
            # print(f'{now} RecvPacket ({ctx.Esi:X}): {header}, 0x{header:X}, {name}')
            agent_id, x, y, plane, unk0 = proc.read(packet + 4, 'IffII')
            print(f'>> agent_id = {agent_id}, x = {x}, y = {y}, plane = {plane}, unk0 = {unk0}')

        if name == 'GAME_SMSG_AGENT_UPDATE_SPEED':
            # print(f'{now} RecvPacket ({ctx.Esi:X}): {header}, 0x{header:X}, {name}')
            agent_id, speed_modifier, unk0 = proc.read(packet + 4, 'IfI')
            print(f'>> agent_id = {agent_id}, speed_modifier = {speed_modifier}, unk0 = {unk0}')

        if name == 'GAME_SMSG_AGENT_UPDATE_ROTATION':
            agent_id, rotation, unk0 = proc.read(packet + 4, 'III')
            print(f'>> agent_id = {agent_id}, rotation = {rotation}, unk0 = {unk0}')

        if name == 'GAME_SMSG_AGENT_MOVEMENT_TICK':
            delta, = proc.read(packet + 4, 'I')
            print(f'>> delta = {delta}')

        if name == 'GAME_SMSG_UPDATE_AGENT_INT_PROPERTY':
            prop_id, agent_id, value = proc.read(packet + 4, 'III')
            print(f'>> prop_id = {prop_id}, agent_id = {agent_id}, value = {value}')

        if name == 'GAME_SMSG_UPDATE_PLAYER_AGENT':
            agent_id, unk0 = proc.read(packet + 4, 'II')
            print(f'>> agent_id = {agent_id}, unk0 = {unk0}') 

        """
        if name == 'GAME_SMSG_UPDATE_AGENT_FLOAT_PROPERTY':
            prop_id, agent_id, value = proc.read(packet + 4, 'IIf')
            print(f'>> prop_id = {prop_id}, agent_id = {agent_id}, value = {value}')

        if name == 'GAME_SMSG_AGENT_SPAWNED':
            data = proc.read(packet + 4, 'IIIIffIffIffIIIIIIIffffIIffI')
            agent_id = data[0]
            model_id = data[1]
            agent_type = data[2]
            h000B = data[3]
            pos_x = data[4]
            pos_y = data[5]
            plane = data[6]
            direction_x = data[7]
            direction_y = data[8]
            h001E = data[9]
            speed_base = data[10]
            h0023 = data[11]
            h0027 = data[12]
            model_type = data[13]
            h002F = data[14]
            h0033 = data[15]
            h0037 = data[16]
            h003B = data[17]
            h003F = data[18]
            h0043_x = data[19]
            h0043_y = data[20]
            h004B_x = data[21]
            h004B_y = data[22]
            h0053 = data[23]
            h0055 = data[24]
            h0059_x = data[25]
            h0059_y = data[26]
            h0061 = data[27]
            print(f'>> agent_id = {agent_id}, model_id = {model_id}, agent_type = {agent_type}, h000B = {h000B}, pos_x = {pos_x}, pos_y = {pos_y}, plane = {plane}, direction_x = {direction_x}, direction_y = {direction_y}, h001E = {h001E}, speed_base = {speed_base}, h0023 = {h0023}, h0027 = {h0027}, model_type = {model_type}, h002F = {h002F}, h0033 = {h0033}, h0037 = {h0037}, h003B = {h003B}, h003F = {h003F}, h0043_x = {h0043_x}, h0043_y = {h0043_y}, h004B_x = {h004B_x}, h004B_y = {h004B_y}, h0053 = {h0053}, h0055 = {h0055}, h0059_x = {h0059_x}, h0059_y = {h0059_y}, h0061 = {h0061}')

            ptr = get_agent_summary_info(agent_id)
            print(f'>>> summary info = {ptr}')

        if name == 'GAME_SMSG_UPDATE_CURRENT_MAP' and False:
            map_id, unk = proc.read(packet + 4, 'II')
            print(f'>> map_id = {map_id}, unk = {unk}')

        if name == 'GAME_SMSG_AGENT_SET_PLAYER' and False:
            agent_id, unk0 = proc.read(packet + 4, 'II')
            print(f'>> agent_id = {agent_id}, unk0 = {unk0}')

        if name == 'GAME_SMSG_INSTANCE_LOADED' and False:
            player_team_token = proc.read(packet + 4, 'I')
            print(f'>> player_team_token = {player_team_token}')
        """

        if name == 'GAME_SMSG_CREATE_NAMED_ITEM':
            item_id, file_id, item_type, dye_tint, dye_colors, materials, unk1, flags, value, model_id, quantity = proc.read(packet + 4, 'IIIIIIIIIII')
            print(f'>> item_id = {item_id}, file_id = 0x{file_id:X}, item_type = {item_type}, dye_tint = {dye_tint}, dye_colors = {dye_colors}, materials = {materials}, unk1 = {unk1}, flags = 0x{flags:X}, value = {value}, model_id = {model_id}, quantity = {quantity}')

        if name == 'GAME_SMSG_CREATE_UNNAMED_ITEM':
            item_id, file_id, item_type, dye_tint, dye_colors, unk5, unk6, flags, unk8 = proc.read(packet + 4, 'IIIIIIIII')
            print(f'>> item_id = {item_id}, file_id = 0x{file_id:X}, item_type = {item_type}, dye_tint = {dye_tint}, dye_colors = {dye_colors}, unk5 = {unk5}, unk6 = {unk6}, flags = 0x{flags:X}, unk8 = {unk8}')

        if name == 'GAME_SMSG_INVENTORY_CREATE_BAG':
            stream_id, bag_type, bag_model_id, bag_id, slot_count, assoc_item_id = proc.read(packet + 4, 'IIIIII')
            bag_type = bag_types[bag_type]
            bag_model_id = bag_model_ids[bag_model_id]
            print(f'>> stream_id = {stream_id}, bag_type = {bag_type}, bag_model_id = {bag_model_id}, bag_id = {bag_id}, slot_count = {slot_count}, assoc_item_id = {assoc_item_id}')

        if name == 'GAME_SMSG_ITEM_SET_PROFESSION':
            item_id, profession = proc.read(packet + 4, 'II')
            profession = professions[profession]
            print(f'>> item_id = {item_id}, profession = {profession}')

        if name == 'GAME_SMSG_ITEM_MOVED_TO_LOCATION':
            stream_id, item_id, bag_id, slot = proc.read(packet + 4, 'IIII')
            print(f'>> stream_id = {stream_id}, item_id = {item_id}, bag_id = {bag_id}, slot = {slot}')

        if name == 'GAME_SMSG_ITEM_CHANGE_LOCATION':
            stream_id, item_id, bag_id, slot = proc.read(packet + 4, 'IIII')
            print(f'>> stream_id = {stream_id}, item_id = {item_id}, bag_id = {bag_id}, slot = {slot}')

        if name == 'GAME_SMSG_ACCOUNT_FEATURE':
            feature_id, param1, param2 = proc.read(packet + 4, 'III')
            print(f'>> feature_id = {feature_id}, param1 = {param1}, param2 = {param2}')

        if name == 'GAME_SMSG_PLAYER_UPDATE_PROFESSION':
            agent_id, primary_profession, secondary_profession, is_pvp = proc.read(packet + 4, 'IIII')
            print(f'>> agent_id = {agent_id}, primary_profession = {primary_profession}, secondary_profession = {secondary_profession}, is_pvp = {is_pvp}')

        if name == 'GAME_SMSG_UPDATE_AGENT_VISUAL_EQUIPMENT':
            agent_id, weapon_item_id, offhand_item_id, body_item_id, boots_item_id, legs_item_id, gloves_item_id, head_item_id, costume_head_item_id, costume_body_item_id = proc.read(packet + 4, 'IIIIIIIIII')
            print(f'>> agent_id = {agent_id}, weapon_item_id = {weapon_item_id}, offhand_item_id = {offhand_item_id}, body_item_id = {body_item_id}, boots_item_id = {boots_item_id}, legs_item_id = {legs_item_id}, gloves_item_id = {gloves_item_id}, head_item_id = {head_item_id}, costume_head_item_id = {costume_head_item_id}, costume_body_item_id = {costume_body_item_id}')

        if name == 'GAME_SMSG_UPDATE_AGENT_PARTYSIZE':
            player_id, party_size = proc.read(packet + 4, 'II')
            print(f'>> player_id = {player_id}, party_size = {party_size}')

        if header == 176:
            a, b = proc.read(packet + 4, 'II')
            print(f'>> a = {a}, b = {b}')

    with ProcessDebugger(proc) as dbg:
        dbg.add_hook(smsg_addr, on_recv_packet)
        dbg.add_hook(cmsg_addr, on_send_packet)
        print(f'Start debugging process {proc.name}, {proc.id}')
        while running:
            dbg.poll(32)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Trace server and client messages', add_help=True)
    parser.add_argument("--proc", type=str, default='Gw.exe',
        help="Process name of the target Guild Wars instance.")
    args = parser.parse_args()
    main(args)
