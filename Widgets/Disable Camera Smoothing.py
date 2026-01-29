from Py4GWCoreLib import *

MODULE_NAME = "Disable Camera Smoothing"

def main():
    pos = Camera.GetCameraPositionToGo()
    Camera.SetCameraPosition(pos[0], pos[1], pos[2])

def configure():
    pass

if __name__ == "__main__":
    main()
