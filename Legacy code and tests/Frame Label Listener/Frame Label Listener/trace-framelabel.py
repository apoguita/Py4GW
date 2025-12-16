import sys
import argparse

from process import *

def main(args):
    if (2 ** 32) < sys.maxsize:
        print('Use a 32 bits version of Python')
        sys.exit(1)

    proc, = GetProcesses(args.proc)
    scanner = ProcessScanner(proc)
    frame_create_addr = scanner.find(b'\x33\xd2\x89\x45\x08\xb9\xc8\x01\x00\x00', -0x27)
    
    print(f'frame_create_addr = 0x{frame_create_addr:08X}')

    running = True
    def signal_handler(sig, frame):
        global running
        running = False

    @Hook.rawcall
    def on_frame_creation(ctx):
        parent_frame_id = proc.read(ctx.Esp + 0x4, 'I')[0]
        child_offset = proc.read(ctx.Esp + 0xC, 'I')[0]
        addr, = proc.read(ctx.Esp + 0x18, 'I')
        label = proc.read_wstring(addr)

        if label == '':
            return

        print(f'Parent Frame id = {parent_frame_id}, child Offset = {child_offset}, Label = {label}')

    with ProcessDebugger(proc) as dbg:
        dbg.add_hook(frame_create_addr, on_frame_creation)
        print(f'Start debugging process {proc.name}, {proc.id}')
        while running:
            dbg.poll(10)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Trace frame label name', add_help=True)
    parser.add_argument("--proc", type=str, default='Gw.exe',
        help="Process name of the target Guild Wars instance.")
    args = parser.parse_args()
    main(args)



