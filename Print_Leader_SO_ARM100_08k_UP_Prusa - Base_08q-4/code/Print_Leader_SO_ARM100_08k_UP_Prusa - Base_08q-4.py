# Units: mm throughout.

from build123d import *
import math

_plane = Plane(
    origin=Vector(0.0, 0.0, 219.6976),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_plane) as sk_main:
    with BuildLine():
        Line((2277.2929, 1751.3133), (2289.2732, 1751.2105))
        RadiusArc((2289.2732, 1751.2105), (2311.6776, 1738.0179), 25.9998)
        Line((2311.6776, 1738.0179), (2329.8776, 1705.8606))
        RadiusArc((2329.8776, 1705.8606), (2303.5115, 1661.0851), 30.0002)
        Line((2303.5115, 1661.0851), (2075.1773, 1663.0443))
        RadiusArc((2075.1773, 1663.0443), (2049.5836, 1708.2655), 30.0)
        Line((2049.5836, 1708.2655), (2068.3327, 1740.1057))
        RadiusArc((2068.3327, 1740.1057), (2090.9601, 1752.9121), 26.0001)
        Line((2090.9601, 1752.9121), (2102.9405, 1752.8093))
        Line((2102.9405, 1752.8093), (2277.2929, 1751.3133))
    _inc_edges = list(BuildSketch._get_context().pending_edges)

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire = Wire.combine(_inc_edges)[0]
_wire = _wire.moved(_plane.location)
_mkf = BRepBuilderAPI_MakeFace(_plane.wrapped, _wire.wrapped, True)
_face = Face(_mkf.Face())

with BuildPart() as part:
    _solid = Solid.extrude(_face, Vector(0.0, 0.0, -(219.6976 - 65.69765568)))
    add(_solid)

