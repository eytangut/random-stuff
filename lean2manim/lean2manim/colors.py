import hashlib

# ManimCE hex colors — all deterministic
PALETTE = [
    "#58C4DD",  # BLUE
    "#83C167",  # GREEN
    "#FC6255",  # RED
    "#FFFF00",  # YELLOW
    "#C3A0F0",  # PURPLE
    "#FF862F",  # ORANGE
    "#1BBC9B",  # TEAL
    "#FF77A8",  # PINK
    "#E8E8E8",  # WHITE
    "#A0A0A0",  # GRAY
]

ACTIVE_COLOR = "#FFFFFF"
DIMMED_COLOR = "#555555"
CLOSED_COLOR = "#83C167"
SHELF_BG = "#1A1A2E"


def var_color(var_name: str) -> str:
    """Deterministically assign a color to a variable name."""
    h = int(hashlib.md5(var_name.encode()).hexdigest(), 16)
    return PALETTE[h % len(PALETTE)]


def expr_color(identity_hash: str) -> str:
    """Deterministically assign a color to an expression node."""
    h = int(hashlib.md5(identity_hash.encode()).hexdigest(), 16)
    return PALETTE[h % len(PALETTE)]
