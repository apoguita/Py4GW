from Py4GWCoreLib.GlobalCache.SharedMemory import HeroAIOptionStruct
import ctypes

struct = HeroAIOptionStruct()
print("Fields of HeroAIOptionStruct:")
for field in struct._fields_:
    print(f"{field[0]}: {field[1]}")
