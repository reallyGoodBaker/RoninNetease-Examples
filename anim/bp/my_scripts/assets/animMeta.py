AnimMeta = {
    "animation.standard_steve.idle": {
        "loop": True,
        "length": 2
    },
    "animation.standard_steve.new": {
        "loop": True,
        "length": -1
    },
    "animation.standard_steve.walk": {
        "loop": True,
        "length": 1
    },
    "animation.standard_steve.diamond": {
        "loop": True,
        "length": -1
    },
    "animation.standard_steve.wood": {
        "loop": True,
        "length": -1
    },
    "animation.standard_steve.iron": {
        "loop": True,
        "length": -1
    },
    "animation.standard_steve.stop": {
        "loop": False,
        "length": 0.25
    },
    "animation.standard_steve.attack.diamond": {
        "loop": "hold_on_last_frame",
        "length": 0.4167,
        "notifies": {
            "0.0": [
                {
                    "name": "stun",
                    "state": 1
                }
            ],
            "0.1875": [
                {
                    "name": "stun",
                    "state": 1
                }
            ],
            "0.25": [
                {
                    "name": "attack",
                    "state": 1
                }
            ],
            "0.375": [
                {
                    "name": "stun",
                    "state": 0
                }
            ],
            "0.3958": [
                {
                    "name": "restore",
                    "state": 1
                }
            ]
        },
        "extra": {}
    }
}