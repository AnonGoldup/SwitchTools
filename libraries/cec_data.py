"""
CEC reference data for SwitchTools.

Conduit internal cross-sectional areas (mm^2) per CEC Table 9 columns,
insulated-conductor areas (mm^2) per CEC Tables 10A-10D, allowable ampacities
per CEC Tables 2 (copper) / 4 (aluminum), derating factors per Table 5C, and
standard overcurrent device ratings.

NOTE: These values were compiled from published dimensional data for the same
conduit/conductor products (they match CEC tables to within rounding, e.g.
#4 RW90 600 V = 52.46 mm^2). Verify against your current CEC code book before
using results for permit/inspection work. All values live in this one file so
they are easy to audit and correct.
"""

# ---------------------------------------------------------------------------
# Conduit trade sizes: (metric designator, inch label)
# ---------------------------------------------------------------------------

TRADE_SIZES = [
    ("12", '3/8"'),
    ("16", '1/2"'),
    ("21", '3/4"'),
    ("27", '1"'),
    ("35", '1-1/4"'),
    ("41", '1-1/2"'),
    ("53", '2"'),
    ("63", '2-1/2"'),
    ("78", '3"'),
    ("91", '3-1/2"'),
    ("103", '4"'),
    ("129", '5"'),
    ("155", '6"'),
]

TRADE_SIZE_LABELS = {m: f"{m} ({inch})" for m, inch in TRADE_SIZES}

# Total internal cross-sectional area, mm^2, keyed by metric designator.
# Ordered smallest to largest (insertion order is relied on for sizing).

CONDUIT_TYPES = {
    "EMT (electrical metallic tubing)": {
        "16": 196, "21": 343, "27": 556, "35": 972, "41": 1314,
        "53": 2165, "63": 3783, "78": 5701, "91": 7451, "103": 9521,
    },
    "Rigid metal conduit (RMC)": {
        "16": 204, "21": 353, "27": 573, "35": 984, "41": 1333,
        "53": 2198, "63": 3137, "78": 4840, "91": 6461, "103": 8316,
        "129": 13050, "155": 18821,
    },
    "Flexible metal conduit (FMC)": {
        "12": 104, "16": 204, "21": 344, "27": 536, "35": 916,
        "41": 1259, "53": 1931, "63": 3275, "78": 4743, "91": 6381,
        "103": 8444,
    },
    "Liquid-tight flexible metal conduit (LFMC)": {
        "12": 110, "16": 204, "21": 344, "27": 536, "35": 916,
        "41": 1259, "53": 1931, "63": 3275, "78": 4743, "91": 6381,
        "103": 8444,
    },
    "Rigid PVC conduit": {
        "16": 184, "21": 327, "27": 535, "35": 940, "41": 1290,
        "53": 2124, "63": 3033, "78": 4693, "91": 6277, "103": 8091,
        "129": 12748, "155": 18433,
    },
    "Rigid Type EB1 PVC conduit": {
        "53": 2500, "78": 5620, "91": 7332, "103": 9322,
        "129": 14320, "155": 20342,
    },
    "Rigid Type DB2/ES2 PVC conduit": {
        "16": 248, "21": 419, "27": 699, "35": 1140, "41": 1499,
        "53": 2353, "63": 3518, "78": 5286, "91": 6899, "103": 8853,
    },
    "ENT (electrical nonmetallic tubing)": {
        "16": 184, "21": 328, "27": 537, "35": 937, "41": 1281,
        "53": 2123,
    },
    "HDPE conduit (Schedule 40)": {
        "16": 184, "21": 327, "27": 535, "35": 940, "41": 1290,
        "53": 2124, "63": 3033, "78": 4693, "91": 6277, "103": 8091,
        "129": 12748, "155": 18433,
    },
    "RTRC (fiberglass) conduit, marked IPS": {
        # Approximated with Schedule 40 IPS internal dimensions - verify.
        "16": 184, "21": 327, "27": 535, "35": 940, "41": 1290,
        "53": 2124, "63": 3033, "78": 4693, "91": 6277, "103": 8091,
        "129": 12748, "155": 18433,
    },
}

CUSTOM_CONDUIT = "Custom (enter internal diameter)"

# ---------------------------------------------------------------------------
# Insulated conductor cross-sectional areas, mm^2 (CEC Tables 10A-10D)
# ---------------------------------------------------------------------------

WIRE_SIZE_ORDER = [
    "14", "12", "10", "8", "6", "4", "3", "2", "1",
    "1/0", "2/0", "3/0", "4/0",
    "250", "300", "350", "400", "500", "600", "700", "750",
    "800", "900", "1000",
]


def wire_size_label(size: str) -> str:
    return f"{size} kcmil" if size.isdigit() and int(size) >= 250 else f"{size} AWG"


