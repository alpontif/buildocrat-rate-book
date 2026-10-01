"""v3 expansion: heavy infrastructure, oil & gas, marine/ports/reclamation, rail, power, water,
building services, industrial, tools, testing. Run once:  python3 tools/extend_v3.py
Appends to rate-data.json (keeps any existing prices). Imported items are priced in US$ and
linked to M-FX-USD, so they re-price automatically when the exchange rate line is updated.
"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "rate-data.json")
D = json.load(open(PATH, encoding="utf-8"))
SET = "2026-10-01"
EST = "Desk estimate (Oct 2026) - no reliable dated Nigerian source; verify with 3 supplier quotes"
LAND = 1.40   # FOB to delivered Abuja: freight, duty/levies, clearing, inland haulage, dealer margin
SPREAD = {"HIGH": 0.08, "MEDIUM": 0.12, "LOW": 0.20}
new_res, new_lab, new_plant, new_items = [], [], [], []

def rnd(v): return round(v, -1 if v < 10000 else -2)
def M(c, g, cat, d, u, r, w=0.05, conf="LOW", src=EST, ev=None, n=""):
    s = SPREAD[conf]
    new_res.append(dict(c=c, g=g, cat=cat, d=d, u=u, w=w, src=src, ev=ev, set=SET, conf=conf, n=n, r=r, lo=rnd(r * (1 - s)), hi=rnd(r * (1 + s))))
def K(c, g, cat, d, u, b, f, s=0.2, w=0.05, conf="LOW", src=None, n=""):
    new_res.append(dict(c=c, g=g, cat=cat, d=d, u=u, w=w, src=src or f"Derived from {b}", ev=None, set=SET, conf=conf, n=n, k=dict(b=b, f=round(f, 6), s=s)))
def U(c, g, cat, d, u, usd, s=0.2, w=0.05, conf="LOW", src=None, n=""):
    K(c, g, cat, d, u, "M-FX-USD", usd * LAND, s, w, conf,
      src or f"Desk estimate US${usd:,.2f} FOB x {LAND} landed x NFEM rate (Oct 2026); verify", n or "Imported: moves with the exchange rate")
def pipe_kg(od, wt): return 0.02466 * (od - wt) * wt

# ------------------------------------------------------------------ FX
G = "Exchange Rate (Imported Items)"
M("M-FX-USD", G, "FX", "Naira per US dollar (CBN NFEM) - drives all imported-item prices", "USD", 1331, 0, "HIGH",
  "CBN NFEM ~N1,331/$ (28 Sep 2026, WithinNigeria/Vanguard)", "2026-09-28", "Update weekly with meta.fx")
for x in new_res: x["lo"], x["hi"] = 1300, 1400

# ------------------------------------------------------------------ OIL & GAS
G = "Oil & Gas: Line Pipe, Fittings & Valves"
DEX = "Dexin, 'API 5L pipe price list 2026' (26 Jan 2026): X52 US$900-1,100/t, X65 US$1,200-1,450/t"
U("M-OG-LPT", G, "Line pipe", "API 5L X52 PSL2 line pipe (ERW/LSAW), bare, per tonne", "t", 1000, 0.12, 0.02, "MEDIUM", DEX + " x 1.40 landed")
U("M-OG-LPT65", G, "Line pipe", "API 5L X65 PSL2 line pipe, bare, per tonne", "t", 1325, 0.12, 0.02, "MEDIUM", DEX + " x 1.40 landed")
U("M-OG-SMLS", G, "Line pipe", "ASTM A106 Gr.B seamless pipe, per tonne", "t", 1450, 0.2, 0.03)
for nps, od, wt in [(4, 114.3, 6.02), (6, 168.3, 7.11), (8, 219.1, 8.18), (10, 273.1, 9.27), (12, 323.9, 9.53), (16, 406.4, 9.53),
                    (20, 508.0, 12.7), (24, 610.0, 12.7), (30, 762.0, 15.9), (36, 914.0, 19.1)]:
    kg = pipe_kg(od, wt)
    K(f"M-OG-X52-{nps}", G, "Line pipe", f"API 5L X52 line pipe {nps}\" ({od}x{wt}mm, {kg:.1f} kg/m), bare, per m", "m", "M-OG-LPT", kg / 1000, 0.12, 0.02, "MEDIUM", "Derived: X52 price per tonne x pipe weight")
for nps, kg in [(2, 5.44), (3, 11.29), (4, 16.07), (6, 28.26)]:
    K(f"M-OG-SMLS{nps}", G, "Process pipe", f"A106 Gr.B seamless pipe {nps}\" sch40 ({kg} kg/m), per m", "m", "M-OG-SMLS", kg / 1000, 0.2, 0.05)
ELB = {2: 8, 4: 22, 6: 45, 8: 85, 12: 210, 16: 380, 20: 620, 24: 900}
for nps, v in ELB.items():
    U(f"M-OG-ELB{nps}", G, "Fittings", f"Butt-weld 90deg LR elbow {nps}\" STD, carbon steel", "nr", v, w=0)
    U(f"M-OG-TEE{nps}", G, "Fittings", f"Butt-weld equal tee {nps}\" STD, carbon steel", "nr", v * 1.7, w=0)
for nm, v in {"4x2": 10, "6x4": 22, "8x6": 38, "12x8": 95, "16x12": 190}.items():
    U(f"M-OG-RED{nm.replace('x','')}", G, "Fittings", f"Concentric reducer {nm}\" STD, carbon steel", "nr", v, w=0)
WN = {2: 12, 4: 25, 6: 40, 8: 60, 12: 120, 16: 210}
for nps, v in WN.items():
    U(f"M-OG-WN150-{nps}", G, "Flanges", f"Weld-neck flange ANSI 150 RF {nps}\", A105", "nr", v, w=0)
    U(f"M-OG-WN300-{nps}", G, "Flanges", f"Weld-neck flange ANSI 300 RF {nps}\", A105", "nr", v * 1.7, w=0)
for nps, v in {2: 10, 4: 22, 6: 38, 8: 58, 12: 115}.items():
    U(f"M-OG-BLF{nps}", G, "Flanges", f"Blind flange ANSI 150 RF {nps}\", A105", "nr", v, w=0)
for nps, v in {2: 4, 4: 6, 6: 9, 8: 12, 12: 18, 16: 30}.items():
    U(f"M-OG-GSK{nps}", G, "Gaskets & bolting", f"Spiral-wound gasket {nps}\" cl150/300 (SS316/graphite)", "nr", v, w=0.05)
for nps, v in {4: 12, 8: 28, 12: 55}.items():
    U(f"M-OG-STUD{nps}", G, "Gaskets & bolting", f"Stud bolt set B7/2H for {nps}\" cl150 flange joint", "set", v, w=0.05)
for nps, v in {2: 180, 4: 420, 6: 750, 8: 1250, 12: 2900}.items():
    U(f"M-OG-GV{nps}", G, "Valves", f"Gate valve cast steel ANSI 150 RF {nps}\" (API 600)", "nr", v, w=0)
for nps, v in {2: 350, 4: 900, 6: 1900, 8: 3500, 12: 8000}.items():
    U(f"M-OG-BV{nps}", G, "Valves", f"Ball valve full-bore ANSI 300 RF {nps}\" (API 6D)", "nr", v, w=0)
for nps, v in {2: 150, 4: 350, 6: 620, 8: 1000}.items():
    U(f"M-OG-CV{nps}", G, "Valves", f"Swing check valve ANSI 150 RF {nps}\"", "nr", v, w=0)
G = "Oil & Gas: Coating, Cathodic Protection & Welding"
U("M-OG-3LPE", G, "Coating", "3-layer polyethylene (3LPE) factory pipe coating, per m2 of pipe surface", "m2", 14, w=0.02)
U("M-OG-FBE", G, "Coating", "Fusion-bonded epoxy (FBE) factory coating, per m2", "m2", 10, w=0.02)
for nps, v in {8: 35, 12: 55, 16: 75, 24: 110}.items():
    U(f"M-OG-HSS{nps}", G, "Coating", f"Heat-shrink field joint sleeve {nps}\" with primer", "nr", v, w=0.03)
U("M-OG-LEP", G, "Coating", "High-build liquid epoxy coating (2-part), per litre", "L", 18, w=0.1)
U("M-OG-CWC", G, "Coating", "Concrete weight coating (3,040 kg/m3), applied, per m3", "m3", 650, w=0.03)
M("M-OG-GRIT", G, "Coating", "Abrasive blasting grit (copper slag/garnet), per tonne", "t", 180000, 0.05)
U("M-OG-MGAN", G, "Cathodic protection", "Magnesium anode 17lb pre-packaged with lead cable", "nr", 60, w=0)
U("M-OG-ZNAN", G, "Cathodic protection", "Zinc anode 30kg", "nr", 120, w=0)
U("M-OG-ALAN", G, "Cathodic protection", "Al-Zn-In sacrificial anode 200kg (offshore/marine piles)", "nr", 900, w=0)
M("M-OG-CPTP", G, "Cathodic protection", "CP test post with terminals", "nr", 85000, 0)
U("M-OG-TRU", G, "Cathodic protection", "Transformer-rectifier unit 50V/50A, oil-cooled", "nr", 6000, w=0)
M("M-OG-CPCAB", G, "Cathodic protection", "CP cable 16mm2 HMWPE, per m", "m", 4500, 0.05)
U("M-OG-E6010", G, "Welding", "Cellulosic electrode E6010 (root pass), per kg", "kg", 4.5, w=0.1)
U("M-OG-E7018", G, "Welding", "Low-hydrogen electrode E7018, per kg", "kg", 3.5, w=0.1)
U("M-OG-ER70", G, "Welding", "MIG/GMAW wire ER70S-6, per kg", "kg", 2.5, w=0.1)
U("M-OG-PIGL", G, "Pipeline equipment", "Pig launcher/receiver 12\" ANSI 300 with closure", "nr", 45000, w=0)
U("M-OG-IJ12", G, "Pipeline equipment", "Monolithic insulating joint 12\" ANSI 300", "nr", 3500, w=0)
M("M-OG-MRK", G, "Pipeline equipment", "Pipeline marker post (steel, painted, with plate)", "nr", 45000, 0)
M("M-OG-WTAPE", G, "Pipeline equipment", "Underground warning tape 300mm, per m", "m", 250, 0.05)
U("M-OG-RSH", G, "Pipeline equipment", "Rockshield mesh for pipe protection, per m2", "m2", 6, w=0.08)
M("M-OG-SBAG", G, "Pipeline equipment", "Sandbag (filled) for pipe supports/trench breakers", "nr", 600, 0.05)
M("M-OG-PSAD", G, "Pipeline equipment", "Pipe support saddle, fabricated steel", "nr", 60000, 0)
U("M-OG-H2S", G, "Pipeline equipment", "Personal H2S/4-gas detector", "nr", 450, w=0)
G = "Oil & Gas: Fuel Stations & Storage"
M("M-OG-UGT", G, "Fuel station", "Underground steel fuel tank 33,000L, coated", "nr", 9500000, 0)
U("M-OG-DISP", G, "Fuel station", "Fuel dispenser, 2-nozzle electronic", "nr", 6500, w=0)
M("M-OG-OIL", G, "Fuel station", "Precast oil/water interceptor", "nr", 1800000, 0)
M("M-OG-PLT", G, "Tank fabrication", "Steel plate S275 for storage tanks, per tonne", "t", 1500000, 0.05)

# ------------------------------------------------------------------ PILING & GROUND ENGINEERING
G = "Piling & Ground Engineering"
U("M-PG-SPT", G, "Sheet piles", "Hot-rolled steel sheet piles S355GP, per tonne", "t", 850, w=0.02)
for code, nm, kg in [("PU12", "PU12 / Larssen 600-type", 110), ("PU18", "PU18", 128), ("PU28", "PU28", 163), ("AZ26", "AZ26-700", 155)]:
    K(f"M-PG-{code}", G, "Sheet piles", f"Sheet pile {nm} ({kg} kg/m2 of wall), per m2", "m2", "M-PG-SPT", kg / 1000, 0.2, 0.03)
U("M-PG-HPT", G, "Bearing piles", "H-section bearing piles S355, per tonne", "t", 900, w=0.03)
for nm, kg in [("HP305x79", 79), ("HP305x110", 110), ("HP356x174", 174)]:
    K(f"M-PG-{nm.replace('x','X')}", G, "Bearing piles", f"H-pile {nm} ({kg} kg/m), per m", "m", "M-PG-HPT", kg / 1000, 0.2, 0.03)
U("M-PG-TPT", G, "Bearing piles", "Spiral-welded steel tubular piles, per tonne", "t", 1000, w=0.03)
for d, t in [(610, 12), (762, 14), (914, 16)]:
    kg = pipe_kg(d, t)
    K(f"M-PG-TP{d}", G, "Bearing piles", f"Steel tubular pile {d}x{t}mm ({kg:.0f} kg/m), per m", "m", "M-PG-TPT", kg / 1000, 0.2, 0.03)
for s, v in [(300, 85000), (350, 110000), (400, 145000), (450, 185000)]:
    M(f"M-PG-PC{s}", G, "Bearing piles", f"Precast reinforced concrete pile {s}x{s}mm, delivered, per m", "m", v, 0.03)
M("M-PG-BENT", G, "Drilling fluids", "Bentonite (API grade), per tonne", "t", 460000, 0.05)
U("M-PG-POLY", G, "Drilling fluids", "Polymer drilling slurry, per kg", "kg", 6)
M("M-PG-SHOE", G, "Bearing piles", "Cast-steel pile shoe", "nr", 120000, 0)
K("M-PG-AB32", G, "Anchors & nails", "Ground anchor bar 32mm high-yield, per m (incl. couplers)", "m", "M-STL-09", 6.313 / 1000 * 1.3, 0.2, 0.05)
K("M-PG-SN25", G, "Anchors & nails", "Soil nail bar 25mm, per m (incl. centralisers)", "m", "M-STL-02", 3.853 / 1000 * 1.2, 0.2, 0.05)
M("M-PG-NHP", G, "Anchors & nails", "Soil nail head plate & nut", "nr", 12000, 0)
U("M-PG-PVD", G, "Ground improvement", "Prefabricated vertical (wick) drain, per m", "m", 0.18, w=0.08)
M("M-PG-SPLT", G, "Instrumentation", "Settlement plate with riser pipe", "nr", 85000, 0)
U("M-PG-INCL", G, "Instrumentation", "Inclinometer casing 70mm, per m", "m", 25)
U("M-PG-PZM", G, "Instrumentation", "Vibrating-wire piezometer with cable", "nr", 450, w=0)
G = "Geosynthetics & Erosion Control"
M("M-GS-WOV", G, "Geotextile", "Woven polypropylene geotextile, per m2", "m2", 1500, 0.1)
M("M-GS-NW400", G, "Geotextile", "Non-woven needle-punched geotextile 400g/m2, per m2", "m2", 2200, 0.1)
M("M-GS-GGB", G, "Geogrid", "Biaxial geogrid 30kN/m, per m2", "m2", 2800, 0.1)
M("M-GS-GGU", G, "Geogrid", "Uniaxial geogrid 80kN/m, per m2", "m2", 4500, 0.1)
M("M-GS-GCELL", G, "Geocell", "HDPE geocell 150mm deep, per m2", "m2", 9500, 0.08)
for t, v in [("1.0", 4500), ("1.5", 6500), ("2.0", 8500)]:
    M(f"M-GS-GM{t.replace('.','')}", G, "Geomembrane", f"HDPE geomembrane {t}mm, per m2", "m2", v, 0.12)
M("M-GS-GCL", G, "Geomembrane", "Geosynthetic clay liner (GCL), per m2", "m2", 7500, 0.15)
M("M-GS-ECB", G, "Erosion control", "Erosion control blanket (coir/straw), per m2", "m2", 2500, 0.1)
M("M-GS-GAB1", G, "Gabions", "Gabion box 2x1x1m, galvanised + PVC-coated mesh", "nr", 55000, 0.02)
M("M-GS-GAB05", G, "Gabions", "Gabion box 2x1x0.5m, galvanised + PVC-coated mesh", "nr", 38000, 0.02)
M("M-GS-RENO", G, "Gabions", "Reno mattress 0.3m thick, per m2", "m2", 10000, 0.03)
M("M-GS-COIR", G, "Erosion control", "Coir log 300mm dia, per m", "m", 8000, 0.03)

# ------------------------------------------------------------------ BRIDGES & HEAVY STRUCTURES
G = "Bridges & Heavy Structures"
U("M-BR-PTS", G, "Post-tensioning", "Prestressing strand 15.2mm (0.6\") 1860MPa low-relax, per tonne", "t", 1250, w=0.03)
U("M-BR-ANC12", G, "Post-tensioning", "Multi-strand anchorage set 12-strand (live/dead)", "set", 480, w=0)
M("M-BR-DUCT", G, "Post-tensioning", "Corrugated PT duct 90mm, per m", "m", 7500, 0.05)
U("M-BR-ELB", G, "Bearings & joints", "Laminated elastomeric bearing, per dm3", "dm3", 2.2, w=0)
U("M-BR-POT2", G, "Bearings & joints", "Pot bearing 2,000kN (guided/free)", "nr", 3800, w=0)
U("M-BR-POT5", G, "Bearings & joints", "Pot bearing 5,000kN (guided/free)", "nr", 7500, w=0)
U("M-BR-SSJ", G, "Bearings & joints", "Strip-seal expansion joint (80mm movement), per m", "m", 320, w=0.02)
U("M-BR-MEJ", G, "Bearings & joints", "Modular expansion joint (160mm movement), per m", "m", 1400, w=0.02)
M("M-BR-RAIL", G, "Bridge furniture", "Galvanised steel bridge parapet railing, per m", "m", 120000, 0.02)
M("M-BR-GIRD", G, "Precast", "Precast pre-tensioned bridge I-girder (25m class), delivered, per m", "m", 650000, 0)
M("M-BR-DWP", G, "Bridge furniture", "Bridge deck waterproofing membrane, per m2", "m2", 9500, 0.08)
M("M-BR-SCUP", G, "Bridge furniture", "Deck drainage scupper with downpipe", "nr", 85000, 0)
K("M-BR-ECR", G, "Reinforcement", "Epoxy-coated high-yield rebar, per tonne", "t", "M-STL-01", 1.28, 0.15, 0.05)
M("M-BR-ALFW", G, "Formwork systems", "Aluminium slab formwork system hire, per m2 per month", "m2", 4500, 0)
M("M-BR-SHOR", G, "Formwork systems", "Heavy-duty shoring tower hire, per tower per month", "nr", 35000, 0)

# ------------------------------------------------------------------ MARINE, PORTS & RECLAMATION
G = "Marine, Ports & Reclamation"
for c, d, v in [("AR13", "Armour rock 1-3t, delivered to site", 32000), ("AR36", "Armour rock 3-6t, delivered to site", 38000),
                ("CORE", "Core rock / quarry run 1-500kg, delivered", 22000), ("UL", "Underlayer/filter rock 50-300kg, delivered", 26000)]:
    M(f"M-MR-{c}", G, "Rock", f"{d}, per tonne", "t", v, 0.03)
M("M-MR-ROY", G, "Reclamation", "Dredged sand licence/royalty & environmental levy, per m3", "m3", 400, 0)
U("M-MR-FCONE", G, "Fenders & mooring", "Cone fender SCN1000 with frontal frame", "nr", 9000, w=0)
U("M-MR-FCYL", G, "Fenders & mooring", "Cylindrical rubber fender 1000mm OD, per m", "m", 450, w=0)
U("M-MR-FD300", G, "Fenders & mooring", "D-fender 300H, per m", "m", 220, w=0)
U("M-MR-BOL50", G, "Fenders & mooring", "Mooring bollard 50t, cast iron/steel", "nr", 2600, w=0)
U("M-MR-BOL100", G, "Fenders & mooring", "Mooring bollard 100t, cast steel", "nr", 4200, w=0)
U("M-MR-RAIL", G, "Quay furniture", "Crane rail A120, per m", "m", 230, w=0.02)
M("M-MR-LADR", G, "Quay furniture", "Galvanised quay ladder, per m", "m", 95000, 0)
U("M-MR-BUOY", G, "Navigation", "Navigation buoy 2.4m with solar lantern", "nr", 15000, w=0)
M("M-MR-CHAIN", G, "Navigation", "Stud-link mooring chain 38mm, per m", "m", 45000, 0.02)
U("M-MR-SILT", G, "Reclamation", "Floating silt curtain (turbidity barrier), per m", "m", 48, w=0.05)
U("M-MR-FPIPE", G, "Reclamation", "Floating HDPE dredge discharge pipeline 800mm with floats, per m", "m", 380, w=0)
U("M-MR-SPIPE", G, "Reclamation", "Steel dredge discharge pipe 800mm, per m", "m", 260, w=0)
M("M-MR-PAINT", G, "Coatings", "Marine epoxy/coal-tar paint, per litre", "L", 14000, 0.1)

# ------------------------------------------------------------------ ROADS (ADDITIONAL)
G = "Roads & Highways (Additional)"
K("M-RD-PMB", G, "Bitumen", "Polymer-modified bitumen (PMB), per tonne", "t", "M-RD-01", 1.25, 0.15, 0.02)
M("M-RD-ABC", G, "Asphalt", "Asphalt base course, ex-plant, per tonne", "t", 145000, 0.03)
M("M-RD-CHIP", G, "Aggregates", "Surface dressing chippings 10/14mm, per tonne", "t", 21000, 0.05)
M("M-RD-COLD", G, "Asphalt", "Cold-mix asphalt (pothole repair), 25kg bag", "bag", 9500, 0.03)
K("M-RD-DWL", G, "Concrete pavement", "Dowel bar 32mm, coated, per m", "m", "M-STL-09", 6.313 / 1000 * 1.15, 0.2, 0.05)
K("M-RD-TIE", G, "Concrete pavement", "Tie bar 16mm deformed, per m", "m", "M-STL-01", 1.578 / 1000, 0.2, 0.05)
M("M-RD-JSL", G, "Concrete pavement", "Hot-poured joint sealant, per kg", "kg", 4500, 0.08)
U("M-RD-TSIG", G, "Traffic", "Traffic signal set, 4-way junction with controller (solar-ready)", "set", 12000, w=0)
M("M-RD-SSL", G, "Street lighting", "Solar street light 60W all-in-one with 6m pole", "nr", 420000, 0)
U("M-RD-SHT", G, "Signs", "Retro-reflective sign sheeting (high intensity), per m2", "m2", 28, w=0.1)
M("M-RD-PLATE", G, "Signs", "Aluminium sign plate 2mm, per m2", "m2", 28000, 0.05)
M("M-RD-TERM", G, "Safety barriers", "Guardrail end terminal", "nr", 450000, 0)
M("M-RD-BAR", G, "Safety barriers", "Precast concrete safety barrier (New Jersey), per m", "m", 95000, 0.02)
M("M-RD-HC600", G, "Drainage", "HDPE twin-wall corrugated culvert pipe 600mm, per m", "m", 55000, 0.03)
M("M-RD-HC900", G, "Drainage", "HDPE twin-wall corrugated culvert pipe 900mm, per m", "m", 95000, 0.03)
M("M-RD-BC15", G, "Drainage", "Precast box culvert 1.5x1.5m, delivered, per m", "m", 420000, 0)
M("M-RD-BC2", G, "Drainage", "Precast box culvert 2.0x2.0m, delivered, per m", "m", 600000, 0)
M("M-RD-HUMP", G, "Traffic", "Rubber speed hump module, per m", "m", 35000, 0.02)
M("M-RD-PNT", G, "Road marking", "Road marking paint, 20L", "pail", 85000, 0.05)

# ------------------------------------------------------------------ RAILWAYS
G = "Railways"
U("M-RL-RST", G, "Rail", "Rail steel (UIC60/54E1 profile), per tonne", "t", 950, w=0.02)
K("M-RL-UIC60", G, "Rail", "Rail UIC60 (60.21 kg/m), per m", "m", "M-RL-RST", 60.21 / 1000, 0.2, 0.02)
K("M-RL-54E1", G, "Rail", "Rail 54E1 (54.77 kg/m), per m", "m", "M-RL-RST", 54.77 / 1000, 0.2, 0.02)
M("M-RL-SLP", G, "Sleepers", "Prestressed concrete sleeper, standard gauge", "nr", 120000, 0.01)
U("M-RL-SSLP", G, "Sleepers", "Steel sleeper", "nr", 90, w=0.01)
M("M-RL-BAL", G, "Ballast", "Track ballast 25-50mm crushed granite, delivered, per tonne", "t", 22000, 0.05)
M("M-RL-SUB", G, "Ballast", "Sub-ballast (graded crushed stone), per tonne", "t", 12000, 0.05)
U("M-RL-FAST", G, "Fastenings", "Elastic rail fastening set per sleeper (clips, pads, insulators)", "set", 28, w=0.02)
U("M-RL-TO12", G, "Turnouts", "Turnout 1:12 UIC60 complete set", "set", 130000, w=0)
U("M-RL-TKIT", G, "Welding", "Aluminothermic (thermite) rail weld kit", "nr", 190, w=0.03)
U("M-RL-FISH", G, "Fastenings", "Fishplate pair with bolts", "set", 60, w=0)
U("M-RL-BUF", G, "Track furniture", "Friction buffer stop", "nr", 9000, w=0)

# ------------------------------------------------------------------ POWER
G = "Power Transmission & Distribution"
M("M-PW-33C240", G, "HV cable", "33kV 1-core 240mm2 Cu XLPE/SWA cable, per m", "m", 53000, 0.03, "MEDIUM",
  "electrical.ng listing (2026): 240mm2 SWA 11-33kV single-core XLPE Cu N48,000-58,000", "2026-10-01")
M("M-PW-33C185AL", G, "HV cable", "33kV 3-core 185mm2 Al XLPE armoured cable, per m", "m", 42000, 0.03)
M("M-PW-11C95", G, "HV cable", "11kV 3-core 95mm2 Cu XLPE armoured cable, per m", "m", 58000, 0.03)
M("M-PW-11C185", G, "HV cable", "11kV 3-core 185mm2 Cu XLPE armoured cable, per m", "m", 105000, 0.03)
for s, v in [(120, 150000), (185, 225000), (240, 290000)]:
    M(f"M-PW-LV{s}", G, "LV cable", f"0.6/1kV 4-core {s}mm2 Cu XLPE/SWA cable, per m", "m", v, 0.03)
M("M-PW-ABC", G, "Overhead lines", "Aerial bundled cable 3x70+54.6mm2, per m", "m", 9500, 0.03)
M("M-PW-AAC100", G, "Overhead lines", "AAC conductor 100mm2, per m", "m", 1200, 0.03)
M("M-PW-ACSR150", G, "Overhead lines", "ACSR conductor 150/25mm2, per m", "m", 2300, 0.03)
M("M-PW-P12", G, "Poles & towers", "Prestressed concrete pole 12m", "nr", 320000, 0)
M("M-PW-P15", G, "Poles & towers", "Prestressed concrete pole 15m", "nr", 480000, 0)
U("M-PW-TWR", G, "Poles & towers", "Galvanised steel lattice transmission tower (132kV), per tonne", "t", 1900, w=0.02)
M("M-PW-PIN", G, "Line hardware", "33kV pin insulator with spindle", "nr", 18000, 0.02)
M("M-PW-DISC", G, "Line hardware", "33kV disc insulator string (3 discs) with fittings", "set", 45000, 0)
M("M-PW-XARM", G, "Line hardware", "Galvanised steel cross-arm 33kV", "nr", 65000, 0)
M("M-PW-STAY", G, "Line hardware", "Stay set complete (rod, wire, insulator)", "set", 75000, 0)
M("M-PW-LA33", G, "Switchgear", "Surge (lightning) arrester 11/33kV", "nr", 85000, 0)
M("M-PW-DOF", G, "Switchgear", "Drop-out fuse set 11/33kV (3 phases)", "set", 650000, 0)
U("M-PW-RMU", G, "Switchgear", "Ring main unit 11kV 3-way SF6", "nr", 18000, w=0)
U("M-PW-VCB33", G, "Switchgear", "33kV outdoor vacuum circuit breaker with CT/relay", "nr", 26000, w=0)
U("M-PW-T7M5", G, "Transformers", "Power transformer 7.5MVA 33/11kV", "nr", 190000, w=0)
M("M-PW-T100", G, "Transformers", "Distribution transformer 100kVA 11/0.415kV (supply)", "nr", 22000000, 0)
M("M-PW-T200", G, "Transformers", "Distribution transformer 200kVA 11/0.415kV (supply)", "nr", 32000000, 0)
M("M-PW-T1000", G, "Transformers", "Distribution transformer 1000kVA 11/0.415kV (supply)", "nr", 95000000, 0)
M("M-PW-FP800", G, "LV distribution", "Feeder pillar 800A, 6-way", "nr", 4500000, 0)
M("M-PW-PPM1", G, "Metering", "Prepaid energy meter, single-phase", "nr", 85000, 0)
M("M-PW-PPM3", G, "Metering", "Prepaid energy meter, three-phase", "nr", 160000, 0)
M("M-PW-33TRM", G, "Cable accessories", "33kV heat-shrink termination kit (3 phases)", "set", 450000, 0)
M("M-PW-11TRM", G, "Cable accessories", "11kV heat-shrink termination kit (3-core)", "set", 280000, 0)
M("M-PW-33JNT", G, "Cable accessories", "33kV straight-through joint kit", "set", 650000, 0)
M("M-PW-CUT", G, "Earthing", "Copper tape 25x3mm (earthing/lightning), per m", "m", 6500, 0.05)
for k, v in [(20, 9500000), (100, 32000000), (250, 65000000), (500, 120000000)]:
    M(f"M-PW-G{k}", G, "Generators", f"Diesel generator {k}kVA soundproof (supply)", "nr", v, 0)

# ------------------------------------------------------------------ WATER & SEWERAGE
G = "Water Supply & Sewerage"
M("M-WT-HDPEKG", G, "HDPE pipe", "HDPE PE100 pressure pipe, price per kg (basis for all sizes)", "kg", 4200, 0)
def hdpe(d, sdr):
    t = d / sdr; return math.pi * (d - t) * t * 0.96 / 1000
for d in [63, 90, 110, 160, 200, 250, 315, 400, 500, 630]:
    K(f"M-WT-H17-{d}", G, "HDPE pipe", f"HDPE PE100 SDR17 (PN10) pipe {d}mm ({hdpe(d,17):.2f} kg/m), per m", "m", "M-WT-HDPEKG", hdpe(d, 17), 0.2, 0.03)
for d in [32, 50, 63, 90, 110]:
    K(f"M-WT-H11-{d}", G, "HDPE pipe", f"HDPE PE100 SDR11 (PN16) pipe {d}mm ({hdpe(d,11):.2f} kg/m), per m", "m", "M-WT-HDPEKG", hdpe(d, 11), 0.2, 0.03)
for d, v in [(110, 12), (160, 22), (250, 60)]:
    U(f"M-WT-EF{d}", G, "HDPE fittings", f"Electrofusion coupler {d}mm", "nr", v, w=0)
U("M-WT-DIT", G, "Ductile iron", "Ductile iron pipe K9 cement-lined, per tonne", "t", 1050, w=0.02)
for dn, kg in [(100, 17), (150, 25.5), (200, 34.5), (300, 58), (400, 82), (600, 140)]:
    K(f"M-WT-DI{dn}", G, "Ductile iron", f"Ductile iron pipe DN{dn} K9 push-fit ({kg} kg/m), per m", "m", "M-WT-DIT", kg / 1000, 0.2, 0.02)
U("M-WT-GRP600", G, "GRP pipe", "GRP pipe DN600 PN10, per m", "m", 140, w=0.02)
U("M-WT-GRP1000", G, "GRP pipe", "GRP pipe DN1000 PN10, per m", "m", 330, w=0.02)
for d, v in [(200, 14000), (250, 21000), (300, 30000)]:
    M(f"M-WT-SW{d}", G, "Sewer pipe", f"uPVC structured-wall sewer pipe {d}mm, per m", "m", v, 0.03)
for dn, v in [(100, 260), (150, 380), (200, 600), (300, 1300)]:
    U(f"M-WT-GV{dn}", G, "Valves", f"Resilient-seat gate valve DN{dn} PN16 (DI)", "nr", v, w=0)
U("M-WT-BF300", G, "Valves", "Butterfly valve DN300 PN16", "nr", 650, w=0)
U("M-WT-BF600", G, "Valves", "Butterfly valve DN600 PN16 with gearbox", "nr", 2400, w=0)
U("M-WT-AV50", G, "Valves", "Double air release valve DN50", "nr", 240, w=0)
U("M-WT-HYD", G, "Fire & metering", "Pillar fire hydrant DN100", "nr", 650, w=0)
U("M-WT-BM100", G, "Fire & metering", "Bulk water meter DN100 (Woltman)", "nr", 900, w=0)
M("M-WT-DM15", G, "Fire & metering", "Domestic water meter 15mm", "nr", 45000, 0)
M("M-WT-ALUM", G, "Treatment", "Aluminium sulphate (alum), 50kg bag", "bag", 28000, 0.03)
M("M-WT-HTH", G, "Treatment", "Calcium hypochlorite (HTH) 70%, 45kg drum", "drum", 230000, 0.02)
M("M-WT-FSAND", G, "Treatment", "Graded filter sand, per tonne", "t", 35000, 0.05)
U("M-WT-GAC", G, "Treatment", "Granular activated carbon, per kg", "kg", 3, w=0.05)
U("M-WT-GRP", G, "Storage", "GRP sectional water tank, per m3 capacity", "m3", 180, w=0)
U("M-WT-STL", G, "Storage", "Galvanised steel panel tank, per m3 capacity", "m3", 220, w=0)
U("M-WT-STP", G, "Sewage treatment", "Package sewage treatment plant 50m3/day", "nr", 48000, w=0)
M("M-WT-D400", G, "Manholes", "Ductile iron manhole cover & frame D400 (heavy duty)", "nr", 280000, 0)
M("M-WT-MR1200", G, "Manholes", "Precast manhole ring 1200mm dia x 1m", "nr", 85000, 0.02)
M("M-WT-CONE", G, "Manholes", "Precast manhole cone/cover slab 1200mm", "nr", 95000, 0.02)
M("M-WT-SAK", G, "Manholes", "Precast soakaway ring 1500mm dia", "nr", 75000, 0.02)
M("M-WT-SP3", G, "Pumps", "Submersible borehole pump 3HP (supply)", "nr", 650000, 0)
M("M-WT-SP55", G, "Pumps", "Submersible borehole pump 5.5HP (supply)", "nr", 1100000, 0)
U("M-WT-ESP15", G, "Pumps", "End-suction centrifugal pump set 15kW", "nr", 2800, w=0)

# ------------------------------------------------------------------ FIRE PROTECTION
G = "Fire Protection"
M("M-FS-CP8", G, "Fire alarm", "Conventional fire alarm panel 8-zone", "nr", 650000, 0)
U("M-FS-AP2", G, "Fire alarm", "Addressable fire alarm panel 2-loop", "nr", 3500, w=0)
U("M-FS-SMK", G, "Fire alarm", "Addressable optical smoke detector with base", "nr", 45, w=0)
U("M-FS-HEAT", G, "Fire alarm", "Addressable heat detector with base", "nr", 40, w=0)
U("M-FS-MCP", G, "Fire alarm", "Addressable manual call point", "nr", 40, w=0)
U("M-FS-SND", G, "Fire alarm", "Addressable sounder-beacon", "nr", 45, w=0)
M("M-FS-CAB", G, "Fire alarm", "Fire-resistant cable 2-core 1.5mm2 (FP200-type), per m", "m", 1800, 0.05)
U("M-FS-SPK", G, "Sprinklers", "Sprinkler head pendent 68degC K5.6", "nr", 6, w=0.02)
M("M-FS-HRC", G, "Hydrants", "Fire hose reel 30m in cabinet, complete", "nr", 450000, 0)
U("M-FS-LV", G, "Hydrants", "Landing valve 2.5\" with blank cap", "nr", 180, w=0)
U("M-FS-PUMP", G, "Pumps", "Fire pump set 500gpm (electric + diesel + jockey) with controllers", "set", 38000, w=0)
M("M-FS-DCP9", G, "Extinguishers", "Dry powder extinguisher 9kg", "nr", 45000, 0)
M("M-FS-CO25", G, "Extinguishers", "CO2 extinguisher 5kg", "nr", 85000, 0)
M("M-FS-FOAM9", G, "Extinguishers", "AFFF foam extinguisher 9L", "nr", 55000, 0)
M("M-FS-BLKT", G, "Extinguishers", "Fire blanket 1.2x1.2m", "nr", 18000, 0)

# ------------------------------------------------------------------ HVAC, LIFTS & ICT
G = "HVAC, Lifts & ICT"
U("M-HV-VRFO", G, "HVAC", "VRF outdoor unit, per HP", "HP", 650, w=0)
U("M-HV-VRFI", G, "HVAC", "VRF indoor 4-way cassette 2HP", "nr", 950, w=0)
M("M-HV-R410", G, "HVAC", "Refrigerant R410A, per kg", "kg", 12000, 0.05)
M("M-HV-DUCT", G, "HVAC", "Galvanised sheet ductwork (fabricated), per m2 of duct surface", "m2", 22000, 0.08)
M("M-HV-DIFF", G, "HVAC", "Square ceiling diffuser 600x600 with plenum", "nr", 45000, 0)
U("M-HV-CHL", G, "HVAC", "Air-cooled chiller, per ton of refrigeration (TR)", "TR", 750, w=0)
M("M-HV-FS3", G, "HVAC", "Floor-standing split AC 3HP (supply)", "nr", 1650000, 0)
M("M-HV-CAS3", G, "HVAC", "Ceiling cassette split AC 3HP (supply)", "nr", 1850000, 0)
M("M-HV-EXF", G, "HVAC", "Inline duct exhaust fan 250mm", "nr", 180000, 0)
U("M-HV-LIFT", G, "Lifts", "Passenger lift 8-person (630kg) 5 stops, machine-room-less, supply & install", "nr", 46000, w=0)
U("M-HV-LSTOP", G, "Lifts", "Passenger lift: each additional stop", "nr", 3500, w=0)
U("M-HV-GLIFT", G, "Lifts", "Goods lift 1000kg 3 stops, supply & install", "nr", 52000, w=0)
U("M-HV-ESC", G, "Lifts", "Escalator 1000mm step, 4.5m rise, supply & install", "nr", 95000, w=0)
M("M-HV-C6O", G, "ICT", "Cat6 RJ45 outlet with faceplate", "nr", 6500, 0)
M("M-HV-PP24", G, "ICT", "Cat6 patch panel 24-port", "nr", 55000, 0)
M("M-HV-SW24", G, "ICT", "Managed PoE network switch 24-port", "nr", 650000, 0)
M("M-HV-IPC", G, "ICT", "IP CCTV camera 4MP (dome/bullet)", "nr", 75000, 0)
M("M-HV-NVR", G, "ICT", "Network video recorder 16-channel with 4TB", "nr", 280000, 0)
M("M-HV-ACC", G, "ICT", "Access control set (reader, maglock, exit button, controller) per door", "set", 350000, 0)
M("M-HV-VDP", G, "ICT", "Video door phone set", "set", 220000, 0)
M("M-HV-FIB12", G, "ICT", "Fibre optic cable 12-core single-mode, per m", "m", 1600, 0.05)
M("M-HV-RACK", G, "ICT", "Server/network rack 42U with PDU", "nr", 900000, 0)
M("M-HV-LAT", G, "Lightning protection", "Lightning air terminal with base", "nr", 35000, 0)
M("M-HV-TCL", G, "Lightning protection", "Test clamp (lightning down conductor)", "nr", 9500, 0)
M("M-HV-SWH", G, "Plumbing services", "Solar water heater 200L (evacuated tube)", "nr", 850000, 0)
M("M-HV-LPG", G, "Plumbing services", "LPG manifold system for commercial kitchen", "set", 650000, 0)

# ------------------------------------------------------------------ ARCHITECTURAL & INDUSTRIAL
G = "Architectural Finishes (Additional)"
U("M-AR-RAF", G, "Floors", "Raised access floor 600x600 with pedestals, per m2", "m2", 55, w=0.03)
M("M-AR-TERR", G, "Floors", "Terrazzo materials (marble chips, white cement, dividers), per m2", "m2", 14000, 0.05)
M("M-AR-GBLK", G, "Walls", "Glass block 190x190x80mm", "nr", 6500, 0.05)
U("M-AR-HPL", G, "Walls", "HPL exterior cladding panel 8mm, per m2", "m2", 65, w=0.08)
M("M-AR-ACP", G, "Walls", "Acoustic wall panel (fabric/wood slat), per m2", "m2", 28000, 0.05)
M("M-AR-WALLP", G, "Walls", "Vinyl wallpaper, 10m roll", "roll", 25000, 0.1)
M("M-AR-BLND", G, "Windows", "Roller blind, per m2", "m2", 22000, 0)
M("M-AR-CTRK", G, "Windows", "Curtain track, per m", "m", 9000, 0.03)
M("M-AR-CUB", G, "Sanitary", "HPL toilet cubicle partition with door & hardware", "nr", 650000, 0)
M("M-AR-VAN", G, "Sanitary", "Vanity unit with countertop basin", "nr", 380000, 0)
M("M-AR-PARQ", G, "Floors", "Hardwood parquet blocks, per m2", "m2", 25000, 0.08)
M("M-AR-ENGW", G, "Floors", "Engineered wood flooring, per m2", "m2", 42000, 0.08)
M("M-AR-RUB", G, "Floors", "Rubber gym flooring 15mm, per m2", "m2", 28000, 0.05)
M("M-AR-VNL", G, "Floors", "Homogeneous vinyl sheet (hospital grade), per m2", "m2", 19000, 0.08)
M("M-AR-BAFF", G, "Ceilings", "Metal baffle ceiling system, per m2", "m2", 35000, 0.05)
M("M-AR-LOUV", G, "Facades", "Aluminium louvre system, per m2", "m2", 75000, 0)
M("M-AR-SKY", G, "Roofs", "Aluminium-framed glass skylight, per m2", "m2", 160000, 0)
G = "Industrial Buildings"
M("M-IN-PUR", G, "Panels", "PU sandwich roof panel 50mm, per m2", "m2", 32000, 0.05)
M("M-IN-PUW", G, "Panels", "PU sandwich wall panel 50mm, per m2", "m2", 29000, 0.05)
M("M-IN-RWP", G, "Panels", "Rockwool fire-rated sandwich panel 100mm, per m2", "m2", 45000, 0.05)
M("M-IN-RSH", G, "Doors", "Galvanised rolling shutter (manual), per m2", "m2", 55000, 0)
M("M-IN-RSM", G, "Doors", "Rolling shutter motor & controls", "nr", 650000, 0)
U("M-IN-SECD", G, "Doors", "Insulated sectional overhead door 4x4m, motorised", "nr", 3800, w=0)
U("M-IN-DOCK", G, "Doors", "Hydraulic dock leveller", "nr", 5500, w=0)
U("M-IN-OHC", G, "Cranes", "Overhead travelling crane 10t, 20m span, single girder", "nr", 48000, w=0)
M("M-IN-FH", G, "Floors", "Dry-shake floor hardener, per kg", "kg", 1200, 0.05)
U("M-IN-CRP", G, "Panels", "Cold-room PU panel 100mm, per m2", "m2", 55, w=0.05)

# ------------------------------------------------------------------ TOOLS, SAFETY, TESTING
G = "Hand Tools & Small Equipment"
for c, d, v in [("SHOV", "Shovel (round mouth)", 6500), ("HPAN", "Head pan", 3500), ("WBAR", "Wheelbarrow heavy duty", 65000), ("PICK", "Pickaxe with handle", 9500),
                ("CUTL", "Cutlass/machete", 4500), ("PHD", "Post-hole digger", 15000), ("RAKE", "Rake", 7500), ("TROW", "Brick trowel", 3500),
                ("FLOAT", "Wooden float", 4000), ("SLVL", "Spirit level 1.2m", 18000), ("TP50", "Measuring tape 50m", 15000), ("TP5", "Measuring tape 5m", 3500),
                ("PLMB", "Plumb bob", 4500), ("MLINE", "Mason line 100m", 2000), ("CLAW", "Claw hammer", 6500), ("SLDG", "Sledge hammer 5kg", 18000),
                ("CROW", "Crowbar 1.5m", 15000), ("HSAW", "Hacksaw", 6500), ("WSAW", "Wood saw", 7500), ("RBND", "Manual rebar bender", 25000),
                ("BOLT", "Bolt cutter 36\"", 28000), ("CHIS", "Chisel set", 12000), ("SPAN", "Spanner set", 35000), ("PWR", "Pipe wrench 18\"", 18000),
                ("THRD", "Manual pipe threader set", 85000), ("PPRW", "PPR pipe welding machine", 45000), ("DRIL", "Electric drill", 55000), ("SDS", "Rotary hammer drill SDS", 120000),
                ("AG9", "Angle grinder 9\"", 85000), ("AG45", "Angle grinder 4.5\"", 38000), ("CSAW", "Circular saw", 95000), ("JSAW", "Jigsaw", 65000),
                ("TCM", "Manual tile cutter", 60000), ("TCW", "Wet tile saw", 180000), ("PVIB", "Poker vibrator (petrol), purchase", 380000), ("WELD", "Inverter welding machine 200A", 180000),
                ("OXY", "Oxy-acetylene cutting set with regulators", 120000), ("O2R", "Oxygen cylinder refill", 18000), ("C2R", "Acetylene cylinder refill", 45000), ("ARR", "Argon cylinder refill", 45000),
                ("GEN25", "Petrol generator 2.5kVA, purchase", 280000), ("EXT50", "Extension reel 50m", 35000), ("RLAS", "Rotary laser level with tripod", 650000), ("DUMPY", "Dumpy level with tripod & staff", 450000),
                ("PUMP2", "2\" water pump (petrol), purchase", 180000), ("LADR", "Aluminium ladder 6m", 150000), ("SCT", "Scaffold tube 6m, purchase", 38000), ("SCC", "Scaffold coupler", 2500),
                ("SCB", "Scaffold board 3.9m", 15000), ("MIXP", "Concrete mixer 1-bag, purchase", 1800000), ("PLTP", "Plate compactor, purchase", 950000)]:
    M(f"M-TL-{c}", G, "Tools", d, "nr", v, 0)
G = "Safety & PPE (Additional)"
for c, d, v in [("FAK", "First aid kit (site, 20-person)", 35000), ("BTAPE", "Barricade tape roll", 3500), ("CONE", "Traffic cone 750mm", 12000), ("SIGN", "Safety sign (aluminium)", 9000),
                ("TORCH", "Head torch", 6500), ("RAIN", "Rain coat", 8000), ("GLOV", "Work gloves, pair", 2500), ("GOGG", "Safety goggles", 3500), ("EARM", "Ear muffs", 9000),
                ("DUST", "Dust masks, box of 20", 6500), ("WHLM", "Welding helmet", 15000), ("LIFEJ", "Life jacket", 25000), ("FRC", "Fire-retardant coverall (oil & gas)", 35000)]:
    M(f"M-SF-{c}", G, "PPE", d, "nr", v, 0)
G = "Testing, Surveys & Investigations"
for c, d, u, v in [("CUBE", "Concrete cube crushing test, set of 3", "set", 15000), ("CORE", "Concrete core test (drill & crush)", "nr", 45000),
                   ("REB", "Rebar tensile & bend test, per sample", "nr", 25000), ("BLK", "Block compressive strength test, set of 3", "set", 18000),
                   ("BH", "Geotechnical borehole with SPT, per m", "m", 35000), ("CPT", "Cone penetration test (CPT), per m", "m", 18000),
                   ("CLS", "Soil classification tests, per sample", "nr", 45000), ("CBR", "CBR test, per sample", "nr", 30000), ("PRO", "Proctor compaction test", "nr", 25000),
                   ("FDT", "Field density test (sand replacement)", "nr", 15000), ("PIT", "Pile integrity test (low-strain), per pile", "nr", 30000),
                   ("PDA", "High-strain dynamic pile test (PDA), per pile", "nr", 650000), ("SPLT", "Static pile load test up to 300t", "nr", 8500000),
                   ("PLT", "Plate load test", "nr", 450000), ("ASP", "Asphalt core & extraction test", "nr", 40000), ("WQ", "Water quality analysis (full)", "nr", 85000),
                   ("RT", "Radiographic weld test, per joint (incl. film)", "nr", 35000), ("UT", "Ultrasonic weld test, per joint", "nr", 20000),
                   ("TOPO", "Topographic survey (service), per hectare", "ha", 120000), ("BATH", "Bathymetric survey (service), per km of line", "km", 450000)]:
    M(f"M-TS-{c}", G, "Tests & surveys", d, u, v, 0)

# ------------------------------------------------------------------ LABOUR
def LB(c, g, d, cat, lo, hi, day=None, mon=None, src="Judgement (Oct 2026); verify locally", conf="LOW"):
    new_lab.append(dict(c=c, g=g, d=d, cat=cat, lo=lo, hi=hi, day=day, mon=mon, src=src, ev=None, set=SET, conf=conf))
G = "Specialist Trades (Infrastructure, Oil & Gas, Marine)"
for c, d, cat, day in [("L-PWL", "Pipeline welder (6G coded)", "Craft", 45000), ("L-PFT", "Pipe fitter", "Craft", 30000), ("L-CTA", "Coating applicator", "Craft", 20000),
                       ("L-BLS", "Abrasive blaster / industrial painter", "Craft", 18000), ("L-NDT", "NDT technician (RT/UT Level II)", "Craft", 50000),
                       ("L-INS", "Insulation technician", "Craft", 18000), ("L-ITC", "Instrument technician", "Craft", 35000), ("L-DIV", "Commercial diver", "Craft", 150000),
                       ("L-DKH", "Deckhand / marine crew", "Craft", 15000), ("L-DRC", "Dredge crew member", "Craft", 25000), ("L-PIL", "Piling hand", "Craft", 12000),
                       ("L-GTC", "Geotechnical technician", "Craft", 25000), ("L-RTW", "Rail track worker", "Craft", 12000), ("L-RWD", "Rail welder (thermite)", "Craft", 35000),
                       ("L-LIN", "Lineman (overhead lines)", "Craft", 18000), ("L-CJT", "HV cable jointer", "Craft", 40000), ("L-HVE", "HV electrician", "Craft", 30000),
                       ("L-LFT", "Lift technician", "Craft", 35000), ("L-FPT", "Fire systems technician", "Craft", 25000), ("L-ICT", "Network / ICT technician", "Craft", 22000),
                       ("L-STM", "Stone mason", "Craft", 16000), ("L-DRY", "Drywall installer", "Craft", 14000), ("L-ESC", "Armed security escort (per day)", "Craft", 25000),
                       ("L-CK", "Camp cook", "Craft", 10000), ("L-FLG", "Flagman / traffic controller", "Craft", 8000)]:
    LB(c, G, d, cat, round(day * 0.8, -2), round(day * 1.25, -2), day)
G2 = "Plant Operators & Drivers"
for c, d, day in [("L-BCR", "Crane barge operator", 60000), ("L-TGC", "Tug master", 90000), ("L-SBO", "Sideboom (pipelayer) operator", 45000),
                  ("L-HDD", "HDD rig operator", 60000), ("L-PDR", "Piling rig operator", 45000), ("L-CPO", "Concrete pump operator", 30000), ("L-BPO", "Batching/asphalt plant operator", 30000)]:
    LB(c, G2, d, "Operator", round(day * 0.8, -2), round(day * 1.25, -2), day)
G3 = "Site Supervision & Professional Staff"
for c, d, mon in [("L-QCE", "QA/QC engineer", 550000), ("L-QCI", "QA/QC inspector", 350000), ("L-PLN", "Planner / scheduler", 600000), ("L-DCC", "Document controller", 250000),
                  ("L-PRC", "Procurement officer", 300000), ("L-MEE", "Mechanical engineer", 550000), ("L-ELN", "Electrical engineer", 550000), ("L-STE", "Structural engineer", 600000),
                  ("L-GEO", "Geotechnical engineer", 600000), ("L-ENV", "Environmental officer", 350000), ("L-CLO", "Community liaison officer", 300000),
                  ("L-PMO", "Pipeline / oil & gas project engineer", 900000), ("L-WIN", "Welding inspector (CSWIP 3.1)", 800000), ("L-MSV", "Marine superintendent", 900000),
                  ("L-CRM", "Camp manager", 300000)]:
    LB(c, G3, d, "Staff", None, None, None, mon)

# ------------------------------------------------------------------ PLANT
def PL(c, g, d, dry, fuel, lpd, op, out, u="day", src="Judgement (Oct 2026). Replace with Yellowmetal or supplier rate card", conf="LOW"):
    new_plant.append(dict(c=c, g=g, d=d, u=u, dry=dry, lo=rnd(dry * 0.8), hi=rnd(dry * 1.25), fuel=fuel, lpd=lpd, op=op, out=out, src=src, set=SET, conf=conf))
DSL, PET = "M-FUE-01", "M-FUE-02"
G = "Piling Plant"
PL("P-PDH", G, "Piling rig with diesel/hydraulic impact hammer (crawler)", 1200000, DSL, 160, "L-PDR", "60-90 m driven/day")
PL("P-VBH", G, "Vibratory hammer with crawler crane (sheet piles)", 1500000, DSL, 200, "L-PDR", "150-250 m2/day")
PL("P-CFA", G, "CFA piling rig", 2500000, DSL, 280, "L-PDR", "150-250 m/day")
PL("P-MPR", G, "Micropile / anchor drilling rig", 450000, DSL, 90, "L-PDR", "20-40 m/day")
PL("P-PRB", G, "PVD (wick drain) stitcher rig", 600000, DSL, 120, "L-PDR", "3,000-5,000 m/day")
G = "Heavy Lifting"
PL("P-CC100", G, "Crawler crane 100t", 2200000, DSL, 250, "L-CRO", "-")
PL("P-CC200", G, "Crawler crane 200t", 4000000, DSL, 350, "L-CRO", "-")
PL("P-PRM", G, "Prime mover with 60t trailer", 500000, DSL, 250, "L-DRV", "-")
G = "Marine & Dredging Fleet"
PL("P-CRB", G, "Crane barge 300t", 12000000, DSL, 1200, "L-BCR", "-")
PL("P-TUG", G, "Tug 1,200hp", 2500000, DSL, 1500, "L-TGC", "-")
PL("P-SPB", G, "Spud barge (hire)", 900000, None, 0, None, "-")
PL("P-FTB", G, "Flat-top barge 1,000t (hire)", 700000, None, 0, None, "-")
PL("P-TSHD", G, "Trailing suction hopper dredger 5,000m3", 45000000, DSL, 15000, "L-DRD", "25,000-40,000 m3/day placed")
PL("P-CSD20", G, "Cutter suction dredger 20\" with discharge line", 9000000, DSL, 2500, "L-DRD", "4,000-6,000 m3/day placed")
PL("P-ECS", G, "Hydrographic survey boat with echo sounder & GNSS", 350000, PET, 80, None, "10-15 km of line/day")
G = "Pipeline Spread"
PL("P-SB583", G, "Sideboom pipelayer (CAT 583 class)", 900000, DSL, 180, "L-SBO", "400-800 m laid/day")
PL("P-PBM", G, "Pipe bending machine 6-36\"", 800000, DSL, 60, "L-OPR", "-")
PL("P-WRG", G, "Diesel welding rig on truck (2 welders)", 150000, DSL, 50, None, "-")
PL("P-HDD", G, "Horizontal directional drilling rig 100t with mud system", 6000000, DSL, 600, "L-HDD", "30-60 m pullback/day")
PL("P-TRN", G, "Chain trencher", 1200000, DSL, 250, "L-OPR", "500-1,000 m/day")
PL("P-HTP", G, "Hydrotest pump unit with recorders", 150000, DSL, 40, None, "-")
PL("P-SBL", G, "Abrasive blasting unit with 750cfm compressor", 250000, DSL, 120, None, "60-80 m2/day")
PL("P-HOL", G, "Holiday (coating) detector", 25000, None, 0, None, "-")
PL("P-XRY", G, "Radiography crawler / X-ray unit (excl. technician)", 300000, None, 0, None, "30-50 joints/day")
G = "Roads & Quarry Plant"
PL("P-ADT", G, "Articulated dump truck 30t", 600000, DSL, 250, "L-DRV", "-")
PL("P-SCR", G, "Motor scraper 15m3", 1200000, DSL, 350, "L-OPD", "-")
PL("P-ASPL", G, "Asphalt mixing plant 120tph (excl. bitumen & aggregate)", 3000000, DSL, 1500, "L-BPO", "800-1,000 t/day")
PL("P-CRU", G, "Stone crushing plant 200tph", 2500000, DSL, 1200, "L-BPO", "1,500-2,000 t/day")
PL("P-SFP", G, "Slipform concrete paver", 3000000, DSL, 300, "L-OPR", "1,000-2,000 m2/day")
PL("P-SST", G, "Soil stabiliser / recycler", 2500000, DSL, 350, "L-OPR", "3,000-5,000 m2/day")
PL("P-DRL", G, "Crawler rock drill", 600000, DSL, 200, "L-OPR", "-")
PL("P-BTH", G, "Bitumen tanker with heater", 300000, DSL, 150, "L-DRV", "-")
PL("P-MBP", G, "Mobile batching plant 30m3/h", 600000, DSL, 150, "L-BPO", "150-200 m3/day")
G = "Rail Plant"
PL("P-TMP", G, "Ballast tamping machine", 3500000, DSL, 400, "L-OPR", "400-800 m/day")
PL("P-RWL", G, "Rail welding & grinding unit", 400000, DSL, 80, None, "8-15 welds/day")
G = "Access & Small Plant"
PL("P-WPT", G, "Wellpoint dewatering system (50 points)", 250000, DSL, 60, None, "-")
PL("P-LTW", G, "Lighting tower", 45000, DSL, 25, None, "-")
PL("P-GN500", G, "Generator 500kVA", 400000, DSL, 650, "L-GEN", "-")
PL("P-CMP750", G, "Air compressor 750cfm", 250000, DSL, 200, None, "-")
PL("P-BML", G, "Articulating boom lift 20m", 250000, DSL, 30, None, "-")
PL("P-SCL", G, "Scissor lift 12m (electric)", 120000, None, 0, None, "-")
PL("P-CDR", G, "Diamond core drill rig", 30000, PET, 4, None, "-")
PL("P-FGR", G, "Floor grinder / polisher", 40000, None, 0, None, "40-80 m2/day")
PL("P-VSC", G, "Vibrating screed (petrol)", 25000, PET, 5, None, "-")
PL("P-SHT", G, "Shotcrete machine", 300000, DSL, 80, None, "20-40 m3/day")
PL("P-GRP", G, "Grout mixer & pump", 120000, DSL, 30, None, "-")

# ------------------------------------------------------------------ COMPOSITE ITEMS
def IT(c, s, d, u, l, n=""):
    new_items.append(dict(c=c, s=s, d=d, u=u, n=n, l=[[t, r, round(q, 6)] for t, r, q in l]))
M_, L_, P_ = "M", "L", "P"
S = "O Oil & gas"
for nps, sb, wrg, pbm, hol, pwl, pft, lab, cta, e10, e18, area in [(8, 800, 350, 4000, 1200, .25, .18, .6, .06, .06, .18, .688), (12, 600, 250, 3000, 1000, .35, .25, .8, .08, .10, .30, 1.018),
                                                                   (24, 175, 120, 1500, 600, .8, .5, 1.5, .15, .25, .8, 1.916)]:
    IT(f"O0{ {8:1,12:2,24:3}[nps] }", S, f"Line pipe {nps}\" X52, 3LPE-coated: string, weld (100% RT), field-joint coat, lower-in and tie-in in prepared trench", "m",
       [(M_, f"M-OG-X52-{nps}", 1.0), (M_, "M-OG-3LPE", area), (M_, f"M-OG-HSS{nps}", 1 / 12), (M_, "M-OG-E6010", e10), (M_, "M-OG-E7018", e18), (M_, "M-TS-RT", 1 / 12),
        (L_, "L-PWL", pwl), (L_, "L-PFT", pft), (L_, "L-CTA", cta), (L_, "L-LAB", lab), (P_, "P-SB583", 1 / sb), (P_, "P-WRG", 1 / wrg), (P_, "P-PBM", 1 / pbm), (P_, "P-HOL", 1 / hol)],
       "Excl. trench (O04), backfill (O05), hydrotest (O06), crossings. 12m joints.")
IT("O04", S, "Pipeline trench excavation 1.0m wide x 1.5m deep by excavator, spoil alongside", "m", [(P_, "P-EXC20", 1 / 200), (L_, "L-LAB", 0.3)])
IT("O05", S, "Backfill pipeline trench with 300mm sand padding and excavated material, compacted", "m", [(M_, "M-AGG-12", 0.6), (P_, "P-EXC20", 1 / 400), (P_, "P-PLT", 1 / 200), (L_, "L-LAB", 0.5)])
IT("O06", S, "Hydrostatic test, dewatering and drying of 12\" pipeline", "m", [(M_, "M-FIN-10", 0.08), (P_, "P-HTP", 1 / 2000), (L_, "L-PFT", 0.02), (L_, "L-LAB", 0.05)])
IT("O07", S, "HDD river/road crossing for 12\" X52 3LPE pipeline incl. drilling fluid", "m", [(M_, "M-OG-X52-12", 1.0), (M_, "M-OG-3LPE", 1.02), (M_, "M-PG-BENT", 0.06), (M_, "M-TS-RT", 1 / 12),
     (P_, "P-HDD", 1 / 40), (P_, "P-EXC20", 1 / 200), (L_, "L-LAB", 3.0), (L_, "L-PWL", 0.35)], "Entry/exit pits and mobilisation excluded.")
IT("O08", S, "Magnesium anode 17lb installed with cable and test post share", "nr", [(M_, "M-OG-MGAN", 1), (M_, "M-OG-CPCAB", 8), (M_, "M-OG-CPTP", 0.25), (L_, "L-ELE", 2), (L_, "L-LAB", 3)])
IT("O09", S, "Install 12\" ANSI 150 gate valve with 2 weld-neck flanges, gaskets and bolting", "nr", [(M_, "M-OG-GV12", 1), (M_, "M-OG-WN150-12", 2), (M_, "M-OG-GSK12", 2), (M_, "M-OG-STUD12", 2),
     (M_, "M-OG-E7018", 2), (M_, "M-TS-RT", 2), (L_, "L-PWL", 6), (L_, "L-PFT", 6), (L_, "L-RIG", 3), (L_, "L-LAB", 6), (P_, "P-CRN", 0.25)])
IT("O10", S, "Pipeline marker post set in concrete", "nr", [(M_, "M-OG-MRK", 1), (M_, "M-CEM-01", 0.15), (L_, "L-LAB", 1.5)])
IT("O11", S, "Underground fuel tank 33,000L installed: excavation, sand surround, concrete anchor slab", "nr", [(M_, "M-OG-UGT", 1), (M_, "M-AGG-12", 25), (M_, "M-CEM-01", 20), (M_, "M-AGG-02", 2.2),
     (M_, "M-AGG-08", 4.2), (M_, "M-STL-01", 0.3), (P_, "P-EXC20", 0.4), (P_, "P-CRN", 0.5), (L_, "L-LAB", 40), (L_, "L-MAS", 8), (L_, "L-IRB", 8), (L_, "L-WEL", 8)])
IT("O12", S, "Fuel dispenser installed with 6m 2\" seamless product line and electrics", "nr", [(M_, "M-OG-DISP", 1), (M_, "M-OG-SMLS2", 6), (L_, "L-PFT", 8), (L_, "L-ELE", 6), (L_, "L-LAB", 4)])
IT("O13", S, "Fuel station canopy: steel frame, aluminium roof and ACP fascia", "m2", [(M_, "M-STL-08", 0.045), (M_, "M-RF-23", 0.35), (M_, "M-RF-02", 1.1), (M_, "M-STL-40", 0.6), (M_, "M-FIN-29", 0.03),
     (L_, "L-WEL", 1.5), (L_, "L-SER", 1.2), (L_, "L-ALU", 0.6), (L_, "L-LAB", 1.5), (P_, "P-CRN", 0.004), (P_, "P-WLG", 0.01)])
IT("O14", S, "Abrasive blast clean to Sa2.5 and apply 3-coat epoxy system to steelwork", "m2", [(M_, "M-OG-LEP", 0.6), (M_, "M-OG-GRIT", 0.03), (P_, "P-SBL", 1 / 60), (L_, "L-BLS", 0.6), (L_, "L-CTA", 0.3)])
IT("O15", S, "Radiographic testing of pipeline weld (service, incl. film)", "nr", [(M_, "M-TS-RT", 1), (L_, "L-LAB", 0.5)])
IT("O16", S, "Fabricate and erect steel storage tank shell/bottom/roof, per tonne of plate", "t", [(M_, "M-OG-PLT", 1.05), (M_, "M-OG-E7018", 25), (P_, "P-CRN", 0.3), (P_, "P-WLG", 2),
     (L_, "L-WEL", 30), (L_, "L-RIG", 12), (L_, "L-LAB", 30)], "Coating, NDT and foundation excluded.")
IT("O17", S, "Install 12\" pig launcher/receiver incl. tie-in welds", "nr", [(M_, "M-OG-PIGL", 1), (M_, "M-TS-RT", 6), (L_, "L-PFT", 24), (L_, "L-PWL", 16), (L_, "L-RIG", 8), (P_, "P-CRN", 1)])

S = "P Piling & ground engineering"
for c, d, conc, reb, bind, bent, pil, exc, lp, li, ll in [("P01", 600, 0.311, 0.035, 0.4, 0.015, 35, 150, 2.0, 1.2, 1.0), ("P02", 900, 0.70, 0.07, 0.8, 0.03, 22, 100, 3.0, 2.2, 1.5),
                                                          ("P03", 1200, 1.24, 0.11, 1.2, 0.05, 15, 70, 4.0, 3.2, 2.0)]:
    IT(c, S, f"Bored cast-in-place pile {d}mm dia in C30/37 concrete incl. rebar cage and drilling fluid", "m",
       [(M_, "M-CON-07", conc), (M_, "M-STL-01", reb), (M_, "M-STL-05", bind), (M_, "M-PG-BENT", bent), (P_, "P-PIL", 1 / pil), (P_, "P-CRN", 1 / pil), (P_, "P-EXC20", 1 / exc),
        (L_, "L-PIL", lp), (L_, "L-IRB", li), (L_, "L-LAB", ll)], "Rig mobilisation, testing and pile-head cut-off measured separately.")
IT("P04", S, "Precast concrete pile 400x400mm supplied and driven", "m", [(M_, "M-PG-PC400", 1.0), (P_, "P-PDH", 1 / 70), (L_, "L-PIL", 0.5), (L_, "L-LAB", 0.4)])
IT("P05", S, "Steel tubular pile 762x14mm supplied and driven incl. splices", "m", [(M_, "M-PG-TP762", 1.0), (M_, "M-OG-E7018", 0.4), (P_, "P-PDH", 1 / 50), (L_, "L-PIL", 0.7), (L_, "L-WEL", 0.3)])
IT("P06", S, "Steel sheet piling PU18, permanent, supplied and driven by vibro hammer", "m2", [(M_, "M-PG-PU18", 1.03), (P_, "P-VBH", 1 / 180), (L_, "L-PIL", 0.35), (L_, "L-WEL", 0.05)])
IT("P07", S, "Temporary sheet piling PU18 driven and extracted (30% material write-off/hire)", "m2", [(M_, "M-PG-PU18", 0.30), (P_, "P-VBH", 2 / 180), (L_, "L-PIL", 0.7)])
IT("P08", S, "Break down pile head 600mm and prepare starter bars", "nr", [(P_, "P-CMP", 1 / 16), (L_, "L-LAB", 3), (L_, "L-IRB", 0.5)])
IT("P09", S, "Pile integrity test (low-strain), per pile", "nr", [(M_, "M-TS-PIT", 1)])
IT("P10", S, "Prefabricated vertical drains installed to 15m", "m", [(M_, "M-PG-PVD", 1.08), (P_, "P-PRB", 1 / 3500), (L_, "L-LAB", 0.01)])
IT("P11", S, "Gabion box 2x1x1m filled with hand-packed stone", "nr", [(M_, "M-GS-GAB1", 1), (M_, "M-AGG-19", 1.75), (P_, "P-EX14", 1 / 40), (L_, "L-LAB", 5), (L_, "L-MAS", 1.5)])
IT("P12", S, "Reno mattress 0.3m filled with stone", "m2", [(M_, "M-GS-RENO", 1.02), (M_, "M-AGG-19", 0.5), (L_, "L-LAB", 1.5), (L_, "L-MAS", 0.4)])
IT("P13", S, "Biaxial geogrid laid in fill", "m2", [(M_, "M-GS-GGB", 1.1), (L_, "L-LAB", 0.04)])
IT("P14", S, "HDPE geomembrane 1.5mm laid and welded (lining)", "m2", [(M_, "M-GS-GM15", 1.12), (P_, "P-GN5", 1 / 800), (L_, "L-WPR", 0.06), (L_, "L-LAB", 0.06)])
IT("P15", S, "Soil nail 25mm x 6m, drilled and grouted, with head plate", "nr", [(M_, "M-PG-SN25", 6.3), (M_, "M-CEM-01", 1.2), (M_, "M-PG-NHP", 1), (P_, "P-MPR", 1 / 20), (P_, "P-GRP", 1 / 20),
     (L_, "L-PIL", 1.5), (L_, "L-LAB", 3)])
IT("P16", S, "Ground/rock anchor 32mm bar, drilled and grouted", "m", [(M_, "M-PG-AB32", 1.05), (M_, "M-CEM-01", 0.25), (P_, "P-MPR", 1 / 30), (P_, "P-GRP", 1 / 40), (L_, "L-PIL", 0.8)], "Stressing and head excluded.")
IT("P17", S, "Geosynthetic clay liner laid with overlaps", "m2", [(M_, "M-GS-GCL", 1.15), (L_, "L-LAB", 0.05)])
IT("P18", S, "Settlement plate installed and initial reading", "nr", [(M_, "M-PG-SPLT", 1), (L_, "L-GTC", 4), (L_, "L-LAB", 2)])
IT("P19", S, "Non-woven geotextile 400g/m2 laid as separator/filter", "m2", [(M_, "M-GS-NW400", 1.1), (L_, "L-LAB", 0.03)])

S = "Q Bridges & heavy structures"
IT("Q01", S, "Post-tensioning: 12x15.2mm tendons supplied, placed, stressed and grouted", "t", [(M_, "M-BR-PTS", 1.0), (M_, "M-BR-ANC12", 3.8), (M_, "M-BR-DUCT", 80), (M_, "M-CEM-18", 30),
     (P_, "P-GRP", 1), (P_, "P-GEN", 1), (L_, "L-IRB", 40), (L_, "L-SER", 16), (L_, "L-LAB", 40)], "Per tonne of strand.")
IT("Q02", S, "Laminated elastomeric bearing supplied and installed", "dm3", [(M_, "M-BR-ELB", 1.0), (L_, "L-MAS", 0.05), (L_, "L-LAB", 0.1)])
IT("Q03", S, "Pot bearing 2,000kN supplied, installed and grouted", "nr", [(M_, "M-BR-POT2", 1), (M_, "M-CEM-18", 2), (P_, "P-CRN", 0.15), (L_, "L-RIG", 4), (L_, "L-LAB", 4)])
IT("Q04", S, "Strip-seal expansion joint with C40 nosing and anchorage steel", "m", [(M_, "M-BR-SSJ", 1), (M_, "M-CON-09", 0.12), (M_, "M-STL-01", 0.015), (L_, "L-WEL", 1), (L_, "L-MAS", 1), (L_, "L-LAB", 2)])
IT("Q05", S, "Galvanised steel bridge parapet railing installed", "m", [(M_, "M-BR-RAIL", 1), (M_, "M-STL-41", 4), (L_, "L-WEL", 0.8), (L_, "L-LAB", 1)])
IT("Q06", S, "Precast pre-tensioned I-girder (25m class) supplied and erected", "m", [(M_, "M-BR-GIRD", 1), (P_, "P-CR80", 1 / 50), (L_, "L-RIG", 0.3), (L_, "L-LAB", 0.4)])
IT("Q07", S, "Bridge deck waterproofing membrane on primed deck", "m2", [(M_, "M-BR-DWP", 1.08), (M_, "M-WP-03", 0.25), (L_, "L-WPR", 0.15)])
IT("Q08", S, "C40/50 ready-mix concrete in bridge deck placed by boom pump", "m3", [(M_, "M-CON-09", 1.0), (P_, "P-CPB", 1 / 180), (P_, "P-VIB", 1 / 40), (L_, "L-MAS", 0.8), (L_, "L-LAB", 3), (L_, "L-CFN", 0.4)],
   "Excl. rebar and formwork.")
IT("Q09", S, "Aluminium system formwork to slab soffit (1 month hire per use)", "m2", [(M_, "M-BR-ALFW", 1.0), (M_, "M-CON-10", 0.05), (L_, "L-CAR", 0.6), (L_, "L-LAB", 0.5)])
IT("Q10", S, "Epoxy-coated reinforcement cut, bent and fixed", "t", [(M_, "M-BR-ECR", 1), (M_, "M-STL-05", 12), (L_, "L-IRB", 28), (L_, "L-LAB", 20)])
IT("Q11", S, "Deck drainage scupper installed", "nr", [(M_, "M-BR-SCUP", 1), (L_, "L-MAS", 2), (L_, "L-LAB", 2)])
IT("Q12", S, "Heavy-duty shoring tower, per tower per month incl. erect and dismantle", "nr", [(M_, "M-BR-SHOR", 1), (L_, "L-SCF", 4), (L_, "L-LAB", 4)])
IT("Q13", S, "Modular expansion joint installed with nosing concrete and anchorage", "m", [(M_, "M-BR-MEJ", 1), (M_, "M-CON-09", 0.25), (M_, "M-STL-01", 0.03), (P_, "P-CRN", 0.05),
     (L_, "L-WEL", 3), (L_, "L-MAS", 2), (L_, "L-LAB", 4)])

S = "K Marine & dredging"
IT("K02", S, "Hydraulic sand fill by 20\" cutter suction dredger incl. discharge line, placed (in-situ m3)", "m3", [(M_, "M-MR-ROY", 1.0), (M_, "M-MR-FPIPE", 0.0005), (P_, "P-CSD20", 1 / 4500),
     (P_, "P-BOT", 1 / 4500), (P_, "P-DZ7", 1 / 6000), (L_, "L-LAB", 0.01)], "Mobilisation and booster stations excluded. Replace with FESTAC actuals.")
IT("K03", S, "Hydraulic sand fill by trailing suction hopper dredger (rainbowing/pump-ashore), placed", "m3", [(M_, "M-MR-ROY", 1.0), (P_, "P-TSHD", 1 / 30000), (L_, "L-LAB", 0.002)],
   "Large reclamations only; mobilisation of the dredger is a major separate cost.")
IT("K04", S, "Spread and compact reclaimed sand in layers", "m3", [(P_, "P-DZ7", 1 / 1500), (P_, "P-RL18", 1 / 1800), (P_, "P-WTK", 1 / 4000), (L_, "L-LAB", 0.01)])
IT("K05", S, "Armour rock 3-6t placed to revetment/breakwater profile", "t", [(M_, "M-MR-AR36", 1.0), (P_, "P-EX30", 1 / 300), (P_, "P-CR80", 1 / 600), (L_, "L-RIG", 0.05), (L_, "L-LAB", 0.05)])
IT("K06", S, "Core rock 1-500kg placed and trimmed", "t", [(M_, "M-MR-CORE", 1.0), (P_, "P-EX30", 1 / 600), (P_, "P-DZ7", 1 / 1500), (L_, "L-LAB", 0.03)])
IT("K07", S, "Underlayer rock 50-300kg placed", "t", [(M_, "M-MR-UL", 1.0), (P_, "P-EX30", 1 / 450), (L_, "L-LAB", 0.04)])
IT("K08", S, "Geotextile under revetment laid incl. underwater placement", "m2", [(M_, "M-GS-NW400", 1.15), (P_, "P-BOT", 1 / 800), (L_, "L-DIV", 0.01), (L_, "L-LAB", 0.05)])
IT("K09", S, "Concrete armour unit (2m3 class) cast in C35/45 and placed", "m3", [(M_, "M-CON-08", 1.02), (M_, "M-TMB-06", 0.2), (P_, "P-VIB", 1 / 30), (P_, "P-CR80", 1 / 40),
     (L_, "L-CAR", 1.2), (L_, "L-MAS", 0.8), (L_, "L-LAB", 3)])
IT("K10", S, "Cone fender SCN1000 with frontal frame supplied and installed", "nr", [(M_, "M-MR-FCONE", 1), (M_, "M-STL-42", 6), (P_, "P-CRN", 0.3), (L_, "L-RIG", 6), (L_, "L-LAB", 6)])
IT("K11", S, "Mooring bollard 100t supplied and installed", "nr", [(M_, "M-MR-BOL100", 1), (M_, "M-STL-42", 4), (M_, "M-CEM-18", 2), (P_, "P-CRN", 0.15), (L_, "L-RIG", 3), (L_, "L-LAB", 4)])
IT("K12", S, "Crane rail A120 on grouted pads with clips", "m", [(M_, "M-MR-RAIL", 1.02), (M_, "M-CEM-18", 0.4), (M_, "M-STL-40", 3), (P_, "P-CRN", 0.01), (L_, "L-WEL", 0.6), (L_, "L-RIG", 0.4), (L_, "L-LAB", 0.8)])
IT("K13", S, "Floating silt curtain deployed and maintained", "m", [(M_, "M-MR-SILT", 1.05), (P_, "P-BOT", 1 / 200), (L_, "L-DKH", 0.5)])
IT("K14", S, "Marine steel tubular pile 762mm driven from crane barge", "m", [(M_, "M-PG-TP762", 1.0), (M_, "M-OG-E7018", 0.4), (P_, "P-CRB", 1 / 40), (P_, "P-TUG", 1 / 40), (P_, "P-PDH", 1 / 40),
     (L_, "L-PIL", 1), (L_, "L-WEL", 0.4), (L_, "L-DKH", 0.5)])
IT("K15", S, "Bathymetric survey with survey boat", "km", [(P_, "P-ECS", 1 / 12), (L_, "L-SVY", 0.7), (L_, "L-CHN", 0.7)])
IT("K16", S, "Navigation buoy supplied and moored with 20m chain and sinker", "nr", [(M_, "M-MR-BUOY", 1), (M_, "M-MR-CHAIN", 20), (P_, "P-TUG", 0.5), (L_, "L-DKH", 8), (L_, "L-DIV", 4)])

S = "R Roads & external"
IT("R17", S, "Cement-stabilised base 150mm (5% cement) mixed in place and compacted", "m2", [(M_, "M-CEM-01", 0.30), (M_, "M-AGG-06", 0.33), (P_, "P-SST", 1 / 3500), (P_, "P-GRD", 1 / 3500),
     (P_, "P-RL18", 1 / 3000), (P_, "P-WTK", 1 / 4000), (L_, "L-LAB", 0.03)])
IT("R18", S, "Double surface dressing with emulsion and 10/14mm chippings", "m2", [(M_, "M-RD-05", 2.6), (M_, "M-RD-CHIP", 0.028), (P_, "P-BDS", 1 / 6000), (P_, "P-CHS", 1 / 6000),
     (P_, "P-RLP", 1 / 6000), (P_, "P-BRM", 1 / 8000), (L_, "L-LAB", 0.02)])
IT("R19", S, "Jointed concrete pavement C35/45 250mm with dowels, tie bars and sealed joints", "m2", [(M_, "M-CON-08", 0.255), (M_, "M-RD-DWL", 0.35), (M_, "M-RD-TIE", 0.25), (M_, "M-RD-JSL", 0.25),
     (P_, "P-SFP", 1 / 1500), (P_, "P-TMX", 0.0057), (P_, "P-CCT", 1 / 400), (L_, "L-CFN", 0.08), (L_, "L-LAB", 0.25)])
IT("R20", S, "Asphalt base course 60mm laid and compacted", "m2", [(M_, "M-RD-ABC", 0.141), (P_, "P-PAV", 1 / 2800), (P_, "P-RLT", 1 / 2800), (P_, "P-RLP", 1 / 2800), (P_, "P-TIP", 1 / 1300), (L_, "L-ASP", 0.03)])
IT("R21", S, "HDPE twin-wall culvert 600mm laid on and surrounded with sand", "m", [(M_, "M-RD-HC600", 1.0), (M_, "M-AGG-12", 0.8), (P_, "P-EX14", 1 / 60), (L_, "L-PIP", 0.4), (L_, "L-LAB", 1.5)])
IT("R22", S, "Precast box culvert 2x2m laid on blinding", "m", [(M_, "M-RD-BC2", 1.0), (M_, "M-CON-06", 0.25), (P_, "P-CR50", 1 / 12), (P_, "P-EXC20", 1 / 20), (L_, "L-RIG", 1), (L_, "L-MAS", 1), (L_, "L-LAB", 3)])
IT("R23", S, "Precast concrete safety barrier installed", "m", [(M_, "M-RD-BAR", 1.0), (P_, "P-HIAB", 1 / 60), (L_, "L-LAB", 0.4)])
IT("R24", S, "Solar street light 60W on 6m pole with concrete base", "nr", [(M_, "M-RD-SSL", 1), (M_, "M-CEM-01", 1.0), (M_, "M-AGG-02", 0.12), (M_, "M-AGG-08", 0.22), (P_, "P-HIAB", 0.05),
     (L_, "L-ELE", 3), (L_, "L-LAB", 4)])
IT("R25", S, "Traffic signal installation, 4-way junction", "set", [(M_, "M-RD-TSIG", 1), (M_, "M-CEM-01", 4), (M_, "M-AGG-02", 0.5), (M_, "M-AGG-08", 0.9), (M_, "M-EL-13", 40), (P_, "P-HIAB", 0.5),
     (L_, "L-ELE", 24), (L_, "L-LAB", 24)])
IT("R26", S, "Retro-reflective road sign on galvanised post with concrete base", "m2", [(M_, "M-RD-SHT", 1.1), (M_, "M-RD-PLATE", 1.05), (M_, "M-STL-28", 0.5), (M_, "M-CEM-01", 0.6), (L_, "L-WEL", 0.5), (L_, "L-LAB", 3)])
IT("R27", S, "Cold mill existing asphalt 50mm and remove", "m2", [(P_, "P-MIL", 1 / 3500), (P_, "P-TIP", 1 / 400), (P_, "P-BRM", 1 / 8000), (L_, "L-LAB", 0.01)])
IT("R28", S, "Rubber speed hump installed", "m", [(M_, "M-RD-HUMP", 1), (M_, "M-STL-41", 4), (L_, "L-LAB", 0.5)])
IT("R29", S, "Road marking with paint, 100mm line", "m", [(M_, "M-RD-PNT", 0.002), (P_, "P-LMK", 1 / 3000), (L_, "L-LAB", 0.02)])
IT("R30", S, "Gabion retaining wall (2x1x1 boxes) incl. geotextile backing", "m3", [(M_, "M-GS-GAB1", 0.5), (M_, "M-AGG-19", 1.75), (M_, "M-GS-NW400", 1.2), (P_, "P-EX14", 1 / 40), (L_, "L-LAB", 5), (L_, "L-MAS", 1.5)])

S = "L Railways"
IT("L01", S, "Standard-gauge track UIC60 on concrete sleepers (600mm c/c) incl. ballast, sub-ballast, fastenings and welds", "m",
   [(M_, "M-RL-UIC60", 2.0), (M_, "M-RL-SLP", 1.67), (M_, "M-RL-FAST", 1.67), (M_, "M-RL-BAL", 2.0), (M_, "M-RL-SUB", 1.2), (M_, "M-RL-TKIT", 0.04),
    (P_, "P-TMP", 1 / 500), (P_, "P-EX14", 1 / 250), (P_, "P-RWL", 1 / 600), (P_, "P-TIP", 1 / 150), (P_, "P-RL18", 1 / 800), (L_, "L-RTW", 3.5), (L_, "L-RWD", 0.08)], "Per metre of single track. Formation excluded.")
IT("L02", S, "Aluminothermic rail weld", "nr", [(M_, "M-RL-TKIT", 1), (P_, "P-RWL", 1 / 12), (L_, "L-RWD", 1.5), (L_, "L-RTW", 1.5)])
IT("L03", S, "Turnout 1:12 UIC60 installed incl. ballast and tamping", "nr", [(M_, "M-RL-TO12", 1), (M_, "M-RL-BAL", 70), (P_, "P-CRN", 2), (P_, "P-TMP", 1), (L_, "L-RTW", 120), (L_, "L-RWD", 8)])
IT("L04", S, "Ballast top-up and tamping", "m", [(M_, "M-RL-BAL", 0.4), (P_, "P-TMP", 1 / 800), (L_, "L-RTW", 0.3)])
IT("L05", S, "Friction buffer stop installed", "nr", [(M_, "M-RL-BUF", 1), (P_, "P-CRN", 0.5), (L_, "L-RTW", 16)])

S = "N Power distribution"
IT("N01", S, "33kV 1-core 240mm2 Cu XLPE cable laid in trench (per cable), with sand and warning tape", "m", [(M_, "M-PW-33C240", 1.03), (M_, "M-AGG-12", 0.1), (M_, "M-OG-WTAPE", 0.33),
     (L_, "L-HVE", 0.12), (L_, "L-LAB", 0.6)], "Trench excluded.")
IT("N02", S, "11kV 3-core 185mm2 Cu armoured cable laid in trench", "m", [(M_, "M-PW-11C185", 1.03), (M_, "M-AGG-12", 0.15), (M_, "M-OG-WTAPE", 1), (L_, "L-HVE", 0.15), (L_, "L-LAB", 0.8)])
IT("N03", S, "33kV cable termination (3 phases) installed and tested", "set", [(M_, "M-PW-33TRM", 1), (L_, "L-CJT", 8), (L_, "L-HVE", 4)])
IT("N04", S, "33kV cable straight-through joint", "nr", [(M_, "M-PW-33JNT", 1), (L_, "L-CJT", 10), (L_, "L-LAB", 6)])
IT("N05", S, "33kV overhead line, ACSR 150 on 15m concrete poles at 60m spans", "m", [(M_, "M-PW-ACSR150", 3.06), (M_, "M-PW-P15", 1 / 60), (M_, "M-PW-PIN", 3 / 60), (M_, "M-PW-DISC", 0.006),
     (M_, "M-PW-XARM", 1 / 60), (M_, "M-PW-STAY", 0.4 / 60), (M_, "M-CEM-01", 2 / 60), (P_, "P-HIAB", 1 / 300), (P_, "P-EX14", 1 / 1200), (L_, "L-LIN", 1.2), (L_, "L-LAB", 1.5)], "Per metre of route.")
IT("N06", S, "11kV ring main unit installed on concrete plinth with 3 terminations", "nr", [(M_, "M-PW-RMU", 1), (M_, "M-PW-11TRM", 3), (M_, "M-CEM-01", 6), (M_, "M-AGG-02", 0.7), (M_, "M-AGG-08", 1.3),
     (M_, "M-STL-01", 0.08), (P_, "P-HIAB", 0.5), (L_, "L-HVE", 16), (L_, "L-CJT", 8), (L_, "L-LAB", 16)])
IT("N07", S, "500kVA 11/0.415kV transformer installed on plinth with HV termination and 20m LV cable", "nr", [(M_, "M-EL-59", 1), (M_, "M-PW-11TRM", 1), (M_, "M-PW-LV240", 20), (M_, "M-CEM-01", 8),
     (M_, "M-AGG-02", 0.9), (M_, "M-AGG-08", 1.7), (M_, "M-STL-01", 0.1), (P_, "P-CRN", 0.5), (L_, "L-HVE", 24), (L_, "L-LAB", 24)])
IT("N08", S, "100kVA pole-mounted transformer on H-pole with fuses and arrester", "nr", [(M_, "M-PW-T100", 1), (M_, "M-PW-P12", 2), (M_, "M-PW-DOF", 1), (M_, "M-PW-LA33", 1), (P_, "P-HIAB", 1),
     (L_, "L-LIN", 16), (L_, "L-HVE", 8)])
IT("N09", S, "Feeder pillar 800A installed on base", "nr", [(M_, "M-PW-FP800", 1), (M_, "M-CEM-01", 2), (L_, "L-ELE", 8), (L_, "L-LAB", 8)])
IT("N10", S, "Prepaid meter single-phase installed with service cable", "nr", [(M_, "M-PW-PPM1", 1), (M_, "M-EL-04", 0.1), (L_, "L-ELE", 2)])
IT("N11", S, "132kV lattice tower steel erected", "t", [(M_, "M-PW-TWR", 1), (P_, "P-CRN", 0.4), (L_, "L-SER", 24), (L_, "L-RIG", 12), (L_, "L-LAB", 24)], "Foundations and stringing excluded.")
IT("N12", S, "100kVA diesel generator installed with ATS, plinth and 15m LV cable", "nr", [(M_, "M-PW-G100", 1), (M_, "M-EL-33", 1), (M_, "M-PW-LV120", 15), (M_, "M-CEM-01", 6), (M_, "M-AGG-02", 0.7),
     (M_, "M-AGG-08", 1.3), (P_, "P-CRN", 0.5), (L_, "L-ELE", 24), (L_, "L-LAB", 16)])
IT("N13", S, "Lightning protection system for a typical 2-storey building (6 air terminals)", "nr", [(M_, "M-HV-LAT", 6), (M_, "M-PW-CUT", 60), (M_, "M-EL-34", 4), (M_, "M-HV-TCL", 4), (L_, "L-ELE", 24), (L_, "L-LAB", 16)])
IT("N14", S, "LV aerial bundled cable 3x70+54.6 on 9m concrete poles at 40m spans", "m", [(M_, "M-PW-ABC", 1.03), (M_, "M-EL-57", 1 / 40), (M_, "M-PW-STAY", 0.3 / 40), (P_, "P-HIAB", 1 / 400),
     (L_, "L-LIN", 0.5), (L_, "L-LAB", 0.8)])

S = "V Water & sewerage"
for c, d, ph, pl, ll, gen, exc, sand in [("V01", 110, 0, .12, .3, 400, 0, .15), ("V02", 160, 0, .16, .4, 300, 0, .2), ("V03", 250, 0, .25, .6, 200, 400, .3), ("V04", 400, 0, .4, .9, 150, 250, .45)]:
    l = [(M_, f"M-WT-H17-{d}", 1.02), (M_, "M-AGG-12", sand), (P_, "P-GEN", 1 / gen), (L_, "L-PLU", pl), (L_, "L-LAB", ll)]
    if exc: l.append((P_, "P-EX14", 1 / exc))
    IT(c, S, f"HDPE PE100 SDR17 pipe {d}mm laid and butt-fused in trench on sand bed", "m", l, "Trench excavation excluded.")
IT("V05", S, "Ductile iron pipe DN150 laid in trench on sand bed", "m", [(M_, "M-WT-DI150", 1.02), (M_, "M-AGG-12", 0.25), (P_, "P-EX14", 1 / 300), (L_, "L-PLU", 0.2), (L_, "L-LAB", 0.6)])
IT("V06", S, "Ductile iron pipe DN300 laid in trench on sand bed", "m", [(M_, "M-WT-DI300", 1.02), (M_, "M-AGG-12", 0.4), (P_, "P-EX14", 1 / 180), (L_, "L-PLU", 0.35), (L_, "L-LAB", 1.0)])
IT("V07", S, "uPVC sewer pipe 200mm laid on granular bed", "m", [(M_, "M-WT-SW200", 1.02), (M_, "M-AGG-12", 0.3), (L_, "L-PIP", 0.25), (L_, "L-LAB", 0.5)])
IT("V08", S, "DI gate valve DN150 installed in block chamber with cover", "nr", [(M_, "M-WT-GV150", 1), (M_, "M-BLK-02", 30), (M_, "M-CEM-01", 2), (M_, "M-AGG-02", 0.25), (M_, "M-PL-40", 1),
     (L_, "L-PLU", 4), (L_, "L-MAS", 4), (L_, "L-LAB", 8)])
IT("V09", S, "Pillar fire hydrant with isolating valve installed", "nr", [(M_, "M-WT-HYD", 1), (M_, "M-WT-GV100", 1), (M_, "M-CEM-01", 1), (L_, "L-PLU", 6), (L_, "L-LAB", 6)])
IT("V10", S, "Bulk water meter DN100 with 2 valves in chamber", "nr", [(M_, "M-WT-BM100", 1), (M_, "M-WT-GV100", 2), (M_, "M-BLK-02", 40), (M_, "M-CEM-01", 3), (M_, "M-PL-40", 1),
     (L_, "L-PLU", 8), (L_, "L-MAS", 5), (L_, "L-LAB", 10)])
IT("V11", S, "Domestic water connection 15mm with meter and stopcock", "nr", [(M_, "M-WT-DM15", 1), (M_, "M-PL-11", 3), (M_, "M-PL-19", 1), (L_, "L-PLU", 3), (L_, "L-LAB", 3)])
IT("V12", S, "Precast manhole 1200mm dia, 2m deep, with D400 cover", "nr", [(M_, "M-WT-MR1200", 2), (M_, "M-WT-CONE", 1), (M_, "M-WT-D400", 1), (M_, "M-CEM-01", 3), (M_, "M-AGG-02", 0.4),
     (M_, "M-AGG-08", 0.6), (P_, "P-HIAB", 0.25), (P_, "P-EX14", 0.2), (L_, "L-MAS", 6), (L_, "L-LAB", 12)])
IT("V13", S, "Two-chamber septic tank (10m3) in solid blockwork with RC cover, and soakaway", "nr", [(M_, "M-BLK-03", 320), (M_, "M-CEM-01", 45), (M_, "M-AGG-02", 4), (M_, "M-AGG-08", 5),
     (M_, "M-STL-01", 0.35), (M_, "M-WT-SAK", 4), (M_, "M-TMB-05", 15), (P_, "P-EX14", 0.5), (L_, "L-MAS", 40), (L_, "L-IRB", 12), (L_, "L-CAR", 12), (L_, "L-LAB", 80)])
IT("V14", S, "GRP sectional water tank on steel base frame, installed", "m3", [(M_, "M-WT-GRP", 1.0), (M_, "M-STL-08", 0.025), (L_, "L-WEL", 0.8), (L_, "L-PLU", 1.5), (L_, "L-LAB", 1.5)])
IT("V15", S, "Package sewage treatment plant 50m3/day installed on concrete base", "nr", [(M_, "M-WT-STP", 1), (M_, "M-CON-04", 8), (M_, "M-STL-01", 0.6), (P_, "P-CRN", 1), (L_, "L-PLU", 40),
     (L_, "L-ELE", 24), (L_, "L-LAB", 60)])
IT("V16", S, "Submersible pump 5.5HP installed in borehole with riser and cable", "nr", [(M_, "M-WT-SP55", 1), (M_, "M-PL-13", 20), (M_, "M-EL-03", 0.8), (L_, "L-PLU", 8), (L_, "L-ELE", 6), (L_, "L-LAB", 8)])
IT("V17", S, "Rapid gravity filter media (graded sand) placed", "m3", [(M_, "M-WT-FSAND", 1.6), (L_, "L-LAB", 2)])
IT("V18", S, "Butterfly valve DN300 installed", "nr", [(M_, "M-WT-BF300", 1), (P_, "P-HIAB", 0.2), (L_, "L-PLU", 6), (L_, "L-LAB", 6)])

S = "X Fire, HVAC, lifts & ICT"
IT("X01", S, "Addressable smoke detection point with 15m FP cable in conduit", "pt", [(M_, "M-FS-SMK", 1), (M_, "M-FS-CAB", 15), (M_, "M-EL-05", 4), (L_, "L-FPT", 1.5), (L_, "L-ELH", 0.5)])
IT("X02", S, "Addressable fire alarm panel 2-loop installed and commissioned", "nr", [(M_, "M-FS-AP2", 1), (L_, "L-FPT", 16)])
IT("X03", S, "Manual call point with 15m FP cable in conduit", "nr", [(M_, "M-FS-MCP", 1), (M_, "M-FS-CAB", 15), (M_, "M-EL-05", 4), (L_, "L-FPT", 1.2)])
IT("X04", S, "Sounder-beacon with 15m FP cable in conduit", "nr", [(M_, "M-FS-SND", 1), (M_, "M-FS-CAB", 15), (M_, "M-EL-05", 4), (L_, "L-FPT", 1.2)])
IT("X05", S, "Sprinkler head with 3m 1\" galvanised branch pipe and hangers", "nr", [(M_, "M-FS-SPK", 1), (M_, "M-STL-29", 0.5), (M_, "M-STL-41", 2), (L_, "L-PLU", 1.5), (L_, "L-PLH", 1.0)])
IT("X06", S, "Fire hose reel cabinet installed with 12m 1\" supply", "nr", [(M_, "M-FS-HRC", 1), (M_, "M-STL-29", 2), (L_, "L-PLU", 4), (L_, "L-LAB", 2)])
IT("X07", S, "Dry powder extinguisher 9kg wall-mounted with sign", "nr", [(M_, "M-FS-DCP9", 1), (M_, "M-SF-SIGN", 1), (L_, "L-LAB", 0.3)])
IT("X08", S, "Fire pump set 500gpm installed on base and commissioned", "set", [(M_, "M-FS-PUMP", 1), (M_, "M-CON-04", 2), (M_, "M-STL-27", 6), (P_, "P-CRN", 0.5), (L_, "L-PLU", 40), (L_, "L-ELE", 24), (L_, "L-LAB", 40)])
IT("X09", S, "VRF air-conditioning per HP installed (outdoor, cassette share, piping, refrigerant)", "HP", [(M_, "M-HV-VRFO", 1), (M_, "M-HV-VRFI", 0.5), (M_, "M-EL-47", 6), (M_, "M-HV-R410", 0.4),
     (M_, "M-EL-02", 0.05), (L_, "L-HVC", 4), (L_, "L-LAB", 2)])
IT("X10", S, "Ceiling cassette split AC 3HP installed with 6m piping", "nr", [(M_, "M-HV-CAS3", 1), (M_, "M-EL-47", 6), (L_, "L-HVC", 8), (L_, "L-LAB", 3)])
IT("X11", S, "Galvanised ductwork with insulation installed", "m2", [(M_, "M-HV-DUCT", 1.1), (M_, "M-RF-19", 1.1), (M_, "M-STL-41", 0.5), (L_, "L-HVC", 0.8), (L_, "L-LAB", 0.8)])
IT("X12", S, "Ceiling diffuser installed and balanced", "nr", [(M_, "M-HV-DIFF", 1), (L_, "L-HVC", 1)])
IT("X13", S, "Passenger lift 8-person 5 stops incl. builder's attendance", "nr", [(M_, "M-HV-LIFT", 1), (M_, "M-CEM-01", 4), (L_, "L-LAB", 40)])
IT("X14", S, "Escalator 4.5m rise incl. builder's attendance and lifting", "nr", [(M_, "M-HV-ESC", 1), (P_, "P-CR50", 1), (L_, "L-LAB", 60)])
IT("X15", S, "Cat6 data point (avg 30m) with outlet and patch panel share", "pt", [(M_, "M-EL-19", 0.1), (M_, "M-HV-C6O", 1), (M_, "M-HV-PP24", 1 / 24), (M_, "M-EL-05", 6), (L_, "L-ICT", 1.5)])
IT("X16", S, "IP CCTV camera installed with 25m Cat6 and NVR share", "nr", [(M_, "M-HV-IPC", 1), (M_, "M-EL-19", 0.082), (M_, "M-HV-NVR", 1 / 16), (M_, "M-EL-05", 5), (L_, "L-ICT", 2)])
IT("X17", S, "Access-controlled door (reader, maglock, exit button)", "nr", [(M_, "M-HV-ACC", 1), (M_, "M-EL-19", 0.05), (L_, "L-ICT", 6), (L_, "L-CAR", 2)])
IT("X18", S, "Solar water heater 200L installed and connected", "nr", [(M_, "M-HV-SWH", 1), (M_, "M-PL-07", 3), (L_, "L-PLU", 8), (L_, "L-LAB", 4)])
IT("X19", S, "Air-cooled chiller per TR installed", "TR", [(M_, "M-HV-CHL", 1), (P_, "P-CR50", 1 / 150), (L_, "L-HVC", 4), (L_, "L-LAB", 2)])
IT("X20", S, "Goods lift 1000kg 3 stops incl. builder's attendance", "nr", [(M_, "M-HV-GLIFT", 1), (L_, "L-LAB", 40)])

S = "Y Industrial buildings"
IT("Y01", S, "PU sandwich roof panel 50mm fixed to purlins incl. flashings", "m2", [(M_, "M-IN-PUR", 1.08), (M_, "M-RF-17", 0.08), (M_, "M-RF-06", 0.08), (P_, "P-TLH", 1 / 400), (L_, "L-ROF", 0.3), (L_, "L-LAB", 0.2)])
IT("Y02", S, "PU sandwich wall panel 50mm fixed to rails", "m2", [(M_, "M-IN-PUW", 1.06), (M_, "M-RF-17", 0.06), (P_, "P-TLH", 1 / 350), (L_, "L-ROF", 0.35), (L_, "L-LAB", 0.2)])
IT("Y03", S, "Galvanised rolling shutter (manual) installed", "m2", [(M_, "M-IN-RSH", 1), (L_, "L-WEL", 0.8), (L_, "L-LAB", 0.8)])
IT("Y04", S, "Insulated sectional door 4x4m motorised, installed", "nr", [(M_, "M-IN-SECD", 1), (L_, "L-WEL", 8), (L_, "L-ELE", 4), (L_, "L-LAB", 8)])
IT("Y05", S, "Overhead crane 10t x 20m span installed incl. 80m crane rail", "nr", [(M_, "M-IN-OHC", 1), (M_, "M-MR-RAIL", 80), (P_, "P-CR50", 2), (L_, "L-SER", 80), (L_, "L-ELE", 24), (L_, "L-LAB", 80)],
   "Runway beams/columns excluded.")
IT("Y06", S, "Dry-shake floor hardener (5kg/m2) power-floated into slab", "m2", [(M_, "M-IN-FH", 5), (P_, "P-FLT", 1 / 250), (L_, "L-CFN", 0.1), (L_, "L-LAB", 0.05)])
IT("Y07", S, "Cold-room PU panel 100mm installed", "m2", [(M_, "M-IN-CRP", 1.05), (L_, "L-ROF", 0.6), (L_, "L-LAB", 0.4)])
IT("Y08", S, "Pre-engineered steel building frame (approx. 35kg/m2), primed and erected", "m2", [(M_, "M-STL-08", 0.035), (M_, "M-STL-40", 0.6), (M_, "M-STL-38", 0.25), (M_, "M-FIN-29", 0.02),
     (P_, "P-CRN", 0.004), (P_, "P-WLG", 0.008), (L_, "L-WEL", 0.8), (L_, "L-SER", 0.8), (L_, "L-LAB", 0.8)], "Per m2 of floor area. Cladding and foundations excluded.")
IT("Y09", S, "Hydraulic dock leveller installed in pit", "nr", [(M_, "M-IN-DOCK", 1), (M_, "M-CON-04", 1.5), (L_, "L-WEL", 8), (L_, "L-ELE", 4), (L_, "L-LAB", 8)])

S = "E Finishes"
IT("E29", S, "Raised access floor 600x600 on adjustable pedestals", "m2", [(M_, "M-AR-RAF", 1.03), (L_, "L-TIL", 0.4), (L_, "L-LAB", 0.2)])
IT("E30", S, "Terrazzo floor 25mm laid, ground and polished", "m2", [(M_, "M-AR-TERR", 1.05), (M_, "M-CEM-01", 0.3), (P_, "P-FGR", 1 / 40), (L_, "L-TIL", 1.5), (L_, "L-LAB", 1.0)])
IT("E31", S, "HPL toilet cubicle partition installed", "nr", [(M_, "M-AR-CUB", 1), (L_, "L-JOI", 6), (L_, "L-LAB", 2)])
IT("E32", S, "Roller blind supplied and fixed", "m2", [(M_, "M-AR-BLND", 1), (L_, "L-JOI", 0.3)])
IT("E33", S, "Hardwood parquet laid on adhesive, sanded and sealed", "m2", [(M_, "M-AR-PARQ", 1.08), (M_, "M-CEM-03", 0.2), (M_, "M-FIN-30", 0.05), (P_, "P-FGR", 1 / 80), (L_, "L-CAR", 1.0), (L_, "L-LAB", 0.3)])
IT("E34", S, "HPL exterior cladding on steel sub-frame", "m2", [(M_, "M-AR-HPL", 1.08), (M_, "M-STL-24", 0.35), (M_, "M-STL-41", 2), (L_, "L-ALU", 1.2), (L_, "L-LAB", 0.5)])
IT("E35", S, "Aluminium louvre system installed", "m2", [(M_, "M-AR-LOUV", 1), (L_, "L-ALU", 1), (L_, "L-LAB", 0.4)])
IT("E36", S, "Acoustic wall panels on timber battens", "m2", [(M_, "M-AR-ACP", 1.05), (M_, "M-TMB-11", 1.5), (L_, "L-CAR", 0.8)])
IT("E37", S, "Rubber gym flooring 15mm laid", "m2", [(M_, "M-AR-RUB", 1.05), (L_, "L-TIL", 0.3)])
IT("E38", S, "Homogeneous vinyl sheet flooring, coved and welded", "m2", [(M_, "M-AR-VNL", 1.08), (M_, "M-CEM-06", 0.15), (L_, "L-TIL", 0.6)])
IT("E39", S, "Aluminium-framed glass skylight installed and sealed", "m2", [(M_, "M-AR-SKY", 1), (M_, "M-WP-12", 0.5), (L_, "L-ALU", 2), (L_, "L-WPR", 0.5), (L_, "L-LAB", 1)])

S = "Z Site, testing & surveys"
IT("Z01", S, "Concrete cube test, set of 3 incl. sampling", "set", [(M_, "M-TS-CUBE", 1), (L_, "L-LAB", 0.5)])
IT("Z02", S, "Geotechnical borehole with SPT (service)", "m", [(M_, "M-TS-BH", 1)])
IT("Z03", S, "Cone penetration test (service)", "m", [(M_, "M-TS-CPT", 1)])
IT("Z04", S, "Plate load test incl. reaction load", "nr", [(M_, "M-TS-PLT", 1), (P_, "P-EX14", 0.5)])
IT("Z05", S, "Static pile load test up to 300t incl. attendance", "nr", [(M_, "M-TS-SPLT", 1), (P_, "P-CRN", 2), (L_, "L-LAB", 24)])
IT("Z06", S, "High-strain dynamic pile test (PDA)", "nr", [(M_, "M-TS-PDA", 1)])
IT("Z07", S, "Topographic survey with total station (in-house)", "ha", [(P_, "P-TST", 0.3), (L_, "L-SVY", 2.4), (L_, "L-CHN", 4.8)])
IT("Z08", S, "Setting out with surveyor and 2 chainmen", "day", [(P_, "P-TST", 1), (L_, "L-SVY", 8), (L_, "L-CHN", 16)])
IT("Z09", S, "Site hoarding 2.4m, corrugated sheets on timber posts, painted", "m", [(M_, "M-CON-13", 1.0), (M_, "M-TMB-03", 0.6), (M_, "M-TMB-02", 0.6), (M_, "M-STL-06", 0.3), (M_, "M-FIN-05", 0.4),
     (L_, "L-CAR", 1), (L_, "L-LAB", 1)])
IT("Z10", S, "Field density test (sand replacement)", "nr", [(M_, "M-TS-FDT", 1)])
IT("Z11", S, "CBR test", "nr", [(M_, "M-TS-CBR", 1)])
IT("Z12", S, "Rebar tensile and bend test", "nr", [(M_, "M-TS-REB", 1)])
IT("Z13", S, "Ultrasonic weld test, per joint", "nr", [(M_, "M-TS-UT", 1)])
IT("Z14", S, "Asphalt core and extraction test", "nr", [(M_, "M-TS-ASP", 1)])
IT("Z15", S, "Water quality analysis (full suite)", "nr", [(M_, "M-TS-WQ", 1)])

# ------------------------------------------------------------------ MERGE + VALIDATE
have = {r["c"] for r in D["resources"]} | {l["c"] for l in D["labour"]} | {p["c"] for p in D["plant"]}
codes = [x["c"] for x in new_res + new_lab + new_plant]
dups = {c for c in codes if codes.count(c) > 1} | (set(codes) & have)
assert not dups, f"duplicate codes: {sorted(dups)}"
allc = have | set(codes)
icodes = {i["c"] for i in D["items"]}
bad = [(i["c"], r) for i in new_items for t, r, q in i["l"] if r not in allc]
assert not bad, f"missing resources: {bad}"
assert not ({i['c'] for i in new_items} & icodes), "duplicate item codes"
for p in new_plant:
    assert p["op"] is None or p["op"] in allc, p
for r in new_res:
    if "k" in r: assert r["k"]["b"] in allc, r
D["resources"] += new_res; D["labour"] += new_lab; D["plant"] += new_plant; D["items"] += new_items
D["sources"] += [["Dexin - API 5L pipe price list 2026 (Jan 2026)", "https://www.dexinpipe.com/api-5l-pipe-price-list/"],
                 ["electrical.ng - 240mm2 11-33kV XLPE single-core cable", "https://electrical.ng/product/240mm%C2%B2-swa-11kv-33kv-single-core-xlpe-pvc-copper-cable/"]]
D["meta"]["version"] = 3
D["changelog"].append(dict(date=SET, note=(f"v3: added {len(new_res)} materials, tools and test services, {len(new_lab)} labour grades, {len(new_plant)} plant items and "
                                           f"{len(new_items)} composite rates covering oil & gas pipelines, piling, bridges, ports and reclamation, railways, power, water and sewerage, "
                                           "fire, HVAC, lifts, ICT and industrial buildings. Imported items now track the naira-dollar rate.")))
json.dump(D, open(PATH, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
print(f"added: {len(new_res)} materials/tools/tests, {len(new_lab)} labour, {len(new_plant)} plant, {len(new_items)} items = {len(new_res)+len(new_lab)+len(new_plant)} resources")
print("totals:", len(D["resources"]), len(D["labour"]), len(D["plant"]), len(D["items"]))
