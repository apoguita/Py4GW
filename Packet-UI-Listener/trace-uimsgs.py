import sys
import argparse

from process import *
from uimsgs import *

def main(args):
    if (2 ** 32) < sys.maxsize:
        print('Use a 32 bits version of Python')
        sys.exit(1)

    proc, = GetProcesses(args.proc)
    scanner = ProcessScanner(proc)
    uimsg_addr = scanner.find(b'\x89\x45\xF8\x8B\x45\x2C', +0x2E)
    print(f'cmsg_addr = 0x{uimsg_addr:08X}')

    running = True
    def signal_handler(sig, frame):
        global running
        running = False

    @Hook.rawcall
    def on_send_uimessage(ctx):
        packet, = proc.read(ctx.Esp + 0x4, 'I')
        arg, = proc.read(ctx.Esp + 0x8, 'I')

        if packet in ui_msgs_names:
            ui_msg = ui_msgs_names[packet]
            output = f"{ui_msg['name']} = "

            if 'wparam' in ui_msg:
                wparam_data = {}
                offset = 0x0
                for key in ui_msg['wparam'].keys():
                    try:
                        value, = proc.read(arg + offset, 'I')
                    except:
                        value = arg
                    wparam_data[key] = f"0x{value:x}"
                    offset += 0x4

                output += f"{wparam_data}"
            else:
                output += "{}"
            print(output)
        else:
            name = 'unknown'
            print(f"0x{packet:x} = 0x{arg:x}")

    with ProcessDebugger(proc) as dbg:
        dbg.add_hook(uimsg_addr, on_send_uimessage)
        print(f'Start debugging process {proc.name}, {proc.id}')
        while running:
            dbg.poll(32)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Trace UI messages', add_help=True)
    parser.add_argument("--proc", type=str, default='Gw.exe',
        help="Process name of the target Guild Wars instance.")
    args = parser.parse_args()
    main(args)
