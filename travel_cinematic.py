from Py4GWCoreLib import *
checkbox_state = True
def DrawWindow():
    global checkbox_state

    if PyImGui.begin("Hello World!"):
       
        if Map.IsInCinematic():
            if PyImGui.button("travel"):
                Map.TravelToDistrict(map_id=123, district_number=1)
    PyImGui.end()


def main():
        DrawWindow()

if __name__ == "__main__":
    main()

