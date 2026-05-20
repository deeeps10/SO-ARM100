# Units: mm throughout.

from build123d import *
from build123d.topology import Compound
import math
try:
    from ocp_vscode import show
    _has_ocp = True
except ImportError:
    _has_ocp = False

# ---- Boolean operation helpers ----
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse as BFuse, BRepAlgoAPI_Cut as BCut

def fuse_solids(solid1, solid2):
    """Fuse two solids with fuzzy tolerance. Falls back to Compound if they do not intersect."""
    from OCP.TopAbs import TopAbs_SOLID
    try:
        fuse_op = BFuse(solid1.wrapped, solid2.wrapped)
        fuse_op.SetFuzzyValue(0.01)
        fuse_op.Build()
        result_shape = fuse_op.Shape()
        if not result_shape.IsNull() and result_shape.ShapeType() == TopAbs_SOLID:
            return Solid(result_shape)
    except:
        pass
    # Non-touching bodies: OCC returns a Compound — accumulate explicitly.
    existing = list(solid1.solids()) if isinstance(solid1, Compound) else [solid1]
    new_s = list(solid2.solids()) if isinstance(solid2, Compound) else [solid2]
    return Compound(existing + new_s)

def cut_solids(shape, tool):
    """Cut tool from shape with fuzzy tolerance. Handles Compound (multi-body) shapes with bbox pre-check."""
    try:
        if isinstance(shape, Compound):
            result_solids = []
            for solid in shape.solids():
                try:
                    sbb = solid.bounding_box()
                    tbb = tool.bounding_box()
                    overlap = (
                        not (sbb.max.X < tbb.min.X or sbb.min.X > tbb.max.X) and
                        not (sbb.max.Y < tbb.min.Y or sbb.min.Y > tbb.max.Y) and
                        not (sbb.max.Z < tbb.min.Z or sbb.min.Z > tbb.max.Z)
                    )
                    if overlap:
                        cut_op = BCut(solid.wrapped, tool.wrapped)
                        cut_op.SetFuzzyValue(0.01)
                        cut_op.Build()
                        cut_result = Solid(cut_op.Shape())
                        if not cut_result.wrapped.IsNull() and len(list(cut_result.faces())) > 0:
                            result_solids.append(cut_result)
                        else:
                            result_solids.append(solid)
                    else:
                        result_solids.append(solid)
                except:
                    result_solids.append(solid)
            return result_solids[0] if len(result_solids) == 1 else Compound(result_solids)
        else:
            sbb = shape.bounding_box()
            tbb = tool.bounding_box()
            overlap = (
                not (sbb.max.X < tbb.min.X or sbb.min.X > tbb.max.X) and
                not (sbb.max.Y < tbb.min.Y or sbb.min.Y > tbb.max.Y) and
                not (sbb.max.Z < tbb.min.Z or sbb.min.Z > tbb.max.Z)
            )
            if overlap:
                cut_op = BCut(shape.wrapped, tool.wrapped)
                cut_op.SetFuzzyValue(0.01)
                cut_op.Build()
                cut_result = Solid(cut_op.Shape())
                if not cut_result.wrapped.IsNull() and len(list(cut_result.faces())) > 0:
                    return cut_result
            return shape
    except:
        return shape

# All dimensions below are raw numbers.