WIRE_TYPES = {
    # Table 10A - XLPE, 600 V, unjacketed
    "R90 / RW75 / RW90 XLPE (600 V, unjacketed)": {
        "14": 8.97, "12": 11.68, "10": 15.68, "8": 28.19, "6": 38.06,
        "4": 52.52, "3": 62.06, "2": 73.94, "1": 98.97,
        "1/0": 117.7, "2/0": 141.3, "3/0": 170.5, "4/0": 206.3,
        "250": 251.9, "300": 292.6, "350": 333.3, "400": 373.0,
        "500": 450.6, "600": 561.9, "700": 640.2, "750": 679.5,
        "800": 717.5, "900": 796.8, "1000": 872.2,
    },
    # Table 10B - XLPE, jacketed / 1000 V
    "RW75 / RW90 XLPE (jacketed, 1000 V)": {
        "14": 18.90, "12": 22.77, "10": 28.19, "8": 53.87, "6": 67.16,
        "4": 86.00, "3": 98.13, "2": 112.9, "1": 171.6,
        "1/0": 196.1, "2/0": 226.1, "3/0": 262.7, "4/0": 306.7,
        "250": 405.9, "300": 457.3, "350": 507.7, "400": 556.5,
        "500": 650.5, "600": 782.9, "750": 920.8, "1000": 1143.0,
    },
    # Table 10C - thermoplastic
    "TW / TW75": {
        "14": 8.97, "12": 11.68, "10": 15.68, "8": 28.19, "6": 46.84,
        "4": 62.77, "3": 73.16, "2": 86.00, "1": 122.6,
        "1/0": 143.4, "2/0": 169.3, "3/0": 201.1, "4/0": 239.9,
        "250": 296.5, "300": 340.7, "350": 384.4, "400": 427.0,
        "500": 509.7, "600": 627.7, "700": 710.3, "750": 751.7,
        "800": 791.7, "900": 874.9, "1000": 953.8,
    },
    "TWN75 / T90 Nylon": {
        "14": 6.26, "12": 8.58, "10": 13.61, "8": 23.61, "6": 32.71,
        "4": 53.16, "3": 62.77, "2": 74.71, "1": 100.8,
        "1/0": 119.7, "2/0": 143.4, "3/0": 172.8, "4/0": 208.8,
        "250": 256.1, "300": 297.3, "350": 338.2, "400": 378.3,
        "500": 456.3, "600": 559.7, "700": 637.9, "750": 677.2,
        "800": 715.2, "900": 794.3, "1000": 869.5,
    },
    # Table 10D - RWU90, 1000 V
    "RWU90 XLPE (1000 V)": {
        "14": 18.90, "12": 22.77, "10": 28.19, "8": 53.87, "6": 67.16,
        "4": 86.00, "3": 98.13, "2": 112.9, "1": 171.6,
        "1/0": 196.1, "2/0": 226.1, "3/0": 262.7, "4/0": 306.7,
        "250": 405.9, "300": 457.3, "350": 507.7, "400": 556.5,
        "500": 650.5, "600": 782.9, "750": 920.8, "1000": 1143.0,
    },
}

# Default insulation temperature rating (deg C) used for ampacity lookups.
WIRE_TYPE_TEMP_DEFAULT = {
    "R90 / RW75 / RW90 XLPE (600 V, unjacketed)": 90,
    "RW75 / RW90 XLPE (jacketed, 1000 V)": 90,
    "TW / TW75": 75,
    "TWN75 / T90 Nylon": 90,
    "RWU90 XLPE (1000 V)": 90,
}


def table8_max_fill_percent(conductor_count: int) -> int:
    """CEC Table 8 maximum conduit/tubing fill."""
    if conductor_count <= 0:
        return 0
    if conductor_count == 1:
        return 53
    if conductor_count == 2:
        return 31
    return 40


# ---------------------------------------------------------------------------
# Allowable ampacity, not more than 3 copper/aluminum conductors in raceway
# (CEC Table 2 / Table 4, 30 C ambient), keyed [material][temp C][size]
# ---------------------------------------------------------------------------

