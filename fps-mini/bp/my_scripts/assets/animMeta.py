AnimMeta = {
    "animation.template.weapons.pistol.fp.rot": {
        "loop": "hold_on_last_frame",
        "length": -1
    },
    "animation.template.weapons.pistol.fp.hold": {
        "loop": "hold_on_last_frame",
        "length": -1
    },
    "animation.template.weapons.pistol.fp.shoot": {
        "loop": "hold_on_last_frame",
        "length": 0.125
    },
    "animation.template.weapons.pistol.fp.aim": {
        "loop": "hold_on_last_frame",
        "length": -1
    },
    "animation.template.weapons.pistol.fp.aim_shoot": {
        "loop": "hold_on_last_frame",
        "length": 0.125
    },
    "animation.template.weapons.pistol.fp.aim_last_shoot": {
        "loop": "hold_on_last_frame",
        "length": 0.125,
        "notifies": {
            "0.0833": [
                {
                    "name": "reset",
                    "state": 1
                }
            ]
        },
        "extra": {}
    },
    "animation.template.weapons.pistol.fp.reload": {
        "loop": "hold_on_last_frame",
        "length": 1.4167,
        "notifies": {
            "1.2917": [
                {
                    "name": "reload",
                    "state": 1
                }
            ]
        },
        "extra": {}
    },
    "animation.template.weapons.pistol.fp.last_shoot": {
        "loop": "hold_on_last_frame",
        "length": 0.125
    },
    "animation.template.weapons.pistol.fp.reload_slide_stop": {
        "loop": "hold_on_last_frame",
        "length": 1.4167,
        "notifies": {
            "1.2917": [
                {
                    "name": "reload",
                    "state": 1
                }
            ]
        },
        "extra": {}
    },
    "animation.template.weapons.pistol.fp.aim_slide_stop": {
        "loop": "hold_on_last_frame",
        "length": -1
    },
    "animation.template.weapons.pistol.fp.hold_slide_stop": {
        "loop": "hold_on_last_frame",
        "length": -1
    }
}