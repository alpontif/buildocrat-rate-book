"""v3b: construction equipment and machinery FOR SALE (purchase prices), new and used.
Run once:  python3 tools/extend_v3b.py
Naira prices come from Nigerian marketplace listings checked on 1 Oct 2026 (Jiji.ng and
others). Lines with no Nigerian listing are US$ desk estimates linked to M-FX-USD.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "rate-data.json")
D = json.load(open(PATH, encoding="utf-8"))
SET = "2026-10-01"
LAND = 1.40
NOTE = "Purchase price, ex-dealer/seller (Lagos/Abuja). Used prices vary a lot with hours, year and condition: inspect and test before paying."
new = []

JIJI = lambda what: f"Jiji.ng {what} listings checked 1 Oct 2026"
SRC = {
    "ex": JIJI("excavator") + ": tokunbo CAT 320D N170m, 320CL N95.5m, 330D N185m, new CAT 330GC N395m, Komatsu PC56 new N60-65m",
    "mini": JIJI("mini excavator") + ": Kubota U17 N30m, Yanmar B37 N45-65m, CAT 306D N65-95m, Kobelco SK75 N49m",
    "doz": JIJI("bulldozer") + ": tokunbo D6H/D6R N145-250m, D7G N160-180m, D8H/D8K N100-150m, new Zoomlion ZD260G N260m, ZD340G N358m",
    "wl": JIJI("wheel loader") + ": new LiuGong 816H N36m, 835H N56m, new 5t SDLG/Lonking N80-120m, tokunbo CAT 950 N55-65m, CAT 966 N110-155m",
    "bh": JIJI("backhoe loader") + ": new Chinese/6-in-1 N85-148m, tokunbo CAT 424B/JCB N75-95m, Nigerian used N25-30m",
    "gr": JIJI("motor grader") + ": Nigerian-used CAT 12G N35-65m, 140G N70-85m, foreign-used 140G N175m, new LiuGong/SDLG/Shantui N108-176m",
    "rol": JIJI("road roller") + ": walk-behind 550-800kg N5-7m, 3t tandem N25-33m, 5t ride-on N49.5-59.5m",
    "asp": JIJI("asphalt equipment") + ": tokunbo CAT/Vogele pavers N145-280m",
    "how": JIJI("Howo truck") + ": new 371 tippers N52-110m, used tippers N48-58m, used tractor head N46.5m, used mixer truck N44m, used tankers N55-57m",
    "lb": JIJI("low-bed") + ": new 100t front-loading N86-92m, new 80t N55m",
    "cr": JIJI("crane") + ": SANY 55t truck crane N140m, 80t N165-170m, Grove 80t N280-300m, Grove 90t N480-605m, Grove 120t N500-650m, new Zoomlion 55t N299m, new XCMG 70t N450m, 150t crawler N240-280m",
    "tc": JIJI("tower crane") + ": used N185-350m, new Potain N450m",
    "fl": JIJI("forklift") + ": new 3t N23-38.5m, 7t N80m, 10t N155m, 16t N285m",
    "bp": JIJI("concrete batch plant") + ": new 35m3/h N115-120m, 50m3/h N165-180m, 75m3/h N192-200m",
    "cp": JIJI("concrete pump") + ": new 15-20m3/h N28-30m, 40m3/h N33-50m, 60m3/h N65-75m, 80m3/h N80m, 100m3/h N110m, used boom trucks N140-175m",
    "blk": "Nigerian Search Guide, 'Cost of block moulding machines in Nigeria (2026)'",
    "q": JIJI("stone crusher") + ": 200tph jaw-cone used N150-200m, 400-500tph N400m, PE900x1200 new N200m, wagon drills N40-90m",
    "gen": "NaijaTechGuide generator price list (17 Jan 2026): Mikano 50kVA N7.2-10m, 100kVA N15.9-20.4m; Lister 250kVA N24.5-30.6m; Perkins 10kVA N1.95-2.95m",
    "dr": JIJI("dredger") + ": jet suction N22-26m, 8\" used N24m, 10/12\" used N45m, small CSD new N50m, Ellicott 20/22\" CSD N950m",
}

def rnd(v): return round(v, -3 if v < 1e6 else -4 if v < 1e8 else -5)
def E(c, g, cat, d, r, lo, hi, conf="MEDIUM", src=None, n=NOTE):
    new.append(dict(c=c, g=g, cat=cat, d=d, u="nr", w=0, src=src or "Desk estimate (Oct 2026); verify with 3 dealer quotes",
                    ev=("2026-10-01" if src and conf != "LOW" else None), set=SET, conf=conf, n=n, r=r, lo=lo, hi=hi))
def L(c, g, cat, d, r, conf="LOW", src=None, s=0.2):
    E(c, g, cat, d, r, rnd(r * (1 - s)), rnd(r * (1 + s)), conf, src)
def U(c, g, cat, d, usd, s=0.2):
    new.append(dict(c=c, g=g, cat=cat, d=d, u="nr", w=0, set=SET, conf="LOW", ev=None,
                    src=f"Desk estimate US${usd:,.0f} FOB China/EU x {LAND} landed x NFEM rate (Oct 2026); verify with dealer quotes",
                    n="Imported new: price moves with the exchange rate. " + NOTE, k=dict(b="M-FX-USD", f=round(usd * LAND, 2), s=s)))
m = 1_000_000

# ---------------------------------------------------------------- EARTHMOVING
G = "Equipment for Sale: Earthmoving"
E("M-EQ-EX17U", G, "Excavators", "Mini excavator 1.5-2t (Kubota/Yanmar), foreign used", 30*m, 25*m, 40*m, src=SRC["mini"])
E("M-EQ-EX35U", G, "Excavators", "Mini excavator 3-4t (Yanmar B37/Kubota), foreign used", 50*m, 45*m, 65*m, src=SRC["mini"])
E("M-EQ-EX35N", G, "Excavators", "Mini excavator 3-4t (Yanmar/Kubota), new", 60*m, 55*m, 75*m, src=SRC["mini"])
E("M-EQ-EX55N", G, "Excavators", "Excavator 5-6t (Komatsu PC56), new", 65*m, 60*m, 75*m, src=SRC["mini"])
E("M-EQ-EX55U", G, "Excavators", "Excavator 5-6t (CAT 306D/Komatsu PC56-58), foreign used", 70*m, 45*m, 95*m, src=SRC["mini"])
E("M-EQ-EX75U", G, "Excavators", "Excavator 7.5-8t (Kobelco SK75/Sumitomo SH75), foreign used", 50*m, 45*m, 65*m, src=SRC["mini"])
U("M-EQ-EX75N", G, "Excavators", "Excavator 7.5-9t, new Chinese (SANY SY75/XCMG XE80)", 45000)
U("M-EQ-EX21C", G, "Excavators", "Excavator 20-22t, new Chinese (SANY SY215/XCMG XE215/LiuGong 922)", 95000)
E("M-EQ-EX21P", G, "Excavators", "Excavator 20-22t, new CAT 320GC/Komatsu PC210", 320*m, 280*m, 380*m, "LOW", SRC["ex"] + " (320GC new scaled from 330GC)")
E("M-EQ-EX21U", G, "Excavators", "Excavator 20-22t (CAT 320D/320GC), foreign used", 170*m, 140*m, 200*m, src=SRC["ex"])
E("M-EQ-EX21O", G, "Excavators", "Excavator 20-22t older model (CAT 320C/320CL/322CL), foreign used", 100*m, 75*m, 140*m, src=SRC["ex"])
E("M-EQ-EX30U", G, "Excavators", "Excavator 30t (CAT 330D/330BL/330CL), foreign used", 160*m, 135*m, 190*m, src=SRC["ex"])
E("M-EQ-EX30P", G, "Excavators", "Excavator 30t, new CAT 330GC", 395*m, 360*m, 430*m, src=SRC["ex"])
U("M-EQ-EX36C", G, "Excavators", "Excavator 36-40t, new Chinese (SANY SY365/XCMG XE370)", 190000)
L("M-EQ-EXLR", G, "Excavators", "Long-reach excavator 20-22t (16-18m boom), foreign used", 210*m)
U("M-EQ-EXAMP", G, "Excavators", "Amphibious (pontoon) excavator 20t, new Chinese", 165000)
L("M-EQ-EXWH", G, "Excavators", "Wheeled excavator 14-16t, foreign used", 110*m)
U("M-EQ-HBRK", G, "Excavator attachments", "Hydraulic breaker for 20t excavator (1.5t class), new", 9000)
L("M-EQ-BKT1", G, "Excavator attachments", "Excavator bucket 1.0-1.2m3 for 20-22t machine, used", 8*m, src=JIJI("excavator") + ": CAT bucket N12m")
U("M-EQ-VRIP", G, "Excavator attachments", "Ripper tooth / vibro-ripper for 20-30t excavator, new", 6000)
E("M-EQ-SSLU", G, "Loaders", "Skid-steer loader (Bobcat S-series), foreign used", 60*m, 45*m, 75*m, src=SRC["wl"])
E("M-EQ-SSLN", G, "Loaders", "Skid-steer loader (Bobcat S650 class), new", 135*m, 110*m, 150*m, "LOW", SRC["wl"])
E("M-EQ-BHLC", G, "Loaders", "Backhoe loader, new Chinese (XCMG/6-in-1 types)", 95*m, 85*m, 140*m, src=SRC["bh"])
E("M-EQ-BHLP", G, "Loaders", "Backhoe loader, new premium (JCB 3CX/CAT 426/Bobcat B730)", 150*m, 130*m, 175*m, "LOW", SRC["bh"])
E("M-EQ-BHLU", G, "Loaders", "Backhoe loader (CAT 424B/426B, JCB 3CX), foreign used", 85*m, 75*m, 95*m, src=SRC["bh"])
E("M-EQ-BHLL", G, "Loaders", "Backhoe loader (JCB/CAT), Nigerian used", 28*m, 25*m, 35*m, src=SRC["bh"])
E("M-EQ-WL16", G, "Loaders", "Wheel loader 1.6t (LiuGong 816H), new", 36*m, 30*m, 42*m, src=SRC["wl"])
E("M-EQ-WL30", G, "Loaders", "Wheel loader 3t (LiuGong 835H), new", 56*m, 50*m, 65*m, src=SRC["wl"])
E("M-EQ-WL50", G, "Loaders", "Wheel loader 5t, new Chinese (LiuGong 855/SDLG/Lonking LG855)", 110*m, 92*m, 120*m, src=SRC["wl"])
E("M-EQ-WL50U", G, "Loaders", "Wheel loader 5t Chinese (LiuGong/SDLG), foreign used", 45*m, 38*m, 55*m, src=SRC["wl"])
E("M-EQ-WL950", G, "Loaders", "Payloader CAT 950 series, foreign used", 55*m, 45*m, 65*m, src=SRC["wl"])
E("M-EQ-WL966", G, "Loaders", "Payloader CAT 966 series, foreign used", 130*m, 110*m, 155*m, src=SRC["wl"])
E("M-EQ-WLNU", G, "Loaders", "Payloader (CAT 950/SDLG), Nigerian used", 30*m, 20*m, 75*m, src=SRC["wl"])
E("M-EQ-DZ6U", G, "Bulldozers", "Bulldozer D6 class (CAT D6H/D6R), foreign used", 200*m, 145*m, 250*m, src=SRC["doz"])
E("M-EQ-DZ7G", G, "Bulldozers", "Bulldozer D7 class (CAT D7G), foreign used", 170*m, 150*m, 190*m, src=SRC["doz"])
E("M-EQ-DZ7R", G, "Bulldozers", "Bulldozer CAT D7R, foreign used", 340*m, 300*m, 360*m, "LOW", SRC["doz"])
E("M-EQ-DZ8U", G, "Bulldozers", "Bulldozer D8 class older (CAT D8H/D8K), foreign used", 125*m, 100*m, 150*m, src=SRC["doz"])
E("M-EQ-DZ26N", G, "Bulldozers", "Bulldozer 220-260hp, new Chinese (Shantui SD22/Zoomlion ZD260G)", 230*m, 200*m, 260*m, src=SRC["doz"])
E("M-EQ-DZ34N", G, "Bulldozers", "Bulldozer 320-340hp, new Chinese (Shantui SD32/Zoomlion ZD340G)", 350*m, 300*m, 380*m, src=SRC["doz"])
U("M-EQ-DZ16N", G, "Bulldozers", "Bulldozer 160hp, new Chinese (Shantui SD16)", 78000)
L("M-EQ-DZLGP", G, "Bulldozers", "Swamp (LGP) bulldozer D6 class, foreign used", 220*m)
L("M-EQ-ADT30", G, "Dump trucks", "Articulated dump truck 25-30t (CAT 730/Volvo A30), foreign used", 220*m)
L("M-EQ-RDT40", G, "Dump trucks", "Rigid off-highway dump truck 40t (CAT 773/Komatsu HD405), foreign used", 350*m)

# ---------------------------------------------------------------- ROAD & COMPACTION
G = "Equipment for Sale: Road Construction & Compaction"
E("M-EQ-GR12N", G, "Graders", "Motor grader CAT 12G/12F, Nigerian used", 50*m, 33*m, 65*m, src=SRC["gr"])
E("M-EQ-GR14N", G, "Graders", "Motor grader CAT 140G, Nigerian used", 80*m, 70*m, 85*m, src=SRC["gr"])
E("M-EQ-GR14U", G, "Graders", "Motor grader CAT 140G/14E/120B, foreign used", 120*m, 75*m, 175*m, src=SRC["gr"])
E("M-EQ-GRCN", G, "Graders", "Motor grader 180-215hp, new Chinese (LiuGong/SDLG/Shantui)", 150*m, 108*m, 176*m, src=SRC["gr"])
U("M-EQ-GRCAT", G, "Graders", "Motor grader CAT 140 GC, new", 230000)
U("M-EQ-SDR12", G, "Rollers", "Single-drum vibratory roller 12-14t, new Chinese (XCMG XS123/LiuGong 6114)", 48000)
L("M-EQ-SDR12U", G, "Rollers", "Single-drum vibratory roller 10-12t (Dynapac CA25/Bomag BW213), foreign used", 55*m)
E("M-EQ-TDR3", G, "Rollers", "Tandem vibratory roller 3t, new", 25*m, 22*m, 33*m, src=SRC["rol"])
E("M-EQ-RR5", G, "Rollers", "Ride-on vibratory roller 5t, new", 55*m, 49.5*m, 59.5*m, src=SRC["rol"])
E("M-EQ-WBR", G, "Rollers", "Walk-behind double-drum roller 550-800kg, new", 6.5*m, 5*m, 7*m, src=SRC["rol"])
E("M-EQ-WBR1", G, "Rollers", "Walk-behind single-drum roller 330kg, new", 3.8*m, 3.7*m, 4.2*m, src=SRC["rol"])
U("M-EQ-PTR", G, "Rollers", "Pneumatic-tyred roller 16-26t, new Chinese", 55000)
E("M-EQ-PAVU", G, "Asphalt", "Asphalt paver (CAT AP-1000/Vogele), foreign used", 250*m, 145*m, 280*m, src=SRC["asp"])
U("M-EQ-PAVN", G, "Asphalt", "Asphalt paver 9m, new Chinese (XCMG RP903/SANY)", 170000)
U("M-EQ-AMP80", G, "Asphalt", "Asphalt batch mixing plant 80 t/h, new Chinese, ex-works", 280000)
U("M-EQ-AMP160", G, "Asphalt", "Asphalt batch mixing plant 160 t/h, new Chinese, ex-works", 480000)
U("M-EQ-BDIS", G, "Asphalt", "Bitumen distributor truck 8,000L, new", 55000)
U("M-EQ-CHSP", G, "Asphalt", "Chip spreader (self-propelled or truck-mounted), new", 40000)
L("M-EQ-MILL", G, "Asphalt", "Cold milling machine 1.0-1.3m drum, foreign used", 200*m)
U("M-EQ-LMRK", G, "Road furniture", "Thermoplastic road-marking machine (hand-push) with pre-heater, new", 6000)
U("M-EQ-KERB", G, "Road furniture", "Kerb/drain slipform machine (small), new", 35000)
U("M-EQ-STAB", G, "Earthworks", "Soil stabiliser / recycler (WR-class), new Chinese", 300000)

# ---------------------------------------------------------------- TRUCKS & HAULAGE
G = "Equipment for Sale: Trucks & Haulage"
E("M-EQ-TIP30N", G, "Tippers", "Tipper truck 6x4 371hp 30t (Sinotruk Howo), new", 100*m, 65*m, 110*m, src=SRC["how"])
E("M-EQ-TIP30U", G, "Tippers", "Tipper truck 6x4 30-35t (Howo), used", 55*m, 48*m, 58*m, src=SRC["how"])
L("M-EQ-TIPMB", G, "Tippers", "Tipper truck (Mack/MAN/Mercedes), foreign used", 60*m)
L("M-EQ-TIP10", G, "Tippers", "Tipper truck 10-15t 4x2, used", 30*m)
L("M-EQ-THN", G, "Haulage", "Tractor head 6x4 (Howo/Shacman), new", 75*m)
E("M-EQ-THU", G, "Haulage", "Tractor head 6x4 (Howo), used", 46.5*m, 40*m, 55*m, src=SRC["how"])
E("M-EQ-LB80", G, "Haulage", "Low-bed trailer 80t (back-loading), new", 55*m, 50*m, 62*m, src=SRC["lb"])
E("M-EQ-LB100", G, "Haulage", "Low-bed trailer 100t front-loading, new", 89*m, 86*m, 92*m, src=SRC["lb"])
L("M-EQ-FLATT", G, "Haulage", "Flatbed trailer 40ft tri-axle, new", 25*m)
U("M-EQ-TM10N", G, "Concrete trucks", "Transit mixer truck 9-10m3 (Howo/SANY), new", 55000)
E("M-EQ-TM10U", G, "Concrete trucks", "Transit mixer truck (Howo), used", 44*m, 38*m, 55*m, src=SRC["how"])
E("M-EQ-WTK", G, "Tankers", "Water tanker truck 20,000-30,000L, used", 55*m, 45*m, 60*m, src=SRC["how"])
U("M-EQ-FBWN", G, "Tankers", "Diesel bowser truck 15,000-20,000L, new", 50000)
E("M-EQ-KNCK", G, "Haulage", "Truck with 10t knuckle-boom crane (Howo/XCMG), used", 110*m, 90*m, 130*m, src=SRC["how"])
L("M-EQ-PU4X4", G, "Site vehicles", "Pickup 4x4 double cabin (Toyota Hilux/Ford Ranger), new", 75*m)
L("M-EQ-PU4U", G, "Site vehicles", "Pickup 4x4 double cabin, foreign used", 35*m)
L("M-EQ-BUS18", G, "Site vehicles", "Staff bus 14-18 seater (Toyota Hiace), foreign used", 45*m)
U("M-EQ-DUMP3", G, "Site vehicles", "Site dumper 3t (front-tip), new", 12000)

# ---------------------------------------------------------------- CRANES & LIFTING
G = "Equipment for Sale: Cranes & Lifting"
U("M-EQ-TC25N", G, "Mobile cranes", "Truck crane 25t, new Chinese (XCMG QY25K/SANY STC250)", 130000)
E("M-EQ-TC55U", G, "Mobile cranes", "Truck crane 50-55t (SANY/XCMG), foreign used", 140*m, 120*m, 160*m, src=SRC["cr"])
E("M-EQ-TC55N", G, "Mobile cranes", "Truck crane 55t, new Chinese (Zoomlion/XCMG)", 300*m, 270*m, 330*m, src=SRC["cr"])
E("M-EQ-TC70N", G, "Mobile cranes", "Truck crane 70t, new Chinese (XCMG)", 450*m, 400*m, 490*m, src=SRC["cr"])
E("M-EQ-TC80U", G, "Mobile cranes", "Truck crane 80t (SANY), foreign used", 168*m, 150*m, 190*m, src=SRC["cr"])
E("M-EQ-AT80U", G, "Mobile cranes", "All-terrain crane 80t (Grove), foreign used", 290*m, 280*m, 320*m, src=SRC["cr"])
E("M-EQ-AT90U", G, "Mobile cranes", "All-terrain crane 90t 4x4 (Grove), foreign used", 540*m, 480*m, 605*m, src=SRC["cr"])
E("M-EQ-AT120U", G, "Mobile cranes", "All-terrain crane 110-120t (Grove), foreign used", 560*m, 300*m, 650*m, src=SRC["cr"])
E("M-EQ-TC400U", G, "Mobile cranes", "Truck crane 350-450t (SANY/Zoomlion), foreign used", 1100*m, 900*m, 1300*m, src=SRC["cr"])
E("M-EQ-CC55U", G, "Crawler cranes", "Crawler crane 55-60t (SANY/XCMG), foreign used", 90*m, 80*m, 100*m, src=SRC["cr"])
E("M-EQ-CC150U", G, "Crawler cranes", "Crawler crane 150t (SANY), foreign used", 260*m, 240*m, 280*m, src=SRC["cr"])
E("M-EQ-TWU", G, "Tower cranes", "Tower crane 6-12t, 50-60m jib, used (Potain/XCMG)", 220*m, 185*m, 350*m, src=SRC["tc"])
E("M-EQ-TWPN", G, "Tower cranes", "Tower crane 6t, 60m jib, new Potain", 450*m, 400*m, 500*m, "LOW", SRC["tc"])
U("M-EQ-TWCN", G, "Tower cranes", "Tower crane QTZ63/QTZ80 (6-8t, 50-55m jib), new Chinese incl. 40m mast", 60000)
E("M-EQ-FL3D", G, "Forklifts", "Forklift 3t diesel, new", 35*m, 23*m, 38.5*m, src=SRC["fl"])
E("M-EQ-FL3E", G, "Forklifts", "Forklift 3t electric, new", 32*m, 30*m, 36*m, src=SRC["fl"])
E("M-EQ-FL7", G, "Forklifts", "Forklift 7t diesel, new", 80*m, 75*m, 85*m, src=SRC["fl"])
E("M-EQ-FL10", G, "Forklifts", "Forklift 10t diesel, new", 155*m, 140*m, 170*m, src=SRC["fl"])
E("M-EQ-FL16", G, "Forklifts", "Forklift 16t diesel, new", 285*m, 270*m, 300*m, src=SRC["fl"])
L("M-EQ-FL3U", G, "Forklifts", "Forklift 3-5t, foreign used", 25*m, src=SRC["fl"])
L("M-EQ-TELU", G, "Access & handling", "Telehandler 4t 14-17m (JCB/Manitou), foreign used", 110*m)
U("M-EQ-HOIST", G, "Access & handling", "Builder's passenger/material hoist 2t twin cage, new Chinese, incl. 50m mast", 28000)
U("M-EQ-SCIS", G, "Access & handling", "Scissor lift 10-12m electric, new", 12000)
L("M-EQ-BOOM", G, "Access & handling", "Articulated boom lift 18-20m diesel, foreign used", 90*m)
L("M-EQ-CHB5", G, "Access & handling", "Chain block 5t x 6m lift", 350000)
U("M-EQ-GNTY", G, "Access & handling", "Gantry crane 10t x 20m span, new Chinese (precast yard)", 30000)

# ---------------------------------------------------------------- CONCRETE & BLOCK MAKING
G = "Equipment for Sale: Concrete & Block Making"
E("M-EQ-BP35", G, "Batching plants", "Concrete batching plant 35 m3/h, new", 118*m, 115*m, 120*m, src=SRC["bp"])
E("M-EQ-BP50", G, "Batching plants", "Concrete batching plant 50 m3/h, new", 170*m, 165*m, 180*m, src=SRC["bp"])
E("M-EQ-BP75", G, "Batching plants", "Concrete batching plant 75 m3/h, new", 196*m, 192*m, 200*m, src=SRC["bp"])
U("M-EQ-BP120", G, "Batching plants", "Concrete batching plant 120 m3/h, new Chinese, ex-works", 165000)
U("M-EQ-BPMOB", G, "Batching plants", "Mobile concrete batching plant 25 m3/h, new", 35000)
U("M-EQ-SILO", G, "Batching plants", "Cement silo 100t bolted, new", 9000)
E("M-EQ-CP20", G, "Concrete pumps", "Concrete trailer pump 15-20 m3/h, new", 29*m, 28*m, 30*m, src=SRC["cp"])
E("M-EQ-CP40", G, "Concrete pumps", "Concrete trailer pump 40 m3/h with 100m pipe, new", 48*m, 33*m, 50*m, src=SRC["cp"])
E("M-EQ-CP60", G, "Concrete pumps", "Concrete trailer pump 60 m3/h, new", 70*m, 65*m, 75*m, src=SRC["cp"])
E("M-EQ-CP80", G, "Concrete pumps", "Concrete trailer pump 80 m3/h, new", 80*m, 75*m, 90*m, src=SRC["cp"])
E("M-EQ-CP100", G, "Concrete pumps", "Concrete trailer pump 100 m3/h, new", 110*m, 100*m, 120*m, src=SRC["cp"])
E("M-EQ-CPBM", G, "Concrete pumps", "Truck-mounted boom pump 34-52m (SANY/Zoomlion), foreign used", 160*m, 140*m, 175*m, src=SRC["cp"])
E("M-EQ-MXPMP", G, "Concrete pumps", "Diesel concrete mixer with pump (mixer-pump), new", 55*m, 50*m, 60*m, src=SRC["cp"])
U("M-EQ-SLMX", G, "Mixers", "Self-loading concrete mixer 3.5-4 m3, new Chinese", 30000)
L("M-EQ-MX2B", G, "Mixers", "Concrete mixer 2-bag diesel (reversing drum), new", 4.5*m)
L("M-EQ-VIBE", G, "Concrete tools", "High-frequency electric poker vibrator 2.2kW with 6m shaft", 350000)
L("M-EQ-PTRW", G, "Concrete tools", "Power trowel (helicopter) 36\" petrol", 1.2*m)
L("M-EQ-FSAW", G, "Concrete tools", "Concrete floor/road saw 18\" petrol", 1.4*m)
L("M-EQ-CORE", G, "Concrete tools", "Diamond core drilling machine up to 200mm, with stand", 1.6*m)
L("M-EQ-RCUT", G, "Rebar machines", "Electric rebar cutter up to 40mm (GQ40)", 1.1*m)
L("M-EQ-RBND", G, "Rebar machines", "Electric rebar bender up to 40mm (GW40)", 1.3*m)
L("M-EQ-RTHR", G, "Rebar machines", "Rebar thread-rolling machine (for couplers)", 3.5*m)
E("M-EQ-BM2", G, "Block machines", "Block moulding machine, locally fabricated (2 blocks per drop)", 550000, 450000, 650000, src=SRC["blk"])
E("M-EQ-BMEL", G, "Block machines", "Electric vibrating block machine 6\"/9\", locally fabricated", 650000, 550000, 750000, src=SRC["blk"])
E("M-EQ-BMEGG", G, "Block machines", "Egg-laying (mobile) block machine, Nigerian fabricated (~1,000 blocks/day)", 900000, 800000, 1.2*m, src=SRC["blk"])
E("M-EQ-BMFT", G, "Block machines", "Block moulding line FT4-5 / mobile type (~3,000 blocks/day)", 5.2*m, 3.9*m, 6.5*m, src=SRC["blk"])
E("M-EQ-BMHY", G, "Block machines", "Hydraulic electric block machine", 8*m, 7*m, 9*m, src=SRC["blk"])
E("M-EQ-BMAUT", G, "Block machines", "Fully automatic block and brick machine (small line)", 17*m, 16*m, 18*m, src=SRC["blk"])
U("M-EQ-QT10", G, "Block machines", "Automatic block and paver plant QT10-15 with pan mixer and stacker, new Chinese", 60000)
U("M-EQ-PANMX", G, "Block machines", "Pan mixer JS500 / JQ350 for block plant, new", 4000)

# ---------------------------------------------------------------- QUARRY, DRILLING, COMPRESSORS
G = "Equipment for Sale: Quarry, Drilling & Compressors"
U("M-EQ-JAWS", G, "Crushers", "Jaw crusher PE-250x400 (small), new Chinese", 4500)
E("M-EQ-JAWL", G, "Crushers", "Jaw crusher PE-900x1200, new", 200*m, 170*m, 230*m, "LOW", SRC["q"])
E("M-EQ-CRU200", G, "Crushers", "Crushing plant 200 t/h (jaw + cone + screens), Nigerian used", 175*m, 150*m, 200*m, src=SRC["q"])
E("M-EQ-CRU450", G, "Crushers", "Crushing plant 400-500 t/h, Nigerian used", 400*m, 350*m, 450*m, src=SRC["q"])
L("M-EQ-MOBCR", G, "Crushers", "Tracked mobile jaw crusher (Metso/Sandvik/Powerscreen class), foreign used", 350*m)
U("M-EQ-SCRN", G, "Crushers", "Vibrating screen 3-deck 1.8x6m, new Chinese", 15000)
U("M-EQ-CONV", G, "Crushers", "Belt conveyor 20m x 800mm with motor, new", 9000)
E("M-EQ-WAGON", G, "Drilling", "Wagon drill (pneumatic crawler drill), foreign used", 65*m, 40*m, 90*m, src=SRC["q"])
L("M-EQ-DTH", G, "Drilling", "Hydraulic surface drill rig (top-hammer/DTH), foreign used", 250*m)
U("M-EQ-BHRG", G, "Drilling", "Water-borehole drilling rig truck-mounted (200-300m), new Chinese", 75000)
L("M-EQ-BHRGU", G, "Drilling", "Water-borehole drilling rig (truck-mounted), Nigerian used", 60*m)
U("M-EQ-AC750", G, "Compressors", "Diesel air compressor 750 cfm, new (Atlas Copco XAS class)", 45000)
U("M-EQ-AC375", G, "Compressors", "Diesel air compressor 375 cfm, new", 22000)
L("M-EQ-AC750U", G, "Compressors", "Diesel air compressor 750 cfm, foreign used", 35*m)
L("M-EQ-AC100", G, "Compressors", "Electric air compressor 100L", 450000)
L("M-EQ-JKHM", G, "Breakers", "Pneumatic jack hammer 25kg with hoses", 650000)
L("M-EQ-EBRK", G, "Breakers", "Electric demolition hammer 30kg", 450000)

# ---------------------------------------------------------------- POWER & PUMPING
G = "Equipment for Sale: Generators & Pumps"
E("M-EQ-G10", G, "Generators", "Diesel generator 10kVA (Perkins/Kipor), new", 2.4*m, 1.6*m, 2.95*m, src=SRC["gen"])
E("M-EQ-G30", G, "Generators", "Diesel generator 30kVA soundproof (Mikano/FG Wilson), new", 7*m, 3.7*m, 8.1*m, src=SRC["gen"])
E("M-EQ-G50", G, "Generators", "Diesel generator 50kVA soundproof (Mikano), new", 8.5*m, 7.2*m, 10*m, src=SRC["gen"])
E("M-EQ-G100", G, "Generators", "Diesel generator 100kVA soundproof (Mikano), new", 18*m, 15.9*m, 20.4*m, src=SRC["gen"])
L("M-EQ-G150", G, "Generators", "Diesel generator 150kVA soundproof (Perkins-engined), new", 25*m, src="Nigerian Price, Perkins list (Mar 2024) from N22m; adjusted")
L("M-EQ-G200", G, "Generators", "Diesel generator 200kVA soundproof (Perkins-engined), new", 28*m, src="Nigerian Price, Perkins list (Mar 2024) from N25m; adjusted")
E("M-EQ-G250", G, "Generators", "Diesel generator 250kVA soundproof (Lister/Perkins-engined), new", 30*m, 24.5*m, 36*m, src=SRC["gen"])
L("M-EQ-G300", G, "Generators", "Diesel generator 300kVA soundproof, new", 42*m, src="Nigerian Price, Perkins list (Mar 2024) from N38.9m; adjusted")
L("M-EQ-G500", G, "Generators", "Diesel generator 500kVA soundproof, new", 60*m, src="Nigerian Price, Perkins list (Mar 2024) from N47m; adjusted")
L("M-EQ-G1000", G, "Generators", "Diesel generator 1,000kVA soundproof, new", 125*m)
E("M-EQ-P55", G, "Generators", "Petrol generator 5.5kVA (Honda/Firman), new", 650000, 405000, 900000, src=SRC["gen"])
E("M-EQ-P10", G, "Generators", "Petrol generator 10kVA (Firman), new", 825000, 800000, 850000, src=SRC["gen"])
U("M-EQ-LTWR", G, "Site power", "Lighting tower 4x1000W diesel, new", 6500)
U("M-EQ-WGEN", G, "Site power", "Diesel welding generator 400A, new", 6000)
U("M-EQ-DP4", G, "Pumps", "Diesel trash/dewatering pump 4\", self-priming, new Chinese", 2500)
U("M-EQ-DP6", G, "Pumps", "Diesel dewatering pump 6\" skid-mounted, self-priming, new", 9000)
L("M-EQ-SUB3", G, "Pumps", "Submersible drainage pump 3\" electric", 650000)
U("M-EQ-WPT", G, "Pumps", "Wellpoint dewatering system (pump + 50 wellpoints + header), new", 25000)
L("M-EQ-DTNK", G, "Fuel storage", "Bunded diesel tank 5,000L skid with dispenser", 3.5*m)

# ---------------------------------------------------------------- MARINE & DREDGING
G = "Equipment for Sale: Marine & Dredging"
E("M-EQ-DJET", G, "Dredgers", "Jet suction sand dredger (Jagaban type), new local", 24*m, 22*m, 26*m, src=SRC["dr"])
E("M-EQ-D8U", G, "Dredgers", "Sand dredger 8\", Nigerian used", 24*m, 20*m, 28*m, src=SRC["dr"])
E("M-EQ-D12U", G, "Dredgers", "Suction dredger 10-12\", Nigerian used", 45*m, 40*m, 50*m, src=SRC["dr"])
E("M-EQ-DCSDS", G, "Dredgers", "Small cutter suction dredger, new local build", 50*m, 40*m, 65*m, "LOW", SRC["dr"])
U("M-EQ-DCSD14", G, "Dredgers", "Cutter suction dredger 14\" (Chinese, dismountable), new", 450000)
E("M-EQ-DCSD20", G, "Dredgers", "Cutter suction dredger 20/22\" (Ellicott), new", 950*m, 850*m, 1100*m, "LOW", SRC["dr"])
U("M-EQ-DPMP", G, "Dredgers", "Dredge pump set 12x10\" with diesel engine, new", 40000)
L("M-EQ-SPUD", G, "Vessels", "Spud barge / work pontoon 30x10m, new local fabrication", 350*m)
L("M-EQ-TUG", G, "Vessels", "Tugboat 1,000-1,200hp, foreign used", 900*m)
L("M-EQ-HOPB", G, "Vessels", "Sand hopper barge 500t, local build", 250*m)
L("M-EQ-CREW", G, "Vessels", "Crew/work boat 30-40 seater (fibreglass, twin outboard)", 180*m)
U("M-EQ-OB200", G, "Vessels", "Outboard engine 200hp, new", 18000)
L("M-EQ-SBGY", G, "Vessels", "Swamp buggy (amphibious excavator/carrier), foreign used", 450*m)

# ---------------------------------------------------------------- PILING
G = "Equipment for Sale: Piling & Foundations"
L("M-EQ-RIGU", G, "Piling rigs", "Rotary bored-pile rig 150-200kNm (SANY SR150/Bauer BG), foreign used", 450*m)
U("M-EQ-RIGN", G, "Piling rigs", "Rotary bored-pile rig 235kNm, new Chinese (SANY SR235)", 420000)
U("M-EQ-VIBH", G, "Piling rigs", "Excavator-mounted vibro hammer (sheet piles), new", 45000)
U("M-EQ-D62", G, "Piling rigs", "Diesel pile hammer D62 class with leader, new", 130000)
U("M-EQ-HPU", G, "Piling rigs", "Hydraulic power pack for vibro hammer, new", 60000)
U("M-EQ-SPDR", G, "Piling rigs", "Small percussion (tripod) bored-pile rig with winch, new", 15000)

# ---------------------------------------------------------------- SITE, SURVEY & SMALL PLANT
G = "Equipment for Sale: Site, Survey & Small Plant"
U("M-EQ-TSTN", G, "Survey instruments", "Total station 2\" (Leica/Sokkia/Topcon), new", 9000)
U("M-EQ-GNSS", G, "Survey instruments", "GNSS RTK set base + rover (CHC/Hi-Target/South), new", 7500)
U("M-EQ-DRONE", G, "Survey instruments", "Mapping drone with RTK (DJI Mavic 3 Enterprise class), new", 5500)
U("M-EQ-ATLV", G, "Survey instruments", "Automatic level with tripod and staff, new", 450)
L("M-EQ-RAMM", G, "Small plant", "Tamping rammer (jumping jack) petrol 4-stroke", 1.8*m)
L("M-EQ-PLT200", G, "Small plant", "Reversible plate compactor 200-300kg diesel", 4.5*m)
L("M-EQ-TOIL", G, "Site facilities", "Portable toilet cabin (plastic), new", 1.2*m)
L("M-EQ-CON40", G, "Site facilities", "40ft container converted site office (insulated, AC, wired)", 12*m)
L("M-EQ-HFRM", G, "Formwork & scaffold", "H-frame scaffold set 1.7m (2 frames, 2 braces, 4 jacks)", 85000)
L("M-EQ-PRPS", G, "Formwork & scaffold", "Adjustable steel prop 1.8-3.5m, new", 18000)
U("M-EQ-ALFW", G, "Formwork & scaffold", "Aluminium wall/slab formwork system, per m2 of panel", 130)  # unit set to m2 in data
L("M-EQ-PWASH", G, "Small plant", "Pressure washer 250 bar petrol", 650000)
L("M-EQ-HYDT", G, "Small plant", "Hydraulic torque wrench / bolt tensioning set", 6*m)

# ---------------------------------------------------------------- apply
have = {r["c"] for r in D["resources"]}
dup = [x["c"] for x in new if x["c"] in have]
assert not dup, f"duplicate codes {dup}"
assert len({x["c"] for x in new}) == len(new), "duplicate within batch"
for x in new:
    if "k" not in x:
        assert x["lo"] <= x["r"] <= x["hi"], x["c"]
D["resources"].extend(new)
srcs = [("Jiji.ng - construction & heavy machinery listings (Oct 2026)", "https://jiji.ng/heavy-equipments-machinery"),
        ("NaijaTechGuide - generator prices in Nigeria (Jan 2026)", "https://www.naijatechguide.com/generator-prices-in-nigeria.html"),
        ("Nigerian Search Guide - block moulding machine costs (2026)", "https://nigeriansearchguide.com/block-moulding-machine-costs-in-nigeria/")]
known = {s[1] for s in D["sources"]}
for s in srcs:
    if s[1] not in known:
        D["sources"].append(list(s))
D["changelog"].append({"date": SET, "note": f"Added {len(new)} construction equipment purchase prices (new and used): excavators, loaders, dozers, graders, rollers, pavers, asphalt and batching plants, tippers, low-beds, cranes, forklifts, concrete pumps, block machines, crushers, drill rigs, compressors, generators, pumps, dredgers, vessels, piling rigs and survey instruments."})
json.dump(D, open(PATH, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
print("added", len(new), "equipment lines; resources now", len(D["resources"]))
