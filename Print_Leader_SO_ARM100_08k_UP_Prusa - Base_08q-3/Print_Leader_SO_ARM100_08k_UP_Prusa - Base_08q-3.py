# Units: mm throughout.
from build123d import *
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.GC import GC_MakeArcOfCircle
from OCP.gp import gp_Ax2, gp_Ax3, gp_Dir, gp_Pln, gp_Pnt

# Profile at y=2230.9193, normal=-y; local x=worldX, local y=worldZ
_plane = Plane(
    origin=Vector(0.0, 2230.9193, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)

with BuildSketch(_plane) as sk_profile:
    with BuildLine():
        Line((674.3677, 504.5226), (674.3677, 627.6976))
        RadiusArc((674.3677, 627.6976), (624.3677, 677.6977), 50.0)
        Line((624.3677, 677.6977), (624.3677, 727.6977))
        Line((624.3677, 727.6977), (574.0528, 727.6977))
        RadiusArc((574.0528, 727.6977), (552.4021, 740.1977), 25.0)
        Line((552.4021, 740.1977), (446.747, 923.1977))
        RadiusArc((446.747, 923.1977), (425.0964, 935.6977), -25.0002)
        Line((425.0964, 935.6977), (368.1091, 935.6977))
        RadiusArc((368.1091, 935.6977), (346.4584, 923.1977), -25.0003)
        Line((346.4584, 923.1977), (123.0921, 536.3157))
        Line((123.0921, 536.3157), (121.6577, 533.3773))
        RadiusArc((121.6577, 533.3773), (119.7427, 523.8157), -25.3286)
        Line((119.7427, 523.8157), (119.7427, 443.6565))
        RadiusArc((119.7427, 443.6565), (123.0921, 431.1565), -24.9997)
        Line((123.0921, 431.1565), (125.7427, 426.5655))
        Line((125.7427, 426.5655), (238.3644, 231.4989))
        RadiusArc((238.3644, 231.4989), (241.7138, 218.9989), 24.9996)
        Line((241.7138, 218.9989), (241.7138, 90.6977))
        RadiusArc((241.7138, 90.6977), (265.7139, 65.7763), -24.922)
        Line((265.7139, 65.7763), (555.3676, 65.7763))
        RadiusArc((555.3676, 65.7763), (579.3677, 90.6977), -24.8449)
        Line((579.3677, 90.6977), (579.3677, 328.6977))
        Line((579.3677, 328.6977), (571.8677, 328.6977))
        RadiusArc((571.8677, 328.6977), (555.7808, 363.1962), 21.0)
        Line((555.7808, 363.1962), (674.3677, 504.5226))
    _inc_edges = list(BuildSketch._get_context().pending_edges)

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire = Wire.combine(_inc_edges)[0]
_wire = _wire.moved(_plane.location)
_mkf = BRepBuilderAPI_MakeFace(_plane.wrapped, _wire.wrapped, True)
_face = Face(_mkf.Face())

# Profile at y=1972.9195, normal=-y; local x=worldX, local y=worldZ
_plane2 = Plane(
    origin=Vector(0.0, 1972.9195, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)

with BuildSketch(_plane2) as sk_profile2:
    with BuildLine():
        Line((582.3677, 483.544), (582.3677, 394.8812))
        Line((582.3677, 394.8812), (555.7808, 363.1962))
        RadiusArc((555.7808, 363.1962), (571.8677, 328.6977), -21.0)
        Line((571.8677, 328.6977), (579.3677, 328.6977))
        Line((579.3677, 328.6977), (579.3677, 90.6977))
        RadiusArc((579.3677, 90.6977), (555.3676, 65.7763), -24.8449)
        Line((555.3676, 65.7763), (554.3677, 65.6976))
        Line((554.3677, 65.6976), (450.8677, 65.6976))
        Line((450.8677, 65.6976), (450.8677, 295.7425))
        Line((450.8677, 295.7425), (582.3677, 483.544))
    _inc_edges2 = list(BuildSketch._get_context().pending_edges)

_wire2 = Wire.combine(_inc_edges2)[0]
_wire2 = _wire2.moved(_plane2.location)
_mkf2 = BRepBuilderAPI_MakeFace(_plane2.wrapped, _wire2.wrapped, True)
_face2 = Face(_mkf2.Face())

# Profiles at y=2254.9194, extruded in -Y to y=2230.91934204
_plane3 = Plane(
    origin=Vector(0.0, 2254.9194, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
_EXT_VEC3 = Vector(0.0, -1.0, 0.0) * (2254.9194 - 2230.91934204)


def _make_top_face(segs):
    _cap = []
    with BuildSketch(_plane3) as _sk:
        with BuildLine():
            for cmd in segs:
                if cmd[0] == 'L':
                    Line(cmd[1], cmd[2])
                else:
                    RadiusArc(cmd[1], cmd[2], cmd[3])
        _cap = list(BuildSketch._get_context().pending_edges)
    _w = Wire.combine(_cap)[0]
    _w = _w.moved(_plane3.location)
    return Face(BRepBuilderAPI_MakeFace(_plane3.wrapped, _w.wrapped, True).Face())


_top_profiles = [
    # p1
    [('A', (674.3677, 627.6976), (659.3677, 630.0007), -57.5261),
     ('L', (659.3677, 630.0007), (659.3677, 486.6463)),
     ('L', (659.3677, 486.6463), (674.3677, 504.5226)),
     ('L', (674.3677, 504.5226), (674.3677, 627.6976))],
    # p2
    [('A', (609.9927, 715.6976), (597.9927, 727.6977), -12.0),
     ('L', (597.9927, 727.6977), (591.9927, 727.6977)),
     ('A', (591.9927, 727.6977), (579.9927, 715.6976),  -12.0),
     ('L', (579.9927, 715.6976), (579.9927, 392.0509)),
     ('L', (579.9927, 392.0509), (609.9927, 427.8035)),
     ('L', (609.9927, 427.8035), (609.9927, 715.6976))],
    # p3
    [('L', (530.6177, 777.9294), (523.01,   791.1063)),
     ('A', (523.01,   791.1063), (500.6177, 785.1063),  -12.0),
     ('L', (500.6177, 785.1063), (500.6177,  90.6977)),
     ('L', (500.6177,  90.6977), (530.6177,  90.6977)),
     ('L', (530.6177,  90.6977), (530.6177, 777.9294))],
    # p4
    [('L', (451.2427, 915.4108), (446.747,  923.1977)),
     ('L', (446.747,  923.1977), (444.2475, 926.7673)),
     ('L', (444.2475, 926.7673), (441.1661, 929.8488)),
     ('A', (441.1661, 929.8488), (421.2427, 920.8287),  -12.0048),
     ('L', (421.2427, 920.8287), (421.2427,  90.6977)),
     ('L', (421.2427,  90.6977), (451.2427,  90.6977)),
     ('L', (451.2427,  90.6977), (451.2427, 915.4108))],
    # p5
    [('A', (371.8677, 920.7515), (352.0394, 929.8488),  -12.0),
     ('L', (352.0394, 929.8488), (348.958,  926.7673)),
     ('L', (348.958,  926.7673), (341.8677, 915.2463)),
     ('L', (341.8677, 915.2463), (341.8677,  90.6977)),
     ('L', (341.8677,  90.6977), (371.8677,  90.6977)),
     ('L', (371.8677,  90.6977), (371.8677, 920.7515))],
    # p6
    [('A', (292.4927, 784.9416), (270.1004, 790.9416),  -12.0),
     ('L', (270.1004, 790.9416), (262.4927, 777.7647)),
     ('L', (262.4927, 777.7647), (262.4927,  90.6977)),
     ('L', (262.4927,  90.6977), (292.4927,  90.6977)),
     ('L', (292.4927,  90.6977), (292.4927, 784.9416))],
    # p7
    [('L', (183.1177, 327.1891), (201.1177, 296.0122)),
     ('L', (201.1177, 296.0122), (213.1177, 316.7968)),
     ('L', (213.1177, 316.7968), (213.1177, 647.4601)),
     ('A', (213.1177, 647.4601), (190.7254, 653.4601),  -12.0),
     ('L', (190.7254, 653.4601), (183.1177, 640.2832)),
     ('L', (183.1177, 640.2832), (183.1177, 327.1891))],
    # p8
    [('L', (133.7427, 440.4219), (133.7427, 524.3918)),
     ('A', (133.7427, 524.3918), (123.0921, 536.3157), -12.0),
     ('A', (123.0921, 536.3157), (119.7427, 523.8157),  -24.9994),
     ('L', (119.7427, 523.8157), (119.7427, 443.6565)),
     ('A', (119.7427, 443.6565), (125.7427, 426.5655), -30.4225),
     ('L', (125.7427, 426.5655), (133.7427, 440.4219))],
]

_top_faces  = [_make_top_face(segs) for segs in _top_profiles]
_top_solids = [Solid.extrude(f, _EXT_VEC3) for f in _top_faces]

# Profile at y=2076.9194, extruded in +Y to y=2094.91943359
_plane4 = Plane(
    origin=Vector(0.0, 2076.9194, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)

with BuildSketch(_plane4) as _sk_p9:
    with BuildLine():
        Line((542.2985, 727.6977), (573.8677, 727.6977))
        Line((573.8677, 727.6977), (573.8677, 677.6977))
        RadiusArc((573.8677, 677.6977), (674.3677, 577.1976), -100.4999)
        Line((674.3677, 577.1976), (674.3677, 504.5226))
        Line((674.3677, 504.5226), (582.3677, 394.8812))
        Line((582.3677, 394.8812), (582.3677, 483.544))
        Line((582.3677, 483.544),  (545.4675, 648.9397))
        RadiusArc((545.4675, 648.9397), (542.2985, 677.6977), 132.0695)
        Line((542.2985, 677.6977), (542.2985, 727.6977))
    _inc_edges_p9 = list(BuildSketch._get_context().pending_edges)

_wire_p9 = Wire.combine(_inc_edges_p9)[0]
_wire_p9 = _wire_p9.moved(_plane4.location)
_mkf_p9  = BRepBuilderAPI_MakeFace(_plane4.wrapped, _wire_p9.wrapped, True)
_face_p9  = Face(_mkf_p9.Face())
_solid_p9 = Solid.extrude(_face_p9, Vector(0.0, 1.0, 0.0) * (2094.91943359 - 2076.9194))

# Diamond cut profiles — world (x, z) coordinates, all at y=2094.9194
# Each profile is a 4-point diamond extruded through the full body along Y
_CUT_BASE_Y = 1972.9195 - 1.0
_CUT_HEIGHT = (2230.9193 + 1.0) - _CUT_BASE_Y  # ~260 mm, clears body entirely

_CUT_PROFILES_XZ = [
    # 1
    [(486.6027, 667.5629), (511.6027, 710.8643), (486.6027, 754.1656), (461.6027, 710.8643)],
    # 2
    [(441.6027, 745.5053), (466.6027, 788.8065), (449.0227, 819.256),  (424.0227, 775.9547)],
    # 3
    [(341.6027, 814.7873), (366.6027, 771.4861), (341.6027, 728.1848), (316.6027, 771.4861)],
    # 4
    [(286.6027, 632.922),  (311.6027, 676.2232), (286.6027, 719.5245), (261.6027, 676.2232)],
    # 5
    [(231.6027, 537.6592), (256.6027, 580.9605), (231.6027, 624.2617), (206.6027, 580.9605)],
    # 6
    [(176.6027, 528.9989), (151.6027, 485.6977), (176.6027, 442.3964), (201.6027, 485.6977)],
    # 7
    [(221.6027, 364.4541), (196.6027, 407.7554), (221.6027, 451.0566), (246.6027, 407.7554)],
    # 8
    [(276.6027, 459.7169), (301.6027, 503.0182), (276.6027, 546.3194), (251.6027, 503.0182)],
    # 9
    [(331.6027, 554.9797), (356.6027, 598.2809), (331.6027, 641.5822), (306.6027, 598.2809)],
    # 10
    [(386.6027, 650.2425), (411.6027, 693.5438), (386.6027, 736.845),  (361.6027, 693.5438)],
    # 11
    [(431.6027, 572.3002), (456.6027, 615.6015), (431.6027, 658.9027), (406.6027, 615.6015)],
    # 12
    [(476.6027, 494.3579), (501.6027, 537.6592), (476.6027, 580.9605), (451.6027, 537.6592)],
    # 13
    [(421.6027, 399.0951), (446.6027, 442.3964), (421.6027, 485.6977), (396.6027, 442.3964)],
    # 14
    [(376.6027, 477.0374), (401.6027, 520.3387), (376.6027, 563.6399), (351.6027, 520.3387)],
    # 15
    [(321.6027, 381.7746), (346.6027, 425.0759), (321.6027, 468.3772), (296.6027, 425.0759)],
    # 16
    [(266.6027, 286.5118), (291.6027, 329.8131), (266.6027, 373.1144), (241.6027, 329.8131)],
    # 17
    [(411.6027, 225.89),   (436.6027, 269.1913), (411.6027, 312.4926), (386.6027, 269.1913)],
    # 18
    [(366.6027, 303.8323), (391.6027, 347.1336), (366.6027, 390.4348), (341.6027, 347.1336)],
    # 19
    [(311.6027, 215.5568), (334.5857, 255.3644), (311.6027, 295.1721), (288.6198, 255.3644)],
    # 20
    [(466.6027, 321.1528), (491.6027, 364.4541), (466.6027, 407.7554), (441.6027, 364.4541)],
    # 21
    [(521.6027, 416.4156), (546.6027, 459.7169), (521.6027, 503.0182), (496.6027, 459.7169)],
    # 22 — 6-point profile
    [(539.1027, 663.2329), (544.446, 653.9781), (551.1487, 623.4753), (531.6027, 589.6207), (506.6027, 632.922), (531.6027, 676.2232)],
    # 23 — 4-point irregular quadrilateral
    [(562.2975, 573.5036), (551.6027, 554.9797), (564.1027, 533.329), (575.7685, 513.1234)],
]


def _make_cut_solid(pts_xz):
    poly = BRepBuilderAPI_MakePolygon()
    for x, z in pts_xz:
        poly.Add(gp_Pnt(x, _CUT_BASE_Y, z))
    poly.Close()
    _f = Face(BRepBuilderAPI_MakeFace(poly.Wire(), True).Face())
    return Solid.extrude(_f, Vector(0.0, 1.0, 0.0) * _CUT_HEIGHT)


_cut_solids = [_make_cut_solid(p) for p in _CUT_PROFILES_XZ]

# 5-point cut profile at y=2230.9193, extruded in -Y to y=2094.91943359
_poly_cut_top = BRepBuilderAPI_MakePolygon()
for _x, _z in [(521.6027, 312.4926), (546.6027, 269.1913), (544.5857, 265.6977),
               (498.6198, 265.6977), (496.6027, 269.1913)]:
    _poly_cut_top.Add(gp_Pnt(_x, 2230.9193, _z))
_poly_cut_top.Close()
_face_cut_top  = Face(BRepBuilderAPI_MakeFace(_poly_cut_top.Wire(), True).Face())
_solid_cut_top = Solid.extrude(_face_cut_top, Vector(0.0, -1.0, 0.0) * (2230.9193 - 2094.91943359))

# 29-point circular cut profile at y=2118.358, through full body along Y
_cut_p1_xz = [
    (356.8677, 186.4291), (339.0059, 168.1892), (336.2508, 164.8378),
    (334.1167, 161.0606), (332.6677, 156.9712), (331.9474, 152.693),
    (331.9778, 148.3546), (332.7576, 144.0868), (334.2636, 140.0181),
    (336.4503, 136.271),  (339.2518, 132.9584), (342.584,  130.18),
    (346.3462, 128.0195), (350.4253, 126.542),  (354.6984, 125.7919),
    (359.0369, 125.7919), (363.3101, 126.542),  (367.3892, 128.0195),
    (371.1515, 130.18),   (374.4836, 132.9584), (377.2852, 136.271),
    (379.4719, 140.0181), (380.9778, 144.0868), (381.7577, 148.3546),
    (381.7879, 152.693),  (381.0678, 156.9712), (379.6188, 161.0606),
    (377.4846, 164.8378), (374.7295, 168.1892),
]
_poly_p1 = BRepBuilderAPI_MakePolygon()
for _x, _z in _cut_p1_xz:
    _poly_p1.Add(gp_Pnt(_x, _CUT_BASE_Y - 100.0, _z))  # extended 100 mm in -Y
_poly_p1.Close()
_solid_cut_p1 = Solid.extrude(
    Face(BRepBuilderAPI_MakeFace(_poly_p1.Wire(), True).Face()),
    Vector(0.0, 1.0, 0.0) * (_CUT_HEIGHT + 200.0),  # extended 100 mm in +Y
)

# Loft cut: transitions from profile at y=2118.358 down to profile at y=2094.9194
_loft_xz1 = [  # 29 pts at y=2118.358
    (356.8677, 186.4291), (339.0059, 168.1892), (336.2508, 164.8378),
    (334.1167, 161.0606), (332.6677, 156.9712), (331.9474, 152.693),
    (331.9778, 148.3546), (332.7576, 144.0868), (334.2636, 140.0181),
    (336.4503, 136.271),  (339.2518, 132.9584), (342.584,  130.18),
    (346.3462, 128.0195), (350.4253, 126.542),  (354.6984, 125.7919),
    (359.0369, 125.7919), (363.3101, 126.542),  (367.3892, 128.0195),
    (371.1515, 130.18),   (374.4836, 132.9584), (377.2852, 136.271),
    (379.4719, 140.0181), (380.9778, 144.0868), (381.7577, 148.3546),
    (381.7879, 152.693),  (381.0678, 156.9712), (379.6188, 161.0606),
    (377.4846, 164.8378), (374.7295, 168.1892),
]
_loft_xz2 = [  # 32 pts at y=2094.9194
    (356.8677, 229.3069), (317.5717, 189.1791), (311.5106, 181.806),
    (306.8154, 173.4961), (303.6276, 164.4995), (302.0432, 155.0873),
    (302.1098, 145.5429), (303.8255, 136.1538), (307.1386, 127.2026),
    (311.9493, 118.959),  (318.1128, 111.6713), (325.4434, 105.5588),
    (333.7204, 100.8057), (342.6945,  97.5552), (352.0954,  95.9051),
    (361.64,    95.9051), (371.041,   97.5552), (376.6027,  99.5698),
    (380.015,  100.8057), (388.292,  105.5588), (394.1027, 110.404),
    (395.6226, 111.6713), (401.7861, 118.959),  (406.5968, 127.2026),
    (409.9099, 136.1538), (411.6256, 145.5429), (411.6922, 155.0873),
    (410.1078, 164.4995), (406.92,   173.4961), (402.2248, 181.806),
    (396.1637, 189.1791), (394.1027, 191.2837),
]

_lpoly1 = BRepBuilderAPI_MakePolygon()
for _x, _z in _loft_xz1:
    _lpoly1.Add(gp_Pnt(_x, 2118.358, _z))
_lpoly1.Close()

_lpoly2 = BRepBuilderAPI_MakePolygon()
for _x, _z in _loft_xz2:
    _lpoly2.Add(gp_Pnt(_x, 2094.9194, _z))
_lpoly2.Close()

_loft_builder = BRepOffsetAPI_ThruSections(True)  # isSolid=True
_loft_builder.AddWire(_lpoly1.Wire())
_loft_builder.AddWire(_lpoly2.Wire())
_loft_builder.Build()
_solid_loft_cut = Solid(_loft_builder.Shape())

# *** IMPORTANT LOFT *** Second loft cut — profile 1: 37 pts (y varies ~2094.9–2096.7), profile 2: 29 pts at y=2124.9194
_loft2_pts1 = [  # full 3-D coords
    (396.6027, 2096.6518, 915.7444), (390.4698, 2095.3752, 910.9071),
    (384.8699, 2094.9194, 905.6977), (376.6027, 2094.9194, 897.2555),
    (361.9947, 2094.9194, 882.3383), (356.6566, 2094.9194, 875.8448),
    (352.5216, 2094.9194, 868.5262), (349.7141, 2094.9194, 860.6029),
    (348.3187, 2094.9194, 852.3135), (348.3774, 2094.9194, 843.9078),
    (349.8884, 2094.9194, 835.6387), (352.8063, 2094.9194, 827.7554),
    (357.0431, 2094.9194, 820.4953), (362.4713, 2094.9194, 814.077),
    (368.9273, 2094.9194, 808.6938), (376.2169, 2094.9194, 804.5077),
    (384.1204, 2094.9194, 801.6449), (392.3997, 2094.9194, 800.1917),
    (400.8057, 2094.9194, 800.1917), (409.0851, 2094.9194, 801.6449),
    (416.9886, 2094.9194, 804.5077), (424.2781, 2094.9194, 808.6938),
    (430.7342, 2094.9194, 814.077),  (436.1624, 2094.9194, 820.4953),
    (439.1027, 2094.9194, 825.5338), (440.3992, 2094.9194, 827.7554),
    (443.3171, 2094.9194, 835.6387), (444.8281, 2094.9194, 843.9078),
    (444.8868, 2094.9194, 852.3135), (443.4914, 2094.9194, 860.6029),
    (440.6839, 2094.9194, 868.5262), (439.1027, 2094.9194, 871.3246),
    (436.5488, 2094.9194, 875.8448), (431.2107, 2094.9194, 882.3383),
    (417.9452, 2094.9194, 895.8846), (408.3355, 2094.9194, 905.6977),
    (402.7357, 2095.3752, 910.9071),
]
_loft2_xz2 = [  # 29 pts at y=2124.9194
    (396.6027, 884.179),  (414.4646, 865.9392), (417.2196, 862.5877),
    (419.3538, 858.8105), (420.8028, 854.7211), (421.523,  850.4429),
    (421.4927, 846.1045), (420.7128, 841.8367), (419.2069, 837.768),
    (417.0201, 834.0209), (414.2186, 830.7083), (410.8865, 827.9299),
    (407.1242, 825.7694), (403.0451, 824.2919), (398.772,  823.5419),
    (394.4335, 823.5419), (390.1604, 824.2919), (386.0812, 825.7694),
    (382.319,  827.9299), (378.9869, 830.7083), (376.1853, 834.0209),
    (373.9986, 837.768),  (372.4926, 841.8367), (371.7128, 846.1045),
    (371.6825, 850.4429), (372.4027, 854.7211), (373.8517, 858.8105),
    (375.9859, 862.5877), (378.7409, 865.9392),
]

# Profile 1 flattened to y=2094.9194 (original pts had tiny y deviations ≤1.7 mm)
_l2p1 = BRepBuilderAPI_MakePolygon()
for _x, _y, _z in _loft2_pts1:
    _l2p1.Add(gp_Pnt(_x, 2094.9194, _z))
_l2p1.Close()

# Profile 2 reversed (keep top start-point, reverse rest) so both profiles wind CW
_loft2_xz2_cw = [_loft2_xz2[0]] + list(reversed(_loft2_xz2[1:]))
_l2p2 = BRepBuilderAPI_MakePolygon()
for _x, _z in _loft2_xz2_cw:
    _l2p2.Add(gp_Pnt(_x, 2124.9194, _z))
_l2p2.Close()

_loft2_builder = BRepOffsetAPI_ThruSections(True)
_loft2_builder.AddWire(_l2p1.Wire())
_loft2_builder.AddWire(_l2p2.Wire())
_loft2_builder.Build()
_solid_loft2_cut = Solid(_loft2_builder.Shape())

# Through cut using same 29-pt profile (CW, y=2124.9194), through full body
_thru2_poly = BRepBuilderAPI_MakePolygon()
for _x, _z in _loft2_xz2_cw:
    _thru2_poly.Add(gp_Pnt(_x, _CUT_BASE_Y - 100.0, _z))
_thru2_poly.Close()
_solid_thru2 = Solid.extrude(
    Face(BRepBuilderAPI_MakeFace(_thru2_poly.Wire(), True).Face()),
    Vector(0.0, 1.0, 0.0) * (_CUT_HEIGHT + 200.0),
)

# Circle cut: dia=15.0000752 mm, centre=(591.9933, 2144.9194, 737.6976), 130 mm along Z (±65 mm)
_cyl_ax = gp_Ax2(
    gp_Pnt(591.9933, 2144.9194, 737.6976 - 65.0),  # bottom of cut
    gp_Dir(0.0, 0.0, 1.0),                           # Z axis
)
_solid_cyl_cut = Solid(BRepPrimAPI_MakeCylinder(_cyl_ax, 15.0000752 / 2.0, 130.0).Solid())

# Profile p9: comb base at y=2254.9194 → y=2230.91934204 (inline, not via _make_top_face)
with BuildSketch(_plane3) as _sk_p9b:
    with BuildLine():
        Line((530.6177,  90.6977), (530.6177,  79.6977))
        Line((530.6177,  79.6977), (576.8177,  79.6977))
        RadiusArc((576.8177,  79.6977), (554.3677,  65.6976), 25.0002)
        Line((554.3677,  65.6976), (266.7138,  65.6976))
        RadiusArc((266.7138,  65.6976), (244.2639,  79.6977), 25.4669)
        Line((244.2639,  79.6977), (262.4927,  79.6977))
        Line((262.4927,  79.6977), (262.4927,  90.6977))
        Line((262.4927,  90.6977), (292.4927,  90.6977))
        Line((292.4927,  90.6977), (292.4927,  79.6977))
        Line((292.4927,  79.6977), (341.8677,  79.6977))
        Line((341.8677,  79.6977), (341.8677,  90.6977))
        Line((341.8677,  90.6977), (371.8677,  90.6977))
        Line((371.8677,  90.6977), (371.8677,  79.6977))
        Line((371.8677,  79.6977), (421.2427,  79.6977))
        Line((421.2427,  79.6977), (421.2427,  90.6977))
        Line((421.2427,  90.6977), (451.2427,  90.6977))
        Line((451.2427,  90.6977), (451.2427,  79.6977))
        Line((451.2427,  79.6977), (500.6177,  79.6977))
        Line((500.6177,  79.6977), (500.6177,  90.6977))
        Line((500.6177,  90.6977), (530.6177,  90.6977))
    _inc_p9b = list(BuildSketch._get_context().pending_edges)

_wire_p9b = Wire.combine(_inc_p9b)[0]
_wire_p9b = _wire_p9b.moved(_plane3.location)
_mkf_p9b  = BRepBuilderAPI_MakeFace(_plane3.wrapped, _wire_p9b.wrapped, True)
_face_p9b  = Face(_mkf_p9b.Face())
_solid_p9b = Solid.extrude(_face_p9b, _EXT_VEC3)

# Profile at y=2094.9194, extruded -Y to y=1972.919500
# Arc P4→P5: R=-24.8449, centre to RIGHT (negative R); centre≈(554.522, 90.606), midpoint≈(572.398, 73.345)
_p11_y  = 2094.9194
_p11_p1 = gp_Pnt(535.1263, _p11_y, 65.7763)
_p11_p2 = gp_Pnt(535.1263, _p11_y, 104.5533)
_p11_p3 = gp_Pnt(579.3677, _p11_y, 104.5533)
_p11_p4 = gp_Pnt(579.3677, _p11_y, 90.6977)
_p11_p5 = gp_Pnt(555.3676, _p11_y, 65.7763)
_p11_pm = gp_Pnt(572.398,  _p11_y, 73.345)
_p11_mw = BRepBuilderAPI_MakeWire()
_p11_mw.Add(BRepBuilderAPI_MakeEdge(_p11_p1, _p11_p2).Edge())
_p11_mw.Add(BRepBuilderAPI_MakeEdge(_p11_p2, _p11_p3).Edge())
_p11_mw.Add(BRepBuilderAPI_MakeEdge(_p11_p3, _p11_p4).Edge())
_p11_mw.Add(BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(_p11_p4, _p11_pm, _p11_p5).Value()).Edge())
_p11_mw.Add(BRepBuilderAPI_MakeEdge(_p11_p5, _p11_p1).Edge())
_face_p11  = Face(BRepBuilderAPI_MakeFace(_p11_mw.Wire(), True).Face())
_solid_p11 = Solid.extrude(_face_p11, Vector(0.0, -1.0, 0.0) * (2094.9194 - 1972.9195))

# Profile at y=1534.9194, extruded +Y to y=1972.91946411
# Arc P3→P4: R=178.6559, centre to LEFT (positive R); midpoint ≈ (618.67, 1534.9194, 514.14)
_p10_y  = 1534.9194
_p10_p1 = gp_Pnt(674.3677, _p10_y, 535.2117)
_p10_p2 = gp_Pnt(659.3677, _p10_y, 535.2117)
_p10_p3 = gp_Pnt(633.1662, _p10_y, 521.7741)
_p10_p4 = gp_Pnt(604.882,  _p10_y, 505.4555)
_p10_pm = gp_Pnt(618.67,   _p10_y, 514.14)
_p10_p5 = gp_Pnt(591.1442, _p10_y, 493.4238)
_p10_p6 = gp_Pnt(579.1413, _p10_y, 478.9362)
_p10_p7 = gp_Pnt(450.8677, _p10_y, 295.7425)
_p10_p8 = gp_Pnt(450.8677, _p10_y, 65.6976)
_p10_p9 = gp_Pnt(674.3677, _p10_y, 65.6976)
_p10_mw = BRepBuilderAPI_MakeWire()
_p10_mw.Add(BRepBuilderAPI_MakeEdge(_p10_p1, _p10_p2).Edge())
_p10_mw.Add(BRepBuilderAPI_MakeEdge(_p10_p2, _p10_p3).Edge())
_p10_mw.Add(BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(_p10_p3, _p10_pm, _p10_p4).Value()).Edge())
_p10_mw.Add(BRepBuilderAPI_MakeEdge(_p10_p4, _p10_p5).Edge())
_p10_mw.Add(BRepBuilderAPI_MakeEdge(_p10_p5, _p10_p6).Edge())
_p10_mw.Add(BRepBuilderAPI_MakeEdge(_p10_p6, _p10_p7).Edge())
_p10_mw.Add(BRepBuilderAPI_MakeEdge(_p10_p7, _p10_p8).Edge())
_p10_mw.Add(BRepBuilderAPI_MakeEdge(_p10_p8, _p10_p9).Edge())
_p10_mw.Add(BRepBuilderAPI_MakeEdge(_p10_p9, _p10_p1).Edge())
_face_p10  = Face(BRepBuilderAPI_MakeFace(_p10_mw.Wire(), True).Face())
_solid_p10 = Solid.extrude(_face_p10, Vector(0.0, 1.0, 0.0) * (1972.91946411 - 1534.9194))

# Cut along X axis: profile in the YZ plane at x=241.7138, extruded through full body width.
# Face placed at x=-100 and extruded +X by 900 to span x=-100..800 (body x range ~119..674).
# Arc: P3→P4 with R=25, centre at (y=2229.9194, z=90.6977); midpoint at 315° sweep.
_xc_x0 = -100.0
_xc_p1 = gp_Pnt(_xc_x0, 2265.8688, 90.6977)
_xc_p2 = gp_Pnt(_xc_x0, 2265.8688, 65.6976)
_xc_p3 = gp_Pnt(_xc_x0, 2229.9194, 65.6976)
_xc_p4 = gp_Pnt(_xc_x0, 2254.9194, 90.6977)
_xc_pm = gp_Pnt(_xc_x0, 2247.597,  73.021)   # 90-deg arc midpoint
_xc_e1   = BRepBuilderAPI_MakeEdge(_xc_p1, _xc_p2).Edge()
_xc_e2   = BRepBuilderAPI_MakeEdge(_xc_p2, _xc_p3).Edge()
_xc_e3   = BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(_xc_p3, _xc_pm, _xc_p4).Value()).Edge()
_xc_e4   = BRepBuilderAPI_MakeEdge(_xc_p4, _xc_p1).Edge()
_xc_mw   = BRepBuilderAPI_MakeWire()
_xc_mw.Add(_xc_e1); _xc_mw.Add(_xc_e2); _xc_mw.Add(_xc_e3); _xc_mw.Add(_xc_e4)
_face_cut_x  = Face(BRepBuilderAPI_MakeFace(_xc_mw.Wire(), True).Face())
_solid_cut_x = Solid.extrude(_face_cut_x, Vector(1.0, 0.0, 0.0) * 900.0)

# Profile at x=550.8677 in YZ plane, cut +X to x=900 (13 straight-line segments)
_p12_x    = 550.8677
_p12_poly = BRepBuilderAPI_MakePolygon()
for _y12, _z12 in [
    (1626.0345, 572.8863),
    (1972.9195, 572.8863),
    (1972.9195, 483.544),
    (1964.9194, 483.544),
    (1952.9195, 462.6226),
    (1952.9195, 325.6977),
    (1902.9195, 325.6977),
    (1902.9195, 65.6976),
    (1681.9194, 65.6976),
    (1681.9194, 325.6977),
    (1634.9194, 325.6977),
    (1634.9194, 449.6976),
    (1626.0345, 457.6976),
]:
    _p12_poly.Add(gp_Pnt(_p12_x, _y12, _z12))
_p12_poly.Close()
_face_p12  = Face(BRepBuilderAPI_MakeFace(_p12_poly.Wire(), True).Face())
_solid_p12 = Solid.extrude(_face_p12, Vector(1.0, 0.0, 0.0) * (900.0 - _p12_x))

# Profile at y=1952.9195 in XZ plane, cut +Y to y=1972.91946411 (6 straight segments)
_p13_y    = 1952.9195
_p13_poly = BRepBuilderAPI_MakePolygon()
for _x13, _z13 in [
    (674.3677, 375.6977),
    (582.3677, 375.6977),
    (582.3677, 483.544),
    (545.9257, 431.4993),
    (550.8677, 498.7275),
    (674.3677, 498.7275),
]:
    _p13_poly.Add(gp_Pnt(_x13, _p13_y, _z13))
_p13_poly.Close()
_face_p13  = Face(BRepBuilderAPI_MakeFace(_p13_poly.Wire(), True).Face())
_solid_p13 = Solid.extrude(_face_p13, Vector(0.0, 1.0, 0.0) * (1972.91946411 - _p13_y))

# Profile on tilted plane (normal ≈ (0.9915, 0, -0.1304)), extruded 25mm towards body (+X)
# All 5 pts coplanar; extrusion vector = 25 * unit_normal = (24.7866, 0, -3.2596)
# Plane defined explicitly (gp_Pln) to avoid OCC auto-detect failure on BRepBuilderAPI_MakeFace
_p14_poly = BRepBuilderAPI_MakePolygon()
for _x14, _y14, _z14 in [
    (506.679,  1874.9194, 411.3407),
    (506.679,  1673.9194, 411.3407),
    (504.5048, 1658.9194, 394.8081),
    (500.8676, 1658.9194, 367.1499),
    (500.8676, 1874.9194, 367.1499),
]:
    _p14_poly.Add(gp_Pnt(_x14, _y14, _z14))
_p14_poly.Close()
_p14_pln  = gp_Pln(gp_Ax3(
    gp_Pnt(506.679, 1874.9194, 411.3407),   # origin (P1)
    gp_Dir(0.99146352, 0.0, -0.1303844),    # normal towards body
    gp_Dir(0.0, 1.0, 0.0),                  # local x = Y axis (perp to normal)
))
_face_p14  = Face(BRepBuilderAPI_MakeFace(_p14_pln, _p14_poly.Wire(), True).Face())
_solid_p14 = Solid.extrude(_face_p14, Vector(24.7866, 0.0, -3.2596))

# 16-pt profile at y=1914.9194, all straight lines
# Cut 1: straight +Y to y=1937.91946411
# Cut 2: tapered 45° in -Y to y=1902.91946411 (profile narrows by 12mm at far end)
_p15_y    = 1914.9194
_p15_poly = BRepBuilderAPI_MakePolygon()
for _x15, _z15 in [
    (674.3677, 288.5995),
    (627.927,  241.1758),
    (620.7638, 232.4621),
    (615.215,  222.6412),
    (611.4476, 212.009),
    (609.5751, 200.8854),
    (609.6538, 189.6057),
    (611.6815, 178.5094),
    (615.597,  167.9308),
    (621.2823, 158.1884),
    (628.5665, 149.5756),
    (637.2299, 142.3517),
    (647.0118, 136.7345),
    (657.6176, 132.8929),
    (668.7277, 130.9428),
    (674.3677, 130.9428),
]:
    _p15_poly.Add(gp_Pnt(_x15, _p15_y, _z15))
_p15_poly.Close()
_face_p15      = Face(BRepBuilderAPI_MakeFace(_p15_poly.Wire(), True).Face())
_solid_cut_p15a = Solid.extrude(_face_p15, Vector(0.0, 1.0, 0.0) * (1937.9195 + 0.01 - _p15_y))
_solid_cut_p15b = Solid.extrude_taper(_face_p15, Vector(0.0, -1.0, 0.0) * (_p15_y - 1902.91946411), taper=-45)
# Mirror both cuts about the plane y=1937.9195 (defined by the given rectangle)
_p15_mirror_plane  = Plane(
    origin=Vector(0.0, 1937.9195, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 1.0, 0.0),   # normal = +Y
)
_solid_cut_p15a_mirror = _solid_cut_p15a.mirror(_p15_mirror_plane)
_solid_cut_p15b_mirror = _solid_cut_p15b.mirror(_p15_mirror_plane)

# Rectangle at x=500.8677 in YZ plane, cut -X to x=440
_p19_x    = 500.8677
_p19_poly = BRepBuilderAPI_MakePolygon()
for _y19, _z19 in [
    (1534.9194, 570.204),
    (1534.9194, 65.6976),
    (1874.9194, 65.6976),
    (1874.9194, 570.204),
]:
    _p19_poly.Add(gp_Pnt(_p19_x, _y19, _z19))
_p19_poly.Close()
_face_p19      = Face(BRepBuilderAPI_MakeFace(_p19_poly.Wire(), True).Face())
_solid_cut_p19 = Solid.extrude(_face_p19, Vector(-1.0, 0.0, 0.0) * (_p19_x - 440.0))

# 9-pt profile at y=1623.9194, cut +Y to y=1683.91937256
_p18_y    = 1623.9194
_p18_poly = BRepBuilderAPI_MakePolygon()
for _x18, _z18 in [
    (674.3677, 618.7891),
    (522.6005, 618.7891),
    (522.6005, 457.6976),
    (595.4828, 457.6976),
    (604.3677, 449.6976),
    (604.3677, 325.6977),
    (639.1139, 325.6977),
    (639.1139, 309.6976),
    (674.3677, 345.6977),
]:
    _p18_poly.Add(gp_Pnt(_x18, _p18_y, _z18))
_p18_poly.Close()
_face_p18      = Face(BRepBuilderAPI_MakeFace(_p18_poly.Wire(), True).Face())
_solid_cut_p18 = Solid.extrude(_face_p18, Vector(0.0, 1.0, 0.0) * (1683.91937256 - _p18_y))

# 30-pt profile at y=1669.9194
# Cut 1: straight -Y to y=1500; Cut 2: tapered 45° +Y to y=1685
_p17_y    = 1669.9194
_p17_poly = BRepBuilderAPI_MakePolygon()
for _x17, _z17 in [
    (674.3677, 345.6977),
    (639.1139, 309.6976),
    (627.927,  298.2739),
    (623.4131, 292.783),
    (620.7638, 289.5603),
    (617.3228, 283.4699),
    (615.215,  279.7394),
    (612.9164, 273.2523),
    (611.4476, 269.1071),
    (610.3238, 262.4317),
    (609.5751, 257.9836),
    (609.6215, 251.3273),
    (609.6538, 246.7039),
    (610.83,   240.267),
    (611.6815, 235.6076),
    (613.9136, 229.5769),
    (615.597,  225.029),
    (618.7812, 219.5725),
    (621.2823, 215.2865),
    (625.2891, 210.549),
    (628.5665, 206.6737),
    (633.2452, 202.7725),
    (637.2299, 199.4499),
    (642.4147, 196.4726),
    (647.0118, 193.8327),
    (652.5271, 191.835),
    (657.6176, 189.9911),
    (663.2838, 188.9965),
    (668.7277, 188.041),
    (674.3677, 188.041),
]:
    _p17_poly.Add(gp_Pnt(_x17, _p17_y, _z17))
_p17_poly.Close()
_face_p17       = Face(BRepBuilderAPI_MakeFace(_p17_poly.Wire(), True).Face())
_solid_cut_p17a = Solid.extrude(_face_p17, Vector(0.0, -1.0, 0.0) * (_p17_y - 1500.0))
_solid_cut_p17b = Solid.extrude_taper(_face_p17, Vector(0.0, 1.0, 0.0) * (1685.0 - _p17_y), taper=-45)

# 29-pt profile at y=1972.9195, cut -Y to y=1950 (22.9195 mm)
_p16_y    = 1972.9195
_p16_poly = BRepBuilderAPI_MakePolygon()
for _x16, _z16 in [
    (571.8677, 363.9902),
    (579.0125, 356.6943),
    (580.1144, 355.3537),
    (580.9681, 353.8428),
    (581.5477, 352.2071),
    (581.8358, 350.4958),
    (581.8237, 348.7604),
    (581.5117, 347.0533),
    (580.9093, 345.4258),
    (580.0347, 343.927),
    (578.9141, 342.602),
    (577.5812, 341.4906),
    (576.0763, 340.6264),
    (574.4447, 340.0354),
    (572.7354, 339.7354),
    (571.0,    339.7354),
    (569.2908, 340.0354),
    (567.6591, 340.6264),
    (566.1542, 341.4906),
    (564.8214, 342.602),
    (563.7007, 343.927),
    (562.826,  345.4258),
    (562.2237, 347.0533),
    (561.9117, 348.7604),
    (561.8996, 350.4958),
    (562.1877, 352.2071),
    (562.7673, 353.8428),
    (563.6209, 355.3537),
    (564.723,  356.6943),
]:
    _p16_poly.Add(gp_Pnt(_x16, _p16_y, _z16))
_p16_poly.Close()
_face_p16  = Face(BRepBuilderAPI_MakeFace(_p16_poly.Wire(), True).Face())
_solid_cut_p16 = Solid.extrude(_face_p16, Vector(0.0, -1.0, 0.0) * (_p16_y - 1950.0))

# 7-pt profile at y=1874.9194, cut to y=2094.91943359
_p20_y = 1874.9194
_p20_p1 = gp_Pnt(450.8677, _p20_y, 122.0519)
_p20_p2 = gp_Pnt(429.0749, _p20_y, 122.0519)
_p20_p3 = gp_Pnt(429.0749, _p20_y,  43.2064)
_p20_p4 = gp_Pnt(484.9523, _p20_y,  43.2064)
_p20_p5 = gp_Pnt(484.9523, _p20_y,  65.6976)
_p20_p6 = gp_Pnt(475.694,  _p20_y,  65.6834)
_p20_p7 = gp_Pnt(450.7387, _p20_y,  90.6388)  # arc end
# Arc P6→P7: R=-25.3288 (center to right of travel), midpoint≈(458.154, y, 73.099)
_p20_pm = gp_Pnt(458.154,  _p20_y,  73.099)
_p20_arc = GC_MakeArcOfCircle(_p20_p6, _p20_pm, _p20_p7).Value()
_p20_mw = BRepBuilderAPI_MakeWire()
_p20_mw.Add(BRepBuilderAPI_MakeEdge(_p20_p1, _p20_p2).Edge())
_p20_mw.Add(BRepBuilderAPI_MakeEdge(_p20_p2, _p20_p3).Edge())
_p20_mw.Add(BRepBuilderAPI_MakeEdge(_p20_p3, _p20_p4).Edge())
_p20_mw.Add(BRepBuilderAPI_MakeEdge(_p20_p4, _p20_p5).Edge())
_p20_mw.Add(BRepBuilderAPI_MakeEdge(_p20_p5, _p20_p6).Edge())
_p20_mw.Add(BRepBuilderAPI_MakeEdge(_p20_arc).Edge())
_p20_mw.Add(BRepBuilderAPI_MakeEdge(_p20_p7, _p20_p1).Edge())  # closing edge
_face_p20 = Face(BRepBuilderAPI_MakeFace(_p20_mw.Wire(), True).Face())
_solid_cut_p20 = Solid.extrude(_face_p20, Vector(0.0, 1.0, 0.0) * (2094.91943359 - _p20_y))

# 29-pt profile at x=500.8677, cut +X to x=550.86769104
_p21_x = 500.8677
_p21_poly = BRepBuilderAPI_MakePolygon()
for _y21, _z21 in [
    (1773.9194, 191.4395),
    (1768.5608, 185.9675),
    (1767.7344, 184.9621),
    (1767.0941, 183.8289),
    (1766.6594, 182.6021),
    (1766.4433, 181.3187),
    (1766.4525, 180.0172),
    (1766.6864, 178.7368),
    (1767.1382, 177.5162),
    (1767.7942, 176.3921),
    (1768.6346, 175.3983),
    (1769.6342, 174.5648),
    (1770.7629, 173.9166),
    (1771.9867, 173.4734),
    (1773.2686, 173.2484),
    (1774.5702, 173.2484),
    (1775.8521, 173.4734),
    (1777.0758, 173.9166),
    (1778.2045, 174.5648),
    (1779.2041, 175.3983),
    (1780.0446, 176.3921),
    (1780.7007, 177.5162),
    (1781.1525, 178.7368),
    (1781.3864, 180.0172),
    (1781.3954, 181.3187),
    (1781.1794, 182.6021),
    (1780.7448, 183.8289),
    (1780.1045, 184.9621),
    (1779.278,  185.9675),
]:
    _p21_poly.Add(gp_Pnt(_p21_x, _y21, _z21))
_p21_poly.Close()
_face_p21 = Face(BRepBuilderAPI_MakeFace(_p21_poly.Wire(), True).Face())
_solid_cut_p21 = Solid.extrude(_face_p21, Vector(1.0, 0.0, 0.0) * (900.0 - _p21_x))

# 30-pt profile at y=1612.9195, cut -Y to y=1520.91943359
_p22_y = 1612.9195
_p22_poly = BRepBuilderAPI_MakePolygon()
for _x22, _z22 in [
    (569.3677, 413.2828),
    (555.0782, 398.6909),
    (553.635,  397.0461),
    (551.7535, 394.1708),
    (550.392,  391.0159),
    (549.5905, 387.6746),
    (549.3728, 384.2453),
    (549.7454, 380.8294),
    (550.6971, 377.5277),
    (552.2,    374.4376),
    (554.2096, 371.6504),
    (556.6666, 369.2483),
    (559.4986, 367.3022),
    (562.6218, 365.8697),
    (565.9443, 364.9928),
    (569.3677, 364.6976),
    (572.7912, 364.9928),
    (576.1135, 365.8697),
    (579.2368, 367.3022),
    (582.0688, 369.2483),
    (584.5258, 371.6504),
    (586.5355, 374.4376),
    (588.0383, 377.5277),
    (588.9901, 380.8294),
    (589.3626, 384.2453),
    (589.1449, 387.6746),
    (588.3435, 391.0159),
    (586.9819, 394.1708),
    (585.1004, 397.0461),
    (583.6572, 398.6909),
]:
    _p22_poly.Add(gp_Pnt(_x22, _p22_y, _z22))
_p22_poly.Close()
_face_p22 = Face(BRepBuilderAPI_MakeFace(_p22_poly.Wire(), True).Face())
_solid_cut_p22 = Solid.extrude(_face_p22, Vector(0.0, -1.0, 0.0) * (_p22_y - 1520.91943359))

# 29-pt profile at y=1612.9195, cut +Y to y=1635
_p23_y = 1612.9195
_p23_poly = BRepBuilderAPI_MakePolygon()
for _x23, _z23 in [
    (569.3677, 398.9902),
    (562.223,  391.6943),
    (561.1209, 390.3537),
    (560.2673, 388.8428),
    (559.6877, 387.2071),
    (559.3996, 385.4958),
    (559.4117, 383.7605),
    (559.7237, 382.0533),
    (560.326,  380.4258),
    (561.2008, 378.927),
    (562.3214, 377.6019),
    (563.6542, 376.4906),
    (565.1591, 375.6264),
    (566.7908, 375.0354),
    (568.5,    374.7354),
    (570.2354, 374.7354),
    (571.9447, 375.0354),
    (573.5763, 375.6264),
    (575.0812, 376.4906),
    (576.414,  377.6019),
    (577.5347, 378.927),
    (578.4093, 380.4258),
    (579.0117, 382.0533),
    (579.3237, 383.7605),
    (579.3358, 385.4958),
    (579.0477, 387.2071),
    (578.4681, 388.8428),
    (577.6144, 390.3537),
    (576.5125, 391.6943),
]:
    _p23_poly.Add(gp_Pnt(_x23, _p23_y, _z23))
_p23_poly.Close()
_face_p23 = Face(BRepBuilderAPI_MakeFace(_p23_poly.Wire(), True).Face())
_solid_cut_p23 = Solid.extrude(_face_p23, Vector(0.0, 1.0, 0.0) * (1635.0 - _p23_y))

# 8-pt profile at y=1634.9194, extruded -Y to y=1623.9194 (ADD)
_p24_y = 1634.9194
_p24_poly = BRepBuilderAPI_MakePolygon()
for _x24, _z24 in [
    (744.3676, 421.5978),
    (744.3676, 505.0051),
    (757.5912, 493.4238),
    (769.5941, 478.9362),
    (784.4655, 457.6976),
    (790.0672, 449.6976),
    (797.8677, 438.5573),
    (797.8677, 421.5978),
]:
    _p24_poly.Add(gp_Pnt(_x24, _p24_y, _z24))
_p24_poly.Close()
_face_p24 = Face(BRepBuilderAPI_MakeFace(_p24_poly.Wire(), True).Face())
_solid_p24 = Solid.extrude(_face_p24, Vector(0.0, -1.0, 0.0) * (_p24_y - 1623.9194))

# 20-pt profile at y=1534.9194, extruded -Y to y=1514.91943359 (ADD, spans mirror plane)
_p25_y = 1534.9194
_p25_poly = BRepBuilderAPI_MakePolygon()
for _x25, _z25 in [
    (743.8535, 431.4164),
    (604.882,  431.4164),
    (604.882,  505.4555),
    (605.3305, 505.7806),
    (607.6484, 507.3669),
    (610.595,  509.3531),
    (613.6742, 511.3356),
    (616.8553, 513.2555),
    (620.1198, 515.072),
    (621.318,  515.6976),
    (623.4581, 516.7952),
    (630.3477, 520.3286),
    (659.3677, 535.2117),
    (689.4397, 535.2117),
    (715.7042, 521.7049),
    (727.4174, 515.6976),
    (732.0591, 513.1576),
    (738.3979, 509.2008),
    (741.987,  506.8184),
    (743.8535, 505.4555),
]:
    _p25_poly.Add(gp_Pnt(_x25, _p25_y, _z25))
_p25_poly.Close()
_face_p25 = Face(BRepBuilderAPI_MakeFace(_p25_poly.Wire(), True).Face())
_solid_p25 = Solid.extrude(_face_p25, Vector(0.0, -1.0, 0.0) * (_p25_y - 1514.91943359))

# 8-pt XY profile, cut -Z by 1100mm (z=1000→z=-100, through full body height)
# Point 4 z corrected to 431.4164 (was 180.707 by mistake)
_p26_z = 1000.0
_p26_p1 = gp_Pnt(597.927,  1534.9194, _p26_z)
_p26_p2 = gp_Pnt(597.927,  1506.8674, _p26_z)
_p26_p3 = gp_Pnt(747.9626, 1506.8674, _p26_z)
_p26_p4 = gp_Pnt(747.9544, 1534.9194, _p26_z)
_p26_p5 = gp_Pnt(743.8535, 1534.9194, _p26_z)
_p26_p6 = gp_Pnt(715.5692, 1514.9194, _p26_z)  # arc 1 end
_p26_p7 = gp_Pnt(633.1662, 1514.9194, _p26_z)
_p26_p8 = gp_Pnt(604.882,  1534.9194, _p26_z)  # arc 2 end
# Arc 1 midpoint: R=-30, P5→P6, centre≈(715.568,1544.919), mid angle≈305.3°
_p26_pm1 = gp_Pnt(732.889, 1520.424, _p26_z)
# Arc 2 midpoint: R=-30, P7→P8, centre≈(633.167,1544.919), mid angle≈234.7°
_p26_pm2 = gp_Pnt(615.846, 1520.424, _p26_z)
_p26_arc1 = GC_MakeArcOfCircle(_p26_p5, _p26_pm1, _p26_p6).Value()
_p26_arc2 = GC_MakeArcOfCircle(_p26_p7, _p26_pm2, _p26_p8).Value()
_p26_mw = BRepBuilderAPI_MakeWire()
_p26_mw.Add(BRepBuilderAPI_MakeEdge(_p26_p1, _p26_p2).Edge())
_p26_mw.Add(BRepBuilderAPI_MakeEdge(_p26_p2, _p26_p3).Edge())
_p26_mw.Add(BRepBuilderAPI_MakeEdge(_p26_p3, _p26_p4).Edge())
_p26_mw.Add(BRepBuilderAPI_MakeEdge(_p26_p4, _p26_p5).Edge())
_p26_mw.Add(BRepBuilderAPI_MakeEdge(_p26_arc1).Edge())
_p26_mw.Add(BRepBuilderAPI_MakeEdge(_p26_p6, _p26_p7).Edge())
_p26_mw.Add(BRepBuilderAPI_MakeEdge(_p26_arc2).Edge())
_p26_mw.Add(BRepBuilderAPI_MakeEdge(_p26_p8, _p26_p1).Edge())
_face_p26 = Face(BRepBuilderAPI_MakeFace(_p26_mw.Wire(), True).Face())
_solid_cut_p26 = Solid.extrude(_face_p26, Vector(0.0, 0.0, -1.0) * 1100.0)

# Profile p28: 18-pt XY at z=1000, cut -Z through full body (debug: profile position check)
_p28_z = 1000.0
_p28_p1  = gp_Pnt(564.2699, 1605.9193, _p28_z)
_p28_p2  = gp_Pnt(564.2699, 1622.9195, _p28_z)
_p28_p3  = gp_Pnt(568.0728, 1626.0345, _p28_z)
_p28_p4  = gp_Pnt(595.4828, 1626.0345, _p28_z)
_p28_p5  = gp_Pnt(595.4828, 1615.0345, _p28_z)
_p28_p6  = gp_Pnt(653.8788, 1615.0345, _p28_z)
_p28_p7  = gp_Pnt(682.758,  1592.1819, _p28_z)
_p28_p8  = gp_Pnt(689.8094, 1539.081,  _p28_z)  # arc1 end
_p28_pm1 = gp_Pnt(697.030,  1567.073,  _p28_z)  # arc1 mid R=-38.5003
_p28_p9  = gp_Pnt(685.4605, 1534.1505, _p28_z)
_p28_p10 = gp_Pnt(682.3677, 1526.9194, _p28_z)  # arc2 end
_p28_pm2 = gp_Pnt(683.177,  1530.848,  _p28_z)  # arc2 mid R=+9.9976
_p28_p11 = gp_Pnt(682.3677, 1500.7154, _p28_z)
_p28_p12 = gp_Pnt(666.3677, 1500.7154, _p28_z)
_p28_p13 = gp_Pnt(666.3677, 1519.9194, _p28_z)
_p28_p14 = gp_Pnt(666.3677, 1526.9194, _p28_z)
_p28_p15 = gp_Pnt(671.6169, 1542.5847, _p28_z)  # arc3 end
_p28_pm3 = gp_Pnt(670.271,  1534.324,  _p28_z)  # arc3 mid R=+25.9991
_p28_p16 = gp_Pnt(674.409,  1545.7205, _p28_z)
_p28_p17 = gp_Pnt(668.856,  1582.1521, _p28_z)  # arc4 end
_p28_pm4 = gp_Pnt(662.154,  1562.502,  _p28_z)  # arc4 mid R=-22.4999
_p28_p18 = gp_Pnt(620.882,  1605.9193, _p28_z)
_p28_arc1 = GC_MakeArcOfCircle(_p28_p7,  _p28_pm1, _p28_p8).Value()
_p28_arc2 = GC_MakeArcOfCircle(_p28_p9,  _p28_pm2, _p28_p10).Value()
_p28_arc3 = GC_MakeArcOfCircle(_p28_p14, _p28_pm3, _p28_p15).Value()
_p28_arc4 = GC_MakeArcOfCircle(_p28_p16, _p28_pm4, _p28_p17).Value()
_p28_mw = BRepBuilderAPI_MakeWire()
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p1,  _p28_p2).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p2,  _p28_p3).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p3,  _p28_p4).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p4,  _p28_p5).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p5,  _p28_p6).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p6,  _p28_p7).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_arc1).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p8,  _p28_p9).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_arc2).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p10, _p28_p11).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p11, _p28_p12).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p12, _p28_p13).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p13, _p28_p14).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_arc3).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p15, _p28_p16).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_arc4).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p17, _p28_p18).Edge())
_p28_mw.Add(BRepBuilderAPI_MakeEdge(_p28_p18, _p28_p1).Edge())
_face_p28 = Face(BRepBuilderAPI_MakeFace(_p28_mw.Wire(), True).Face())
_solid_cut_p28 = Solid.extrude(_face_p28, Vector(0.0, 0.0, -1.0) * 1100.0)