# -- Circle cut: diameter 201.00007251mm, centre (2190.54572251, 1802.0595342, 219.69764709) --
_circ_plane = Plane(origin=Vector(2190.54572251, 1802.0595342, 219.69764709))
_circ_edge = Edge.make_circle(100.50003626, _circ_plane)
_circ_wire = Wire([_circ_edge])
_circ_face = Face(BRepBuilderAPI_MakeFace(_circ_wire.wrapped).Face())
_circ_depth = 219.69764709 - 201.69765472
_circ_solid = Solid.extrude(_circ_face, Vector(0.0, 0.0, -_circ_depth))
_result = part.part.cut(_circ_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Profile cut along Y axis --
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCP.gp import gp_Pnt
_prof_pts = [
    (2107.5737,1732.7689,165.9902),(2100.4294,1732.8302,158.6943),(2099.3274,1732.8397,157.3537),
    (2098.4737,1732.847,155.8428),(2097.8941,1732.8519,154.2071),(2097.606,1732.8543,152.4958),
    (2097.6181,1732.8543,150.7604),(2097.9301,1732.8516,149.0533),(2098.5324,1732.8464,147.4258),
    (2099.407,1732.8389,145.927),(2100.5276,1732.8293,144.6019),(2101.8605,1732.8178,143.4906),
    (2103.3653,1732.8049,142.6264),(2104.9969,1732.791,142.0354),(2106.7061,1732.7763,141.7354),
    (2108.4415,1732.7614,141.7354),(2110.1506,1732.7467,142.0354),(2111.7822,1732.7327,142.6264),
    (2113.287,1732.7199,143.4906),(2114.6199,1732.7084,144.6019),(2115.7405,1732.6988,145.927),
    (2116.6151,1732.6912,147.4258),(2117.2174,1732.6862,149.0533),(2117.5294,1732.6834,150.7604),
    (2117.5415,1732.6833,152.4958),(2117.2534,1732.6859,154.2071),(2116.6739,1732.6907,155.8428),
    (2115.8202,1732.6981,157.3537),(2114.7182,1732.7075,158.6943),
]
_avg_y = sum(p[1] for p in _prof_pts) / len(_prof_pts)
_pp = BRepBuilderAPI_MakePolygon()
for _pt in _prof_pts:
    _pp.Add(gp_Pnt(_pt[0], _pt[1], _pt[2]))
_pp.Close()
_prof_wire = Wire(_pp.Wire())
_prof_plane = Plane(origin=Vector(0.0, _avg_y, 0.0), x_dir=Vector(1.0,0.0,0.0), z_dir=Vector(0.0,1.0,0.0))
_prof_face = Face(BRepBuilderAPI_MakeFace(_prof_plane.wrapped, _prof_wire.wrapped, True).Face())
_prof_pos = Solid.extrude(_prof_face, Vector(0.0, 1000.0, 0.0))
_prof_neg = Solid.extrude(_prof_face, Vector(0.0, -1000.0, 0.0))
_result = part.part.cut(_prof_pos)
part.part = _result[0] if isinstance(_result, ShapeList) else _result
_result = part.part.cut(_prof_neg)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Second profile cut along Y axis --
_prof2_pts = [
    (2272.3158,1731.3572,165.9896),(2265.1719,1731.4184,158.6942),(2264.0699,1731.4279,157.3536),
    (2263.2164,1731.4352,155.8427),(2262.6367,1731.4402,154.2069),(2262.3486,1731.4426,152.4956),
    (2262.3609,1731.4426,150.7603),(2262.6728,1731.4399,149.0532),(2263.2752,1731.4347,147.4257),
    (2264.1499,1731.4272,145.9269),(2265.2705,1731.4176,144.6018),(2266.6033,1731.4062,143.4905),
    (2268.1081,1731.3933,142.6263),(2269.7395,1731.3774,142.0354),(2271.449,1731.3647,141.7354),
    (2273.1842,1731.3498,141.7354),(2274.8935,1731.3352,142.0354),(2276.525,1731.3212,142.6265),
    (2278.0299,1731.3083,143.4907),(2279.3626,1731.2969,144.6021),(2280.4832,1731.2873,145.9271),
    (2281.3578,1731.2798,147.426),(2281.9602,1731.2746,149.0535),(2282.2721,1731.2719,150.7606),
    (2282.2841,1731.2718,152.4959),(2281.996,1731.2743,154.2072),(2281.4164,1731.2792,155.843),
    (2280.5628,1731.2865,157.3539),(2279.4602,1731.296,158.695),
]
_avg_y2 = sum(p[1] for p in _prof2_pts) / len(_prof2_pts)
_pp2 = BRepBuilderAPI_MakePolygon()
for _pt in _prof2_pts:
    _pp2.Add(gp_Pnt(_pt[0], _pt[1], _pt[2]))
_pp2.Close()
_prof2_wire = Wire(_pp2.Wire())
_prof2_plane = Plane(origin=Vector(0.0, _avg_y2, 0.0), x_dir=Vector(1.0,0.0,0.0), z_dir=Vector(0.0,1.0,0.0))
_prof2_face = Face(BRepBuilderAPI_MakeFace(_prof2_plane.wrapped, _prof2_wire.wrapped, True).Face())
_prof2_pos = Solid.extrude(_prof2_face, Vector(0.0, 1000.0, 0.0))
_prof2_neg = Solid.extrude(_prof2_face, Vector(0.0, -1000.0, 0.0))
_result = part.part.cut(_prof2_pos)
part.part = _result[0] if isinstance(_result, ShapeList) else _result
_result = part.part.cut(_prof2_neg)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Third cut: loft between profile A (Y≈1662.77) and profile B (Y≈1732.77) --
_loft3a_pts = [
    (2106.9731,1662.7715,180.2828),(2092.6843,1662.894,165.6909),(2090.4803,1662.9129,163.0098),
    (2088.773,1662.9276,159.988),(2087.6138,1662.9375,156.7165),(2087.0377,1662.9425,153.2939),
    (2087.0619,1662.9422,149.8232),(2087.6859,1662.9369,146.409),(2088.8905,1662.9266,143.154),
    (2090.6398,1662.9115,140.1563),(2092.881,1662.8923,137.5062),(2095.5466,1662.8694,135.2835),
    (2098.5562,1662.8436,133.5551),(2101.8195,1662.8157,132.3731),(2105.2379,1662.7863,131.7731),
    (2108.7085,1662.7565,131.7731),(2112.1269,1662.7272,132.3731),(2115.39,1662.6991,133.5551),
    (2118.3998,1662.6733,135.2835),(2121.0654,1662.6505,137.5062),(2123.3066,1662.6312,140.1563),
    (2125.0558,1662.6163,143.154),(2126.2605,1662.6059,146.409),(2126.8845,1662.6006,149.8232),
    (2126.9086,1662.6004,153.2939),(2126.3326,1662.6053,156.7165),(2125.1733,1662.6152,159.988),
    (2123.466,1662.6299,163.0098),(2121.2621,1662.6488,165.6909),
]
_loft3b_pts = [
    (2107.5737,1732.7689,180.2828),(2093.2849,1732.8914,165.6909),(2091.0809,1732.9103,163.0098),
    (2089.3736,1732.925,159.988),(2088.2144,1732.9349,156.7165),(2087.6382,1732.9399,153.2939),
    (2087.6625,1732.9396,149.8232),(2088.2864,1732.9343,146.409),(2089.4911,1732.924,143.154),
    (2091.2404,1732.9089,140.1563),(2093.4816,1732.8897,137.5062),(2096.1472,1732.8668,135.2835),
    (2099.157,1732.841,133.5551),(2102.42,1732.8131,132.3731),(2105.8385,1732.7837,131.7731),
    (2109.3091,1732.7539,131.7731),(2112.7275,1732.7246,132.3731),(2115.9906,1732.6967,133.5551),
    (2119.0004,1732.6707,135.2835),(2121.666,1732.6479,137.5062),(2123.9072,1732.6286,140.1563),
    (2125.6564,1732.6137,143.154),(2126.8611,1732.6033,146.409),(2127.485,1732.598,149.8232),
    (2127.5093,1732.5978,153.2939),(2126.9331,1732.6027,156.7165),(2125.7739,1732.6126,159.988),
    (2124.0666,1732.6273,163.0098),(2121.8626,1732.6462,165.6909),
]
_pp3a = BRepBuilderAPI_MakePolygon()
for _pt in _loft3a_pts:
    _pp3a.Add(gp_Pnt(_pt[0], _pt[1], _pt[2]))
_pp3a.Close()
_pp3b = BRepBuilderAPI_MakePolygon()
for _pt in _loft3b_pts:
    _pp3b.Add(gp_Pnt(_pt[0], _pt[1], _pt[2]))
_pp3b.Close()
# Build loft solid via triangulated faces (each triangle is planar — always valid)
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS_Shell
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.BRepLib import BRepLib

_sew3 = BRepBuilderAPI_Sewing(0.001)
_n3 = len(_loft3a_pts)

# Side triangles connecting profile A to profile B
for _i in range(_n3):
    _i1 = (_i + 1) % _n3
    for _tri in [
        (_loft3a_pts[_i], _loft3a_pts[_i1], _loft3b_pts[_i]),
        (_loft3b_pts[_i], _loft3a_pts[_i1], _loft3b_pts[_i1]),
    ]:
        _tp = BRepBuilderAPI_MakePolygon()
        for _pt in _tri:
            _tp.Add(gp_Pnt(*_pt))
        _tp.Close()
        _tf = BRepBuilderAPI_MakeFace(_tp.Wire())
        if _tf.IsDone():
            _sew3.Add(_tf.Face())

# End cap A — single planar face
_pp3a = BRepBuilderAPI_MakePolygon()
for _pt in _loft3a_pts:
    _pp3a.Add(gp_Pnt(*_pt))
_pp3a.Close()
_avg_ya3 = sum(p[1] for p in _loft3a_pts) / len(_loft3a_pts)
_cap3a_plane = Plane(origin=Vector(0.0, _avg_ya3, 0.0), x_dir=Vector(1.0,0.0,0.0), z_dir=Vector(0.0,1.0,0.0))
_cap3a_wire = Wire(_pp3a.Wire())
_cap3a_mkf = BRepBuilderAPI_MakeFace(_cap3a_plane.wrapped, _cap3a_wire.wrapped, True)
if _cap3a_mkf.IsDone():
    _sew3.Add(_cap3a_mkf.Face())

# End cap B — single planar face
_pp3b = BRepBuilderAPI_MakePolygon()
for _pt in _loft3b_pts:
    _pp3b.Add(gp_Pnt(*_pt))
_pp3b.Close()
_avg_yb3 = sum(p[1] for p in _loft3b_pts) / len(_loft3b_pts)
_cap3b_plane = Plane(origin=Vector(0.0, _avg_yb3, 0.0), x_dir=Vector(1.0,0.0,0.0), z_dir=Vector(0.0,1.0,0.0))
_cap3b_wire = Wire(_pp3b.Wire())
_cap3b_mkf = BRepBuilderAPI_MakeFace(_cap3b_plane.wrapped, _cap3b_wire.wrapped, True)
if _cap3b_mkf.IsDone():
    _sew3.Add(_cap3b_mkf.Face())

_sew3.Perform()
_shell3 = TopoDS_Shell()
_bb3 = BRep_Builder()
_bb3.MakeShell(_shell3)
_exp3 = TopExp_Explorer(_sew3.SewedShape(), TopAbs_FACE)
while _exp3.More():
    _bb3.Add(_shell3, _exp3.Current())
    _exp3.Next()
_mk3 = BRepBuilderAPI_MakeSolid()
_mk3.Add(_shell3)
_loft3_solid = Solid(_mk3.Solid())
BRepLib.OrientClosedSolid_s(_loft3_solid.wrapped)
export_step(_loft3_solid, "/Users/softage/Documents/stls/5may/loft_debug.step")

_result = part.part.cut(_loft3_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Fourth cut: loft between profile A (Y≈1661.35) and profile B (Y≈1731.35) --
_loft4a_pts = [
    (2271.7159,1661.3579,180.2828),(2257.4269,1661.4806,165.6909),(2255.2229,1661.4993,163.0098),
    (2253.5156,1661.514,159.988),(2252.3566,1661.524,156.7165),(2251.7804,1661.5289,153.2939),
    (2251.8047,1661.5288,149.8232),(2252.4284,1661.5234,146.409),(2253.6331,1661.5131,143.154),
    (2255.3825,1661.4981,140.1563),(2257.6236,1661.4787,137.5062),(2260.2893,1661.456,135.2835),
    (2263.299,1661.4301,133.5551),(2266.562,1661.4021,132.3731),(2269.9805,1661.3728,131.7731),
    (2273.4511,1661.3429,131.7731),(2276.8695,1661.3136,132.3731),(2280.1328,1661.2857,133.5551),
    (2283.1424,1661.2599,135.2835),(2285.808,1661.237,137.5062),(2288.0492,1661.2178,140.1563),
    (2289.7984,1661.2027,143.154),(2291.0031,1661.1925,146.409),(2291.627,1661.187,149.8232),
    (2291.6513,1661.1868,153.2939),(2291.0751,1661.1917,156.7165),(2289.9159,1661.2018,159.988),
    (2288.2088,1661.2164,163.0098),(2286.0048,1661.2354,165.6909),
]
_loft4b_pts = [
    (2272.3164,1731.3553,180.2828),(2258.0275,1731.478,165.6909),(2255.8235,1731.4969,163.0098),
    (2254.1162,1731.5115,159.988),(2252.9572,1731.5215,156.7165),(2252.381,1731.5263,153.2939),
    (2252.4052,1731.5262,149.8232),(2253.029,1731.5208,146.409),(2254.2337,1731.5105,143.154),
    (2255.9831,1731.4955,140.1563),(2258.2242,1731.4763,137.5062),(2260.8899,1731.4534,135.2835),
    (2263.8995,1731.4275,133.5551),(2267.1628,1731.3995,132.3731),(2270.5811,1731.3702,131.7731),
    (2274.0517,1731.3405,131.7731),(2277.4701,1731.311,132.3731),(2280.7333,1731.2831,133.5551),
    (2283.743,1731.2573,135.2835),(2286.4085,1731.2344,137.5062),(2288.6497,1731.2152,140.1563),
    (2290.399,1731.2001,143.154),(2291.6039,1731.1899,146.409),(2292.2276,1731.1844,149.8232),
    (2292.2519,1731.1842,153.2939),(2291.6757,1731.1893,156.7165),(2290.5165,1731.1992,159.988),
    (2288.8094,1731.2138,163.0098),(2286.6054,1731.2328,165.6909),
]

_sew4 = BRepBuilderAPI_Sewing(0.001)
_n4 = len(_loft4a_pts)

for _i in range(_n4):
    _i1 = (_i + 1) % _n4
    for _tri in [
        (_loft4a_pts[_i], _loft4a_pts[_i1], _loft4b_pts[_i]),
        (_loft4b_pts[_i], _loft4a_pts[_i1], _loft4b_pts[_i1]),
    ]:
        _tp = BRepBuilderAPI_MakePolygon()
        for _pt in _tri:
            _tp.Add(gp_Pnt(*_pt))
        _tp.Close()
        _tf = BRepBuilderAPI_MakeFace(_tp.Wire())
        if _tf.IsDone():
            _sew4.Add(_tf.Face())

_pp4a = BRepBuilderAPI_MakePolygon()
for _pt in _loft4a_pts:
    _pp4a.Add(gp_Pnt(*_pt))
_pp4a.Close()
_avg_ya4 = sum(p[1] for p in _loft4a_pts) / len(_loft4a_pts)
_cap4a_plane = Plane(origin=Vector(0.0, _avg_ya4, 0.0), x_dir=Vector(1.0,0.0,0.0), z_dir=Vector(0.0,1.0,0.0))
_cap4a_wire = Wire(_pp4a.Wire())
_cap4a_mkf = BRepBuilderAPI_MakeFace(_cap4a_plane.wrapped, _cap4a_wire.wrapped, True)
if _cap4a_mkf.IsDone():
    _sew4.Add(_cap4a_mkf.Face())

_pp4b = BRepBuilderAPI_MakePolygon()
for _pt in _loft4b_pts:
    _pp4b.Add(gp_Pnt(*_pt))
_pp4b.Close()
_avg_yb4 = sum(p[1] for p in _loft4b_pts) / len(_loft4b_pts)
_cap4b_plane = Plane(origin=Vector(0.0, _avg_yb4, 0.0), x_dir=Vector(1.0,0.0,0.0), z_dir=Vector(0.0,1.0,0.0))
_cap4b_wire = Wire(_pp4b.Wire())
_cap4b_mkf = BRepBuilderAPI_MakeFace(_cap4b_plane.wrapped, _cap4b_wire.wrapped, True)
if _cap4b_mkf.IsDone():
    _sew4.Add(_cap4b_mkf.Face())

_sew4.Perform()
_shell4 = TopoDS_Shell()
_bb4 = BRep_Builder()
_bb4.MakeShell(_shell4)
_exp4 = TopExp_Explorer(_sew4.SewedShape(), TopAbs_FACE)
while _exp4.More():
    _bb4.Add(_shell4, _exp4.Current())
    _exp4.Next()
_mk4 = BRepBuilderAPI_MakeSolid()
_mk4.Add(_shell4)
_loft4_solid = Solid(_mk4.Solid())
BRepLib.OrientClosedSolid_s(_loft4_solid.wrapped)

_result = part.part.cut(_loft4_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

export_step(part.part, "/Users/softage/Documents/stls/5may/Print_Leader_SO_ARM100_08k_UP_Prusa - Base_08q-4.step")
export_stl(part.part, "/Users/softage/Documents/stls/5may/Print_Leader_SO_ARM100_08k_UP_Prusa - Base_08q-4.stl")
