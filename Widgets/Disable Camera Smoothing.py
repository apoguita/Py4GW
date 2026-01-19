from Py4GWCoreLib import *

MODULE_NAME = "Disable Camera Smoothing"

def main():
    computed = Camera.ComputeCameraPos()
    Camera.SetCameraPosition(computed.x, computed.y, computed.z)

def configure():
    pass

if __name__ == "__main__":
    main()
