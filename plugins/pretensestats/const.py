from core import get_translation

_ = get_translation(__name__.split('.')[1])


PRETENSE_RANKS = {
    1: {"name": _("E-1 Airman basic"), "requiredXP": 0},
    2: {"name": _("E-2 Airman"), "requiredXP": 2000},
    3: {"name": _("E-3 Airman first class"), "requiredXP": 4500},
    4: {"name": _("E-4 Senior airman"), "requiredXP": 7700},
    5: {"name": _("E-5 Staff sergeant"), "requiredXP": 11800},
    6: {"name": _("E-6 Technical sergeant"), "requiredXP": 17000},
    7: {"name": _("E-7 Master sergeant"), "requiredXP": 23500},
    8: {"name": _("E-8 Senior master sergeant"), "requiredXP": 31500},
    9: {"name": _("E-9 Chief master sergeant"), "requiredXP": 42000},
    10: {"name": _("O-1 First lieutenant"), "requiredXP": 52800},
    11: {"name": _("O-2 Captain"), "requiredXP": 66500},
    12: {"name": _("O-3 Major"), "requiredXP": 82500},
    13: {"name": _("O-4 Lieutenant colonel"), "requiredXP": 101000},
    14: {"name": _("O-5 Colonel"), "requiredXP": 122200},
    15: {"name": _("O-6 Brigadier general"), "requiredXP": 146300},
    16: {"name": _("O-7 Major general"), "requiredXP": 173500},
    17: {"name": _("O-8 Lieutenant general"), "requiredXP": 204000},
    18: {"name": _("O-9 General"), "requiredXP": 238000}
}