# 'Sketch2': 22 segments → Line/RadiusArc profile
_inclined_plane_1 = Plane(
    origin=Vector(39.0329, -145.6744, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_1) as sk_Sketch2:
    with BuildLine():
        Line((-257.6977, 2244.5941), (-265.6977, 2244.5941))
        Line((-265.6977, 2244.5941), (-265.6977, 2230.7377))
        Line((-265.6977, 2230.7377), (-265.6977, 2184.5941))
        Line((-265.6977, 2184.5941), (-265.6977, 2174.594))
        Line((-265.6977, 2174.594), (-255.6977, 2174.594))
        Line((-255.6977, 2174.594), (-248.6977, 2174.5941))
        Line((-248.6977, 2174.5941), (-248.6977, 1774.594))
        Line((-248.6977, 1774.594), (-268.6977, 1774.594))
        Line((-268.6977, 1774.594), (-268.6977, 1674.594))
        Line((-268.6977, 1674.594), (-288.6976, 1674.594))
        Line((-288.6976, 1674.594), (-288.6976, 1584.6039))
        Line((-288.6976, 1584.6039), (-288.6976, 1574.5939))
        Line((-288.6976, 1574.5939), (-257.4365, 1574.5939))
        Line((-257.4365, 1574.5939), (-238.6977, 1574.5939))
        Line((-238.6977, 1574.5939), (-230.3617, 1591.6485))
        Line((-230.3617, 1591.6485), (-130.3591, 1796.2439))
        Line((-130.3591, 1796.2439), (-128.0362, 1800.9964))
        Line((-128.0362, 1800.9964), (-127.4788, 1806.2567))
        Line((-127.4788, 1806.2567), (-84.5458, 2211.4329))
        Line((-84.5458, 2211.4329), (-81.032, 2244.5941))
        Line((-81.032, 2244.5941), (-114.3788, 2244.5941))
        Line((-114.3788, 2244.5941), (-257.6977, 2244.5941))
    _inc_edges_sk_Sketch2 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch2 = Wire.combine(_inc_edges_sk_Sketch2)[0]
_wire_sk_Sketch2 = _wire_sk_Sketch2.moved(_inclined_plane_1.location)
_mkf_sk_Sketch2 = BRepBuilderAPI_MakeFace(_inclined_plane_1.wrapped, _wire_sk_Sketch2.wrapped, True)
_face_sk_Sketch2 = Face(_mkf_sk_Sketch2.Face())

# 'Sketch4': 4 segments → Line/RadiusArc profile
_inclined_plane_2 = Plane(
    origin=Vector(0.0, 0.0, 288.6976),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_2) as sk_Sketch4_2:
    with BuildLine():
        Line((2471.6795, 413.7264), (2227.6235, 348.3327))
        Line((2227.6235, 348.3327), (2129.7922, 713.4491))
        Line((2129.7922, 713.4491), (2373.8482, 778.8428))
        Line((2373.8482, 778.8428), (2471.6795, 413.7264))
    _inc_edges_sk_Sketch4_2 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch4_2 = Wire.combine(_inc_edges_sk_Sketch4_2)[0]
_wire_sk_Sketch4_2 = _wire_sk_Sketch4_2.moved(_inclined_plane_2.location)
_mkf_sk_Sketch4_2 = BRepBuilderAPI_MakeFace(_inclined_plane_2.wrapped, _wire_sk_Sketch4_2.wrapped, True)
_face_sk_Sketch4_2 = Face(_mkf_sk_Sketch4_2.Face())

# 'Sketch3': 48 segments → Line/RadiusArc profile
_inclined_plane_3 = Plane(
    origin=Vector(0.0, 0.0, 288.6976),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_3) as sk_Sketch3_3:
    with BuildLine():
        Line((2117.2708, 620.498), (2243.8245, 693.5638))
        Line((2243.8245, 693.5638), (2281.145, 703.5638))
        Line((2281.145, 703.5638), (2289.9167, 705.9142))
        Line((2289.9167, 705.9142), (2306.3445, 710.3159))
        Line((2306.3445, 710.3159), (2354.9821, 723.3484))
        Line((2354.9821, 723.3484), (2359.1241, 707.8938))
        Line((2359.1241, 707.8938), (2390.5989, 716.3274))
        Line((2390.5989, 716.3274), (2374.8615, 860.9132))
        Line((2374.8615, 860.9132), (1426.8351, 659.716))
        Line((1426.8351, 659.716), (1478.3436, 237.1632))
        Line((1478.3436, 237.1632), (1559.974, 261.8604))
        Line((1559.974, 261.8604), (1559.2735, 266.2298))
        Line((1559.2735, 266.2298), (1559.1507, 268.1965))
        Line((1559.1507, 268.1965), (1559.39, 273.3079))
        Line((1559.39, 273.3079), (1560.4449, 278.4602))
        Line((1560.4449, 278.4602), (1562.1384, 283.2122))
        Line((1562.1384, 283.2122), (1564.7415, 288.3495))
        Line((1564.7415, 288.3495), (1567.9698, 293.2556))
        Line((1567.9698, 293.2556), (1572.3227, 298.623))
        Line((1572.3227, 298.623), (1577.7985, 304.2546))
        Line((1577.7985, 304.2546), (1585.4823, 310.9396))
        Line((1585.4823, 310.9396), (1593.654, 317.0868))
        Line((1593.654, 317.0868), (1602.486, 323.0013))
        Line((1602.486, 323.0013), (1611.9444, 328.746))
        Line((1611.9444, 328.746), (1622.003, 334.365))
        Line((1622.003, 334.365), (1632.639, 339.8901))
        Line((1632.639, 339.8901), (1641.4374, 344.2053))
        Line((1641.4374, 344.2053), (1643.0983, 344.9977))
        Line((1643.0983, 344.9977), (1663.4906, 354.2548))
        Line((1663.4906, 354.2548), (1685.2075, 363.3659))
        Line((1685.2075, 363.3659), (1704.2725, 370.9067))
        Line((1704.2725, 370.9067), (1734.7491, 382.3316))
        Line((1734.7491, 382.3316), (1774.8167, 396.5762))
        Line((1774.8167, 396.5762), (1844.6429, 420.4218))
        Line((1844.6429, 420.4218), (1865.6638, 427.5543))
        Line((1865.6638, 427.5543), (1931.5681, 450.5164))
        Line((1931.5681, 450.5164), (1955.8244, 459.2139))
        Line((1955.8244, 459.2139), (1990.1863, 472.2861))
        Line((1990.1863, 472.2861), (2018.6836, 483.9001))
        Line((2018.6836, 483.9001), (2042.7531, 494.496))
        Line((2042.7531, 494.496), (2063.2262, 504.3056))
        Line((2063.2262, 504.3056), (2080.6891, 513.4821))
        Line((2080.6891, 513.4821), (2086.4671, 517.3695))
        RadiusArc((2086.4671, 517.3695), (2102.1689, 554.265), -42.5262)
        Line((2102.1689, 554.265), (2097.702, 573.2545))
        RadiusArc((2097.702, 573.2545), (2111.6263, 616.5914), 42.0004)
        RadiusArc((2111.6263, 616.5914), (2115.551, 619.4492), 42.0429)
        Line((2115.551, 619.4492), (2117.2708, 620.498))
    _inc_edges_sk_Sketch3_3 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch3_3 = Wire.combine(_inc_edges_sk_Sketch3_3)[0]
_wire_sk_Sketch3_3 = _wire_sk_Sketch3_3.moved(_inclined_plane_3.location)
_mkf_sk_Sketch3_3 = BRepBuilderAPI_MakeFace(_inclined_plane_3.wrapped, _wire_sk_Sketch3_3.wrapped, True)
_face_sk_Sketch3_3 = Face(_mkf_sk_Sketch3_3.Face())

# 'Sketch5': 10 segments → Line/RadiusArc profile
_inclined_plane_4 = Plane(
    origin=Vector(0.0, 0.0, 288.6976),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_4) as sk_Sketch5_4:
    with BuildLine():
        Line((2529.392, 384.1404), (2399.6574, 682.5201))
        Line((2399.6574, 682.5201), (2231.3342, 637.4179))
        Line((2231.3342, 637.4179), (2235.2165, 622.929))
        Line((2235.2165, 622.929), (2202.6787, 614.2106))
        RadiusArc((2202.6787, 614.2106), (2172.9802, 562.7713), -42.0)
        Line((2172.9802, 562.7713), (2207.1444, 435.2691))
        Line((2207.1444, 435.2691), (1559.974, 261.8604))
        Line((1559.974, 261.8604), (1478.2022, 237.2998))
        Line((1478.2022, 237.2998), (1503.003, 154.7283))
        Line((1503.003, 154.7283), (2529.392, 384.1404))
    _inc_edges_sk_Sketch5_4 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch5_4 = Wire.combine(_inc_edges_sk_Sketch5_4)[0]
_wire_sk_Sketch5_4 = _wire_sk_Sketch5_4.moved(_inclined_plane_4.location)
_mkf_sk_Sketch5_4 = BRepBuilderAPI_MakeFace(_inclined_plane_4.wrapped, _wire_sk_Sketch5_4.wrapped, True)
_face_sk_Sketch5_4 = Face(_mkf_sk_Sketch5_4.Face())

# 'Sketch6': 30 segments → Line/RadiusArc profile
_inclined_plane_5 = Plane(
    origin=Vector(39.033, -145.6743, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_5) as sk_Sketch6_5:
    with BuildLine():
        Line((-74.6605, 2305.7709), (-82.7917, 2227.9876))
        Line((-82.7917, 2227.9876), (-83.5226, 2221.0892))
        Line((-83.5226, 2221.0892), (50.585, 2221.0892))
        Line((50.585, 2221.0892), (50.585, 2546.1609))
        Line((50.585, 2546.1609), (-341.7648, 2546.1609))
        Line((-341.7648, 2546.1609), (-341.7648, 2230.8899))
        Line((-341.7648, 2230.8899), (-265.6977, 2230.8899))
        Line((-265.6977, 2230.8899), (-265.6977, 2385.513))
        Line((-265.6977, 2385.513), (-265.6977, 2230.8899))
        Line((-265.6977, 2230.8899), (-265.6977, 2385.513))
        Line((-265.6977, 2385.513), (-265.6977, 2230.8899))
        Line((-265.6977, 2230.8899), (-265.6977, 2385.513))
        Line((-265.6977, 2385.513), (-265.6977, 2230.8899))
        Line((-265.6977, 2230.8899), (-265.6977, 2385.513))
        Line((-265.6977, 2385.513), (-265.6977, 2230.8899))
        Line((-265.6977, 2230.8899), (-265.6977, 2385.513))
        Line((-265.6977, 2385.513), (-265.6977, 2230.8899))
        Line((-265.6977, 2230.8899), (-265.6977, 2385.513))
        Line((-265.6977, 2385.513), (-265.6977, 2230.8899))
        Line((-265.6977, 2230.8899), (-265.6977, 2385.513))
        Line((-265.6977, 2385.513), (-265.6977, 2230.8899))
        Line((-265.6977, 2394.5941), (-265.6977, 2385.513))
        Line((-264.2408, 2411.6013), (-265.6977, 2394.5941))
        Line((-261.9004, 2421.8893), (-264.2408, 2411.6013))
        RadiusArc((-73.872, 2434.1927), (-261.9004, 2421.8893), -100.0)
        RadiusArc((-65.9361, 2401.1222), (-73.872, 2434.1927), -102.7513)
        Line((-65.7226, 2393.4212), (-65.9361, 2401.1222))
        Line((-66.2379, 2384.2139), (-65.7226, 2393.4212))
        Line((-74.6605, 2305.7709), (-66.2379, 2384.2139))
        Line((-66.2379, 2384.2139), (-74.6605, 2305.7709))
    _inc_edges_sk_Sketch6_5 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch6_5 = Wire.combine(_inc_edges_sk_Sketch6_5)[0]
_wire_sk_Sketch6_5 = _wire_sk_Sketch6_5.moved(_inclined_plane_5.location)
_mkf_sk_Sketch6_5 = BRepBuilderAPI_MakeFace(_inclined_plane_5.wrapped, _wire_sk_Sketch6_5.wrapped, True)
_face_sk_Sketch6_5 = Face(_mkf_sk_Sketch6_5.Face())

# 'Sketch8': 7 segments → Line/RadiusArc profile
_inclined_plane_6 = Plane(
    origin=Vector(-32.1422, 119.9552, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_6) as sk_Sketch8_6:
    with BuildLine():
        Line((-139.0683, 2345.0966), (-127.3948, 2333.665))
        Line((-127.3948, 2333.665), (-125.2499, 2331.9018))
        Line((-125.2499, 2331.9018), (-122.8325, 2330.5358))
        # Arc split: sweep=228.98deg >= 150 — emitted as two half-arcs
        RadiusArc((-122.8325, 2330.5358), (-100.2002, 2345.0965), -16.0)
        RadiusArc((-100.2002, 2345.0965), (-122.8325, 2359.6572), -16.0)
        Line((-122.8325, 2359.6572), (-125.2499, 2358.2914))
        Line((-125.2499, 2358.2914), (-127.3948, 2356.5281))
        Line((-127.3948, 2356.5281), (-139.0683, 2345.0966))
    _inc_edges_sk_Sketch8_6 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch8_6 = Wire.combine(_inc_edges_sk_Sketch8_6)[0]
_wire_sk_Sketch8_6 = _wire_sk_Sketch8_6.moved(_inclined_plane_6.location)
_mkf_sk_Sketch8_6 = BRepBuilderAPI_MakeFace(_inclined_plane_6.wrapped, _wire_sk_Sketch8_6.wrapped, True)
_face_sk_Sketch8_6 = Face(_mkf_sk_Sketch8_6.Face())

# 'Sketch9': 5 segments → Line/RadiusArc profile
_inclined_plane_7 = Plane(
    origin=Vector(-32.1422, 119.9553, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_7) as sk_Sketch9_7:
    with BuildLine():
        Line((-226.3898, 2333.665), (-238.0633, 2345.0966))
        Line((-238.0633, 2345.0966), (-226.3898, 2356.5281))
        RadiusArc((-226.3898, 2356.5281), (-219.2102, 2360.5845), 15.9994)
        # Arc split: sweep=228.98deg >= 150 — emitted as two half-arcs
        RadiusArc((-219.2102, 2360.5845), (-199.436, 2342.3303), 16.0)
        RadiusArc((-199.436, 2342.3303), (-224.2448, 2331.9018), 16.0)
        Line((-224.2448, 2331.9018), (-226.3898, 2333.665))
    _inc_edges_sk_Sketch9_7 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch9_7 = Wire.combine(_inc_edges_sk_Sketch9_7)[0]
_wire_sk_Sketch9_7 = _wire_sk_Sketch9_7.moved(_inclined_plane_7.location)
_mkf_sk_Sketch9_7 = BRepBuilderAPI_MakeFace(_inclined_plane_7.wrapped, _wire_sk_Sketch9_7.wrapped, True)
_face_sk_Sketch9_7 = Face(_mkf_sk_Sketch9_7.Face())

# 'Sketch10': 3 segments → Line/RadiusArc profile
_inclined_plane_8 = Plane(
    origin=Vector(-32.1423, 119.9553, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_8) as sk_Sketch10_8:
    with BuildLine():
        Line((-176.8923, 2383.1625), (-188.5658, 2394.594))
        Line((-188.5658, 2394.594), (-176.8923, 2406.0256))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-176.8923, 2406.0256), (-149.6978, 2394.594), 15.9999)
        RadiusArc((-149.6978, 2394.594), (-176.8923, 2383.1625), 15.9999)
    _inc_edges_sk_Sketch10_8 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch10_8 = Wire.combine(_inc_edges_sk_Sketch10_8)[0]
_wire_sk_Sketch10_8 = _wire_sk_Sketch10_8.moved(_inclined_plane_8.location)
_mkf_sk_Sketch10_8 = BRepBuilderAPI_MakeFace(_inclined_plane_8.wrapped, _wire_sk_Sketch10_8.wrapped, True)
_face_sk_Sketch10_8 = Face(_mkf_sk_Sketch10_8.Face())

# 'Sketch11': 3 segments → Line/RadiusArc profile
_inclined_plane_9 = Plane(
    origin=Vector(-32.1423, 119.9552, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_9) as sk_Sketch11_9:
    with BuildLine():
        Line((-226.3898, 2432.6599), (-238.0633, 2444.0916))
        Line((-238.0633, 2444.0916), (-226.3898, 2455.5231))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-226.3898, 2455.5231), (-199.195, 2444.0916), 16.0001)
        RadiusArc((-199.195, 2444.0916), (-226.3898, 2432.6599), 16.0001)
    _inc_edges_sk_Sketch11_9 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch11_9 = Wire.combine(_inc_edges_sk_Sketch11_9)[0]
_wire_sk_Sketch11_9 = _wire_sk_Sketch11_9.moved(_inclined_plane_9.location)
_mkf_sk_Sketch11_9 = BRepBuilderAPI_MakeFace(_inclined_plane_9.wrapped, _wire_sk_Sketch11_9.wrapped, True)
_face_sk_Sketch11_9 = Face(_mkf_sk_Sketch11_9.Face())

# 'Sketch12': 3 segments → Line/RadiusArc profile
_inclined_plane_10 = Plane(
    origin=Vector(-32.1423, 119.9552, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_10) as sk_Sketch12_10:
    with BuildLine():
        Line((-127.3948, 2432.6599), (-139.0683, 2444.0916))
        Line((-139.0683, 2444.0916), (-127.3948, 2455.5231))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-127.3948, 2455.5231), (-100.2, 2444.0916), 16.0001)
        RadiusArc((-100.2, 2444.0916), (-127.3948, 2432.6599), 16.0001)
    _inc_edges_sk_Sketch12_10 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch12_10 = Wire.combine(_inc_edges_sk_Sketch12_10)[0]
_wire_sk_Sketch12_10 = _wire_sk_Sketch12_10.moved(_inclined_plane_10.location)
_mkf_sk_Sketch12_10 = BRepBuilderAPI_MakeFace(_inclined_plane_10.wrapped, _wire_sk_Sketch12_10.wrapped, True)
_face_sk_Sketch12_10 = Face(_mkf_sk_Sketch12_10.Face())

# 'Sketch13': 4 segments → Line/RadiusArc profile
_inclined_plane_11 = Plane(
    origin=Vector(-32.1422, 119.9553, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_11) as sk_Sketch13_11:
    with BuildLine():
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-234.086, 2325.8058), (-188.1949, 2345.0966), -27.0001)
        RadiusArc((-188.1949, 2345.0966), (-234.086, 2364.3873), -27.0001)
        Line((-234.086, 2364.3873), (-251.9681, 2346.8758))
        Line((-251.9681, 2346.8758), (-253.7851, 2345.0965))
        Line((-253.7851, 2345.0965), (-234.086, 2325.8058))
    _inc_edges_sk_Sketch13_11 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch13_11 = Wire.combine(_inc_edges_sk_Sketch13_11)[0]
_wire_sk_Sketch13_11 = _wire_sk_Sketch13_11.moved(_inclined_plane_11.location)
_mkf_sk_Sketch13_11 = BRepBuilderAPI_MakeFace(_inclined_plane_11.wrapped, _wire_sk_Sketch13_11.wrapped, True)
_face_sk_Sketch13_11 = Face(_mkf_sk_Sketch13_11.Face())

# 'Sketch14': 4 segments → Line/RadiusArc profile
_inclined_plane_12 = Plane(
    origin=Vector(-32.1422, 119.9553, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_12) as sk_Sketch14_12:
    with BuildLine():
        Line((-135.0911, 2325.8058), (-154.7902, 2345.0965))
        Line((-154.7902, 2345.0965), (-152.9731, 2346.8758))
        Line((-152.9731, 2346.8758), (-135.0911, 2364.3873))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-135.0911, 2364.3873), (-89.2, 2345.0966), 27.0001)
        RadiusArc((-89.2, 2345.0966), (-135.0911, 2325.8058), 27.0001)
    _inc_edges_sk_Sketch14_12 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch14_12 = Wire.combine(_inc_edges_sk_Sketch14_12)[0]
_wire_sk_Sketch14_12 = _wire_sk_Sketch14_12.moved(_inclined_plane_12.location)
_mkf_sk_Sketch14_12 = BRepBuilderAPI_MakeFace(_inclined_plane_12.wrapped, _wire_sk_Sketch14_12.wrapped, True)
_face_sk_Sketch14_12 = Face(_mkf_sk_Sketch14_12.Face())

