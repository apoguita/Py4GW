from Py4GWCoreLib import *

MODULE_NAME = "Disable Camera Smoothing"

def main():
    computed = Camera.ComputeCameraPos()
    current = Camera.GetPosition()
    Camera.SetCameraPosition(computed.x, computed.y, current[2])

def configure():
    pass

if __name__ == "__main__":
    main()
