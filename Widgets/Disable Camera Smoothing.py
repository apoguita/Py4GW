from Py4GWCoreLib import *

MODULE_NAME = "Disable Camera Smoothing"

def main():
    cam = GLOBAL_CACHE.Camera._camera_instance
    computed = cam.ComputeCameraPos()
    cam.SetCameraPos(computed.x, computed.y, computed.z)

def configure():
    pass

if __name__ == "__main__":
    main()