# 'Sketch15': 16 segments → Line/RadiusArc profile
_inclined_plane_13 = Plane(
    origin=Vector(-32.1423, 119.9553, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_13) as sk_Sketch15_13:
    with BuildLine():
        Line((-213.3345, 2417.1557), (-208.6855, 2417.888))
        Line((-208.6855, 2417.888), (-204.2341, 2419.4164))
        Line((-204.2341, 2419.4164), (-200.1159, 2421.6947))
        Line((-200.1159, 2421.6947), (-196.4558, 2424.6535))
        RadiusArc((-196.4558, 2424.6535), (-188.3454, 2441.2465), -27.0001)
        Line((-188.3454, 2441.2465), (-187.0951, 2453.046))
        RadiusArc((-187.0951, 2453.046), (-170.1542, 2459.137), 10.0)
        Line((-170.1542, 2459.137), (-135.0911, 2424.8007))
        RadiusArc((-135.0911, 2424.8007), (-119.0452, 2417.2418), -27.0001)
        Line((-119.0452, 2417.2418), (-67.1796, 2411.746))
        Line((-67.1796, 2411.746), (-48.4042, 2410.6894))
        Line((-48.4042, 2410.6894), (-115.6928, 2516.707))
        Line((-115.6928, 2516.707), (-245.5102, 2479.709))
        Line((-245.5102, 2479.709), (-261.9004, 2421.8893))
        Line((-261.9004, 2421.8893), (-218.0402, 2417.2418))
        Line((-218.0402, 2417.2418), (-213.3345, 2417.1557))
    _inc_edges_sk_Sketch15_13 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch15_13 = Wire.combine(_inc_edges_sk_Sketch15_13)[0]
_wire_sk_Sketch15_13 = _wire_sk_Sketch15_13.moved(_inclined_plane_13.location)
_mkf_sk_Sketch15_13 = BRepBuilderAPI_MakeFace(_inclined_plane_13.wrapped, _wire_sk_Sketch15_13.wrapped, True)
_face_sk_Sketch15_13 = Face(_mkf_sk_Sketch15_13.Face())

# 'Sketch17': 8 segments → Line/RadiusArc profile
_inclined_plane_14 = Plane(
    origin=Vector(39.033, -145.6743, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_14) as sk_Sketch17_14:
    with BuildLine():
        Line((-104.8423, 2304.5941), (-78.7161, 2304.5941))
        Line((-78.7161, 2304.5941), (-53.0475, 2333.8696))
        Line((-53.0475, 2333.8696), (-289.8158, 2363.3623))
        Line((-289.8158, 2363.3623), (-286.4124, 2319.2318))
        Line((-286.4124, 2319.2318), (-265.6977, 2320.2796))
        Line((-265.6977, 2320.2796), (-232.6107, 2320.2796))
        RadiusArc((-232.6107, 2320.2796), (-122.1087, 2304.5941), -99.9995)
        Line((-122.1087, 2304.5941), (-104.8423, 2304.5941))
    _inc_edges_sk_Sketch17_14 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch17_14 = Wire.combine(_inc_edges_sk_Sketch17_14)[0]
_wire_sk_Sketch17_14 = _wire_sk_Sketch17_14.moved(_inclined_plane_14.location)
_mkf_sk_Sketch17_14 = BRepBuilderAPI_MakeFace(_inclined_plane_14.wrapped, _wire_sk_Sketch17_14.wrapped, True)
_face_sk_Sketch17_14 = Face(_mkf_sk_Sketch17_14.Face())

# 'Sketch18': 92 segments → Line/RadiusArc profile
_inclined_plane_15 = Plane(
    origin=Vector(39.033, -145.6743, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_15) as sk_Sketch18_15:
    with BuildLine():
        Line((-130.8451, 2211.6495), (-130.5875, 2211.4502))
        Line((-130.5875, 2211.4502), (-130.3482, 2211.2293))
        Line((-130.3482, 2211.2293), (-130.1089, 2211.0084))
        Line((-130.1089, 2211.0084), (-129.6919, 2210.5083))
        Line((-129.6919, 2210.5083), (-129.2754, 2210.0088))
        Line((-129.2754, 2210.0088), (-128.9511, 2209.444))
        Line((-128.9511, 2209.444), (-128.6273, 2208.8801))
        Line((-128.6273, 2208.8801), (-128.4054, 2208.2677))
        Line((-128.4054, 2208.2677), (-128.184, 2207.6563))
        Line((-128.184, 2207.6563), (-128.0714, 2207.0149))
        Line((-128.0714, 2207.0149), (-127.959, 2206.3744))
        Line((-127.959, 2206.3744), (-127.9448, 2206.0489))
        Line((-127.9448, 2206.0489), (-127.9307, 2205.7237))
        Line((-127.9307, 2205.7237), (-127.9448, 2205.3981))
        Line((-127.9448, 2205.3981), (-127.959, 2205.0729))
        Line((-127.959, 2205.0729), (-128.0716, 2204.4313))
        Line((-128.0716, 2204.4313), (-128.184, 2203.791))
        Line((-128.184, 2203.791), (-128.4059, 2203.1785))
        Line((-128.4059, 2203.1785), (-128.6273, 2202.5672))
        Line((-128.6273, 2202.5672), (-128.9517, 2202.0023))
        Line((-128.9517, 2202.0023), (-129.2754, 2201.4385))
        Line((-129.2754, 2201.4385), (-129.6926, 2200.9382))
        Line((-129.6926, 2200.9382), (-130.1089, 2200.4389))
        Line((-130.1089, 2200.4389), (-130.6063, 2200.0183))
        Line((-130.6063, 2200.0183), (-131.1027, 2199.5984))
        Line((-131.1027, 2199.5984), (-131.3644, 2199.4293))
        Line((-131.3644, 2199.4293), (-131.6652, 2199.2702))
        Line((-131.6652, 2199.2702), (-131.9265, 2199.1013))
        Line((-131.9265, 2199.1013), (-132.2268, 2198.9425))
        Line((-132.2268, 2198.9425), (-132.5255, 2198.8168))
        Line((-132.5255, 2198.8168), (-132.8375, 2198.7164))
        Line((-132.8375, 2198.7164), (-133.1368, 2198.5905))
        Line((-133.1368, 2198.5905), (-133.4474, 2198.4906))
        Line((-133.4474, 2198.4906), (-133.7646, 2198.4183))
        Line((-133.7646, 2198.4183), (-134.0878, 2198.3736))
        Line((-134.0878, 2198.3736), (-134.4038, 2198.3015))
        Line((-134.4038, 2198.3015), (-134.7278, 2198.2566))
        Line((-134.7278, 2198.2566), (-135.0537, 2198.2402))
        Line((-135.0537, 2198.2402), (-135.3785, 2198.2521))
        Line((-135.3785, 2198.2521), (-135.7038, 2198.2356))
        Line((-135.7038, 2198.2356), (-136.0293, 2198.2475))
        Line((-136.0293, 2198.2475), (-136.3527, 2198.2877))
        Line((-136.3527, 2198.2877), (-136.6709, 2198.3556))
        Line((-136.6709, 2198.3556), (-136.995, 2198.3958))
        Line((-136.995, 2198.3958), (-137.3128, 2198.4636))
        Line((-137.3128, 2198.4636), (-137.6259, 2198.5596))
        Line((-137.6259, 2198.5596), (-137.9259, 2198.6808))
        Line((-137.9259, 2198.6808), (-138.2379, 2198.7764))
        Line((-138.2379, 2198.7764), (-138.5396, 2198.8983))
        Line((-138.5396, 2198.8983), (-138.8873, 2199.0792))
        Line((-138.8873, 2199.0792), (-139.1057, 2199.2182))
        Line((-139.1057, 2199.2182), (-139.454, 2199.3994))
        Line((-139.454, 2199.3994), (-139.6727, 2199.5386))
        Line((-139.6727, 2199.5386), (-140.175, 2199.9515))
        Line((-140.175, 2199.9515), (-140.6782, 2200.3651))
        Line((-140.6782, 2200.3651), (-143.4017, 2203.0322))
        Line((-143.4017, 2203.0322), (-146.1501, 2205.7237))
        Line((-146.1501, 2205.7237), (-143.4238, 2208.3934))
        Line((-143.4238, 2208.3934), (-140.6782, 2211.0822))
        Line((-140.6782, 2211.0822), (-140.4359, 2211.2997))
        Line((-140.4359, 2211.2997), (-140.1934, 2211.5173))
        Line((-140.1934, 2211.5173), (-139.9331, 2211.7129))
        Line((-139.9331, 2211.7129), (-139.6727, 2211.9087))
        Line((-139.6727, 2211.9087), (-139.3965, 2212.081))
        Line((-139.3965, 2212.081), (-139.1201, 2212.2535))
        Line((-139.1201, 2212.2535), (-138.8299, 2212.4011))
        Line((-138.8299, 2212.4011), (-138.5396, 2212.5489))
        Line((-138.5396, 2212.5489), (-138.2376, 2212.671))
        Line((-138.2376, 2212.671), (-137.9356, 2212.793))
        Line((-137.9356, 2212.793), (-137.6242, 2212.8883))
        Line((-137.6242, 2212.8883), (-137.3128, 2212.9837))
        Line((-137.3128, 2212.9837), (-136.9943, 2213.0516))
        Line((-136.9943, 2213.0516), (-136.6757, 2213.1196))
        Line((-136.6757, 2213.1196), (-136.3525, 2213.1597))
        Line((-136.3525, 2213.1597), (-136.0293, 2213.1997))
        Line((-136.0293, 2213.1997), (-135.7038, 2213.2116))
        Line((-135.7038, 2213.2116), (-135.3783, 2213.2235))
        Line((-135.3783, 2213.2235), (-135.053, 2213.207))
        Line((-135.053, 2213.207), (-134.7278, 2213.1907))
        Line((-134.7278, 2213.1907), (-134.4051, 2213.1461))
        Line((-134.4051, 2213.1461), (-134.0825, 2213.1015))
        Line((-134.0825, 2213.1015), (-133.7649, 2213.0291))
        Line((-133.7649, 2213.0291), (-133.4474, 2212.9567))
        Line((-133.4474, 2212.9567), (-133.1373, 2212.857))
        Line((-133.1373, 2212.857), (-132.8273, 2212.7574))
        Line((-132.8273, 2212.7574), (-132.527, 2212.6311))
        Line((-132.527, 2212.6311), (-132.2268, 2212.5049))
        Line((-132.2268, 2212.5049), (-131.9386, 2212.3531))
        Line((-131.9386, 2212.3531), (-131.6505, 2212.2013))
        Line((-131.6505, 2212.2013), (-131.3765, 2212.0251))
        Line((-131.3765, 2212.0251), (-131.1027, 2211.8489))
        Line((-131.1027, 2211.8489), (-130.8451, 2211.6495))
    _inc_edges_sk_Sketch18_15 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch18_15 = Wire.combine(_inc_edges_sk_Sketch18_15)[0]
_wire_sk_Sketch18_15 = _wire_sk_Sketch18_15.moved(_inclined_plane_15.location)
_mkf_sk_Sketch18_15 = BRepBuilderAPI_MakeFace(_inclined_plane_15.wrapped, _wire_sk_Sketch18_15.wrapped, True)
_face_sk_Sketch18_15 = Face(_mkf_sk_Sketch18_15.Face())

# 'Sketch19': 128 segments → Line/RadiusArc profile
_inclined_plane_16 = Plane(
    origin=Vector(39.033, -145.6743, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_16) as sk_Sketch19_16:
    with BuildLine():
        Line((-149.2738, 2099.5557), (-149.6384, 2099.7836))
        Line((-149.6384, 2099.7836), (-149.6836, 2099.8007))
        Line((-149.6836, 2099.8007), (-149.7528, 2099.8342))
        Line((-149.7528, 2099.8342), (-150.2044, 2100.1041))
        Line((-150.2044, 2100.1041), (-150.2979, 2100.1626))
        Line((-150.2979, 2100.1626), (-150.3476, 2100.1923))
        Line((-150.3476, 2100.1923), (-150.7598, 2100.5415))
        Line((-150.7598, 2100.5415), (-151.2153, 2100.9218))
        Line((-151.2153, 2100.9218), (-153.7875, 2103.4407))
        Line((-153.7875, 2103.4407), (-153.9386, 2103.5886))
        Line((-153.9386, 2103.5886), (-156.6873, 2106.2803))
        Line((-156.6873, 2106.2803), (-153.9644, 2108.9467))
        Line((-153.9644, 2108.9467), (-151.2153, 2111.6389))
        Line((-151.2153, 2111.6389), (-150.7585, 2112.0201))
        Line((-150.7585, 2112.0201), (-150.3311, 2112.3804))
        Line((-150.3311, 2112.3804), (-150.2835, 2112.4087))
        Line((-150.2835, 2112.4087), (-150.205, 2112.4575))
        Line((-150.205, 2112.4575), (-149.8392, 2112.6848))
        Line((-149.8392, 2112.6848), (-149.3768, 2112.96))
        Line((-149.3768, 2112.96), (-149.1757, 2113.0498))
        Line((-149.1757, 2113.0498), (-149.1118, 2113.0805))
        Line((-149.1118, 2113.0805), (-149.0723, 2113.0954))
        Line((-149.0723, 2113.0954), (-148.5687, 2113.2857))
        Line((-148.5687, 2113.2857), (-148.3178, 2113.3977))
        Line((-148.3178, 2113.3977), (-148.2079, 2113.4206))
        Line((-148.2079, 2113.4206), (-147.8472, 2113.5292))
        Line((-147.8472, 2113.5292), (-147.7666, 2113.5536))
        Line((-147.7666, 2113.5536), (-147.3001, 2113.6507))
        Line((-147.3001, 2113.6507), (-146.872, 2113.7256))
        Line((-146.872, 2113.7256), (-146.7398, 2113.7335))
        Line((-146.7398, 2113.7335), (-146.653, 2113.7435))
        Line((-146.653, 2113.7435), (-146.566, 2113.7458))
        Line((-146.566, 2113.7458), (-146.2902, 2113.7625))
        Line((-146.2902, 2113.7625), (-145.7996, 2113.7753))
        Line((-145.7996, 2113.7753), (-145.4249, 2113.7587))
        Line((-145.4249, 2113.7587), (-145.2661, 2113.738))
        Line((-145.2661, 2113.738), (-144.8429, 2113.6829))
        Line((-144.8429, 2113.6829), (-144.7453, 2113.661))
        Line((-144.7453, 2113.661), (-144.3862, 2113.6098))
        Line((-144.3862, 2113.6098), (-144.1057, 2113.5424))
        Line((-144.1057, 2113.5424), (-143.9873, 2113.5043))
        Line((-143.9873, 2113.5043), (-143.9398, 2113.493))
        Line((-143.9398, 2113.493), (-143.5063, 2113.3533))
        Line((-143.5063, 2113.3533), (-142.9439, 2113.1388))
        Line((-142.9439, 2113.1388), (-142.7693, 2113.0506))
        Line((-142.7693, 2113.0506), (-142.4176, 2112.873))
        Line((-142.4176, 2112.873), (-142.3312, 2112.8187))
        Line((-142.3312, 2112.8187), (-142.3091, 2112.8103))
        Line((-142.3091, 2112.8103), (-141.8324, 2112.5366))
        Line((-141.8324, 2112.5366), (-141.7711, 2112.4893))
        Line((-141.7711, 2112.4893), (-141.6478, 2112.3952))
        Line((-141.6478, 2112.3952), (-141.3308, 2112.1501))
        Line((-141.3308, 2112.1501), (-140.9889, 2111.8892))
        Line((-140.9889, 2111.8892), (-140.8102, 2111.7133))
        Line((-140.8102, 2111.7133), (-140.6579, 2111.5536))
        Line((-140.6579, 2111.5536), (-140.3993, 2111.2821))
        Line((-140.3993, 2111.2821), (-140.3416, 2111.2093))
        Line((-140.3416, 2111.2093), (-140.2232, 2111.0927))
        Line((-140.2232, 2111.0927), (-139.9899, 2110.8092))
        Line((-139.9899, 2110.8092), (-139.8897, 2110.6556))
        Line((-139.8897, 2110.6556), (-139.8278, 2110.5557))
        Line((-139.8278, 2110.5557), (-139.5546, 2110.1147))
        Line((-139.5546, 2110.1147), (-139.3315, 2109.7728))
        Line((-139.3315, 2109.7728), (-139.2791, 2109.6509))
        Line((-139.2791, 2109.6509), (-139.1806, 2109.4296))
        Line((-139.1806, 2109.4296), (-139.0343, 2109.1009))
        Line((-139.0343, 2109.1009), (-139.009, 2109.0266))
        Line((-139.009, 2109.0266), (-138.8727, 2108.7093))
        Line((-138.8727, 2108.7093), (-138.8224, 2108.5022))
        Line((-138.8224, 2108.5022), (-138.7338, 2108.2098))
        Line((-138.7338, 2108.2098), (-138.7184, 2108.159))
        Line((-138.7184, 2108.159), (-138.6252, 2107.6326))
        Line((-138.6252, 2107.6326), (-138.5349, 2107.2605))
        Line((-138.5349, 2107.2605), (-138.5329, 2107.1966))
        Line((-138.5329, 2107.1966), (-138.5122, 2106.9301))
        Line((-138.5122, 2106.9301), (-138.4969, 2106.4557))
        Line((-138.4969, 2106.4557), (-138.5165, 2106.2796))
        Line((-138.5165, 2106.2796), (-138.4904, 2105.9431))
        Line((-138.4904, 2105.9431), (-138.519, 2105.6318))
        Line((-138.519, 2105.6318), (-138.5585, 2105.2771))
        Line((-138.5585, 2105.2771), (-138.6325, 2104.9916))
        Line((-138.6325, 2104.9916), (-138.6644, 2104.644))
        Line((-138.6644, 2104.644), (-138.7421, 2104.3532))
        Line((-138.7421, 2104.3532), (-138.8025, 2104.1199))
        Line((-138.8025, 2104.1199), (-138.9612, 2103.741))
        Line((-138.9612, 2103.741), (-139.0395, 2103.4479))
        Line((-139.0395, 2103.4479), (-139.1837, 2103.1325))
        Line((-139.1837, 2103.1325), (-139.2328, 2103.0153))
        Line((-139.2328, 2103.0153), (-139.5023, 2102.5653))
        Line((-139.5023, 2102.5653), (-139.6294, 2102.2874))
        Line((-139.6294, 2102.2874), (-139.823, 2102.0023))
        Line((-139.823, 2102.0023), (-139.8288, 2101.9926))
        Line((-139.8288, 2101.9926), (-140.1704, 2101.573))
        Line((-140.1704, 2101.573), (-140.2433, 2101.5059))
        Line((-140.2433, 2101.5059), (-140.3872, 2101.2939))
        Line((-140.3872, 2101.2939), (-140.6597, 2101.0092))
        Line((-140.6597, 2101.0092), (-140.9825, 2100.7123))
        Line((-140.9825, 2100.7123), (-141.1583, 2100.5921))
        Line((-141.1583, 2100.5921), (-141.3345, 2100.4078))
        Line((-141.3345, 2100.4078), (-141.6514, 2100.1713))
        Line((-141.6514, 2100.1713), (-141.9234, 2099.9855))
        Line((-141.9234, 2099.9855), (-142.2127, 2099.8439))
        Line((-142.2127, 2099.8439), (-142.3732, 2099.7241))
        Line((-142.3732, 2099.7241), (-142.4325, 2099.6875))
        Line((-142.4325, 2099.6875), (-142.7727, 2099.5168))
        Line((-142.7727, 2099.5168), (-142.9696, 2099.4205))
        Line((-142.9696, 2099.4205), (-143.381, 2099.2884))
        Line((-143.381, 2099.2884), (-143.5618, 2099.1976))
        Line((-143.5618, 2099.1976), (-143.9891, 2099.0615))
        Line((-143.9891, 2099.0615), (-144.0934, 2099.028))
        Line((-144.0934, 2099.028), (-144.6306, 2098.9382))
        Line((-144.6306, 2098.9382), (-144.7667, 2098.8948))
        Line((-144.7667, 2098.8948), (-144.8459, 2098.8772))
        Line((-144.8459, 2098.8772), (-145.2691, 2098.8217))
        Line((-145.2691, 2098.8217), (-145.8102, 2098.8104))
        Line((-145.8102, 2098.8104), (-145.916, 2098.8237))
        Line((-145.916, 2098.8237), (-146.0681, 2098.8037))
        Line((-146.0681, 2098.8037), (-146.5655, 2098.8165))
        Line((-146.5655, 2098.8165), (-147.0007, 2098.8709))
        Line((-147.0007, 2098.8709), (-147.2054, 2098.9274))
        Line((-147.2054, 2098.9274), (-147.297, 2098.9297))
        Line((-147.297, 2098.9297), (-147.3848, 2098.9399))
        Line((-147.3848, 2098.9399), (-147.846, 2099.036))
        Line((-147.846, 2099.036), (-148.1625, 2099.1233))
        Line((-148.1625, 2099.1233), (-148.4578, 2099.253))
        Line((-148.4578, 2099.253), (-148.565, 2099.2754))
        Line((-148.565, 2099.2754), (-149.0716, 2099.467))
        Line((-149.0716, 2099.467), (-149.2738, 2099.5557))
    _inc_edges_sk_Sketch19_16 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch19_16 = Wire.combine(_inc_edges_sk_Sketch19_16)[0]
_wire_sk_Sketch19_16 = _wire_sk_Sketch19_16.moved(_inclined_plane_16.location)
_mkf_sk_Sketch19_16 = BRepBuilderAPI_MakeFace(_inclined_plane_16.wrapped, _wire_sk_Sketch19_16.wrapped, True)
_face_sk_Sketch19_16 = Face(_mkf_sk_Sketch19_16.Face())

# 'Sketch20': 138 segments → Line/RadiusArc profile
_inclined_plane_17 = Plane(
    origin=Vector(39.033, -145.6743, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_17) as sk_Sketch20_17:
    with BuildLine():
        Line((-160.0655, 2000.2597), (-160.1765, 2000.3384))
        Line((-160.1765, 2000.3384), (-160.2147, 2000.3527))
        Line((-160.2147, 2000.3527), (-160.2854, 2000.3868))
        Line((-160.2854, 2000.3868), (-160.7423, 2000.6591))
        Line((-160.7423, 2000.6591), (-160.9516, 2000.8076))
        Line((-160.9516, 2000.8076), (-161.2475, 2001.0684))
        Line((-161.2475, 2001.0684), (-161.2948, 2001.0966))
        Line((-161.2948, 2001.0966), (-161.7524, 2001.4785))
        Line((-161.7524, 2001.4785), (-162.1271, 2001.8454))
        Line((-162.1271, 2001.8454), (-164.8577, 2004.5194))
        Line((-164.8577, 2004.5194), (-167.2244, 2006.837))
        Line((-167.2244, 2006.837), (-164.4961, 2009.5087))
        Line((-164.4961, 2009.5087), (-161.7524, 2012.1956))
        Line((-161.7524, 2012.1956), (-161.3219, 2012.558))
        Line((-161.3219, 2012.558), (-161.0577, 2012.7935))
        Line((-161.0577, 2012.7935), (-160.9826, 2012.8391))
        Line((-160.9826, 2012.8391), (-160.7429, 2013.0157))
        Line((-160.7429, 2013.0157), (-160.7085, 2013.0411))
        Line((-160.7085, 2013.0411), (-160.2757, 2013.3037))
        Line((-160.2757, 2013.3037), (-159.9931, 2013.4752))
        Line((-159.9931, 2013.4752), (-159.739, 2013.5874))
        Line((-159.739, 2013.5874), (-159.6699, 2013.6212))
        Line((-159.6699, 2013.6212), (-159.6067, 2013.6455))
        Line((-159.6067, 2013.6455), (-159.2721, 2013.7933))
        Line((-159.2721, 2013.7933), (-158.7883, 2013.9794))
        Line((-158.7883, 2013.9794), (-158.512, 2014.0498))
        Line((-158.512, 2014.0498), (-158.3824, 2014.0774))
        Line((-158.3824, 2014.0774), (-158.0776, 2014.1552))
        Line((-158.0776, 2014.1552), (-157.6254, 2014.2514))
        Line((-157.6254, 2014.2514), (-157.2905, 2014.283))
        Line((-157.2905, 2014.283), (-157.2099, 2014.2926))
        Line((-157.2099, 2014.2926), (-157.1024, 2014.296))
        Line((-157.1024, 2014.296), (-156.8732, 2014.3176))
        Line((-156.8732, 2014.3176), (-156.3956, 2014.3322))
        Line((-156.3956, 2014.3322), (-155.9753, 2014.3103))
        Line((-155.9753, 2014.3103), (-155.8036, 2014.2884))
        Line((-155.8036, 2014.2884), (-155.3858, 2014.235))
        Line((-155.3858, 2014.235), (-155.3034, 2014.2169))
        Line((-155.3034, 2014.2169), (-155.1973, 2014.2114))
        Line((-155.1973, 2014.2114), (-154.7085, 2014.118))
        Line((-154.7085, 2014.118), (-154.6638, 2014.1034))
        Line((-154.6638, 2014.1034), (-154.5251, 2014.0595))
        Line((-154.5251, 2014.0595), (-154.1281, 2013.9292))
        Line((-154.1281, 2013.9292), (-153.7085, 2013.7962))
        Line((-153.7085, 2013.7962), (-153.4969, 2013.6973))
        Line((-153.4969, 2013.6973), (-153.3086, 2013.603))
        Line((-153.3086, 2013.603), (-152.965, 2013.4307))
        Line((-152.965, 2013.4307), (-152.8927, 2013.3859))
        Line((-152.8927, 2013.3859), (-152.7108, 2013.301))
        Line((-152.7108, 2013.301), (-152.3609, 2013.0865))
        Line((-152.3609, 2013.0865), (-152.3292, 2013.0622))
        Line((-152.3292, 2013.0622), (-152.184, 2012.953))
        Line((-152.184, 2012.953), (-151.9125, 2012.7441))
        Line((-151.9125, 2012.7441), (-151.5884, 2012.5004))
        Line((-151.5884, 2012.5004), (-151.3633, 2012.2889))
        Line((-151.3633, 2012.2889), (-151.1928, 2012.1123))
        Line((-151.1928, 2012.1123), (-150.949, 2011.8598))
        Line((-150.949, 2011.8598), (-150.8969, 2011.7951))
        Line((-150.8969, 2011.7951), (-150.8617, 2011.762))
        Line((-150.8617, 2011.762), (-150.6388, 2011.5099))
        Line((-150.6388, 2011.5099), (-150.5185, 2011.3292))
        Line((-150.5185, 2011.3292), (-150.3694, 2011.1089))
        Line((-150.3694, 2011.1089), (-150.1652, 2010.8073))
        Line((-150.1652, 2010.8073), (-149.9591, 2010.4979))
        Line((-149.9591, 2010.4979), (-149.8375, 2010.2379))
        Line((-149.8375, 2010.2379), (-149.7214, 2009.9843))
        Line((-149.7214, 2009.9843), (-149.5887, 2009.694))
        Line((-149.5887, 2009.694), (-149.5623, 2009.6192))
        Line((-149.5623, 2009.6192), (-149.4511, 2009.3814))
        Line((-149.4511, 2009.3814), (-149.3887, 2009.1366))
        Line((-149.3887, 2009.1366), (-149.274, 2008.7655))
        Line((-149.274, 2008.7655), (-149.2459, 2008.6746))
        Line((-149.2459, 2008.6746), (-149.171, 2008.2612))
        Line((-149.171, 2008.2612), (-149.0878, 2007.9343))
        Line((-149.0878, 2007.9343), (-149.0777, 2007.7984))
        Line((-149.0777, 2007.7984), (-149.0494, 2007.4864))
        Line((-149.0494, 2007.4864), (-149.0322, 2007.2547))
        Line((-149.0322, 2007.2547), (-149.0579, 2006.8363))
        Line((-149.0579, 2006.8363), (-149.032, 2006.5521))
        Line((-149.032, 2006.5521), (-149.032, 2006.4763))
        Line((-149.032, 2006.4763), (-149.0575, 2006.1881))
        Line((-149.0575, 2006.1881), (-149.0715, 2005.9609))
        Line((-149.0715, 2005.9609), (-149.1607, 2005.5466))
        Line((-149.1607, 2005.5466), (-149.1872, 2005.2473))
        Line((-149.1872, 2005.2473), (-149.2728, 2004.9079))
        Line((-149.2728, 2004.9079), (-149.2852, 2004.8503))
        Line((-149.2852, 2004.8503), (-149.4019, 2004.5042))
        Line((-149.4019, 2004.5042), (-149.5, 2004.2991))
        Line((-149.5, 2004.2991), (-149.5608, 2004.0579))
        Line((-149.5608, 2004.0579), (-149.5852, 2003.9882))
        Line((-149.5852, 2003.9882), (-149.7206, 2003.6895))
        Line((-149.7206, 2003.6895), (-149.8575, 2003.4035))
        Line((-149.8575, 2003.4035), (-150.044, 2003.1259))
        Line((-150.044, 2003.1259), (-150.1518, 2002.888))
        Line((-150.1518, 2002.888), (-150.3665, 2002.5631))
        Line((-150.3665, 2002.5631), (-150.4838, 2002.3887))
        Line((-150.4838, 2002.3887), (-150.7435, 2002.0907))
        Line((-150.7435, 2002.0907), (-150.7771, 2002.0593))
        Line((-150.7771, 2002.0593), (-150.892, 2001.8855))
        Line((-150.892, 2001.8855), (-150.9382, 2001.8276))
        Line((-150.9382, 2001.8276), (-151.1925, 2001.5613))
        Line((-151.1925, 2001.5613), (-151.4459, 2001.3258))
        Line((-151.4459, 2001.3258), (-151.6902, 2001.1422))
        Line((-151.6902, 2001.1422), (-151.8419, 2000.9833))
        Line((-151.8419, 2000.9833), (-152.1849, 2000.7222))
        Line((-152.1849, 2000.7222), (-152.2547, 2000.6697))
        Line((-152.2547, 2000.6697), (-152.5945, 2000.4665))
        Line((-152.5945, 2000.4665), (-152.7471, 2000.3958))
        Line((-152.7471, 2000.3958), (-152.8787, 2000.2956))
        Line((-152.8787, 2000.2956), (-152.9434, 2000.255))
        Line((-152.9434, 2000.255), (-153.3076, 2000.069))
        Line((-153.3076, 2000.069), (-153.5115, 1999.9745))
        Line((-153.5115, 1999.9745), (-153.8832, 1999.8476))
        Line((-153.8832, 1999.8476), (-153.9163, 1999.8401))
        Line((-153.9163, 1999.8401), (-154.0744, 1999.7593))
        Line((-154.0744, 1999.7593), (-154.5245, 1999.6129))
        Line((-154.5245, 1999.6129), (-154.8776, 1999.5325))
        Line((-154.8776, 1999.5325), (-155.1648, 1999.4983))
        Line((-155.1648, 1999.4983), (-155.2808, 1999.4606))
        Line((-155.2808, 1999.4606), (-155.3585, 1999.4429))
        Line((-155.3585, 1999.4429), (-155.8036, 1999.3821))
        Line((-155.8036, 1999.3821), (-155.9073, 1999.3698))
        Line((-155.9073, 1999.3698), (-156.2998, 1999.3644))
        Line((-156.2998, 1999.3644), (-156.4535, 1999.3786))
        Line((-156.4535, 1999.3786), (-156.5887, 1999.3601))
        Line((-156.5887, 1999.3601), (-157.103, 1999.3714))
        Line((-157.103, 1999.3714), (-157.3433, 1999.3935))
        Line((-157.3433, 1999.3935), (-157.73, 1999.4706))
        Line((-157.73, 1999.4706), (-157.7449, 1999.4752))
        Line((-157.7449, 1999.4752), (-157.8251, 1999.477))
        Line((-157.8251, 1999.477), (-157.9063, 1999.4861))
        Line((-157.9063, 1999.4861), (-158.3855, 1999.584))
        Line((-158.3855, 1999.584), (-158.7452, 1999.696))
        Line((-158.7452, 1999.696), (-158.9973, 1999.8046))
        Line((-158.9973, 1999.8046), (-159.0922, 1999.8239))
        Line((-159.0922, 1999.8239), (-159.611, 2000.0186))
        Line((-159.611, 2000.0186), (-159.7211, 2000.066))
        Line((-159.7211, 2000.066), (-160.0655, 2000.2597))
    _inc_edges_sk_Sketch20_17 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch20_17 = Wire.combine(_inc_edges_sk_Sketch20_17)[0]
_wire_sk_Sketch20_17 = _wire_sk_Sketch20_17.moved(_inclined_plane_17.location)
_mkf_sk_Sketch20_17 = BRepBuilderAPI_MakeFace(_inclined_plane_17.wrapped, _wire_sk_Sketch20_17.wrapped, True)
_face_sk_Sketch20_17 = Face(_mkf_sk_Sketch20_17.Face())

# 'Sketch21': 143 segments → Line/RadiusArc profile
_inclined_plane_18 = Plane(
    origin=Vector(39.033, -145.6744, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_18) as sk_Sketch21_18:
    with BuildLine():
        Line((-169.6272, 1900.3796), (-170.1482, 1900.5748))
        Line((-170.1482, 1900.5748), (-170.3514, 1900.6703))
        Line((-170.3514, 1900.6703), (-170.6607, 1900.8537))
        Line((-170.6607, 1900.8537), (-170.7149, 1900.8933))
        Line((-170.7149, 1900.8933), (-170.7518, 1900.9072))
        Line((-170.7518, 1900.9072), (-170.8228, 1900.9414))
        Line((-170.8228, 1900.9414), (-171.2806, 1901.2141))
        Line((-171.2806, 1901.2141), (-171.5157, 1901.3858))
        Line((-171.5157, 1901.3858), (-171.7847, 1901.6251))
        Line((-171.7847, 1901.6251), (-171.8316, 1901.653))
        Line((-171.8316, 1901.653), (-172.2896, 1902.0351))
        Line((-172.2896, 1902.0351), (-175.0196, 1904.7086))
        Line((-175.0196, 1904.7086), (-177.7616, 1907.3937))
        Line((-177.7616, 1907.3937), (-175.2464, 1909.8567))
        Line((-175.2464, 1909.8567), (-175.0316, 1910.0671))
        Line((-175.0316, 1910.0671), (-172.2896, 1912.7523))
        Line((-172.2896, 1912.7523), (-171.8638, 1913.1113))
        Line((-171.8638, 1913.1113), (-171.5774, 1913.3645))
        Line((-171.5774, 1913.3645), (-171.4974, 1913.4132))
        Line((-171.4974, 1913.4132), (-171.2791, 1913.5709))
        Line((-171.2791, 1913.5709), (-171.2088, 1913.6217))
        Line((-171.2088, 1913.6217), (-170.7813, 1913.882))
        Line((-170.7813, 1913.882), (-170.4931, 1914.0521))
        Line((-170.4931, 1914.0521), (-170.2819, 1914.1426))
        Line((-170.2819, 1914.1426), (-170.2118, 1914.1771))
        Line((-170.2118, 1914.1771), (-170.1444, 1914.203))
        Line((-170.1444, 1914.203), (-169.6643, 1914.3884))
        Line((-169.6643, 1914.3884), (-169.2965, 1914.5459))
        Line((-169.2965, 1914.5459), (-169.1633, 1914.5744))
        Line((-169.1633, 1914.5744), (-168.92, 1914.6359))
        Line((-168.92, 1914.6359), (-168.6322, 1914.7086))
        Line((-168.6322, 1914.7086), (-168.1827, 1914.8047))
        Line((-168.1827, 1914.8047), (-167.8305, 1914.8435))
        Line((-167.8305, 1914.8435), (-167.751, 1914.8531))
        Line((-167.751, 1914.8531), (-167.6398, 1914.8566))
        Line((-167.6398, 1914.8566), (-167.5115, 1914.8708))
        Line((-167.5115, 1914.8708), (-167.0915, 1914.8664))
        Line((-167.0915, 1914.8664), (-166.6163, 1914.8813))
        Line((-166.6163, 1914.8813), (-166.515, 1914.8695))
        Line((-166.515, 1914.8695), (-166.3408, 1914.8473))
        Line((-166.3408, 1914.8473), (-165.9241, 1914.7943))
        Line((-165.9241, 1914.7943), (-165.8443, 1914.7768))
        Line((-165.8443, 1914.7768), (-165.5808, 1914.7461))
        Line((-165.5808, 1914.7461), (-165.4385, 1914.7012))
        Line((-165.4385, 1914.7012), (-165.0648, 1914.6054))
        Line((-165.0648, 1914.6054), (-164.8123, 1914.5407))
        Line((-164.8123, 1914.5407), (-164.395, 1914.4088))
        Line((-164.395, 1914.4088), (-164.0357, 1914.2563))
        Line((-164.0357, 1914.2563), (-163.845, 1914.1609))
        Line((-163.845, 1914.1609), (-163.5028, 1913.9897))
        Line((-163.5028, 1913.9897), (-163.433, 1913.9464))
        Line((-163.433, 1913.9464), (-163.3491, 1913.9108))
        Line((-163.3491, 1913.9108), (-163.0329, 1913.7321))
        Line((-163.0329, 1913.7321), (-162.8839, 1913.6204))
        Line((-162.8839, 1913.6204), (-162.7255, 1913.5036))
        Line((-162.7255, 1913.5036), (-162.4457, 1913.2973))
        Line((-162.4457, 1913.2973), (-162.1248, 1913.0565))
        Line((-162.1248, 1913.0565), (-161.9091, 1912.843))
        Line((-161.9091, 1912.843), (-161.7354, 1912.6635))
        Line((-161.7354, 1912.6635), (-161.4941, 1912.4142))
        Line((-161.4941, 1912.4142), (-161.4432, 1912.3509))
        Line((-161.4432, 1912.3509), (-161.274, 1912.1835))
        Line((-161.274, 1912.1835), (-161.0498, 1911.9008))
        Line((-161.0498, 1911.9008), (-161.0215, 1911.8569))
        Line((-161.0215, 1911.8569), (-160.8976, 1911.6717))
        Line((-160.8976, 1911.6717), (-160.7313, 1911.4146))
        Line((-160.7313, 1911.4146), (-160.5283, 1911.1108))
        Line((-160.5283, 1911.1108), (-160.3691, 1910.8043))
        Line((-160.3691, 1910.8043), (-160.2499, 1910.5449))
        Line((-160.2499, 1910.5449), (-160.1196, 1910.2614))
        Line((-160.1196, 1910.2614), (-160.0931, 1910.1865))
        Line((-160.0931, 1910.1865), (-160.0876, 1910.1761))
        Line((-160.0876, 1910.1761), (-159.9534, 1909.8431))
        Line((-159.9534, 1909.8431), (-159.8739, 1909.5741))
        Line((-159.8739, 1909.5741), (-159.8093, 1909.3227))
        Line((-159.8093, 1909.3227), (-159.7868, 1909.2463))
        Line((-159.7868, 1909.2463), (-159.7187, 1908.8956))
        Line((-159.7187, 1908.8956), (-159.6368, 1908.5767))
        Line((-159.6368, 1908.5767), (-159.6161, 1908.3631))
        Line((-159.6161, 1908.3631), (-159.5863, 1908.043))
        Line((-159.5863, 1908.043), (-159.5725, 1907.9007))
        Line((-159.5725, 1907.9007), (-159.5723, 1907.5401))
        Line((-159.5723, 1907.5401), (-159.5863, 1907.3927))
        Line((-159.5863, 1907.3927), (-159.5607, 1907.1176))
        Line((-159.5607, 1907.1176), (-159.5605, 1907.0401))
        Line((-159.5605, 1907.0401), (-159.5861, 1906.7443))
        Line((-159.5861, 1906.7443), (-159.6061, 1906.5349))
        Line((-159.6061, 1906.5349), (-159.6737, 1906.1842))
        Line((-159.6737, 1906.1842), (-159.6975, 1906.1035))
        Line((-159.6975, 1906.1035), (-159.7226, 1905.8126))
        Line((-159.7226, 1905.8126), (-159.8095, 1905.4646))
        Line((-159.8095, 1905.4646), (-159.8871, 1905.201))
        Line((-159.8871, 1905.201), (-160.0214, 1904.8664))
        Line((-160.0214, 1904.8664), (-160.0289, 1904.852))
        Line((-160.0289, 1904.852), (-160.0868, 1904.62))
        Line((-160.0868, 1904.62), (-160.1119, 1904.548))
        Line((-160.1119, 1904.548), (-160.2497, 1904.2423))
        Line((-160.2497, 1904.2423), (-160.4065, 1903.9393))
        Line((-160.4065, 1903.9393), (-160.5749, 1903.6784))
        Line((-160.5749, 1903.6784), (-160.6789, 1903.4475))
        Line((-160.6789, 1903.4475), (-160.8973, 1903.1155))
        Line((-160.8973, 1903.1155), (-160.923, 1903.0758))
        Line((-160.923, 1903.0758), (-161.1467, 1902.7927))
        Line((-161.1467, 1902.7927), (-161.3153, 1902.617))
        Line((-161.3153, 1902.617), (-161.4252, 1902.45))
        Line((-161.4252, 1902.45), (-161.4727, 1902.3903))
        Line((-161.4727, 1902.3903), (-161.7308, 1902.119))
        Line((-161.7308, 1902.119), (-161.8107, 1902.0357))
        Line((-161.8107, 1902.0357), (-162.0816, 1901.8025))
        Line((-162.0816, 1901.8025), (-162.2276, 1901.6995))
        Line((-162.2276, 1901.6995), (-162.3746, 1901.5449))
        Line((-162.3746, 1901.5449), (-162.7222, 1901.2794))
        Line((-162.7222, 1901.2794), (-162.8697, 1901.1753))
        Line((-162.8697, 1901.1753), (-163.1832, 1900.9962))
        Line((-163.1832, 1900.9962), (-163.2835, 1900.9511))
        Line((-163.2835, 1900.9511), (-163.41, 1900.8544))
        Line((-163.41, 1900.8544), (-163.4756, 1900.8131))
        Line((-163.4756, 1900.8131), (-163.8441, 1900.6243))
        Line((-163.8441, 1900.6243), (-164.0703, 1900.5225))
        Line((-164.0703, 1900.5225), (-164.4093, 1900.4074))
        Line((-164.4093, 1900.4074), (-164.4535, 1900.3969))
        Line((-164.4535, 1900.3969), (-164.6075, 1900.318))
        Line((-164.6075, 1900.318), (-165.0616, 1900.1697))
        Line((-165.0616, 1900.1697), (-165.3689, 1900.0973))
        Line((-165.3689, 1900.0973), (-165.7016, 1900.0519))
        Line((-165.7016, 1900.0519), (-165.814, 1900.0153))
        Line((-165.814, 1900.0153), (-165.8914, 1899.9975))
        Line((-165.8914, 1899.9975), (-166.3404, 1899.9358))
        Line((-166.3404, 1899.9358), (-166.3638, 1899.9326))
        Line((-166.3638, 1899.9326), (-166.7212, 1899.9183))
        Line((-166.7212, 1899.9183), (-166.9909, 1899.9334))
        Line((-166.9909, 1899.9334), (-167.1231, 1899.9152))
        Line((-167.1231, 1899.9152), (-167.6404, 1899.9263))
        Line((-167.6404, 1899.9263), (-167.7294, 1899.9312))
        Line((-167.7294, 1899.9312), (-167.8076, 1899.9329))
        Line((-167.8076, 1899.9329), (-167.8877, 1899.9419))
        Line((-167.8877, 1899.9419), (-168.37, 1900.0399))
        Line((-168.37, 1900.0399), (-168.727, 1900.0946))
        Line((-168.727, 1900.0946), (-168.9219, 1900.1439))
        Line((-168.9219, 1900.1439), (-169.0742, 1900.1824))
        Line((-169.0742, 1900.1824), (-169.4112, 1900.3028))
        Line((-169.4112, 1900.3028), (-169.5345, 1900.3608))
        Line((-169.5345, 1900.3608), (-169.6272, 1900.3796))
    _inc_edges_sk_Sketch21_18 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch21_18 = Wire.combine(_inc_edges_sk_Sketch21_18)[0]
_wire_sk_Sketch21_18 = _wire_sk_Sketch21_18.moved(_inclined_plane_18.location)
_mkf_sk_Sketch21_18 = BRepBuilderAPI_MakeFace(_inclined_plane_18.wrapped, _wire_sk_Sketch21_18.wrapped, True)
_face_sk_Sketch21_18 = Face(_mkf_sk_Sketch21_18.Face())

# 'Sketch22': 139 segments → Line/RadiusArc profile
_inclined_plane_19 = Plane(
    origin=Vector(39.0331, -145.6744, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_19) as sk_Sketch22_19:
    with BuildLine():
        Line((-180.6852, 1801.1322), (-180.8252, 1801.1943))
        Line((-180.8252, 1801.1943), (-180.8627, 1801.2083))
        Line((-180.8627, 1801.2083), (-180.9335, 1801.2424))
        Line((-180.9335, 1801.2424), (-181.3907, 1801.5149))
        Line((-181.3907, 1801.5149), (-181.7241, 1801.7055))
        Line((-181.7241, 1801.7055), (-181.8169, 1801.772))
        Line((-181.8169, 1801.772), (-182.0344, 1801.9278))
        Line((-182.0344, 1801.9278), (-182.0814, 1801.9558))
        Line((-182.0814, 1801.9558), (-182.3688, 1802.2098))
        Line((-182.3688, 1802.2098), (-182.8267, 1802.5918))
        Line((-182.8267, 1802.5918), (-185.5551, 1805.2637))
        Line((-185.5551, 1805.2637), (-188.2987, 1807.9504))
        Line((-188.2987, 1807.9504), (-185.5701, 1810.6224))
        Line((-185.5701, 1810.6224), (-182.8267, 1813.309))
        Line((-182.8267, 1813.309), (-182.399, 1813.6694))
        Line((-182.399, 1813.6694), (-182.0504, 1813.9712))
        Line((-182.0504, 1813.9712), (-181.9723, 1814.0186))
        Line((-181.9723, 1814.0186), (-181.8124, 1814.1213))
        Line((-181.8124, 1814.1213), (-181.4604, 1814.3473))
        Line((-181.4604, 1814.3473), (-181.0306, 1814.6086))
        Line((-181.0306, 1814.6086), (-180.8179, 1814.7031))
        Line((-180.8179, 1814.7031), (-180.748, 1814.7373))
        Line((-180.748, 1814.7373), (-180.6825, 1814.7626))
        Line((-180.6825, 1814.7626), (-180.2006, 1814.9483))
        Line((-180.2006, 1814.9483), (-179.9229, 1815.0716))
        Line((-179.9229, 1815.0716), (-179.7916, 1815.0996))
        Line((-179.7916, 1815.0996), (-179.458, 1815.1971))
        Line((-179.458, 1815.1971), (-179.3445, 1815.2303))
        Line((-179.3445, 1815.2303), (-178.8933, 1815.3264))
        Line((-178.8933, 1815.3264), (-178.4893, 1815.3946))
        Line((-178.4893, 1815.3946), (-178.3664, 1815.4026))
        Line((-178.3664, 1815.4026), (-178.2867, 1815.4122))
        Line((-178.2867, 1815.4122), (-178.1774, 1815.4157))
        Line((-178.1774, 1815.4157), (-177.9413, 1815.431))
        Line((-177.9413, 1815.431), (-177.4646, 1815.4457))
        Line((-177.4646, 1815.4457), (-177.0509, 1815.4181))
        Line((-177.0509, 1815.4181), (-176.8783, 1815.3961))
        Line((-176.8783, 1815.3961), (-176.4603, 1815.3428))
        Line((-176.4603, 1815.3428), (-176.3801, 1815.325))
        Line((-176.3801, 1815.325), (-176.171, 1815.3111))
        Line((-176.171, 1815.3111), (-176.0304, 1815.2666))
        Line((-176.0304, 1815.2666), (-175.599, 1815.1734))
        Line((-175.599, 1815.1734), (-175.569, 1815.1669))
        Line((-175.569, 1815.1669), (-175.235, 1815.0552))
        Line((-175.235, 1815.0552), (-174.8163, 1814.9228))
        Line((-174.8163, 1814.9228), (-174.5735, 1814.8084))
        Line((-174.5735, 1814.8084), (-174.3842, 1814.7136))
        Line((-174.3842, 1814.7136), (-174.0409, 1814.5416))
        Line((-174.0409, 1814.5416), (-173.9704, 1814.4979))
        Line((-173.9704, 1814.4979), (-173.7367, 1814.3879))
        Line((-173.7367, 1814.3879), (-173.5894, 1814.2772))
        Line((-173.5894, 1814.2772), (-173.2612, 1814.0617))
        Line((-173.2612, 1814.0617), (-173.146, 1813.986))
        Line((-173.146, 1813.986), (-172.855, 1813.7395))
        Line((-172.855, 1813.7395), (-172.5328, 1813.4975))
        Line((-172.5328, 1813.4975), (-172.4411, 1813.4022))
        Line((-172.4411, 1813.4022), (-172.2689, 1813.224))
        Line((-172.2689, 1813.224), (-172.0264, 1812.9732))
        Line((-172.0264, 1812.9732), (-171.975, 1812.9093))
        Line((-171.975, 1812.9093), (-171.8022, 1812.7298))
        Line((-171.8022, 1812.7298), (-171.5652, 1812.4271))
        Line((-171.5652, 1812.4271), (-171.443, 1812.2439))
        Line((-171.443, 1812.2439), (-171.4337, 1812.229))
        Line((-171.4337, 1812.229), (-171.2397, 1811.921))
        Line((-171.2397, 1811.921), (-171.0354, 1811.6148))
        Line((-171.0354, 1811.6148), (-170.9076, 1811.3572))
        Line((-170.9076, 1811.3572), (-170.7898, 1811.1003))
        Line((-170.7898, 1811.1003), (-170.6585, 1810.814))
        Line((-170.6585, 1810.814), (-170.6319, 1810.7388))
        Line((-170.6319, 1810.7388), (-170.5905, 1810.6553))
        Line((-170.5905, 1810.6553), (-170.456, 1810.2961))
        Line((-170.456, 1810.2961), (-170.3924, 1810.0478))
        Line((-170.3924, 1810.0478), (-170.3483, 1809.8791))
        Line((-170.3483, 1809.8791), (-170.2956, 1809.678))
        Line((-170.2956, 1809.678), (-170.237, 1809.3021))
        Line((-170.237, 1809.3021), (-170.1546, 1808.9797))
        Line((-170.1546, 1808.9797), (-170.1512, 1808.9165))
        Line((-170.1512, 1808.9165), (-170.1221, 1808.6))
        Line((-170.1221, 1808.6), (-170.0963, 1808.3207))
        Line((-170.0963, 1808.3207), (-170.0962, 1808.2435))
        Line((-170.0962, 1808.2435), (-170.0794, 1807.925))
        Line((-170.0794, 1807.925), (-170.105, 1807.6326))
        Line((-170.105, 1807.6326), (-170.1214, 1807.3008))
        Line((-170.1214, 1807.3008), (-170.1239, 1807.2499))
        Line((-170.1239, 1807.2499), (-170.1812, 1806.8736))
        Line((-170.1812, 1806.8736), (-170.2362, 1806.6605))
        Line((-170.2362, 1806.6605), (-170.262, 1806.3657))
        Line((-170.262, 1806.3657), (-170.3483, 1806.0217))
        Line((-170.3483, 1806.0217), (-170.3887, 1805.8655))
        Line((-170.3887, 1805.8655), (-170.5222, 1805.5051))
        Line((-170.5222, 1805.5051), (-170.569, 1805.4099))
        Line((-170.569, 1805.4099), (-170.6282, 1805.1739))
        Line((-170.6282, 1805.1739), (-170.653, 1805.1028))
        Line((-170.653, 1805.1028), (-170.7897, 1804.8003))
        Line((-170.7897, 1804.8003), (-170.9111, 1804.5533))
        Line((-170.9111, 1804.5533), (-171.1131, 1804.2302))
        Line((-171.1131, 1804.2302), (-171.2189, 1803.9961))
        Line((-171.2189, 1803.9961), (-171.4355, 1803.6674))
        Line((-171.4355, 1803.6674), (-171.6712, 1803.364))
        Line((-171.6712, 1803.364), (-171.8529, 1803.174))
        Line((-171.8529, 1803.174), (-171.9651, 1803.0038))
        Line((-171.9651, 1803.0038), (-172.012, 1802.945))
        Line((-172.012, 1802.945), (-172.2683, 1802.676))
        Line((-172.2683, 1802.676), (-172.351, 1802.5894))
        Line((-172.351, 1802.5894), (-172.6408, 1802.3423))
        Line((-172.6408, 1802.3423), (-172.765, 1802.2565))
        Line((-172.765, 1802.2565), (-172.9142, 1802.0999))
        Line((-172.9142, 1802.0999), (-173.2596, 1801.8366))
        Line((-173.2596, 1801.8366), (-173.4508, 1801.7046))
        Line((-173.4508, 1801.7046), (-173.7877, 1801.5197))
        Line((-173.7877, 1801.5197), (-173.8198, 1801.5061))
        Line((-173.8198, 1801.5061), (-173.9488, 1801.4077))
        Line((-173.9488, 1801.4077), (-174.0138, 1801.3668))
        Line((-174.0138, 1801.3668), (-174.3804, 1801.1793))
        Line((-174.3804, 1801.1793), (-174.6994, 1801.0444))
        Line((-174.6994, 1801.0444), (-174.9911, 1800.9548))
        Line((-174.9911, 1800.9548), (-175.147, 1800.8751))
        Line((-175.147, 1800.8751), (-175.5993, 1800.7276))
        Line((-175.5993, 1800.7276), (-175.6731, 1800.705))
        Line((-175.6731, 1800.705), (-176.0508, 1800.6301))
        Line((-176.0508, 1800.6301), (-176.2391, 1800.6125))
        Line((-176.2391, 1800.6125), (-176.3531, 1800.5753))
        Line((-176.3531, 1800.5753), (-176.4306, 1800.5576))
        Line((-176.4306, 1800.5576), (-176.8779, 1800.4963))
        Line((-176.8779, 1800.4963), (-177.0699, 1800.4784))
        Line((-177.0699, 1800.4784), (-177.4515, 1800.4816))
        Line((-177.4515, 1800.4816), (-177.5278, 1800.4901))
        Line((-177.5278, 1800.4901), (-177.6614, 1800.4718))
        Line((-177.6614, 1800.4718), (-178.1774, 1800.4829))
        Line((-178.1774, 1800.4829), (-178.4836, 1800.5169))
        Line((-178.4836, 1800.5169), (-178.819, 1800.5896))
        Line((-178.819, 1800.5896), (-178.898, 1800.5913))
        Line((-178.898, 1800.5913), (-178.9788, 1800.6004))
        Line((-178.9788, 1800.6004), (-179.4597, 1800.6983))
        Line((-179.4597, 1800.6983), (-179.4982, 1800.7067))
        Line((-179.4982, 1800.7067), (-179.5919, 1800.7257))
        Line((-179.5919, 1800.7257), (-179.9543, 1800.8438))
        Line((-179.9543, 1800.8438), (-180.1651, 1800.9372))
        Line((-180.1651, 1800.9372), (-180.6852, 1801.1322))
    _inc_edges_sk_Sketch22_19 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch22_19 = Wire.combine(_inc_edges_sk_Sketch22_19)[0]
_wire_sk_Sketch22_19 = _wire_sk_Sketch22_19.moved(_inclined_plane_19.location)
_mkf_sk_Sketch22_19 = BRepBuilderAPI_MakeFace(_inclined_plane_19.wrapped, _wire_sk_Sketch22_19.wrapped, True)
_face_sk_Sketch22_19 = Face(_mkf_sk_Sketch22_19.Face())

# 'Sketch23': circle on inclined plane
_inclined_plane_20 = Plane(
    origin=Vector(32.2744, 8.6479, 315.3315),
    x_dir=Vector(-0.960548, -0.257378, 0.105371),
    z_dir=Vector(-0.101781, -0.027272, -0.994433),
)
with BuildSketch(_inclined_plane_20) as sk_Sketch23_20:
    with Locations((-2127.4774, -150.8132)):
        Circle(radius=7.5)

# 'Sketch24': circle on inclined plane
_inclined_plane_21 = Plane(
    origin=Vector(32.2744, 8.6479, 315.3315),
    x_dir=Vector(-0.960548, -0.257378, 0.105371),
    z_dir=Vector(-0.101781, -0.027272, -0.994433),
)
with BuildSketch(_inclined_plane_21) as sk_Sketch24_21:
    with Locations((-2027.4775, -150.8131)):
        Circle(radius=7.4999)

# 'Sketch25': circle on inclined plane
_inclined_plane_22 = Plane(
    origin=Vector(32.2744, 8.6479, 315.3315),
    x_dir=Vector(-0.960548, -0.257378, 0.105371),
    z_dir=Vector(-0.101781, -0.027272, -0.994433),
)
with BuildSketch(_inclined_plane_22) as sk_Sketch25_22:
    with Locations((-1927.4774, -150.8132)):
        Circle(radius=7.5)

# 'Sketch26': circle on inclined plane
_inclined_plane_23 = Plane(
    origin=Vector(32.2744, 8.6479, 315.3315),
    x_dir=Vector(-0.960548, -0.257378, 0.105371),
    z_dir=Vector(-0.101781, -0.027272, -0.994433),
)
with BuildSketch(_inclined_plane_23) as sk_Sketch26_23:
    with Locations((-1827.4775, -150.8133)):
        Circle(radius=7.5)

# 'Sketch28': circle on inclined plane
_inclined_plane_24 = Plane(
    origin=Vector(384.2584, 102.9617, 813.887),
    x_dir=Vector(-0.867809, -0.232529, 0.439133),
    z_dir=Vector(-0.42417, -0.113656, -0.898422),
)
with BuildSketch(_inclined_plane_24) as sk_Sketch28_24:
    with Locations((-1411.859, -150.7888)):
        Circle(radius=7.4642)

# 'Sketch29': circle on inclined plane
_inclined_plane_25 = Plane(
    origin=Vector(384.2584, 102.9617, 813.887),
    x_dir=Vector(-0.867809, -0.232529, 0.439133),
    z_dir=Vector(-0.42417, -0.113656, -0.898422),
)
with BuildSketch(_inclined_plane_25) as sk_Sketch29_25:
    with Locations((-1511.8298, -150.8131)):
        Circle(radius=7.4999)

# 'Sketch30': circle on inclined plane
_inclined_plane_26 = Plane(
    origin=Vector(0.0, 0.0, 268.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -0.0, 1.0),
)
with BuildSketch(_inclined_plane_26) as sk_Sketch30_26:
    with Locations((1704.8629, 300.6833)):
        Circle(radius=7.4999)

# 'Sketch31': 23 segments → Line/RadiusArc profile
_inclined_plane_27 = Plane(
    origin=Vector(-9.8843, 36.8855, 0.0),
    x_dir=Vector(-0.965926, -0.258819, 0.0),
    z_dir=Vector(0.258819, -0.965926, 0.0),
)
with BuildSketch(_inclined_plane_27) as sk_Sketch31_27:
    with BuildLine():
        Line((-2354.6795, -163.0843), (-2355.6791, -156.4445))
        Line((-2355.6791, -156.4445), (-2357.7751, -150.0655))
        Line((-2357.7751, -150.0655), (-2360.9088, -144.127))
        Line((-2360.9088, -144.127), (-2364.9915, -138.7963))
        Line((-2364.9915, -138.7963), (-2369.5941, -134.4727))
        Line((-2369.5941, -134.4727), (-2419.5941, -134.4727))
        Line((-2419.5941, -134.4727), (-2424.1969, -138.7963))
        Line((-2424.1969, -138.7963), (-2428.2796, -144.127))
        Line((-2428.2796, -144.127), (-2431.4131, -150.0655))
        Line((-2431.4131, -150.0655), (-2433.5092, -156.4445))
        Line((-2433.5092, -156.4445), (-2434.5087, -163.0843))
        Line((-2434.5087, -163.0843), (-2434.3834, -169.7976))
        Line((-2434.3834, -169.7976), (-2433.1371, -176.3955))
        Line((-2433.1371, -176.3955), (-2430.8046, -182.6919))
        Line((-2430.8046, -182.6919), (-2427.4517, -188.5094))
        Line((-2427.4517, -188.5094), (-2423.173, -193.6842))
        Line((-2423.173, -193.6842), (-2394.5941, -222.868))
        Line((-2394.5941, -222.868), (-2366.0152, -193.6842))
        Line((-2366.0152, -193.6842), (-2361.7365, -188.5094))
        Line((-2361.7365, -188.5094), (-2358.3836, -182.6919))
        Line((-2358.3836, -182.6919), (-2356.0512, -176.3955))
        Line((-2356.0512, -176.3955), (-2354.8048, -169.7976))
        Line((-2354.8048, -169.7976), (-2354.6795, -163.0843))
    _inc_edges_sk_Sketch31_27 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch31_27 = Wire.combine(_inc_edges_sk_Sketch31_27)[0]
_wire_sk_Sketch31_27 = _wire_sk_Sketch31_27.moved(_inclined_plane_27.location)
_mkf_sk_Sketch31_27 = BRepBuilderAPI_MakeFace(_inclined_plane_27.wrapped, _wire_sk_Sketch31_27.wrapped, True)
_face_sk_Sketch31_27 = Face(_mkf_sk_Sketch31_27.Face())

# 'Sketch32': 23 segments → Line/RadiusArc profile
_inclined_plane_28 = Plane(
    origin=Vector(-12.4724, 46.5447, 0.0),
    x_dir=Vector(-0.965926, -0.258819, 0.0),
    z_dir=Vector(0.258819, -0.965926, -0.0),
)
with BuildSketch(_inclined_plane_28) as sk_Sketch32_28:
    with BuildLine():
        Line((-2364.6935, -163.74), (-2365.4423, -158.766))
        Line((-2365.4423, -158.766), (-2367.0124, -153.9874))
        Line((-2367.0124, -153.9874), (-2369.3599, -149.5388))
        Line((-2369.3599, -149.5388), (-2372.4337, -145.5254))
        Line((-2372.4337, -145.5254), (-2373.5544, -144.4726))
        Line((-2373.5544, -144.4726), (-2415.6339, -144.4726))
        Line((-2415.6339, -144.4726), (-2416.7547, -145.5255))
        Line((-2416.7547, -145.5255), (-2419.8284, -149.5387))
        Line((-2419.8284, -149.5387), (-2422.1758, -153.9874))
        Line((-2422.1758, -153.9874), (-2423.746, -158.766))
        Line((-2423.746, -158.766), (-2424.4948, -163.7399))
        Line((-2424.4948, -163.7399), (-2424.4009, -168.769))
        Line((-2424.4009, -168.769), (-2423.4672, -173.7116))
        Line((-2423.4672, -173.7116), (-2421.72, -178.4283))
        Line((-2421.72, -178.4283), (-2419.2082, -182.7863))
        Line((-2419.2082, -182.7863), (-2415.7342, -186.988))
        Line((-2415.7342, -186.988), (-2394.5941, -208.5755))
        Line((-2394.5941, -208.5755), (-2373.454, -186.988))
        Line((-2373.454, -186.988), (-2369.98, -182.7863))
        Line((-2369.98, -182.7863), (-2367.4682, -178.4283))
        Line((-2367.4682, -178.4283), (-2365.721, -173.7116))
        Line((-2365.721, -173.7116), (-2364.7873, -168.769))
        Line((-2364.7873, -168.769), (-2364.6935, -163.74))
    _inc_edges_sk_Sketch32_28 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch32_28 = Wire.combine(_inc_edges_sk_Sketch32_28)[0]
_wire_sk_Sketch32_28 = _wire_sk_Sketch32_28.moved(_inclined_plane_28.location)
_mkf_sk_Sketch32_28 = BRepBuilderAPI_MakeFace(_inclined_plane_28.wrapped, _wire_sk_Sketch32_28.wrapped, True)
_face_sk_Sketch32_28 = Face(_mkf_sk_Sketch32_28.Face())

# 'Sketch33': 7 segments → Line/RadiusArc profile
_inclined_plane_29 = Plane(
    origin=Vector(-13.764, 51.365, 0.0),
    x_dir=Vector(0.0, 0.0, -1.0),
    z_dir=Vector(0.258823, -0.965925, 0.0),
)
with BuildSketch(_inclined_plane_29) as sk_Sketch33_29:
    with BuildLine():
        Line((-68.8731, 2419.5944), (-149.1145, 2419.5944))
        Line((-149.1145, 2419.5944), (-163.2702, 2393.3941))
        Line((-163.2702, 2393.3941), (-149.1145, 2369.5945))
        Line((-149.1145, 2369.5945), (-67.7869, 2369.5945))
        Line((-67.7869, 2369.5945), (-53.3178, 2369.6432))
        Line((-53.3178, 2369.6432), (-52.1512, 2419.5944))
        Line((-52.1512, 2419.5944), (-68.8731, 2419.5944))
    _inc_edges_sk_Sketch33_29 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch33_29 = Wire.combine(_inc_edges_sk_Sketch33_29)[0]
_wire_sk_Sketch33_29 = _wire_sk_Sketch33_29.moved(_inclined_plane_29.location)
_mkf_sk_Sketch33_29 = BRepBuilderAPI_MakeFace(_inclined_plane_29.wrapped, _wire_sk_Sketch33_29.wrapped, True)
_face_sk_Sketch33_29 = Face(_mkf_sk_Sketch33_29.Face())

# -- Build --
with BuildPart() as part:
    # -- Extrude1 --
    _face = _face_sk_Sketch2
    _vec = Vector(0.258819, -0.965926, 0.0) * -240.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid)
    # Fusion depth expression: -240 mm
    
    # -- Extrude3 --
    _face = _face_sk_Sketch4_2
    _vec = Vector(0.0, 0.0, 1.0) * -250.0
    _solid = Solid.extrude(_face, _vec)
    part.part = fuse_solids(part.part, _solid)
    # Fusion depth expression: -250.000000 mm
    
    # -- Extrude2 --
    _face = _face_sk_Sketch3_3
    _vec = Vector(0.0, 0.0, 1.0) * -300.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -300.000000 mm
    
    # -- Extrude4 --
    _face = _face_sk_Sketch5_4
    _vec = Vector(0.0, 0.0, 1.0) * -550.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -550.000000 mm
    
    # -- Extrude5 --
    _face = _face_sk_Sketch6_5
    _vec = Vector(0.258819, -0.965926, 0.0) * -550.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -550.000000 mm
    
    # -- Extrude6 --
    _face = _face_sk_Sketch8_6
    _vec = Vector(0.258819, -0.965926, 0.0) * 260.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 260.000000 mm
    
    # -- Extrude7 --
    _face = _face_sk_Sketch9_7
    _vec = Vector(0.258819, -0.965926, 0.0) * 230.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 230.000000 mm
    
    # -- Extrude8 --
    _face = _face_sk_Sketch10_8
    _vec = Vector(0.258819, -0.965926, 0.0) * 270.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 270.000000 mm
    
    # -- Extrude9 --
    _face = _face_sk_Sketch11_9
    _vec = Vector(0.258819, -0.965926, 0.0) * 180.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 180.000000 mm
    
    # -- Extrude10 --
    _face = _face_sk_Sketch12_10
    _vec = Vector(0.258819, -0.965926, 0.0) * 180.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 180.000000 mm
    
    # -- Extrude11 --
    _face = _face_sk_Sketch13_11
    _vec = Vector(0.258819, -0.965926, 0.0) * 51.0001
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 51.000104529 mm
    
    # -- Extrude12 --
    _face = _face_sk_Sketch14_12
    _vec = Vector(0.258819, -0.965926, 0.0) * 51.0001
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 51.000104529 mm
    
    # -- Extrude13 --
    _face = _face_sk_Sketch15_13
    _vec = Vector(0.258819, -0.965926, 0.0) * 51.0001
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 51.000057437 mm
    
    # -- Extrude15 --
    _face = _face_sk_Sketch17_14
    _vec = Vector(0.258819, -0.965926, 0.0) * -189.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -188.999951928 mm
    
    # -- Extrude16 --
    _face = _face_sk_Sketch18_15
    _vec = Vector(0.258819, -0.965926, 0.0) * -260.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -260.000000 mm
    
    # -- Extrude17 --
    _face = _face_sk_Sketch19_16
    _vec = Vector(0.258819, -0.965926, 0.0) * -430.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -430.000000 mm
    
    # -- Extrude18 --
    _face = _face_sk_Sketch20_17
    _vec = Vector(0.258819, -0.965926, 0.0) * -200.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -200.000000 mm
    
    # -- Extrude19 --
    _face = _face_sk_Sketch21_18
    _vec = Vector(0.258819, -0.965926, 0.0) * -140.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -140.000000 mm
    
    # -- Extrude20 --
    _face = _face_sk_Sketch22_19
    _vec = Vector(0.258819, -0.965926, 0.0) * -185.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -185.000000 mm
    
    # -- Extrude21 --
    extrude(sk_Sketch23_20.sketch, amount=-165.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -165.000000 mm
    
    # -- Extrude22 --
    extrude(sk_Sketch24_21.sketch, amount=-165.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -165 mm
    
    # -- Extrude23 --
    extrude(sk_Sketch25_22.sketch, amount=-165.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -165 mm
    
    # -- Extrude24 --
    extrude(sk_Sketch26_23.sketch, amount=-165.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -165 mm
    
    # -- Extrude25 --
    extrude(sk_Sketch28_24.sketch, amount=-60.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -59.999968145 mm
    
    # -- Extrude26 --
    extrude(sk_Sketch29_25.sketch, amount=-160.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -160.000000 mm
    
    # -- Extrude27 --
    extrude(sk_Sketch30_26.sketch, amount=-50.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -50 mm
    
    # -- Extrude28 --
    _face = _face_sk_Sketch31_27
    _vec = Vector(0.258819, -0.965926, 0.0) * -10.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -9.99997464 mm
    # Fusion taper angle expression: -45 deg
    
    # -- Extrude29 --
    _face = _face_sk_Sketch32_28
    _vec = Vector(0.258819, -0.965926, -0.0) * -5.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: -5 mm
    
    # -- Extrude30 --
    _face = _face_sk_Sketch33_29
    _vec = Vector(0.258823, -0.965925, 0.0) * 41.0
    _solid = Solid.extrude(_face, _vec)
    part.part = cut_solids(part.part, _solid)
    # Fusion depth expression: 41.000000 mm
    


# -- Mirror body along plane defined by 4 points --
_mirror_plane = Plane(
    origin=Vector(2074.6191, 399.7591, 172.5613),
    z_dir=Vector(-0.258820, 0.965926, 0.000000),
)
_mirrored = part.part.mirror(_mirror_plane)
_result = part.part.fuse(_mirrored)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Export --
# export_step(part.part, 'Print_Follower_SO_ARM100_08k_UP_Prusa - Moving_Jaw_08d-1.step')
# export_stl(part.part,  'Print_Follower_SO_ARM100_08k_UP_Prusa - Moving_Jaw_08d-1.stl')
if _has_ocp: show(part)
