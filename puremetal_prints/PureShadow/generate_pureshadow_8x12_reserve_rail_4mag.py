# generate_pureshadow_8x12_reserve_rail_4mag.py
# PureShadow - 8x12 Reserve Rail (4 magnet prototype = 2 magnets per rail)
# Generates ONE rail body with two magnet pockets, exports STL.
#
# Run (headless):
#   FreeCADCmd.exe generate_pureshadow_8x12_reserve_rail_4mag.py
#
# Notes:
# - Units: mm
# - Magnet: MIKEDE cup magnet OD 16.0mm, thickness 4.83mm
# - Pocket: dia 16.2mm, depth 4.75mm (flush/slightly proud)
# - Rail depth: 20.3mm (0.80")

import os
import FreeCAD as App
import Part
import Mesh

# -----------------------------
# Parameters (edit here)
# -----------------------------
RAIL_LENGTH = 240.0   # mm  (~75% of 12" = 304.8mm)
RAIL_WIDTH  = 18.0    # mm  bonding face width (~0.7")
RAIL_DEPTH  = 20.3    # mm  stand-off depth (0.80")

POCKET_DIA   = 16.2   # mm
POCKET_DEPTH = 4.75   # mm  (flush/slightly proud)
END_OFFSET   = 25.0   # mm  magnet center offset from each end

# Export settings
OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
OUT_NAME = "PureShadow_8x12_Reserve_Rail_4Mag"
STL_LINEAR_DEFLECTION = 0.10  # mm (smaller = finer)
STL_ANGULAR_DEFLECTION = 0.35 # radians

# -----------------------------
# Build geometry
# -----------------------------
def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def make_rail_with_pockets():
    # Rail body (box)
    body = Part.makeBox(RAIL_LENGTH, RAIL_WIDTH, RAIL_DEPTH)

    # Pocket cylinders (cut from steel-facing side)
    # Z=0 is "bottom" of the solid. We'll place pockets near the "front/steel face"
    # Define steel face as the Z-max face for easy reasoning: pockets start at (RAIL_DEPTH - POCKET_DEPTH)
    z0 = RAIL_DEPTH - POCKET_DEPTH
    y_center = RAIL_WIDTH / 2.0

    # Pocket 1 near "top" end
    x1 = END_OFFSET
    cyl1 = Part.makeCylinder(POCKET_DIA / 2.0, POCKET_DEPTH, App.Vector(x1, y_center, z0), App.Vector(0, 0, 1))

    # Pocket 2 near "bottom" end
    x2 = RAIL_LENGTH - END_OFFSET
    cyl2 = Part.makeCylinder(POCKET_DIA / 2.0, POCKET_DEPTH, App.Vector(x2, y_center, z0), App.Vector(0, 0, 1))

    # Cut pockets
    rail = body.cut(cyl1).cut(cyl2)
    rail = rail.removeSplitter()
    return rail

def export_stl(shape, out_path: str):
    # Convert Part shape to Mesh with deflections
    mesh = Mesh.Mesh()
    mesh.addFacets(shape.tessellate(STL_LINEAR_DEFLECTION))
    # Note: tessellate() uses linear deflection; angular is not directly set here in older builds.
    mesh.write(out_path)

def main():
    ensure_dir(OUT_DIR)

    doc = App.newDocument("PureShadow_Rail_Gen")
    rail_shape = make_rail_with_pockets()

    obj = doc.addObject("Part::Feature", "Rail")
    obj.Shape = rail_shape
    doc.recompute()

    stl_path = os.path.join(OUT_DIR, f"{OUT_NAME}.stl")
    export_stl(obj.Shape, stl_path)

    # Optional: also save a FreeCAD file for inspection
    fcstd_path = os.path.join(OUT_DIR, f"{OUT_NAME}.FCStd")
    doc.saveAs(fcstd_path)

    print("OK")
    print("STL:", stl_path)
    print("FCStd:", fcstd_path)

if __name__ == "__main__":
    main()