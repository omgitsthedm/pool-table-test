"""
wpa_spec.py — the WPA Recommended Equipment Specifications, as numbers.

Every constant here is quoted from the official document (effective November
2001), archived in this repo at:

    assets/wpa/WPA-Recommended-Equipment-Specifications.pdf
    https://wpapool.com/wp-content/uploads/2024/01/RECOMMENDED-EQUIPMENT-SPECIFICATIONS.pdf

Section numbers in the comments refer to that document. Nothing in the render
pipeline is allowed to invent a dimension: if a number matters, it comes from
here, and if the spec gives a range we pick a value inside it and say so.
"""

IN = 0.0254                        # metres per inch

# --- 2. Table bed height ---------------------------------------------------
# "Shall be between 29 1/4 inches [74.295 cm] and 31 inches [78.74 cm]."
BED_MIN = 29.25 * IN
BED_MAX = 31.0 * IN
BED = 30.0 * IN                    # 0.762 m — mid-range

# --- 4. Slates -------------------------------------------------------------
# "The thickness must be at least 1 inch [2.54 cm]... a set of slates
#  consisting of three pieces of equal size with wooden frame of at least
#  3/4 inch [1.905 cm] thick lumber attached underneath the slate."
SLATE_T = 1.0 * IN
SLATE_FRAME_T = 0.75 * IN
SLATE_PIECES = 3

# --- 5. Playing surface ----------------------------------------------------
# "9 foot - 100 (+1/8) x 50 (+1/8) inches (except cushions)"
# "8 foot -  92 (+1/8) x 46 (+1/8) inches"
# Measured cushion nose to cushion nose.
TABLE_9FT = (100.0 * IN, 50.0 * IN)          # (length, width) = 2.54 x 1.27 m
TABLE_8FT = (92.0 * IN, 46.0 * IN)
# The WPA does not publish a 7-foot spec; the bar-box standard is 78 x 39 in.
TABLE_7FT = (78.0 * IN, 39.0 * IN)

# --- 6. Rail and cushion ---------------------------------------------------
# "The rail width must be between 4 [10.16 cm] and 7 1/2 inches [19.05 cm]
#  including the rubber cushions."
RAIL_W_MIN = 4.0 * IN
RAIL_W_MAX = 7.5 * IN
RAIL_W = 5.0 * IN                  # 0.127 m, incl. cushion — inside the range

# "18 sights (or 17 and a name plate) shall be attached flush on the rail cap"
# "12 1/2 inches [31.75 cm] from sight to sight on a 9-foot regulation table"
# "The center of each sight should be located 3 11/16 (+) inches
#  [93.6625 mm (+3.175 mm)] from the nose of the cushion."
SIGHT_COUNT = 18
SIGHT_SPACING_9FT = 12.5 * IN
SIGHT_SPACING_8FT = 11.5 * IN
SIGHT_FROM_NOSE = 3.6875 * IN      # 93.6625 mm
# "diamond-shaped (between 1 x 7/16 [25.4 x 11.11 mm] and 1 1/4 x 5/8 inch)"
SIGHT_DIAMOND = (1.125 * IN, 0.53 * IN)

# --- 7. Height of the cushion ----------------------------------------------
# "Rubber cushions should be triangular in shape with the width of the
#  cloth-covered cushion being between 1 7/8 [4.76 cm] and 2 inches [5.40 cm]
#  measured from the outer edge of the featherstrip to the nose of the
#  cushion. Rail height (nose-line to table-bed) should be 63 1/2% (+1%) or
#  between 62 1/2% and 64 1/2% of the diameter of the ball."
CUSHION_W = 2.0 * IN               # 0.0508 m
NOSE_FRACTION = 0.635              # of ball diameter
NOSE_FRACTION_MIN = 0.625
NOSE_FRACTION_MAX = 0.645

# --- 9. Pocket openings and measurements -----------------------------------
# "Corner Pocket Mouth: between 4.5 [11.43 cm] and 4.625 inches [11.75 cm]"
# "Side Pocket Mouth: between 5 [12.7 cm] and 5.125 inches [13.0175 cm]"
CORNER_MOUTH = 4.5 * IN            # 0.1143 m — tightest legal
SIDE_MOUTH = 5.0 * IN              # 0.1270 m — tightest legal
# "Vertical Pocket Angle (Back Draft): 12 degrees minimum to 15 maximum."
BACK_DRAFT_DEG = 13.0
# "The cut angles of the rubber cushion and its wood backing (rail liner) for
#  both sides of the corner pocket entrance must be 142 degrees (+1). ...for
#  both sides of the side pocket entrance must be 104 degrees (+1)."
CORNER_JAW_DEG = 142.0
# pooltool's pocket_angle parameter is not the WPA cut angle directly; these
# two values are calibrated so the geometry it builds *measures* 142 / 104
# degrees at the jaw. Verified by export_table.py on every run.
CORNER_JAW_TUNE = 7.00
SIDE_JAW_TUNE = 14.50
SIDE_JAW_DEG = 104.0
# "Corner Pocket Shelf: between 1 [2.54 cm] and 2 1/4 inches [5.715 cm]"
# "Side Pocket Shelf: between 0 and .375 inches [.9525 cm]"
CORNER_SHELF = 1.5 * IN
SIDE_SHELF = 0.25 * IN
# "Only rubber facings of minimum 1/16 [1.5875 mm] to maximum 1/4 inch
#  [6.35 mm]... The WPA-preferred maximum thickness for facings is 1/8 inch."
FACING_T = 0.125 * IN