AMPACITY = {
    "Copper": {
        60: {
            "14": 15, "12": 20, "10": 30, "8": 40, "6": 55, "4": 70,
            "3": 85, "2": 95, "1": 110, "1/0": 125, "2/0": 145,
            "3/0": 165, "4/0": 195, "250": 215, "300": 240, "350": 260,
            "400": 280, "500": 320, "600": 355, "700": 385, "750": 400,
            "800": 410, "900": 435, "1000": 455,
        },
        75: {
            "14": 20, "12": 25, "10": 35, "8": 50, "6": 65, "4": 85,
            "3": 100, "2": 115, "1": 130, "1/0": 150, "2/0": 175,
            "3/0": 200, "4/0": 230, "250": 255, "300": 285, "350": 310,
            "400": 335, "500": 380, "600": 420, "700": 460, "750": 475,
            "800": 490, "900": 520, "1000": 545,
        },
        90: {
            "14": 25, "12": 30, "10": 40, "8": 55, "6": 75, "4": 95,
            "3": 115, "2": 130, "1": 145, "1/0": 170, "2/0": 195,
            "3/0": 225, "4/0": 260, "250": 290, "300": 320, "350": 350,
            "400": 380, "500": 430, "600": 475, "700": 520, "750": 535,
            "800": 555, "900": 585, "1000": 615,
        },
    },
    "Aluminum": {
        60: {
            "12": 15, "10": 25, "8": 35, "6": 40, "4": 55,
            "3": 65, "2": 75, "1": 85, "1/0": 100, "2/0": 115,
            "3/0": 130, "4/0": 150, "250": 170, "300": 195, "350": 210,
            "400": 225, "500": 260, "600": 285, "700": 315, "750": 320,
            "800": 330, "900": 355, "1000": 375,
        },
        75: {
            "12": 20, "10": 30, "8": 40, "6": 50, "4": 65,
            "3": 75, "2": 90, "1": 100, "1/0": 120, "2/0": 135,
            "3/0": 155, "4/0": 180, "250": 205, "300": 230, "350": 250,
            "400": 270, "500": 310, "600": 340, "700": 375, "750": 385,
            "800": 395, "900": 425, "1000": 445,
        },
        90: {
            "12": 25, "10": 35, "8": 45, "6": 55, "4": 75,
            "3": 85, "2": 100, "1": 115, "1/0": 135, "2/0": 150,
            "3/0": 175, "4/0": 205, "250": 230, "300": 260, "350": 280,
            "400": 305, "500": 350, "600": 385, "700": 425, "750": 435,
            "800": 445, "900": 480, "1000": 500,
        },
    },
}


def table5c_derating_factor(conductor_count: int) -> float:
    """CEC Table 5C ampacity correction for conductor count in a raceway."""
    if conductor_count <= 3:
        return 1.00
    if conductor_count <= 6:
        return 0.80
    if conductor_count <= 24:
        return 0.70
    if conductor_count <= 42:
        return 0.60
    return 0.50


def min_conductor_size(required_amps: float, material: str, temp: int):
    """Smallest conductor with ampacity >= required_amps.

    Returns (size, ampacity) or None if nothing is large enough.
    """
    table = AMPACITY[material][temp]
    for size in WIRE_SIZE_ORDER:
        amp = table.get(size)
        if amp is not None and amp >= required_amps:
            return size, amp
    return None


def fill_percent(total_area: float, inside_area: float) -> float:
    """Conductor area as a percentage of a raceway's internal area."""
    return total_area / inside_area * 100.0


def min_conduit_size(conduit_name: str, total_area: float, max_fill_pct: float):
    """Smallest trade size of this conduit type whose fill stays within
    max_fill_pct.

    Returns (metric designator, internal area) or None if nothing is large enough.
    """
    for metric, area in CONDUIT_TYPES[conduit_name].items():
        if fill_percent(total_area, area) <= max_fill_pct:
            return metric, area
    return None


# ---------------------------------------------------------------------------
# Standard overcurrent device ratings (CEC Rule 14-010 / Table 13 range)
# ---------------------------------------------------------------------------

STANDARD_OCP_RATINGS = [
    15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125,
    150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800,
    1000, 1200, 1600, 2000, 2500, 3000, 4000, 5000, 6000,
]


def next_standard_ocp(amps: float):
    """Smallest standard OCP rating >= amps (None if beyond the table)."""
    for r in STANDARD_OCP_RATINGS:
        if r >= amps:
            return r
    return None


def largest_standard_ocp_at_or_below(amps: float):
    """Largest standard OCP rating <= amps (None if below 15 A)."""
    result = None
    for r in STANDARD_OCP_RATINGS:
        if r <= amps:
            result = r
        else:
            break
    return result


# ---------------------------------------------------------------------------
# Voltage drop: DC resistance at 75 C, ohms per km (stranded conductors)
# ---------------------------------------------------------------------------

RESISTANCE_OHM_PER_KM = {
    "Copper": {
        "14": 10.30, "12": 6.50, "10": 4.07, "8": 2.55, "6": 1.61,
        "4": 1.01, "3": 0.804, "2": 0.637, "1": 0.505,
        "1/0": 0.400, "2/0": 0.317, "3/0": 0.251, "4/0": 0.200,
        "250": 0.169, "300": 0.141, "350": 0.120, "400": 0.105,
        "500": 0.0847, "600": 0.0702, "700": 0.0604, "750": 0.0561,
        "800": 0.0528, "900": 0.0469, "1000": 0.0423,
    },
    "Aluminum": {
        "12": 10.66, "10": 6.69, "8": 4.20, "6": 2.65,
        "4": 1.67, "3": 1.32, "2": 1.05, "1": 0.830,
        "1/0": 0.659, "2/0": 0.522, "3/0": 0.413, "4/0": 0.328,
        "250": 0.278, "300": 0.232, "350": 0.198, "400": 0.174,
        "500": 0.139, "600": 0.116, "700": 0.0994, "750": 0.0925,
        "800": 0.0869, "900": 0.0771, "1000": 0.0695,
    },
}
