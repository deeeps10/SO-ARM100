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
    

# -- Export --
# export_step(part.part, 'fusion_features.step')
# export_stl(part.part,  'fusion_features.stl')
if _has_ocp: show(part)