# --- 11. Ball return and drop pockets --------------------------------------
# "Drop pockets must have a basket capacity of at least 6 balls."
POCKET_BASKET_BALLS = 6

# --- 12. Cloth -------------------------------------------------------------
# "80% to 85% combed worsted wool, 15% to 20% nylon... Only the colors of
#  yellow-green, blue-green or electric blue are acceptable."
CLOTH_RGB = (0.055, 0.215, 0.115)  # a tournament blue-green, linear

# --- 15. Lights ------------------------------------------------------------
# "The bed and rails of the table must receive at least 520 lux (48
#  footcandles) of light at every point... If the light fixture above the
#  table may be moved aside, the minimum height of the fixture should be no
#  lower than 40 inches [1.016 m] above the bed of the table. If the light
#  fixture above the table is non-movable, the fixture should be no lower
#  than 65 inches [1.65 m] above the bed."
LIGHT_MIN_LUX = 520
LIGHT_H_MOVABLE = 40.0 * IN
LIGHT_H_FIXED = 65.0 * IN
LIGHT_H = 44.0 * IN                # above the bed — clears the movable minimum
# "The rest of the venue (bleachers, etc.) should receive at least 50 lux."
VENUE_MIN_LUX = 50

# --- 16. Balls and ball rack -----------------------------------------------
# "measure 2 1/4 (+.005) inches [5.715 cm (+.127 mm)] in diameter and weigh
#  5 1/2 to 6 oz [156 to 170 gms]"
BALL_D = 2.25 * IN                 # 0.05715 m
BALL_R = BALL_D / 2.0
BALL_MASS = 0.163                  # kg, mid-range

# "The object balls numbered 1 through 8 have solid colors as follows:
#  1=yellow, 2=blue, 3=red, 4=purple, 5=orange, 6=green, 7=maroon, 8=black.
#  The object balls numbered 9 through 15 are white with a centered band of
#  color as follows: 9=yellow, 10=blue, 11=red, 12=purple, 13=orange,
#  14=green and 15=maroon."
BALL_HUES = {
    1: (0.92, 0.72, 0.05),         # yellow
    2: (0.05, 0.16, 0.55),         # blue
    3: (0.72, 0.07, 0.05),         # red
    4: (0.24, 0.06, 0.34),         # purple
    5: (0.88, 0.30, 0.04),         # orange
    6: (0.03, 0.32, 0.12),         # green
    7: (0.40, 0.07, 0.10),         # maroon
    8: (0.020, 0.020, 0.022),      # black
}
for _n in range(9, 16):
    BALL_HUES[_n] = BALL_HUES[_n - 8]
CUE_BALL_RGB = (0.93, 0.91, 0.855)
# "Each object ball has its number printed twice, opposite each other, one of
#  the two numbers upside down, black on a white round background. The two
#  printed numbers 6 and 9 are underscored."
NUMBER_PRINTS = 2
UNDERSCORED = (6, 9)

# --- 17. Cue sticks --------------------------------------------------------
# "Length of Cue: 40 inches [1.016 m] minimum / No Maximum.
#  Weight: No minimum / 25 oz. maximum. Width of Tip: 14mm maximum."
CUE_LEN_MIN = 40.0 * IN
CUE_LEN = 58.0 * IN                # 1.4732 m, the common playing length
CUE_TIP_MAX = 0.014
CUE_TIP = 0.0128

# --- 19. Spacing between tables --------------------------------------------
# "a minimum measurement of 6 feet [1.83 m] is required between the outside
#  edge of the table rail in every horizontal direction and obstacle"
TABLE_CLEARANCE = 6.0 * 12 * IN


def nose_height(ball_d=BALL_D):
    """Cushion nose height above the bed — WPA sec.7."""
    return NOSE_FRACTION * ball_d


def sight_spacing(length):
    """Sight-to-sight spacing for a table of this playing length — sec.6."""
    return SIGHT_SPACING_9FT if length > 96 * IN else SIGHT_SPACING_8FT