with BuildPart() as part:
    # Extrude from y=2230.9193 to y=2094.91943359
    _vec = Vector(0.0, -1.0, 0.0) * (2230.9193 - 2094.91943359)
    _solid = Solid.extrude(_face, _vec)
    add(_solid)
    # Extrude from y=1972.9195 to y=2094.91943359
    _vec2 = Vector(0.0, 1.0, 0.0) * (2094.91943359 - 1972.9195)
    _solid2 = Solid.extrude(_face2, _vec2)
    add(_solid2)
    # Profile at y=2094.9194 → y=1972.919500
    add(_solid_p11)
    # Tilted-plane profile extruded 25mm towards body (+X normal)
    add(_solid_p14)
    # Profile at y=1534.9194 → y=1972.91946411
    add(_solid_p10)
    # Add top profiles (y=2254.9194 → y=2230.91934204)
    for _ts in _top_solids:
        add(_ts)
    # Profile at y=2076.9194 → y=2094.91943359
    add(_solid_p9)
    # Comb base profile y=2254.9194 → y=2230.91934204
    add(_solid_p9b)
    # Cut from y=2230.9193 down to y=2094.91943359
    add(_solid_cut_top, mode=Mode.SUBTRACT)
    # 29-point circular cut through full body (±100 mm extended)
    add(_solid_cut_p1, mode=Mode.SUBTRACT)
    # Loft cut from y=2118.358 down to y=2094.9194
    add(_solid_loft_cut, mode=Mode.SUBTRACT)
    # Second loft cut (y~2094.9 → y=2124.9194) + through cut
    add(_solid_loft2_cut, mode=Mode.SUBTRACT)
    add(_solid_thru2, mode=Mode.SUBTRACT)
    # Circle cut dia=15.0000752 mm along Z, centre (591.9933, 2144.9194, 737.6976)
    add(_solid_cyl_cut, mode=Mode.SUBTRACT)
    # X-axis cut: profile in YZ plane at x=241.7138, through full body width
    add(_solid_cut_x, mode=Mode.SUBTRACT)
    # Cut at x=550.8677, 13-pt YZ profile, extruded +X to x=900
    add(_solid_p12, mode=Mode.SUBTRACT)
    # Cut at y=1952.9195, 6-pt XZ profile, extruded +Y to y=1972.91946411
    add(_solid_p13, mode=Mode.SUBTRACT)
    # Rectangle at x=500.8677, cut -X to x=440
    add(_solid_cut_p19, mode=Mode.SUBTRACT)
    # 9-pt profile at y=1623.9194, cut +Y to y=1683.91937256
    add(_solid_cut_p18, mode=Mode.SUBTRACT)
    # 30-pt profile at y=1669.9194: straight cut -Y to y=1500
    add(_solid_cut_p17a, mode=Mode.SUBTRACT)
    # 30-pt profile at y=1669.9194: tapered 45° cut +Y to y=1685
    add(_solid_cut_p17b, mode=Mode.SUBTRACT)
    # 29-pt circular profile at y=1972.9195, cut -Y to y=1950
    add(_solid_cut_p16, mode=Mode.SUBTRACT)
    # 16-pt profile at y=1914.9194: straight cut +Y to y=1937.91946411
    add(_solid_cut_p15a, mode=Mode.SUBTRACT)
    # Mirror of straight cut reflected about plane y=1937.9195
    add(_solid_cut_p15a_mirror, mode=Mode.SUBTRACT)
    # 16-pt profile at y=1914.9194: tapered -45° cut -Y to y=1902.91946411
    add(_solid_cut_p15b, mode=Mode.SUBTRACT)
    # Mirror of tapered cut reflected about plane y=1937.9195
    add(_solid_cut_p15b_mirror, mode=Mode.SUBTRACT)
    # 7-pt profile at y=1874.9194, cut +Y to y=2094.91943359
    add(_solid_cut_p20, mode=Mode.SUBTRACT)
    # 29-pt profile at x=500.8677, cut +X to x=900
    add(_solid_cut_p21, mode=Mode.SUBTRACT)
    # 30-pt profile at y=1612.9195, cut -Y to y=1520.91943359
    add(_solid_cut_p22, mode=Mode.SUBTRACT)
    # 29-pt profile at y=1612.9195, cut +Y to y=1635
    add(_solid_cut_p23, mode=Mode.SUBTRACT)
    # Subtract all diamond cut profiles
    for _cs in _cut_solids:
        add(_cs, mode=Mode.SUBTRACT)
    # Fillet edges formed by the 30-pt semi-teardrop cut at y=1534.9194, R=30mm
    # Filter by y-plane AND XZ bounding box of the 30-pt profile (x:609-675, z:187-346)
    _fillet_edges_p17 = [
        e for e in part.edges()
        if abs(e.center().Y - 1534.9194) < 0.5
        and 609.0 < e.center().X < 675.0
        and 187.0 < e.center().Z < 346.0
    ]
    fillet(_fillet_edges_p17, radius=30.0)
    # Fillet 3 edges meeting at corner (500.8677, 1534.9194, 65.6976), R=30mm
    _fillet_edges_3 = [
        e for e in part.edges()
        if (  # Edge 1: x=500.8677, y=1534.9194, z midpoint≈216.42 (z:65.6976→367.1499)
            (abs(e.center().X - 500.8677) < 0.5 and abs(e.center().Y - 1534.9194) < 0.5
             and abs(e.center().Z - 216.4238) < 2.0)
            or  # Edge 2: x midpoint≈587.62, y=1534.9194, z=65.6976 (x:500.8677→674.3677)
            (abs(e.center().X - 587.6177) < 2.0 and abs(e.center().Y - 1534.9194) < 0.5
             and abs(e.center().Z - 65.6976) < 0.5)
            or  # Edge 3: x=500.8677, y midpoint≈1704.92, z=65.6976 (y:1534.9194→1874.9194)
            (abs(e.center().X - 500.8677) < 0.5 and abs(e.center().Y - 1704.9194) < 2.0
             and abs(e.center().Z - 65.6976) < 0.5)
        )
    ]
    fillet(_fillet_edges_3, radius=30.0)
    # Fillet 3 edges of the 29-pt circular cut bottom face, R=15mm
    _fillet_edges_4 = [
        e for e in part.edges()
        if (  # Edge 4: y=1681.9194, z=65.6976, x midpoint≈612.62 (x:550.8677→674.3677)
            (abs(e.center().X - 612.6177) < 2.0 and abs(e.center().Y - 1681.9194) < 0.5
             and abs(e.center().Z - 65.6976) < 0.5)
            or  # Edge 5: x=550.8677, z=65.6976, y midpoint≈1792.42 (y:1681.9194→1902.9195)
            (abs(e.center().X - 550.8677) < 0.5 and abs(e.center().Y - 1792.4195) < 2.0
             and abs(e.center().Z - 65.6976) < 0.5)
            or  # Edge 6: y=1902.9195, z=65.6976, x midpoint≈612.62 (x:550.8677→674.3677)
            (abs(e.center().X - 612.6177) < 2.0 and abs(e.center().Y - 1902.9195) < 0.5
             and abs(e.center().Z - 65.6976) < 0.5)
        )
    ]
    fillet(_fillet_edges_4, radius=15.0)
    # Fillet edges 7 & 8 at y=1874.9194 meeting at corner (450.8677, 1874.9194, 65.6976), R=10mm
    _fillet_edges_78 = [
        e for e in part.edges()
        if (  # Edge 7: x=450.8677, y=1874.9194, z midpoint≈180.72 (z:295.7425→65.6976)
            (abs(e.center().X - 450.8677) < 0.5 and abs(e.center().Y - 1874.9194) < 0.5
             and abs(e.center().Z - 180.7201) < 2.0)
            or  # Edge 8: y=1874.9194, z=65.6976, x in range 440→530
            (440.0 < e.center().X < 530.0 and abs(e.center().Y - 1874.9194) < 0.5
             and abs(e.center().Z - 65.6976) < 0.5)
        )
    ]
    fillet(_fillet_edges_78, radius=10.0)
    # Mirror entire body about plane at x=674.3677 (normal = +X)
    _body_mirror_plane = Plane(
        origin=Vector(674.3677, 0.0, 0.0),
        x_dir=Vector(0.0, 1.0, 0.0),
        z_dir=Vector(1.0, 0.0, 0.0),
    )
    add(part.part.mirror(_body_mirror_plane))
    # 8-pt profile at y=1634.9194 → y=1623.9194 (added after mirror so it protrudes from symmetric body)
    add(_solid_p24)
    # 20-pt profile at y=1534.9194, extruded -Y to y=1514.91943359 (spans mirror plane)
    add(_solid_p25)
    # 8-pt XY profile, cut -Z through full body height
    add(_solid_cut_p26, mode=Mode.SUBTRACT)
    # 18-pt XY profile at z=568.2117, cut -Z to z=457.69763947
    add(_solid_cut_p28, mode=Mode.SUBTRACT)

export_step(part.part, "/Users/softage/Documents/5may/Print_Leader_SO_ARM100_08k_UP_Prusa - Base_08q-3.step")
export_stl(part.part, "/Users/softage/Documents/5may/Print_Leader_SO_ARM100_08k_UP_Prusa - Base_08q-3.stl")
