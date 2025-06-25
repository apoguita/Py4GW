import time
import random
import traceback
from multiprocessing import Process, current_process
from shared_state_ctypes import SharedState

TEST_SHM_NAME = "stress_test_shm"

def writer_process(id):
    ss = SharedState(name=TEST_SHM_NAME)
    try:
        for _ in range(100):
            op = random.choice(["model", "choice", "position"])
            if op == "model":
                mid = random.randint(1000, 9999)
                ss.set_model_id(mid)
                print(f"[Writer {id}] Set model_id = {mid}")
            elif op == "choice":
                choice = random.randint(1, 5)
                ss.set_choice(choice)
                print(f"[Writer {id}] Set choice = {choice}")
            else:
                x = random.uniform(0, 1000)
                y = random.uniform(0, 1000)
                ss.set_position(x, y)
                print(f"[Writer {id}] Set position = ({x:.2f}, {y:.2f})")
            time.sleep(random.uniform(0.01, 0.1))
    except Exception as e:
        print(f"[Writer {id}] ERROR: {e}")
        traceback.print_exc()


def reader_process(id):
    ss = SharedState(name=TEST_SHM_NAME)
    try:
        last_ts = 0.0
        for _ in range(200):
            mid = ss.get_model_id()
            choice = ss.get_choice()
            x, y, ts = ss.get_position()

            # Validate monotonic timestamp
            if ts < last_ts:
                print(f"[Reader {id}] ERROR: Timestamp went backwards! {ts:.3f} < {last_ts:.3f}")
            last_ts = ts

            print(f"[Reader {id}] Read model_id={mid}, choice={choice}, pos=({x:.1f},{y:.1f}), ts={ts:.2f}")
            time.sleep(random.uniform(0.01, 0.05))
    except Exception as e:
        print(f"[Reader {id}] ERROR: {e}")
        traceback.print_exc()


def main():
    processes = []

    for i in range(3):  # 3 writers
        p = Process(target=writer_process, args=(i,))
        processes.append(p)

    for i in range(2):  # 2 readers
        p = Process(target=reader_process, args=(i,))
        processes.append(p)

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    print("Stress test completed.")

if __name__ == "__main__":
    main()