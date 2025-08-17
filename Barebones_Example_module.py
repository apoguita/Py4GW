from Py4GWCoreLib import *

var = 0

#this is the absolute minimum you can do to make a script run.
def main():
    global var
    var += 1
    Py4GW.Console.Log("Barebones Module", f"Cycles Evaluated: {var}",Py4GW.Console.MessageType.Notice)

if __name__ == "__main__":
    main()
