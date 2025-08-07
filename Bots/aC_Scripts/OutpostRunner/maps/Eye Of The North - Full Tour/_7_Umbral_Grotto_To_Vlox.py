from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_7_umbral_grotto_to_vlox_ids = {
    "outpost_id": outpost_name_to_id["Umbral Grotto"],
}


_7_umbral_grotto_to_vlox_outpost_path = [
    (-24463.523437, 11560.543945),
    (-26128.982421, 10676.186523),  
]

_7_umbral_grotto_to_vlox_segments = [
    {
        "map_id": explorable_name_to_id["Vloxen Excavations (level 1)"],
        "path": [
            (-13807.781250, 16442.718750),
            (-14953.253906, 13218.502929),
            (-17230.427734,  9955.362304),
            (-16309.177734,  7241.766113),
            (-16266.636718,  5037.340820),
            (-17457.251953,  1882.958984),
            (-17889.468750, -1212.505981),
            (-16952.267578, -3971.341308),
            (-17606.107421, -7403.375000),
            (-16884.861328,-10819.688476),
            (-18920.699218,-11642.852539),
            (-19454.873040,-11828.130850),
            (-19921.515625,-11963.304687),
        ],
    },
    {
        "map_id": outpost_name_to_id["Vlox's Falls"],
        "path": [],  
    },
]