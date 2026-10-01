"""Static, crawlable website for the Nigeria Construction Rate Book.

Called by assemble.py after the interactive page is built. Everything is generated from
rate-data.json, so the weekly price update refreshes every page, the sitemap, the feed,
llms.txt and the structured data automatically.
"""
import csv, datetime as dt, html, io, json, os, re
from engine_py import Engine

BASE = "https://rates.buildocrat.store"
LAUNCH = "2026-09-29"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
e = html.escape

UNIT = {"m2": "m²", "m3": "m³", "nr": "unit", "t": "tonne", "pt": "point", "h": "hour", "L": "litre",
        "pail": "20L pail", "coil": "100m coil", "length": "length", "load": "load"}
def u(x): return UNIT.get(x, x)
def naira(v):
    if v is None: return "-"
    if abs(v) < 0.005: return "₦0"
    if abs(v) < 100: return "₦" + f"{v:,.2f}"
    return "₦" + f"{round(v):,}"
def slug(s, n=64):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", " and ")).strip("-")
    return s[:n].rstrip("-")
def sec_name(s): return s.split(" ", 1)[1] if re.match(r"^[A-Z] ", s) else s

# ------------------------------------------------------------------ hub definitions
HUBS = [
 dict(slug="cement", name="Cement", h1="Price of cement in Nigeria today", q="How much is a bag of cement in Nigeria today?",
      primary="M-CEM-01", codes=["M-CEM-01", "M-CEM-07", "M-CEM-08", "M-CEM-09", "M-CEM-10", "M-CEM-11", "M-CEM-12"],
      drivers="Cement prices follow energy costs at the plants, diesel for haulage, the naira exchange rate for imported parts and seasonal demand. Buying a trailer load (600 bags) direct from a depot is usually a few hundred naira cheaper per bag than retail."),
 dict(slug="iron-rods", name="Iron rods (rebar)", h1="Price of iron rods (rebar) in Nigeria today", q="How much is a tonne of iron rod in Nigeria today?",
      primary="M-STL-01", codes=["M-STL-03", "M-STL-01", "M-STL-02", "M-STL-09", "M-STL-10", "M-STL-11", "M-STL-12", "M-STL-13", "M-STL-14", "M-STL-15", "M-STL-16"],
      drivers="Rebar prices track global steel and scrap prices, the exchange rate and energy costs at local mills. Imported TMT bars usually cost more than local bars, and small diameters often cost more per tonne. Weigh-check deliveries: undersized bars are common."),
 dict(slug="blocks", name="Blocks", h1="Price of blocks in Nigeria today (9-inch and 6-inch)", q="How much is a 9-inch block in Nigeria today?",
      primary="M-BLK-01", codes=["M-BLK-01", "M-BLK-02", "M-BLK-04", "M-BLK-08", "M-BLK-03", "M-BLK-09", "M-BLK-10", "M-BLK-11"],
      drivers="Block prices depend on cement and sand prices, block size and strength, and whether blocks are machine-vibrated and properly cured. Specify blocks that meet NIS 87 strength requirements for load-bearing walls."),
 dict(slug="sand", name="Sand", h1="Price of sharp sand in Nigeria today", q="How much is a trip of sharp sand in Nigeria?",
      primary="M-AGG-01", codes=["M-AGG-01", "M-AGG-02", "M-AGG-03", "M-AGG-04", "M-AGG-11", "M-AGG-12", "M-AGG-05", "M-AGG-06"],
      drivers="Sand is sold by the tipper load ('trip'), and trip sizes differ between cities, so always confirm the tonnage. Price depends on haulage distance from the source, diesel prices and local mining rules."),
 dict(slug="granite", name="Granite", h1="Price of granite in Nigeria today", q="How much is 30 tonnes of granite in Nigeria?",
      primary="M-AGG-07", codes=["M-AGG-07", "M-AGG-08", "M-AGG-13", "M-AGG-14", "M-AGG-15", "M-AGG-16", "M-AGG-17", "M-AGG-09", "M-AGG-10"],
      drivers="Granite is sold per tonne or per tipper load. Price depends on stone size (1/4 inch to 1 inch), distance from the quarry and diesel costs for haulage."),
 dict(slug="roofing-sheets", name="Roofing sheets", h1="Price of roofing sheets in Nigeria today", q="How much is aluminium roofing sheet per square metre in Nigeria?",
      primary="M-RF-01", codes=["M-RF-11", "M-RF-03", "M-RF-01", "M-RF-09", "M-RF-02", "M-RF-10", "M-RF-04", "M-RF-12", "M-RF-05", "M-RF-15"],
      drivers="Aluminium roofing is priced per square metre and by thickness. Market-grade sheets are often thinner than their labelled gauge; caliper-grade sheets match the stated thickness and cost more. Stone-coated tiles are priced per piece."),
 dict(slug="tiles", name="Tiles", h1="Price of tiles in Nigeria today", q="How much are 60x60 floor tiles per square metre in Nigeria?",
      primary="M-FIN-01", codes=["M-FIN-01", "M-FIN-02", "M-FIN-11", "M-FIN-12", "M-FIN-13", "M-FIN-14", "M-FIN-03"],
      drivers="Tile prices depend on size, body (ceramic or porcelain), finish and country of origin. Allow 8-10% extra for cutting and breakage, plus adhesive and grout."),
 dict(slug="paint", name="Paint", h1="Price of paint in Nigeria today", q="How much is a 20-litre bucket of emulsion paint in Nigeria?",
      primary="M-FIN-04", codes=["M-FIN-04", "M-FIN-25", "M-FIN-06", "M-FIN-27", "M-FIN-08"],
      drivers="Paint is sold by the 20-litre pail. Quality varies widely between brands; coverage per litre and the number of coats matter more than the pail price."),
 dict(slug="timber", name="Timber", h1="Price of timber and wood in Nigeria today", q="How much is a 2x4 hardwood in Nigeria?",
      primary="M-TMB-03", codes=["M-TMB-01", "M-TMB-02", "M-TMB-03", "M-TMB-04", "M-TMB-09", "M-TMB-05", "M-TMB-06", "M-TMB-14", "M-TMB-15"],
      drivers="Timber prices depend on species (Gmelina, Mahogany, Iroko), size, and whether it is treated or dressed. Formwork boards are reused several times, which lowers the cost per use."),
 dict(slug="diesel-petrol", name="Diesel and petrol", h1="Diesel and petrol prices for construction in Nigeria", q="What is the price of diesel in Nigeria today?",
      primary="M-FUE-01", codes=["M-FUE-01", "M-FUE-02", "M-FUE-03"],
      drivers="Diesel and petrol are deregulated. Pump prices follow the refinery gantry price, crude oil prices and the exchange rate. Diesel drives the cost of plant hire and haulage on every site."),
 dict(slug="water-tanks", name="Water tanks", h1="Price of water tanks in Nigeria today", q="How much is a 2,000-litre water tank in Nigeria?",
      primary="M-PL-06", codes=["M-PL-31", "M-PL-32", "M-PL-06", "M-PL-33", "M-PL-34", "M-PL-35", "M-PL-36"],
      drivers="Polyethylene tank prices rise with capacity and wall thickness. Add the cost of a tank stand, fittings and delivery."),
 dict(slug="solar", name="Solar equipment", h1="Price of solar panels, inverters and batteries in Nigeria", q="How much is a 5kVA inverter in Nigeria?",
      primary="M-EL-50", codes=["M-EL-49", "M-EL-50", "M-EL-51", "M-EL-52", "M-EL-53", "M-EL-54"],
      drivers="Solar equipment is mostly imported, so prices follow the exchange rate. Lithium (LiFePO4) batteries cost more than tubular batteries but last much longer."),
 dict(slug="ready-mix-concrete", name="Ready-mix concrete", h1="Price of ready-mix concrete per cubic metre in Nigeria", q="How much is ready-mix concrete per cubic metre in Nigeria?",
      primary="M-CON-04", codes=["M-CON-06", "M-CON-04", "M-CON-07", "M-CON-08", "M-CON-09", "M-CON-05"],
      drivers="Ready-mix is priced per cubic metre by strength grade, plus pumping. Small pours cost more per cubic metre because of minimum loads and pump charges."),
 dict(slug="electrical-cables", name="Electrical cables", h1="Price of electrical cables in Nigeria today", q="How much is a coil of 2.5mm cable in Nigeria?",
      primary="M-EL-02", codes=["M-EL-11", "M-EL-01", "M-EL-02", "M-EL-03", "M-EL-04", "M-EL-13", "M-EL-14", "M-EL-15", "M-EL-16", "M-EL-17"],
      drivers="Cable prices follow copper prices and the exchange rate. Buy pure-copper cable from reputable brands; aluminium-core and undersized cables are common fakes."),
 dict(slug="doors-windows", name="Doors and windows", h1="Price of doors and windows in Nigeria today", q="How much is an aluminium casement window per square metre in Nigeria?",
      primary="M-DW-04", codes=["M-DW-04", "M-DW-05", "M-DW-09", "M-DW-01", "M-DW-02", "M-DW-03", "M-DW-06"],
      drivers="Window and door prices depend on the aluminium or uPVC profile, glass type and thickness, and hardware. Most are supplied and fixed by specialist fabricators."),
 dict(slug='line-pipe', name='Line pipe & pipeline materials', h1='Price of API 5L line pipe and pipeline materials in Nigeria', q='How much is API 5L line pipe per metre in Nigeria?',
      primary='M-OG-X52-12', codes=['M-OG-X52-12', 'M-OG-LPT', 'M-OG-LPT65', 'M-OG-SMLS', 'M-OG-X52-4', 'M-OG-X52-6', 'M-OG-X52-8', 'M-OG-X52-10', 'M-OG-X52-16', 'M-OG-X52-20', 'M-OG-X52-24', 'M-OG-X52-30'],
      drivers='Line pipe, flanges and valves are almost all imported, so naira prices move with the exchange rate, global steel prices and shipping. Prices here are estimates built from USD supplier lists plus a landed-cost factor; get mill or stockist quotes for any real tender.'),
 dict(slug='sheet-piles', name='Sheet piles & piling', h1='Price of sheet piles and piling materials in Nigeria', q='How much do steel sheet piles cost in Nigeria?',
      primary='M-PG-PU18', codes=['M-PG-PU18', 'M-PG-SPT', 'M-PG-PU12', 'M-PG-PU28', 'M-PG-AZ26', 'M-PG-HPT', 'M-PG-HP305X79', 'M-PG-HP305X110', 'M-PG-HP356X174', 'M-PG-TPT', 'M-PG-TP610', 'M-PG-TP762'],
      drivers='Steel sheet piles are imported and priced by weight, so the exchange rate and global steel prices drive cost. Hire or buy-back arrangements for temporary works can cut the cost sharply.'),
 dict(slug='hdpe-pipes', name='HDPE & water pipes', h1='Price of HDPE and water pipes in Nigeria', q='How much is a 110mm HDPE pipe per metre in Nigeria?',
      primary='M-WT-H17-110', codes=['M-WT-H17-110', 'M-WT-HDPEKG', 'M-WT-H17-63', 'M-WT-H17-90', 'M-WT-H17-160', 'M-WT-H17-200', 'M-WT-H17-250', 'M-WT-H17-315', 'M-WT-H17-400', 'M-WT-H17-500', 'M-WT-H17-630', 'M-WT-H11-32'],
      drivers='HDPE pipe is priced per kilogram of polymer, so heavier pressure classes (lower SDR) cost more per metre. Polymer prices follow the exchange rate and crude oil prices.'),
 dict(slug='power-cables-transformers', name='Power cables & transformers', h1='Price of power cables and transformers in Nigeria', q='How much is a 33kV cable or a 500kVA transformer in Nigeria?',
      primary='M-PW-33C240', codes=['M-PW-33C240', 'M-PW-33C185AL', 'M-PW-11C95', 'M-PW-11C185', 'M-PW-LV120', 'M-PW-LV185', 'M-PW-LV240', 'M-PW-ABC', 'M-PW-AAC100', 'M-PW-ACSR150', 'M-PW-P12', 'M-PW-P15'],
      drivers='Copper and aluminium prices, the exchange rate and import duties drive cable and transformer prices. Utility (DisCo) approval and metering costs are extra.'),
 dict(slug='fire-safety', name='Fire safety equipment', h1='Price of fire extinguishers and fire safety equipment in Nigeria', q='How much is a fire extinguisher in Nigeria?',
      primary='M-FS-DCP9', codes=['M-FS-DCP9', 'M-FS-CP8', 'M-FS-AP2', 'M-FS-SMK', 'M-FS-HEAT', 'M-FS-MCP', 'M-FS-SND', 'M-FS-CAB', 'M-FS-SPK', 'M-FS-HRC', 'M-FS-LV', 'M-FS-PUMP'],
      drivers='Most fire equipment is imported; buy from suppliers who provide certified, refillable units and annual servicing.'),
 dict(slug='construction-tools', name='Construction tools', h1='Price of construction tools in Nigeria', q='How much is a wheelbarrow and other site tools in Nigeria?',
      primary='M-TL-WBAR', codes=['M-TL-WBAR', 'M-TL-SHOV', 'M-TL-HPAN', 'M-TL-PICK', 'M-TL-CUTL', 'M-TL-PHD', 'M-TL-RAKE', 'M-TL-TROW', 'M-TL-FLOAT', 'M-TL-SLVL', 'M-TL-TP50', 'M-TL-TP5'],
      drivers='Hand tools vary widely by brand and origin; cheap imports wear out fast on site, so price the durable grade for long jobs.'),
 dict(slug='armour-rock', name='Armour rock & marine materials', h1='Price of armour rock and marine construction materials in Nigeria', q='How much is armour rock per tonne in Nigeria?',
      primary='M-MR-AR36', codes=['M-MR-AR36', 'M-MR-AR13', 'M-MR-CORE', 'M-MR-UL', 'M-MR-ROY', 'M-MR-FCONE', 'M-MR-FCYL', 'M-MR-FD300', 'M-MR-BOL50', 'M-MR-BOL100', 'M-MR-RAIL', 'M-MR-LADR'],
      drivers='Rock for breakwaters and shore protection is quarried inland and hauled long distances, so haulage and barge transport usually cost more than the rock itself.'),
 dict(slug='excavators', name='Excavators', h1='Price of excavators in Nigeria (new and tokunbo)', q='How much is an excavator in Nigeria?',
      primary='M-EQ-EX21U', codes=['M-EQ-EX17U', 'M-EQ-EX35U', 'M-EQ-EX35N', 'M-EQ-EX55N', 'M-EQ-EX55U', 'M-EQ-EX75U', 'M-EQ-EX75N', 'M-EQ-EX21C', 'M-EQ-EX21P', 'M-EQ-EX21U', 'M-EQ-EX21O', 'M-EQ-EX30U', 'M-EQ-EX30P', 'M-EQ-EX36C', 'M-EQ-EXLR', 'M-EQ-EXAMP', 'M-EQ-EXWH', 'M-EQ-HBRK', 'M-EQ-BKT1', 'M-EQ-VRIP'],
      drivers='Excavator prices depend mostly on size (tonnes), brand, year and working hours. Chinese brands (SANY, XCMG, LiuGong) cost much less new than CAT or Komatsu. Tokunbo (foreign-used) CAT machines hold their value well. Imported new machines move with the exchange rate. Check the hour meter, undercarriage wear and hydraulic leaks, and do a test dig before paying.'),
 dict(slug='bulldozers-loaders', name='Bulldozers & payloaders', h1='Price of bulldozers, payloaders and backhoes in Nigeria', q='How much is a bulldozer or payloader in Nigeria?',
      primary='M-EQ-DZ6U', codes=['M-EQ-SSLU', 'M-EQ-SSLN', 'M-EQ-BHLC', 'M-EQ-BHLP', 'M-EQ-BHLU', 'M-EQ-BHLL', 'M-EQ-WL16', 'M-EQ-WL30', 'M-EQ-WL50', 'M-EQ-WL50U', 'M-EQ-WL950', 'M-EQ-WL966', 'M-EQ-WLNU', 'M-EQ-DZ6U', 'M-EQ-DZ7G', 'M-EQ-DZ7R', 'M-EQ-DZ8U', 'M-EQ-DZ26N', 'M-EQ-DZ34N', 'M-EQ-DZ16N', 'M-EQ-DZLGP', 'M-EQ-ADT30', 'M-EQ-RDT40'],
      drivers='Older CAT D8H/D8K and 966 machines are still traded widely in Nigeria. New Chinese dozers and loaders (Shantui, Zoomlion, LiuGong, SDLG) cost less and come with a dealer warranty. On used machines, check the undercarriage, final drives, transmission and engine blow-by.'),
 dict(slug='road-construction-equipment', name='Road construction equipment', h1='Price of graders, rollers, pavers and asphalt plants in Nigeria', q='How much is a road roller or motor grader in Nigeria?',
      primary='M-EQ-GR14N', codes=['M-EQ-GR12N', 'M-EQ-GR14N', 'M-EQ-GR14U', 'M-EQ-GRCN', 'M-EQ-GRCAT', 'M-EQ-SDR12', 'M-EQ-SDR12U', 'M-EQ-TDR3', 'M-EQ-RR5', 'M-EQ-WBR', 'M-EQ-WBR1', 'M-EQ-PTR', 'M-EQ-PAVU', 'M-EQ-PAVN', 'M-EQ-AMP80', 'M-EQ-AMP160', 'M-EQ-BDIS', 'M-EQ-CHSP', 'M-EQ-MILL', 'M-EQ-LMRK', 'M-EQ-KERB', 'M-EQ-STAB'],
      drivers='Road plant is mostly imported, so new prices follow the exchange rate. Used CAT graders (12G, 140G) are common and cheap to maintain locally. Asphalt plants are quoted ex-works: budget for shipping, installation and commissioning.'),
 dict(slug='tipper-trucks', name='Tipper trucks & haulage', h1='Price of tipper trucks, low-beds and mixer trucks in Nigeria', q='How much is a Howo tipper truck in Nigeria?',
      primary='M-EQ-TIP30N', codes=['M-EQ-TIP30N', 'M-EQ-TIP30U', 'M-EQ-TIPMB', 'M-EQ-TIP10', 'M-EQ-THN', 'M-EQ-THU', 'M-EQ-LB80', 'M-EQ-LB100', 'M-EQ-FLATT', 'M-EQ-TM10N', 'M-EQ-TM10U', 'M-EQ-WTK', 'M-EQ-FBWN', 'M-EQ-KNCK', 'M-EQ-PU4X4', 'M-EQ-PU4U', 'M-EQ-BUS18', 'M-EQ-DUMP3'],
      drivers='Sinotruk Howo tippers dominate the Nigerian market. New prices vary with horsepower, axle and tyre count, and body size. On used trucks, check the customs papers and confirm the chassis and engine numbers.'),
 dict(slug='cranes', name='Cranes & forklifts', h1='Price of cranes and forklifts in Nigeria', q='How much is a crane in Nigeria?',
      primary='M-EQ-TC55U', codes=['M-EQ-TC25N', 'M-EQ-TC55U', 'M-EQ-TC55N', 'M-EQ-TC70N', 'M-EQ-TC80U', 'M-EQ-AT80U', 'M-EQ-AT90U', 'M-EQ-AT120U', 'M-EQ-TC400U', 'M-EQ-CC55U', 'M-EQ-CC150U', 'M-EQ-TWU', 'M-EQ-TWPN', 'M-EQ-TWCN', 'M-EQ-FL3D', 'M-EQ-FL3E', 'M-EQ-FL7', 'M-EQ-FL10', 'M-EQ-FL16', 'M-EQ-FL3U', 'M-EQ-TELU', 'M-EQ-HOIST', 'M-EQ-SCIS', 'M-EQ-BOOM', 'M-EQ-CHB5', 'M-EQ-GNTY'],
      drivers='Crane prices rise steeply with lifting capacity, and Grove all-terrain cranes cost more than Chinese truck cranes of the same size. Ask for the load chart, the last load test and the wire rope certificate before buying any used crane.'),
 dict(slug='generators', name='Generators & pumps', h1='Price of generators and pumps in Nigeria', q='How much is a 100kVA generator in Nigeria?',
      primary='M-EQ-G100', codes=['M-EQ-G10', 'M-EQ-G30', 'M-EQ-G50', 'M-EQ-G100', 'M-EQ-G150', 'M-EQ-G200', 'M-EQ-G250', 'M-EQ-G300', 'M-EQ-G500', 'M-EQ-G1000', 'M-EQ-P55', 'M-EQ-P10', 'M-EQ-LTWR', 'M-EQ-WGEN', 'M-EQ-DP4', 'M-EQ-DP6', 'M-EQ-SUB3', 'M-EQ-WPT', 'M-EQ-DTNK'],
      drivers='Generator prices depend on engine brand (Perkins, Cummins, Mikano, FG Wilson), alternator, whether the set is soundproof, and whether an ATS and installation are included. Size the generator to the real load plus motor starting currents.'),
 dict(slug='concrete-equipment', name='Concrete equipment', h1='Price of concrete batching plants, pumps and mixers in Nigeria', q='How much is a concrete batching plant in Nigeria?',
      primary='M-EQ-BP50', codes=['M-EQ-BP35', 'M-EQ-BP50', 'M-EQ-BP75', 'M-EQ-BP120', 'M-EQ-BPMOB', 'M-EQ-SILO', 'M-EQ-CP20', 'M-EQ-CP40', 'M-EQ-CP60', 'M-EQ-CP80', 'M-EQ-CP100', 'M-EQ-CPBM', 'M-EQ-MXPMP', 'M-EQ-SLMX', 'M-EQ-MX2B', 'M-EQ-VIBE', 'M-EQ-PTRW', 'M-EQ-FSAW', 'M-EQ-CORE', 'M-EQ-RCUT', 'M-EQ-RBND', 'M-EQ-RTHR'],
      drivers='Batching plant prices are for the plant only; foundations, installation, power supply and a weighbridge are extra. Pump prices depend on output (m3/h) and the length of delivery pipe supplied.'),
 dict(slug='block-making-machines', name='Block making machines', h1='Price of block making machines in Nigeria', q='How much is a block moulding machine in Nigeria?',
      primary='M-EQ-BMFT', codes=['M-EQ-BM2', 'M-EQ-BMEL', 'M-EQ-BMEGG', 'M-EQ-BMFT', 'M-EQ-BMHY', 'M-EQ-BMAUT', 'M-EQ-QT10', 'M-EQ-PANMX'],
      drivers='Locally fabricated block machines are cheap but slow. Hydraulic and automatic machines make denser, more uniform blocks at much higher output. Choose a machine that can meet NIS 87 strength requirements.'),
 dict(slug='quarry-equipment', name='Quarry & drilling equipment', h1='Price of stone crushers, drill rigs and compressors in Nigeria', q='How much is a stone crushing plant in Nigeria?',
      primary='M-EQ-CRU200', codes=['M-EQ-JAWS', 'M-EQ-JAWL', 'M-EQ-CRU200', 'M-EQ-CRU450', 'M-EQ-MOBCR', 'M-EQ-SCRN', 'M-EQ-CONV', 'M-EQ-WAGON', 'M-EQ-DTH', 'M-EQ-BHRG', 'M-EQ-BHRGU', 'M-EQ-AC750', 'M-EQ-AC375', 'M-EQ-AC750U', 'M-EQ-AC100', 'M-EQ-JKHM', 'M-EQ-EBRK'],
      drivers='Crushing plant prices depend on capacity (tonnes per hour) and on whether you buy a jaw crusher only or jaw plus cone with screens. Quarry licences, explosives permits and a power supply add to the cost.'),
 dict(slug='dredgers', name='Dredgers & marine equipment', h1='Price of dredgers and marine equipment in Nigeria', q='How much is a sand dredger in Nigeria?',
      primary='M-EQ-D12U', codes=['M-EQ-DJET', 'M-EQ-D8U', 'M-EQ-D12U', 'M-EQ-DCSDS', 'M-EQ-DCSD14', 'M-EQ-DCSD20', 'M-EQ-DPMP', 'M-EQ-SPUD', 'M-EQ-TUG', 'M-EQ-HOPB', 'M-EQ-CREW', 'M-EQ-OB200', 'M-EQ-SBGY'],
      drivers='Locally built jet-suction dredgers are cheap and widely used for sand mining. Cutter suction dredgers cost far more but can cut compacted material and pump much further. Budget for the discharge pipeline, pontoons and a support boat.'),
 dict(slug='piling-rigs', name='Piling rigs', h1='Price of piling rigs and pile hammers in Nigeria', q='How much is a piling rig in Nigeria?',
      primary='M-EQ-RIGU', codes=['M-EQ-RIGU', 'M-EQ-RIGN', 'M-EQ-VIBH', 'M-EQ-D62', 'M-EQ-HPU', 'M-EQ-SPDR'],
      drivers='Piling rigs are almost all imported; new Chinese rotary rigs cost far less than European ones. Budget for transport on low-beds, tooling (augers, casings, buckets) and a trained operator.'),
 dict(slug='survey-site-equipment', name='Survey & site equipment', h1='Price of survey instruments and site equipment in Nigeria', q='How much is a total station in Nigeria?',
      primary='M-EQ-TSTN', codes=['M-EQ-TSTN', 'M-EQ-GNSS', 'M-EQ-DRONE', 'M-EQ-ATLV', 'M-EQ-RAMM', 'M-EQ-PLT200', 'M-EQ-TOIL', 'M-EQ-CON40', 'M-EQ-HFRM', 'M-EQ-PRPS', 'M-EQ-ALFW', 'M-EQ-PWASH', 'M-EQ-HYDT'],
      drivers='Survey instruments are imported and priced in dollars. Buy from dealers who can calibrate and service them locally.'),
]

BUNGALOW = [("A01", 450), ("A02", 38), ("A04", 20), ("A07", 150), ("A08", 150), ("B01", 3.2), ("B02", 16), ("B06", 1.2), ("B12", 0.4),
            ("B07", 55), ("C03", 42), ("A05", 45), ("A06", 150), ("C01", 380), ("B03", 6), ("B09", 90), ("D01", 190), ("D02", 190),
            ("D04", 60), ("E01", 760), ("E02", 330), ("E03", 140), ("E04", 115), ("E06", 40), ("E07", 760), ("E08", 330), ("E20", 140),
            ("J01", 8), ("J03", 1), ("J04", 18), ("F01", 32), ("F02", 28), ("F23", 1), ("F03", 3), ("F04", 3), ("F05", 1), ("F12", 9), ("F14", 7)]
BUNGALOW_GFA = 140

EXTRA_CSS = """
.crumbs{font-size:14px;color:var(--muted);margin:18px 0 6px}
.crumbs a{color:var(--muted)}
main.static{display:block}
main.static h1{font-size:clamp(34px,5vw,56px);line-height:1;margin:6px 0 14px;max-width:22ch}
main.static h2{margin:40px 0 10px}
main.static h3{font:700 17px/1.35 var(--body);margin:20px 0 4px}
main.static p,main.static li{max-width:72ch}
main.static a.btn,.browse a.btn{color:var(--accent-ink)}
.meta{font-size:14px;color:var(--muted);margin:0}
.answer{font-size:18px;line-height:1.55;max-width:70ch;margin:0 0 10px}
.pricecard{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 28px;align-items:end;background:var(--board);color:var(--board-ink);border-top:6px solid var(--plant);border-radius:2px 2px 6px 6px;padding:22px 26px;margin:6px 0 18px;max-width:880px}
.pricecard .pc-k{margin:0;color:var(--board-muted);font-size:16px;grid-column:1/-1}
.pricecard .pc-v{margin:0;font:700 clamp(40px,6vw,64px)/1 var(--display);letter-spacing:-.005em}
.pricecard .pc-v small{font:600 20px var(--display);color:var(--board-muted);margin-left:6px}
.pricecard .pc-r{margin:0;color:var(--board-muted);font-size:15px;text-align:right;max-width:34ch}
.pricecard .pc-r b{color:var(--board-ink)}
.pricecard .btn{background:var(--plant);color:var(--plant-ink)!important;grid-column:1/-1;justify-self:start;margin-top:10px}
.linkgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:0;margin:14px 0;padding:0;list-style:none;background:var(--surface);border:1px solid var(--line);border-radius:6px;overflow:hidden}
.linkgrid li{max-width:none;box-shadow:0 0 0 .5px var(--line)}
.linkgrid a{display:block;height:100%;padding:13px 16px;background:var(--surface);color:var(--ink);text-decoration:none}
.linkgrid a:hover{background:var(--accent-soft)}
.linkgrid b{font:600 18px/1.2 var(--display);display:block}
.linkgrid small{display:block;color:var(--muted);font-size:14px;margin-top:2px}
.cite{font-size:14px;color:var(--muted);border-top:1px solid var(--line);padding-top:12px;margin-top:36px}
.btnlink{margin:8px 0}
.faq h3{margin-top:16px}
td.n b{font-weight:700}
.browse{margin-top:44px}
.browse h2{margin:34px 0 4px}
@media (max-width:640px){.pricecard{grid-template-columns:1fr;padding:20px}.pricecard .pc-r{text-align:left}}
"""


class Site:
    def __init__(self, root, data, cfg):
        self.root, self.D, self.cfg = root, data, cfg
        self.E = Engine(data)
        self.P = data["params"]
        self.upd = data["meta"]["updated"]
        d = dt.date.fromisoformat(self.upd)
        self.date_long = f"{d.day} {d.strftime('%B %Y')}"
        self.mon = d.strftime("%b %Y")
        self.R = {r["c"]: r for r in data["resources"]}
        self.items = {i["c"]: i for i in data["items"]}
        self.locs = data["locations"]
        self.pages = []            # (path, priority)
        self.item_path = {i["c"]: f"rates/{i['c'].lower()}-{slug(i['d'], 56)}/" for i in data["items"]}
        self.hub_of = {}
        for h in HUBS:
            for c in h["codes"]:
                self.hub_of.setdefault(c, h)

    # -------------------------------------------------------------- helpers
    def out(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(text)

    def change(self, r):
        if not r.get("pr") or "r" not in r: return ""
        ch = (r["r"] - r["pr"]) / r["pr"]
        if abs(ch) < 0.0005: return '<span class="muted">no change</span>'
        return f'<span class="{"up" if ch > 0 else "down"}">{"▲" if ch > 0 else "▼"} {ch*100:.1f}%</span>'

    def org(self):
        return {"@type": "Organization", "@id": BASE + "/#org", "name": "Buildocrat Property Technologies Ltd", "alternateName": "Buildocrat",
                "url": "https://buildocrat.store", "logo": BASE + "/icons/icon-512.png", "email": "buildocrat@gmail.com",
                "telephone": "+234-701-802-4292",
                "address": {"@type": "PostalAddress", "streetAddress": "No 30 Anthony Enahoro Street, Utako", "addressLocality": "Abuja",
                            "addressRegion": "FCT", "addressCountry": "NG"},
                "identifier": {"@type": "PropertyValue", "propertyID": "CAC RC", "value": "7019619"},
                "founder": {"@type": "Person", "name": "Engr. Kola Ibrahim", "jobTitle": "Founder and Managing Director",
                            "honorificSuffix": "MNSE, R.COREN, PMP", "sameAs": ["https://www.linkedin.com/in/kolaibrahim/"]},
                "areaServed": {"@type": "Country", "name": "Nigeria"},
                "knowsAbout": ["construction cost estimating", "building material prices in Nigeria", "bill of quantities", "construction material price locking"]}

    def website(self):
        return {"@type": "WebSite", "@id": BASE + "/#website", "url": BASE + "/", "name": "Nigeria Construction Rate Book",
                "alternateName": "Buildocrat Rate Book", "inLanguage": "en-NG", "publisher": {"@id": BASE + "/#org"}}

    def dataset(self):
        D = self.D
        return {"@type": "Dataset", "@id": BASE + "/#dataset", "name": "Nigeria Construction Rate Book - building material prices, labour, plant hire and BoQ unit rates",
                "description": (f"Weekly-updated construction cost data for Nigeria: {len(D['resources'])} building material prices, {len(D['labour'])} labour grades, "
                                f"{len(D['plant'])} plant and equipment hire rates and {len(D['items'])} first-principles bill of quantities (BoQ) unit rates, "
                                f"with location factors for {len(self.locs)} Nigerian locations. Abuja base prices in naira (NGN)."),
                "url": BASE + "/data/", "sameAs": BASE + "/", "creator": {"@id": BASE + "/#org"}, "publisher": {"@id": BASE + "/#org"},
                "license": LICENSE_URL, "isAccessibleForFree": True, "inLanguage": "en-NG",
                "datePublished": LAUNCH, "dateModified": self.upd, "temporalCoverage": f"{LAUNCH}/..",
                "spatialCoverage": {"@type": "Place", "name": "Nigeria", "address": {"@type": "PostalAddress", "addressCountry": "NG"}},
                "keywords": ["Nigeria", "construction costs", "building materials prices", "cement price", "iron rod price", "BoQ rates", "unit rates", "labour rates", "equipment hire", "construction equipment prices", "excavator price", "generator price", "quantity surveying"],
                "variableMeasured": ["Material price (NGN)", "Labour daily wage (NGN)", "Plant hire day rate (NGN)", "BoQ unit rate (NGN)"],
                "measurementTechnique": "Dated market price research; first-principles rate build-ups (materials x waste + labour hours + plant days)",
                "distribution": [
                    {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": BASE + "/data/rate-data.json"},
                    {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE + "/data/materials.csv"},
                    {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE + "/data/composite-rates.csv"},
                    {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE + "/data/labour.csv"},
                    {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE + "/data/plant.csv"}]}

    def analytics(self):
        """Analytics tags, only when IDs are set in site-config.json. Also tracks key actions on every page."""
        ga = (self.cfg.get("ga4_measurement_id") or "").strip()
        cf = (self.cfg.get("cloudflare_web_analytics_token") or "").strip()
        out = ""
        if ga:
            out += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={e(ga)}"></script>\n'
                    f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{e(ga)}");</script>\n')
        if cf:
            out += f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\": \"{e(cf)}\"}}'></script>\n"
        if ga:
            out += """<script>document.addEventListener("click",function(ev){var a=ev.target.closest&&ev.target.closest("a");if(!a||typeof gtag!=="function")return;var h=a.getAttribute("href")||"";
if(h.indexOf("wa.me/")>-1)gtag("event","whatsapp_click",{link_text:(a.textContent||"").trim().slice(0,60),page_path:location.pathname});
else if(/\\.(csv|json|txt)$/.test(h))gtag("event","data_download",{file_name:h.split("/").pop()});
else if(a.classList.contains("btn")&&h.indexOf("http")!==0)gtag("event","open_rate_book",{page_path:location.pathname});},true);</script>
"""
        return out

    def head_meta(self, url, title, desc, extra_graph=()):
        g = [self.org(), self.website()] + list(extra_graph)
        v = self.cfg.get("google_site_verification"); b = self.cfg.get("bing_site_verification")
        ver = (f'<meta name="google-site-verification" content="{e(v)}">\n' if v else "") + (f'<meta name="msvalidate.01" content="{e(b)}">\n' if b else "")
        return f"""<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en-NG" href="{url}">
<link rel="alternate" hreflang="x-default" href="{url}">
<meta property="og:site_name" content="Buildocrat Rate Book">
<meta property="og:locale" content="en_NG">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Nigeria Construction Rate Book by Buildocrat - prices as at {self.date_long}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{BASE}/og.png">
<meta name="author" content="Buildocrat Property Technologies Ltd">
<meta name="theme-color" content="#0C6A4C">
{ver}<link rel="alternate" type="application/atom+xml" title="Buildocrat Rate Book - weekly price updates" href="{BASE}/feed.xml">
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": g}, ensure_ascii=False)}</script>
{self.analytics()}"""

    def nav(self, pre, current=""):
        links = [("prices/", "Material prices"), ("prices/#equipment", "Equipment"), ("rates/", "BoQ rates"), ("labour/", "Labour"),
                 ("plant/", "Plant hire"), ("locations/", "Locations"), ("guides/cost-to-build-3-bedroom-bungalow/", "Cost guide"), ("about/", "About")]
        cur = ' aria-current="page"'
        return '<nav class="sitenav" aria-label="Site">' + "".join(
            f'<a href="{pre}{h}"{cur if h == current else ""}>{t}</a>' for h, t in links) + "</nav>"

    def masthead(self, pre, current=""):
        return f"""<header class="mast">
    <a class="wordmark" href="{pre}" aria-label="Buildocrat Rate Book home"><b>Build<span>ocrat</span></b><small>Rate Book</small></a>
    {self.nav(pre, current)}
    <div class="actions"><a class="wa" href="https://wa.me/2347018024292?text=Hello%20Buildocrat%2C%20I%27d%20like%20to%20lock%20prices%20for%20my%20project." target="_blank" rel="noopener">WhatsApp us</a></div>
  </header>"""

    def footer(self, pre):
        return f"""<footer>
    <div class="fbrand">Build<span>ocrat</span></div>
    <div>The Nigeria Construction Rate Book is published by Buildocrat. Prices as at {self.date_long}; key prices are re-checked every week against dated market sources. See the <a href="{pre}updates/">update log</a>, <a href="{pre}methodology/">methodology</a>, <a href="{pre}data/">data downloads</a> and <a href="{pre}privacy/">privacy notice</a>.</div>
    <div class="fcorp">Buildocrat Property Technologies Ltd (RC 7019619), No 30 Anthony Enahoro Street, Utako, Abuja. WhatsApp <span class="sel">+234 701 802 4292</span>, email <span class="sel">buildocrat@gmail.com</span>. <a href="{pre}about/">About Buildocrat</a></div>
    <div>Indicative market rates for budgeting and first-pass BoQ pricing. Confirm LOW-confidence items with at least three supplier quotes before relying on them in a tender.</div>
  </footer>"""

    def page(self, path, title, desc, h1, body, crumbs, graph=(), faq=None, priority="0.6", current=""):
        depth = path.count("/")
        pre = "../" * depth
        url = BASE + "/" + path
        items = [{"@type": "ListItem", "position": 1, "name": "Rate Book", "item": BASE + "/"}]
        crumb_html = f'<a href="{pre}">Rate Book</a>'
        for i, (name, cp) in enumerate(crumbs, 2):
            items.append({"@type": "ListItem", "position": i, "name": name, "item": BASE + "/" + cp})
            crumb_html += f" &rsaquo; " + (f'<a href="{pre}{cp}">{e(name)}</a>' if cp != path else e(name))
        g = [{"@type": "WebPage", "@id": url, "url": url, "name": title, "description": desc, "isPartOf": {"@id": BASE + "/#website"},
              "publisher": {"@id": BASE + "/#org"}, "inLanguage": "en-NG", "datePublished": LAUNCH, "dateModified": self.upd,
              "primaryImageOfPage": BASE + "/og.png", "breadcrumb": {"@id": url + "#breadcrumb"}},
             {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": items}] + list(graph)
        faq_html = ""
        if faq:
            g.append({"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in faq]})
            faq_html = '<section class="faq" id="faq"><h2>Frequently asked questions</h2>' + "".join(f"<h3>{e(q)}</h3><p>{a}</p>" for q, a in faq) + "</section>"
        doc = f"""<!doctype html>
<html lang="en-NG">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
{self.head_meta(url, title, desc, g)}
<link rel="manifest" href="{pre}manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="{pre}icons/icon-192.png">
<link rel="apple-touch-icon" href="{pre}icons/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Source+Sans+3:wght@400;600;700&display=swap">
<link rel="stylesheet" href="{pre}assets/site.css">
</head>
<body>
<div class="wrap">
  {self.masthead(pre, current)}
  <nav class="crumbs" aria-label="Breadcrumb">{crumb_html}</nav>
  <main class="static">
    <p class="meta">Prices as at {self.date_long}, checked weekly. Base location Abuja.</p>
    <h1>{h1}</h1>
{body}
{faq_html}
    <p class="cite"><b>How to cite:</b> Buildocrat, <i>Nigeria Construction Rate Book</i>, {BASE}/{path}, prices as at {self.date_long}.</p>
  </main>
  {self.footer(pre)}
</div>
<script>if("serviceWorker" in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("{pre}sw.js").catch(()=>{{}}));</script>
</body>
</html>
"""
        self.out(os.path.join(path, "index.html"), doc)
        self.pages.append((path, priority))

    def link_item(self, pre, c, text=None):
        return f'<a href="{pre}{self.item_path[c]}">{e(text or self.items[c]["d"])}</a>'

    def table(self, head, rows, numeric=(), hide=()):
        def cl(i):
            c = (["n"] if i in numeric else []) + (["hm"] if i in hide else [])
            return f' class="{" ".join(c)}"' if c else ""
        h = "".join(f'<th{cl(i)} scope="col">{x}</th>' for i, x in enumerate(head))
        b = "".join("<tr>" + "".join(f'<td{cl(i)}>{x}</td>' for i, x in enumerate(r)) + "</tr>" for r in rows)
        return f'<div class="tablebox"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

    def primary_sentence(self, code, loc=None):
        r = self.R[code]; v = self.E.rate(code)
        return f"{naira(v)} per {u(r['u'])}"

    # -------------------------------------------------------------- pages
    def build_hubs(self):
        for h in HUBS:
            path = f"prices/{h['slug']}/"; pre = "../../"
            p = self.R[h["primary"]]; pv = self.E.rate(h["primary"])
            lo, hi = self.E.rate(h["primary"], "lo"), self.E.rate(h["primary"], "hi")
            chg = ""
            if p.get("pr"):
                ch = (p["r"] - p["pr"]) / p["pr"]
                chg = f" That is {'up' if ch > 0 else 'down'} {abs(ch)*100:.1f}% from {naira(p['pr'])} at the previous update." if abs(ch) >= 0.0005 else " That is unchanged since the previous update."
            others = [c for c in h["codes"] if c != h["primary"]][:4]
            oth = "; ".join(f"{e(self.R[c]['d'])}: {naira(self.E.rate(c))} per {u(self.R[c]['u'])}" for c in others)
            answer = (f"As at {self.date_long}, <b>{e(p['d'])}</b> costs about <b>{naira(pv)} per {u(p['u'])}</b> in Abuja "
                      f"(market range {naira(lo)} to {naira(hi)}).{chg} Other lines: {oth}.")
            rows = []
            for c in h["codes"]:
                r = self.R[c]
                rows.append([f"<b>{e(r['d'])}</b>", u(r["u"]), f"<b>{naira(self.E.rate(c))}</b>",
                             f"{naira(self.E.rate(c,'lo'))} - {naira(self.E.rate(c,'hi'))}", self.change(r) or "-",
                             f'<span class="chip c-{r["conf"]}">{r["conf"].capitalize()}</span>', e(r.get("ev") or "derived")])
            tbl = self.table(["Item", "Unit", "Abuja price", "Range", "Change", "Confidence", "Evidence date"], rows, numeric=(2, 3), hide=(1, 3, 4, 6))
            loc_rows = [[e(n), f"{naira(pv*fm)}", f"{fm:.2f}"] for n, fm, fl, fp in self.locs]
            loc_tbl = self.table(["Location", f"Estimated price per {u(p['u'])}", "Materials factor"], loc_rows, numeric=(1, 2))
            # usage in build-ups
            uses = []
            for it in self.D["items"]:
                for t, c, q in it["l"]:
                    if t == "M" and c in h["codes"]:
                        r = self.R[c]; qq = q * (1 + (r.get("w") or 0)); res = self.E.item(it)
                        cost = qq * self.E.rate(c)
                        uses.append((it["c"], c, qq, cost, res["net"]))
            use_html = ""
            if uses:
                urows = [[self.link_item(pre, ic), f"{qq:.3g} {u(self.R[c]['u'])} per {u(self.items[ic]['u'])}", naira(cost), f"{cost/net*100:.0f}%" if net else "-"]
                         for ic, c, qq, cost, net in uses[:14]]
                use_html = (f"<h2>How much {e(h['name'].lower())} each item of work uses</h2><p>These quantities come from Buildocrat's rate build-ups and include a waste allowance. "
                            f"They show how a change in the {e(h['name'].lower())} price moves the cost of finished work.</p>"
                            + self.table(["Item of work", "Quantity used", "Cost in the rate", "Share of rate"], urows, numeric=(2, 3)))
            elif h["slug"] == "diesel-petrol":
                prow = []
                for pl in self.D["plant"]:
                    if pl.get("fuel") and pl["lpd"] >= 80:
                        pp = self.E.plant_parts(pl)
                        prow.append([e(pl["d"]), f"{pl['lpd']} L", naira(pp["fuel"]), naira(pp["total"])])
                use_html = ("<h2>What diesel adds to plant hire</h2><p>Buildocrat's all-in plant rates include fuel at the current pump price, so a diesel price change moves every rate that uses machines.</p>"
                            + self.table(["Plant", "Fuel per day", "Fuel + lubricants per day", "All-in day rate"], prow[:14], numeric=(1, 2, 3)))
            srcs = sorted({self.R[c]["src"] for c in h["codes"] if not self.R[c].get("k")})
            card = (f'<div class="pricecard"><p class="pc-k">{e(p["d"])}, Abuja</p><p class="pc-v">{naira(pv)}<small>per {u(p["u"])}</small></p>'
                    f'<p class="pc-r">Market range <b>{naira(lo)}</b> to <b>{naira(hi)}</b> as at {self.date_long}.</p>'
                    f'<a class="btn" href="{pre}">Price a whole BoQ in the rate book</a></div>')
            body = f"""    {card}
    <p class="answer">{answer}</p>
    <h2>{e(h['name'])} prices in Nigeria ({self.mon})</h2>
    {tbl}
    <p class="muted">Prices are Abuja market prices, delivered within the city, excluding VAT unless stated. "Change" compares with the previous weekly update.</p>
    <h2>{e(h['name'])} prices by location</h2>
    <p>Estimated by applying Buildocrat's materials location factor to the Abuja price. Always confirm with a local supplier.</p>
    {loc_tbl}
    {use_html}
    <h2>What affects the price</h2>
    <p>{e(h['drivers'])}</p>
    <h2>Sources</h2>
    <ul>{''.join(f'<li>{e(s)}</li>' for s in srcs)}</ul>"""
            lagos = next(l for l in self.locs if l[0] == "Lagos"); ph = next(l for l in self.locs if l[0] == "Port Harcourt")
            faq = [(h["q"], f"As at {self.date_long}, {e(p['d'])} costs about {naira(pv)} per {u(p['u'])} in Abuja, within a market range of {naira(lo)} to {naira(hi)}, according to Buildocrat's Nigeria Construction Rate Book."),
                   (f"How much does it cost in Lagos and Port Harcourt?", f"Applying Buildocrat's location factors, the same item is estimated at about {naira(pv*lagos[1])} in Lagos and {naira(pv*ph[1])} in Port Harcourt."),
                   ("What affects the price?", e(h["drivers"])),
                   ("How often is this price updated?", f"Buildocrat re-checks key prices every Monday against dated market sources. This page was last updated on {self.date_long}.")]
            title = f"{h['h1'].replace(' today','')} ({self.mon}) - {naira(pv)} per {u(p['u'])} | Buildocrat"
            desc = f"{h['name']} prices in Nigeria as at {self.date_long}: {p['d']} about {naira(pv)} per {u(p['u'])} in Abuja. Brand and size prices, city estimates and how much each item of work uses. Updated weekly."
            eq = h["primary"].startswith("M-EQ-")
            crumbs = [("Equipment prices", "prices/#equipment"), (h["name"], path)] if eq else [("Material prices", "prices/"), (h["name"], path)]
            self.page(path, title, desc[:300], e(h["h1"]), body, crumbs, faq=faq, priority="0.9", current="prices/#equipment" if eq else "prices/")

    def build_prices_index(self):
        path = "prices/"; pre = "../"
        card = lambda h: f'<li><a href="{pre}prices/{h["slug"]}/"><b>{e(h["name"])}</b><small>{naira(self.E.rate(h["primary"]))} per {u(self.R[h["primary"]]["u"])}</small></a></li>'
        cards = "".join(card(h) for h in HUBS if not h["primary"].startswith("M-EQ-"))
        eqcards = "".join(card(h) for h in HUBS if h["primary"].startswith("M-EQ-"))
        groups = {}
        for r in self.D["resources"]:
            groups.setdefault(r["g"], []).append(r)
        parts = []
        for g, rs in groups.items():
            rows = [[f'<code>{r["c"]}</code>', (f'<a href="{pre}prices/{self.hub_of[r["c"]]["slug"]}/">{e(r["d"])}</a>' if r["c"] in self.hub_of else e(r["d"])),
                     u(r["u"]), f"<b>{naira(self.E.rate(r['c']))}</b>", f"{naira(self.E.rate(r['c'],'lo'))} - {naira(self.E.rate(r['c'],'hi'))}",
                     f'<span class="chip c-{r["conf"]}">{r["conf"].capitalize()}</span>'] for r in rs]
            parts.append(f'<h2 id="{slug(g)}">{e(g.title() if g.isupper() else g)}</h2>' + self.table(["Code", "Material", "Unit", "Price (Abuja)", "Range", "Confidence"], rows, numeric=(3, 4)))
        body = f"""    <p class="answer">Current prices for {len(self.D['resources'])} building materials, tools and construction equipment in Nigeria as at {self.date_long}, from cement, iron rods, blocks, sand and granite to excavators, tipper trucks, cranes, generators and roofing, tiles, paint, electrical and plumbing items. Prices are Abuja market prices delivered within the city; use the <a href="{pre}locations/">location pages</a> for other cities.</p>
    <h2>Building materials</h2><ul class="linkgrid">{cards}</ul>
    <h2 id="equipment">Construction equipment for sale</h2>
    <p>Purchase prices for new and used (tokunbo) machines. For daily hire rates see <a href="{pre}plant/">plant hire</a>.</p>
    <ul class="linkgrid">{eqcards}</ul>
    <h2>Full price list</h2>
    {''.join(parts)}"""
        self.page(path, f"Building materials prices in Nigeria ({self.mon}) - {len(self.D['resources'])} items | Buildocrat",
                  f"Current prices of {len(self.D['resources'])} building materials and construction equipment in Nigeria as at {self.date_long}: cement, iron rods, blocks, sand, granite, excavators, tippers, generators, roofing sheets, tiles, paint, timber, cables and more. Updated weekly.",
                  "Building materials prices in Nigeria", body, [("Material prices", path)], priority="0.9", current="prices/")

    def build_rate_pages(self):
        mk = self.E.markup(); P = self.P
        by_sec = {}
        for it in self.D["items"]:
            by_sec.setdefault(it["s"], []).append(it)
        for it in self.D["items"]:
            path = self.item_path[it["c"]]; pre = "../../"
            res = self.E.item(it); unit = u(it["u"])
            lines = [[{"M": "Material", "L": "Labour (hours)", "P": "Plant (days)"}[x["t"]],
                      (f'<a href="{pre}prices/{self.hub_of[x["code"]]["slug"]}/">{e(x["d"])}</a>' if x["code"] in self.hub_of else e(x["d"])),
                      f"{x['q']:.4g} {e(u(x['u']) if x['t']=='M' else ('h' if x['t']=='L' else 'day'))}",
                      f"{x['w']*100:.0f}%" if x["w"] else "-", naira(x["rate"]), naira(x["cost"])] for x in res["lines"]]
            lines += [["", "<b>Materials</b>", "", "", "", naira(res["m"])], ["", "<b>Labour</b>", "", "", "", naira(res["l"])],
                      ["", "<b>Plant</b>", "", "", "", naira(res["p"])], ["", f"<b>Net unit rate per {unit}</b>", "", "", "", f"<b>{naira(res['net'])}</b>"]]
            bu = self.table(["Resource type", "Resource", "Quantity per unit", "Waste", "Rate", "Cost"], lines, numeric=(2, 3, 4, 5), hide=(0, 3))
            lrows = []
            for n, fm, fl, fp in self.locs:
                r2 = self.E.item(it, (fm, fl, fp))
                lrows.append([e(n), naira(r2["net"]), naira(r2["net"] * mk)])
            ltbl = self.table(["Location", f"Net rate per {unit}", "Tender rate incl. OH&P and VAT"], lrows, numeric=(1, 2))
            rel = [x for x in by_sec[it["s"]] if x["c"] != it["c"]]
            rel_html = "".join(f'<li><a href="{pre}{self.item_path[x["c"]]}"><b>{x["c"]}</b> {e(x["d"])}<small>{naira(self.E.item(x)["net"])} per {u(x["u"])}</small></a></li>' for x in rel[:18])
            short = it["d"][0].lower() + it["d"][1:]
            answer = (f"As at {self.date_long}, the net unit rate for <b>{e(short)}</b> is <b>{naira(res['net'])} per {unit}</b> in Abuja: "
                      f"{naira(res['m'])} materials, {naira(res['l'])} labour and {naira(res['p'])} plant. With overheads ({P['oh']*100:g}%), contingency ({P['cont']*100:g}%), "
                      f"profit ({P['profit']*100:g}%) and VAT ({P['vat']*100:g}%) the tender rate is about <b>{naira(res['net']*mk)} per {unit}</b>.")
            lag = next(l for l in self.locs if l[0] == "Lagos"); lr = self.E.item(it, tuple(lag[1:]))
            mats = ", ".join(sorted({x["d"].split(",")[0] for x in res["lines"] if x["t"] == "M"})[:6]) or "no materials"
            labs = ", ".join(sorted({x["d"].replace(" - all-in", "") for x in res["lines"] if x["t"] == "L"})) or "no labour"
            plants = ", ".join(sorted({x["d"].replace(" - all-in wet", "") for x in res["lines"] if x["t"] == "P"})) or "no plant"
            faq = [(f"How much does {short} cost per {unit} in Nigeria?", f"About {naira(res['net'])} per {unit} net in Abuja as at {self.date_long}, or about {naira(res['net']*mk)} per {unit} as a tender rate including overheads, contingency, profit and VAT (Buildocrat Nigeria Construction Rate Book)."),
                   (f"What is the rate in Lagos?", f"Applying Buildocrat's Lagos location factors, the net rate is about {naira(lr['net'])} per {unit} and the tender rate about {naira(lr['net']*mk)} per {unit}."),
                   ("What does the rate include?", f"Materials ({e(mats)}) with waste allowances; labour ({e(labs)}) at all-in rates including feeding, transport, idle time and statutory costs; and plant ({e(plants)}) including fuel and operator. Overheads, profit and VAT are excluded from the net rate." + (f" Scope note: {e(it['n'])}" if it.get("n") else ""))]
            card = (f'<div class="pricecard"><p class="pc-k">Net unit rate in Abuja, excluding overheads, profit and VAT</p><p class="pc-v">{naira(res["net"])}<small>per {unit}</small></p>'
                    f'<p class="pc-r">Tender rate about <b>{naira(res["net"]*mk)}</b> per {unit} with overheads, contingency, profit and VAT.</p>'
                    f'<a class="btn" href="{pre}">Price a BoQ with this rate</a></div>')
            body = f"""    {card}
    <p class="answer">{answer}</p>
    <h2>Rate build-up (Abuja, {self.mon})</h2>
    {bu}
    {f'<p class="muted">Scope note: {e(it["n"])}</p>' if it.get("n") else ''}
    <h2>Rate by location</h2>
    <p>Materials, labour and plant are adjusted separately with Buildocrat's location factors.</p>
    {ltbl}
    <h2>Related {e(sec_name(it['s']).lower())} rates</h2>
    <ul class="linkgrid">{rel_html}</ul>"""
            title = f"{it['d'][:70].rstrip(' ,')} - cost per {unit} in Nigeria ({self.mon}) | Buildocrat"
            desc = f"{it['d']}: {naira(res['net'])} per {unit} net in Abuja as at {self.date_long} ({naira(res['net']*mk)} tender rate). Full rate build-up and rates for 12 Nigerian locations."
            self.page(path, title, desc[:300], f"{e(it['d'])}: cost per {unit} in Nigeria", body,
                      [("BoQ rates", "rates/"), (f"{it['c']}", path)], faq=faq, priority="0.7", current="rates/")

    def build_rates_index(self):
        path = "rates/"; pre = "../"
        by_sec = {}
        for it in self.D["items"]:
            by_sec.setdefault(it["s"], []).append(it)
        parts = []; toc = []
        for s in sorted(by_sec):
            sid = slug(sec_name(s)); toc.append(f'<li><a href="#{sid}"><b>{e(sec_name(s))}</b><small>{len(by_sec[s])} rates</small></a></li>')
            rows = []
            for it in sorted(by_sec[s], key=lambda x: x["c"]):
                r = self.E.item(it)
                rows.append([f"<code>{it['c']}</code>", self.link_item(pre, it["c"]), u(it["u"]), naira(r["m"]), naira(r["l"]), naira(r["p"]), f"<b>{naira(r['net'])}</b>"])
            parts.append(f'<h2 id="{sid}">{e(sec_name(s))}</h2>' + self.table(["Code", "Item", "Unit", "Materials", "Labour", "Plant", "Net rate"], rows, numeric=(3, 4, 5, 6)))
        body = f"""    <p class="answer">{len(self.D['items'])} first-principles bill of quantities (BoQ) unit rates for Nigeria as at {self.date_long}, covering earthworks, concrete, reinforcement, formwork, blockwork, roofing, finishes, doors and windows, electrical, plumbing, steelwork, waterproofing, roads and drainage. Rates are net (Abuja) and show the materials, labour and plant split. Open any item for its full build-up and rates in 12 locations.</p>
    <ul class="linkgrid">{''.join(toc)}</ul>
    {''.join(parts)}"""
        self.page(path, f"BoQ unit rates in Nigeria ({self.mon}) - {len(self.D['items'])} construction rates | Buildocrat",
                  f"{len(self.D['items'])} construction unit rates for pricing bills of quantities in Nigeria as at {self.date_long}: concrete, blockwork, rebar, formwork, roofing, plastering, tiling, painting, MEP, roads. Full build-ups; updated weekly.",
                  "Construction unit rates for BoQs in Nigeria", body, [("BoQ rates", path)], priority="0.9", current="rates/")

    def build_labour(self):
        path = "labour/"; pre = "../"
        lag, ph, kano = [next(l for l in self.locs if l[0] == n) for n in ("Lagos", "Port Harcourt", "Kano")]
        rows = []
        for l in self.D["labour"]:
            day = self.E.lab_day(l)
            wage = f"{naira(l['mon'])} / month" if l["cat"] == "Staff" else f"{naira(l['day'])} / day"
            rng = "-" if l["cat"] == "Staff" else f"{naira(l['lo'])} - {naira(l['hi'])}"
            rows.append([e(l["d"]), e(l["cat"]), wage, rng, f"<b>{naira(day)}</b>", naira(day * lag[2]), naira(day * ph[2]), naira(day * kano[2])])
        tbl = self.table(["Trade / grade", "Type", "Wage (Abuja)", "Range", "All-in day (Abuja)", "Lagos", "Port Harcourt", "Kano"], rows, numeric=(2, 3, 4, 5, 6, 7))
        L = {l["c"]: l for l in self.D["labour"]}
        def w(c): return L[c]
        faq = [("How much is a bricklayer (mason) paid per day in Nigeria?", f"About {naira(w('L-MAS')['day'])} a day in Abuja (range {naira(w('L-MAS')['lo'])} to {naira(w('L-MAS')['hi'])}) as at {self.date_long}; about {naira(w('L-MAS')['day']*lag[2])} in Lagos."),
               ("How much is a labourer paid per day in Nigeria?", f"About {naira(w('L-LAB')['day'])} a day in Abuja (range {naira(w('L-LAB')['lo'])} to {naira(w('L-LAB')['hi'])})."),
               ("How much do carpenters, iron benders and tilers charge per day?", f"In Abuja: carpenter about {naira(w('L-CAR')['day'])}, iron bender about {naira(w('L-IRB')['day'])}, tiler about {naira(w('L-TIL')['day'])}, electrician about {naira(w('L-ELE')['day'])} and plumber about {naira(w('L-PLU')['day'])} per day."),
               ("What is the 'all-in' labour rate?", f"The daily wage plus {self.P['craftUplift']*100:.0f}% for feeding, transport, non-productive time, statutory cover and small tools. It is the true cost to a contractor, and the rate used in Buildocrat's BoQ build-ups."),
               ("How much is a site engineer paid in Nigeria?", f"Buildocrat uses {naira(w('L-SEN')['mon'])} a month for a COREN-registered site engineer in Abuja, before on-costs of {self.P['staffOncost']*100:.1f}% (pension, NSITF, ITF, HMO and leave).")]
        body = f"""    <p class="answer">As at {self.date_long}, a mason in Abuja earns about <b>{naira(w('L-MAS')['day'])} a day</b>, a labourer about <b>{naira(w('L-LAB')['day'])}</b>, a carpenter about <b>{naira(w('L-CAR')['day'])}</b> and an electrician about <b>{naira(w('L-ELE')['day'])}</b>. Buildocrat's all-in rates add {self.P['craftUplift']*100:.0f}% for feeding, transport, idle time, statutory costs and tools. This page lists {len(self.D['labour'])} trades, plant operators and site staff grades with estimates for Lagos, Port Harcourt and Kano.</p>
    <h2>Construction labour rates in Nigeria ({self.mon})</h2>
    {tbl}
    <p class="muted">Staff are shown as monthly salaries; their all-in day = salary / {self.P['dpm']} x (1 + {self.P['staffOncost']*100:.1f}% on-costs). City columns apply Buildocrat's labour location factors.</p>"""
        self.page(path, f"Construction labour rates in Nigeria ({self.mon}) - daily pay by trade | Buildocrat",
                  f"Daily pay for masons, labourers, carpenters, iron benders, electricians, plumbers, tilers and painters in Nigeria as at {self.date_long}, plus operators and site staff salaries. Abuja, Lagos, Port Harcourt, Kano.",
                  "Construction labour rates in Nigeria: daily pay by trade", body, [("Labour rates", path)], faq=faq, priority="0.85", current="labour/")

    def build_plant(self):
        path = "plant/"; pre = "../"
        rows = []; groups = {}
        for p in self.D["plant"]:
            groups.setdefault(p["g"], []).append(p)
        parts = []
        for g, ps in groups.items():
            rows = []
            for p in ps:
                x = self.E.plant_parts(p)
                rows.append([e(p["d"]), naira(p["dry"]), f"{naira(p['lo'])} - {naira(p['hi'])}", f"{p['lpd']} L" if p.get("fuel") else "-", naira(x["fuel"]), naira(x["op"]), f"<b>{naira(x['total'])}</b> / {e(p['u'])}", e(p.get("out") or ""), f'<span class="chip c-{p["conf"]}">{p["conf"]}</span>'])
            parts.append(f"<h2>{e(g.title() if g.isupper() else g)}</h2>" + self.table(["Plant", "Dry hire / day", "Range", "Fuel", "Fuel + lube", "Operator", "All-in", "Typical output", "Confidence"], rows, numeric=(1, 2, 3, 4, 5, 6)))
        Pl = {p["c"]: p for p in self.D["plant"]}
        def a(c): return naira(self.E.plant_parts(Pl[c])["total"])
        faq = [("How much does it cost to hire an excavator per day in Nigeria?", f"A 20-22 tonne excavator (CAT 320 class) hires for about {naira(Pl['P-EXC20']['dry'])} a day dry in Abuja as at {self.date_long}. With about {Pl['P-EXC20']['lpd']} litres of diesel and an operator, the all-in cost is about {a('P-EXC20')} a day. Mobilisation by low-bed is extra."),
               ("How much is bulldozer hire per day in Nigeria?", f"A D7-class bulldozer is about {naira(Pl['P-DZ7']['dry'])} a day dry, or about {a('P-DZ7')} all-in with fuel and operator."),
               ("How much is a backhoe (JCB) per day?", f"About {naira(Pl['P-BHL']['dry'])} a day dry, about {a('P-BHL')} all-in."),
               ("How much is a 25-tonne crane per day?", f"About {naira(Pl['P-CRN']['dry'])} a day dry, about {a('P-CRN')} all-in."),
               ("Why are Buildocrat's all-in plant rates higher than hire quotes?", "Hire quotes are often dry (machine only). The all-in rate adds diesel at the current pump price, lubricants and an operator, which is what the work actually costs.")]
        body = f"""    <p class="answer">As at {self.date_long}, a 20-tonne excavator costs about <b>{naira(Pl['P-EXC20']['dry'])} a day</b> to hire dry in Abuja and about <b>{a('P-EXC20')} a day all-in</b> with diesel and an operator. This page lists {len(self.D['plant'])} items of construction plant and equipment, from excavators, dozers and rollers to cranes, concrete pumps, generators, road plant and dredgers, with fuel use and typical outputs.</p>
    {''.join(parts)}
    <p class="muted">Fuel is costed at the current diesel or petrol pump price plus {self.P['lube']*100:.0f}% for lubricants. Mobilisation (P-LOW) is priced separately.</p>"""
        self.page(path, f"Construction equipment hire rates in Nigeria ({self.mon}) - excavator, dozer, crane | Buildocrat",
                  f"Daily hire rates for {len(self.D['plant'])} construction machines in Nigeria as at {self.date_long}: excavators, bulldozers, graders, rollers, tippers, cranes, concrete pumps, generators. Dry and all-in rates with fuel.",
                  "Construction equipment hire rates in Nigeria", body, [("Plant hire", path)], faq=faq, priority="0.85", current="plant/")

    COMMON = ["C01", "C02", "B02", "B03", "B06", "B08", "B09", "E01", "E02", "E03", "E04", "E07", "E08", "D01", "D02", "D03", "J04", "F01", "F02", "R06", "G01", "R14"]

    def build_locations(self):
        idx = []
        for n, fm, fl, fp in self.locs:
            s = slug(n.replace("(FCT)", "").replace("(Osun)", "osun"))
            path = f"locations/{s}/"; pre = "../../"
            idx.append((n, path, fm, fl, fp))
            mrows = [[f'<a href="{pre}prices/{h["slug"]}/">{e(self.R[h["primary"]]["d"])}</a>', u(self.R[h["primary"]]["u"]), naira(self.E.rate(h["primary"]) * fm)] for h in HUBS]
            L = {l["c"]: l for l in self.D["labour"]}
            lrows = [[e(L[c]["d"]), naira(L[c]["day"] * fl), naira(self.E.lab_day(L[c]) * fl)] for c in ["L-MAS", "L-LAB", "L-CAR", "L-IRB", "L-ELE", "L-PLU", "L-TIL", "L-PAI", "L-PLA", "L-WEL"]]
            rrows = []
            for c in self.COMMON:
                it = self.items[c]; r = self.E.item(it, (fm, fl, fp))
                rrows.append([self.link_item(pre, c), u(it["u"]), f"<b>{naira(r['net'])}</b>", naira(r["net"] * self.E.markup())])
            cem = self.E.rate("M-CEM-01") * fm; blk = self.E.item(self.items["C01"], (fm, fl, fp))["net"]
            answer = (f"As at {self.date_long}, Buildocrat estimates a 50kg bag of cement at about <b>{naira(cem)}</b> in {e(n)}, a mason at about <b>{naira(L['L-MAS']['day']*fl)} a day</b>, "
                      f"and 225mm blockwork at about <b>{naira(blk)} per m²</b> net. Rates for {e(n)} apply location factors to the Abuja base: materials {fm:.2f}, labour {fl:.2f}, plant {fp:.2f}.")
            body = f"""    <p class="answer">{answer}</p>
    <h2>Key material prices in {e(n)}</h2>{self.table(["Material", "Unit", "Estimated price"], mrows, numeric=(2,))}
    <h2>Labour rates in {e(n)}</h2>{self.table(["Trade", "Daily wage", "All-in day"], lrows, numeric=(1, 2))}
    <h2>Common BoQ rates in {e(n)}</h2>{self.table(["Item", "Unit", "Net rate", "Tender rate"], rrows, numeric=(2, 3))}
    <p class="muted">Location factors are starting points based on market evidence and judgement; confirm with local quotes. <a href="{pre}methodology/">How the factors work</a>.</p>"""
            faq = [(f"How much is cement in {n}?", f"About {naira(cem)} per 50kg bag (Buildocrat estimate, {self.date_long})."),
                   (f"How much is a mason paid per day in {n}?", f"About {naira(L['L-MAS']['day']*fl)} a day, or {naira(self.E.lab_day(L['L-MAS'])*fl)} all-in."),
                   (f"How much does blockwork cost per square metre in {n}?", f"225mm hollow sandcrete blockwork is about {naira(blk)} per m² net, or {naira(blk*self.E.markup())} including overheads, profit and VAT.")]
            self.page(path, f"Construction costs in {n} ({self.mon}) - material prices, labour and BoQ rates | Buildocrat",
                      f"Building costs in {n}, Nigeria as at {self.date_long}: cement about {naira(cem)} per bag, mason {naira(L['L-MAS']['day']*fl)} a day, blockwork {naira(blk)} per m². Key material prices, labour and 22 common BoQ rates.",
                      f"Construction costs in {e(n)}", body, [("Locations", "locations/"), (n, path)], faq=faq, priority="0.8", current="locations/")
        path = "locations/"; pre = "../"
        rows = [[f'<a href="{pre}{p}">{e(n)}</a>', f"{fm:.2f}", f"{fl:.2f}", f"{fp:.2f}", naira(self.E.rate("M-CEM-01") * fm), naira(self.E.item(self.items["C01"], (fm, fl, fp))["net"])] for n, p, fm, fl, fp in idx]
        body = f"""    <p class="answer">Buildocrat prices everything at Abuja market rates and adjusts materials, labour and plant separately for {len(self.locs)} locations in Nigeria. Pick a location for its key prices, labour rates and common BoQ rates.</p>
    {self.table(["Location", "Materials", "Labour", "Plant", "Cement / bag", "225mm blockwork / m²"], rows, numeric=(1, 2, 3, 4, 5))}"""
        self.page(path, f"Construction costs by city in Nigeria ({self.mon}) | Buildocrat",
                  f"Construction cost location factors and key prices for {len(self.locs)} Nigerian locations including Abuja, Lagos, Port Harcourt, Ibadan, Kano and Enugu, as at {self.date_long}.",
                  "Construction costs by location in Nigeria", body, [("Locations", path)], priority="0.8", current="locations/")

    def bungalow_totals(self, f=(1, 1, 1)):
        P = self.P; rows = []; meas = 0
        for c, q in BUNGALOW:
            r = self.E.item(self.items[c], f); amt = r["net"] * q; meas += amt; rows.append((c, q, r["net"], amt))
        pre = meas * 0.10; net = meas + pre; oh = net * P["oh"]; cont = (net + oh) * P["cont"]; pro = (net + oh + cont) * P["profit"]
        ten = net + oh + cont + pro; vat = ten * P["vat"]
        return rows, dict(meas=meas, pre=pre, net=net, oh=oh, cont=cont, pro=pro, ten=ten, vat=vat, total=ten + vat)

    def build_guide(self):
        path = "guides/cost-to-build-3-bedroom-bungalow/"; pre = "../../"
        rows, t = self.bungalow_totals()
        trs = [[self.link_item(pre, c, f"{c} {self.items[c]['d']}"), f"{q:g} {u(self.items[c]['u'])}", naira(rate), naira(amt)] for c, q, rate, amt in rows]
        tbl = self.table(["Item", "Quantity", "Net rate", "Amount"], trs, numeric=(1, 2, 3))
        P = self.P
        summ = self.table(["", "Amount"], [["Measured works (net)", naira(t["meas"])], ["Preliminaries (10%)", naira(t["pre"])], ["<b>Net cost</b>", f"<b>{naira(t['net'])}</b>"],
                                           [f"Overheads ({P['oh']*100:g}%)", naira(t["oh"])], [f"Contingency ({P['cont']*100:g}%)", naira(t["cont"])], [f"Profit ({P['profit']*100:g}%)", naira(t["pro"])],
                                           ["<b>Contract sum excl. VAT</b>", f"<b>{naira(t['ten'])}</b>"], [f"VAT ({P['vat']*100:g}%)", naira(t["vat"])],
                                           ["<b>Contract sum incl. VAT</b>", f"<b>{naira(t['total'])}</b>"], [f"Cost per m² ({BUNGALOW_GFA} m², incl. VAT)", f"<b>{naira(t['total']/BUNGALOW_GFA)}</b>"]], numeric=(1,))
        lrows = []
        for n, fm, fl, fp in self.locs:
            _, tt = self.bungalow_totals((fm, fl, fp))
            lrows.append([e(n), naira(tt["total"]), naira(tt["total"] / BUNGALOW_GFA)])
        ltbl = self.table(["Location", "Contract sum incl. VAT", "Per m²"], lrows, numeric=(1, 2))
        answer = (f"Using Buildocrat's rates as at {self.date_long}, the main building works for a typical <b>{BUNGALOW_GFA} m² three-bedroom bungalow in Abuja</b> come to about <b>{naira(t['total'])}</b> "
                  f"(about <b>{naira(t['total']/BUNGALOW_GFA)} per m²</b>) including preliminaries, overheads, contingency, profit and VAT. This covers substructure, blockwork, roof, plastering, screed, floor and wall tiles, ceilings, painting, doors, windows and basic electrical and plumbing. It excludes land, approvals, professional fees, external works, fencing, borehole, septic tank and furnishings.")
        body = f"""    <p class="answer">{answer}</p>
    <p><b>Important:</b> the quantities below are for an illustrative plan, not your drawings. Use them to budget and compare quotes, then get a bill of quantities measured from your own design.</p>
    <h2>Summary</h2>{summ}
    <h2>Cost by location</h2>{ltbl}
    <h2>Priced items</h2>{tbl}
    <p><a class="btn btnlink" href="{pre}">Price your own list in the estimator</a></p>"""
        faq = [("How much does it cost to build a 3-bedroom bungalow in Nigeria?", f"About {naira(t['total'])} in Abuja for the main building works of a typical {BUNGALOW_GFA} m² bungalow as at {self.date_long}, or about {naira(t['total']/BUNGALOW_GFA)} per m², including overheads, profit and VAT but excluding land, fees, external works and borehole (Buildocrat estimate)."),
               ("What is the cost of building per square metre in Nigeria?", f"For a standard-finish bungalow, about {naira(t['total']/BUNGALOW_GFA)} per m² in Abuja on Buildocrat's {self.mon} rates. Higher finishes, suspended floors and full MEP increase this."),
               ("What is excluded?", "Land, survey and approvals, professional fees, external works, fencing, borehole, septic tank, landscaping, air-conditioning and furnishings.")]
        self.page(path, f"Cost to build a 3-bedroom bungalow in Nigeria ({self.mon}) - {naira(t['total'])} | Buildocrat",
                  f"What it costs to build a {BUNGALOW_GFA} m² three-bedroom bungalow in Nigeria as at {self.date_long}: about {naira(t['total'])} ({naira(t['total']/BUNGALOW_GFA)} per m²) in Abuja, with priced items and costs for 12 locations.",
                  "How much does it cost to build a 3-bedroom bungalow in Nigeria?", body, [("Guides", path), ("3-bedroom bungalow cost", path)], faq=faq, priority="0.9", current="guides/cost-to-build-3-bedroom-bungalow/")
        return t

    def build_method(self):
        path = "methodology/"; pre = "../"; P = self.P
        cnt = lambda c: sum(1 for r in self.D["resources"] if r["conf"] == c)
        srcs = "".join(f'<li><a href="{e(u_)}" rel="nofollow noopener" target="_blank">{e(n)}</a></li>' for n, u_ in self.D["sources"])
        body = f"""    <p class="answer">Every rate in the Nigeria Construction Rate Book is composed from its resources, never guessed: material quantity x (1 + waste) x material price, plus labour hours x the all-in hourly rate, plus plant days x the all-in plant rate. Overheads, contingency, profit and VAT are added once, on top.</p>
    <h2>The rate formula</h2>
    <p>Unit rate = Σ material quantity × (1 + waste %) × price + Σ labour hours × all-in hourly rate + Σ plant days × all-in day rate.</p>
    <ul><li><b>All-in labour</b> = daily wage × (1 + {P['craftUplift']*100:.0f}%) for feeding, transport, non-productive time, statutory cover (NSITF) and small tools, divided by an {P['hrs']}-hour day.</li>
    <li><b>Salaried staff</b> = monthly salary ÷ {P['dpm']} × (1 + {P['staffOncost']*100:.1f}%) for pension, NSITF, ITF, HMO and leave.</li>
    <li><b>All-in plant</b> = dry hire + fuel (litres per day × current pump price × 1.{int(P['lube']*100):02d} for lubricants) + operator all-in day.</li>
    <li><b>Derived prices</b>: rebar per 12 m length and steel sections are priced by weight from the per-tonne steel price.</li></ul>
    <h2>Tender rates</h2><p>Tender rate = net rate × (1 + {P['oh']*100:g}% overheads) × (1 + {P['cont']*100:g}% contingency) × (1 + {P['profit']*100:g}% profit) × (1 + {P['vat']*100:g}% VAT). Withholding tax ({P['wht']*100:g}%) is deducted at source and reduces cash, not price.</p>
    <h2>Locations</h2><p>Abuja is the base. Materials, labour and plant are adjusted separately for each location. The factors are starting points based on market evidence and judgement.</p>
    <h2>Confidence grades</h2>
    <ul><li><b>HIGH</b> ({cnt('HIGH')} materials): several dated sources from the last month agree.</li>
    <li><b>MEDIUM</b> ({cnt('MEDIUM')}): dated 2026 evidence adjusted to the price date.</li>
    <li><b>LOW</b> ({cnt('LOW')}): desk estimate or derived; confirm with three supplier quotes.</li></ul>
    <p>Prices older than {P['stale']} days are flagged STALE.</p>
    <h2>Weekly updates</h2><p>Every Monday, key prices (cement, iron rods, diesel, petrol, gas, roofing, blocks, sand, granite and the exchange rate) are re-checked against dated sources. A price changes only when a dated source supports it; a move of more than 25% needs two independent sources. Every change is logged on the <a href="{pre}updates/">updates page</a>.</p>
    <h2>Who publishes it</h2><p>The rate book is published by Buildocrat Property Technologies Ltd (RC 7019619), Abuja. Buildocrat's founder, Engr. Kola Ibrahim (MNSE, R.COREN, PMP), is a COREN-registered civil and structural engineer.</p>
    <h2>Sources</h2><ul>{srcs}</ul>"""
        self.page(path, "How the Nigeria Construction Rate Book is built - methodology | Buildocrat",
                  "How Buildocrat builds construction unit rates for Nigeria: first-principles build-ups, all-in labour and plant rates, location factors, confidence grades and weekly price checks.",
                  "Methodology: how the rates are built", body, [("Methodology", path)], priority="0.6", current="methodology/")

    def build_about(self):
        path = "about/"; pre = "../"
        body = f"""    <p class="answer">Buildocrat Property Technologies Ltd (RC 7019619) is an Abuja-based property technology company that gives Nigerian builders price certainty on construction materials. Its flagship product, Buildocrat Price Lock, fixes today's price for cement, steel and other key materials for an agreed period.</p>
    <h2>What Buildocrat does</h2>
    <ul><li><b>Price Lock</b>: lock today's price for cement, steel and other key materials for an agreed period, secured with an activation deposit from 10% of order value depending on customer type. Materials are delivered to site on your schedule.</li>
    <li><b>Material stockpiling plans</b> (3, 6 and 12 months): accumulate cement and blocks gradually while Buildocrat stores them, avoiding storage, spoilage, theft and inflation.</li>
    <li><b>Free material estimation</b> from your building drawings.</li>
    <li><b>Withdrawal and delivery</b> to sites across Nigeria, typically within 24 hours.</li>
    <li><b>The Nigeria Construction Rate Book</b>: free, weekly-checked prices and BoQ unit rates.</li></ul>
    <h2>Company details</h2>
    {self.table(["", ""], [["Registered name", "Buildocrat Property Technologies Ltd"], ["CAC RC No.", "7019619"], ["Office", "No 30 Anthony Enahoro Street, Utako, Abuja, FCT, Nigeria"], ["WhatsApp", "+234 701 802 4292"], ["Email", "buildocrat@gmail.com"], ["Website", '<a href="https://buildocrat.store">buildocrat.store</a>'], ["Founder & MD", 'Engr. Kola Ibrahim, MNSE, R.COREN, PMP (<a href="https://www.linkedin.com/in/kolaibrahim/" rel="noopener">LinkedIn</a>)']])}
    <p><a class="btn btnlink" href="https://wa.me/2347018024292?text=Hello%20Buildocrat%2C%20I%27d%20like%20to%20lock%20prices%20for%20my%20project." rel="noopener">Lock my prices on WhatsApp</a></p>"""
        self.page(path, "About Buildocrat - price certainty for Nigerian construction materials", "Buildocrat Property Technologies Ltd (RC 7019619), Abuja: Price Lock for cement and steel, material stockpiling plans, free material estimation and the Nigeria Construction Rate Book.",
                  "About Buildocrat", body, [("About", path)], graph=[{"@type": "AboutPage", "@id": BASE + "/about/#about", "about": {"@id": BASE + "/#org"}}], priority="0.6", current="about/")

    def build_updates(self):
        path = "updates/"; pre = "../"
        log = "".join(f'<div class="log"><b>{e(c["date"])}</b><div>{e(c["note"])}</div></div>' for c in reversed(self.D["changelog"]))
        body = f"""    <p class="answer">Key prices are re-checked every Monday against dated market sources. Each weekly change is listed here, newest first. Follow the <a href="{pre}feed.xml">update feed</a> to be notified.</p>
    {log}"""
        self.page(path, f"Construction price updates for Nigeria - weekly log | Buildocrat", "Weekly log of changes to Nigerian construction prices in the Buildocrat rate book: cement, iron rods, diesel, roofing, blocks, sand and granite.",
                  "Weekly price updates", body, [("Updates", path)], priority="0.7", current="")

    def build_privacy(self):
        path = "privacy/"
        on = bool((self.cfg.get("ga4_measurement_id") or "").strip() or (self.cfg.get("cloudflare_web_analytics_token") or "").strip())
        body = f"""    <p class="answer">Buildocrat uses {'Google Analytics' if (self.cfg.get('ga4_measurement_id') or '').strip() else 'privacy-friendly analytics'} to count visits and see which prices and tools people use, so we can improve the rate book. We do not sell data or use it for advertising.</p>
    <h2>What we collect</h2>
    <ul><li>Pages visited, how visitors arrived (for example from Google or an AI assistant), approximate location (country or city), device and browser type.</li>
    <li>Actions such as opening a rate build-up, adding a line to the estimator, downloading data or tapping the WhatsApp button.</li>
    <li>Estimator lines and your chosen location are saved only in your own browser and are never sent to us.</li></ul>
    <h2>What we do not collect</h2><p>We do not ask for your name, phone number or email on this site. If you contact us on WhatsApp or by email, we use your details only to reply.</p>
    <h2>Your choices</h2><p>You can block analytics with your browser's privacy settings or an ad-blocker; the rate book works the same. For questions or requests under the Nigeria Data Protection Act 2023, contact buildocrat@gmail.com.</p>
    <p class="muted">Controller: Buildocrat Property Technologies Ltd (RC 7019619), No 30 Anthony Enahoro Street, Utako, Abuja. Analytics active: {'yes' if on else 'not yet'}.</p>"""
        self.page(path, "Privacy notice | Buildocrat Rate Book", "How the Buildocrat Nigeria Construction Rate Book measures visits and handles data.",
                  "Privacy notice", body, [("Privacy", path)], priority="0.3")

    def build_data(self):
        path = "data/"; pre = "../"
        body = f"""    <p class="answer">The full rate book is free to download and reuse under the <a href="{LICENSE_URL}" rel="license">Creative Commons Attribution 4.0</a> licence. Please credit "Buildocrat Nigeria Construction Rate Book" with a link to {BASE}.</p>
    <h2>Downloads (prices as at {self.date_long})</h2>
    <ul><li><a href="{pre}data/materials.csv">materials.csv</a>: {len(self.D['resources'])} material prices with ranges, confidence and sources</li>
    <li><a href="{pre}data/composite-rates.csv">composite-rates.csv</a>: {len(self.D['items'])} BoQ unit rates with materials, labour and plant split</li>
    <li><a href="{pre}data/labour.csv">labour.csv</a>: {len(self.D['labour'])} labour grades</li>
    <li><a href="{pre}data/plant.csv">plant.csv</a>: {len(self.D['plant'])} plant items</li>
    <li><a href="{pre}data/rate-data.json">rate-data.json</a>: everything, including rate recipes and location factors</li>
    <li><a href="{pre}llms-full.txt">llms-full.txt</a>: the whole rate book as plain text</li></ul>
    <h2>How to cite</h2><p>Buildocrat (2026). <i>Nigeria Construction Rate Book</i>. Buildocrat Property Technologies Ltd, Abuja. {BASE}. Prices as at {self.date_long}.</p>"""
        self.page(path, "Nigeria construction cost data - free CSV and JSON downloads | Buildocrat",
                  f"Download Nigerian construction cost data: {len(self.D['resources'])} material prices, {len(self.D['items'])} BoQ unit rates, labour and plant hire rates. CSV and JSON, CC BY 4.0, updated weekly.",
                  "Download the data", body, [("Data", path)], graph=[self.dataset()], priority="0.6")

    # -------------------------------------------------------------- data + machine-readable files
    def write_csvs(self):
        def w(name, head, rows):
            s = io.StringIO(); c = csv.writer(s); c.writerow(head); c.writerows(rows)
            self.out(f"data/{name}", s.getvalue())
        w("materials.csv", ["code", "group", "description", "unit", "price_ngn", "low_ngn", "high_ngn", "waste_pct", "confidence", "evidence_date", "price_set", "source", "location"],
          [[r["c"], r["g"], r["d"], r["u"], round(self.E.rate(r["c"]), 2), round(self.E.rate(r["c"], "lo"), 2), round(self.E.rate(r["c"], "hi"), 2), r.get("w", 0), r["conf"], r.get("ev") or "", r["set"], r["src"], "Abuja"] for r in self.D["resources"]])
        mk = self.E.markup()
        w("composite-rates.csv", ["code", "section", "description", "unit", "materials_ngn", "labour_ngn", "plant_ngn", "net_rate_ngn", "tender_rate_ngn", "url", "location"],
          [[i["c"], sec_name(i["s"]), i["d"], i["u"], round(r["m"], 2), round(r["l"], 2), round(r["p"], 2), round(r["net"], 2), round(r["net"] * mk, 2), BASE + "/" + self.item_path[i["c"]], "Abuja"] for i in self.D["items"] for r in [self.E.item(i)]])
        w("labour.csv", ["code", "trade", "type", "daily_wage_ngn", "low_ngn", "high_ngn", "monthly_salary_ngn", "all_in_day_ngn", "all_in_hour_ngn", "confidence", "source"],
          [[l["c"], l["d"], l["cat"], l.get("day") or "", l.get("lo") or "", l.get("hi") or "", l.get("mon") or "", round(self.E.lab_day(l), 2), round(self.E.lab_day(l) / self.P["hrs"], 2), l["conf"], l["src"]] for l in self.D["labour"]])
        w("plant.csv", ["code", "plant", "unit", "dry_hire_ngn", "low_ngn", "high_ngn", "fuel_litres_per_day", "fuel_cost_ngn", "operator_ngn", "all_in_ngn", "typical_output", "confidence", "source"],
          [[p["c"], p["d"], p["u"], p["dry"], p["lo"], p["hi"], p["lpd"], round(x["fuel"], 2), round(x["op"], 2), round(x["total"], 2), p.get("out") or "", p["conf"], p["src"]] for p in self.D["plant"] for x in [self.E.plant_parts(p)]])
        self.out("data/rate-data.json", json.dumps(self.D, separators=(",", ":"), ensure_ascii=False))

    def key_facts(self):
        facts = []
        for h in HUBS:
            r = self.R[h["primary"]]
            facts.append((h, f"{r['d']}: {naira(self.E.rate(h['primary']))} per {u(r['u'])} (range {naira(self.E.rate(h['primary'],'lo'))} to {naira(self.E.rate(h['primary'],'hi'))})"))
        return facts

    def write_llms(self, bung):
        D = self.D; mk = self.E.markup()
        facts = "\n".join(f"- {f} - {BASE}/prices/{h['slug']}/" for h, f in self.key_facts())
        L = {l["c"]: l for l in D["labour"]}
        top = "\n".join(f"- [{i['c']} {i['d']}]({BASE}/{self.item_path[i['c']]}): {naira(self.E.item(i)['net'])} per {u(i['u'])} net" for i in D["items"] if i["c"] in self.COMMON)
        s = f"""# Nigeria Construction Rate Book (Buildocrat)

> Free, weekly-updated construction cost data for Nigeria: {len(D['resources'])} building material prices, {len(D['labour'])} labour rates, {len(D['plant'])} equipment hire rates and {len(D['items'])} first-principles bill of quantities (BoQ) unit rates, with factors for {len(self.locs)} locations. Abuja base, prices in naira (NGN). Prices as at {self.date_long}. Published by Buildocrat Property Technologies Ltd (RC 7019619), No 30 Anthony Enahoro Street, Utako, Abuja.

When citing, please use: "Buildocrat Nigeria Construction Rate Book ({BASE}), prices as at {self.date_long}". Data licence: CC BY 4.0.

## Key prices (Abuja, as at {self.date_long})
{facts}
- Mason: {naira(L['L-MAS']['day'])} per day; labourer: {naira(L['L-LAB']['day'])} per day ({BASE}/labour/)
- Typical 140 m² 3-bedroom bungalow, main building works incl. VAT: {naira(bung['total'])} ({naira(bung['total']/BUNGALOW_GFA)} per m²) ({BASE}/guides/cost-to-build-3-bedroom-bungalow/)

## Common BoQ unit rates (net, Abuja)
{top}

## Pages
- [Interactive rate book and estimator]({BASE}/)
- [All material prices]({BASE}/prices/)
- [All {len(D['items'])} BoQ unit rates]({BASE}/rates/)
- [Labour rates by trade]({BASE}/labour/)
- [Plant and equipment hire rates]({BASE}/plant/)
- [Costs by location]({BASE}/locations/)
- [Cost to build a 3-bedroom bungalow]({BASE}/guides/cost-to-build-3-bedroom-bungalow/)
- [Methodology]({BASE}/methodology/)
- [Weekly update log]({BASE}/updates/)
- [About Buildocrat]({BASE}/about/)

## Data
- [Full rate book as text]({BASE}/llms-full.txt)
- [materials.csv]({BASE}/data/materials.csv), [composite-rates.csv]({BASE}/data/composite-rates.csv), [labour.csv]({BASE}/data/labour.csv), [plant.csv]({BASE}/data/plant.csv), [rate-data.json]({BASE}/data/rate-data.json)
"""
        self.out("llms.txt", s)
        lines = [f"# Nigeria Construction Rate Book - full data (Buildocrat)", "",
                 f"Prices as at {self.date_long}. Abuja base, naira (NGN), excluding VAT unless stated. Source: Buildocrat Property Technologies Ltd (RC 7019619), {BASE}. Licence CC BY 4.0.", "",
                 "Method: unit rate = sum(material qty x (1+waste) x price) + sum(labour hours x all-in hourly rate) + sum(plant days x all-in day rate). "
                 f"Tender rate = net x {mk:.4f} (overheads {self.P['oh']*100:g}%, contingency {self.P['cont']*100:g}%, profit {self.P['profit']*100:g}%, VAT {self.P['vat']*100:g}%).", "",
                 "## Material prices", "code | material | unit | price | range | confidence | evidence date | source"]
        for r in D["resources"]:
            lines.append(f"{r['c']} | {r['d']} | {r['u']} | {naira(self.E.rate(r['c']))} | {naira(self.E.rate(r['c'],'lo'))}-{naira(self.E.rate(r['c'],'hi'))} | {r['conf']} | {r.get('ev') or 'derived'} | {r['src']}")
        lines += ["", "## BoQ unit rates (net, Abuja)", "code | section | item | unit | materials | labour | plant | net rate | tender rate"]
        for i in D["items"]:
            x = self.E.item(i)
            lines.append(f"{i['c']} | {sec_name(i['s'])} | {i['d']} | {i['u']} | {naira(x['m'])} | {naira(x['l'])} | {naira(x['p'])} | {naira(x['net'])} | {naira(x['net']*mk)}")
        lines += ["", "## Labour", "code | trade | type | wage | all-in day"]
        for l in D["labour"]:
            lines.append(f"{l['c']} | {l['d']} | {l['cat']} | {naira(l['mon'])+'/month' if l['cat']=='Staff' else naira(l['day'])+'/day'} | {naira(self.E.lab_day(l))}")
        lines += ["", "## Plant hire", "code | plant | dry hire | fuel L/day | all-in | typical output"]
        for p in D["plant"]:
            lines.append(f"{p['c']} | {p['d']} | {naira(p['dry'])}/{p['u']} | {p['lpd']} | {naira(self.E.plant_parts(p)['total'])}/{p['u']} | {p.get('out') or ''}")
        lines += ["", "## Location factors (materials, labour, plant; Abuja = 1.00)"] + [f"{n}: {a:.2f}, {b:.2f}, {c:.2f}" for n, a, b, c in self.locs]
        lines += ["", "## Update log"] + [f"{c['date']}: {c['note']}" for c in D["changelog"]]
        self.out("llms-full.txt", "\n".join(lines) + "\n")

    def write_feed(self):
        entries = "".join(f"""
  <entry>
    <title>Price update {e(c['date'])}</title>
    <id>{BASE}/updates/#{e(c['date'])}</id>
    <link href="{BASE}/updates/"/>
    <updated>{c['date']}T06:00:00+01:00</updated>
    <summary>{e(c['note'])}</summary>
  </entry>""" for c in reversed(self.D["changelog"]))
        self.out("feed.xml", f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Buildocrat Rate Book - Nigeria construction price updates</title>
  <link href="{BASE}/feed.xml" rel="self"/>
  <link href="{BASE}/"/>
  <id>{BASE}/</id>
  <updated>{self.upd}T06:00:00+01:00</updated>
  <author><name>Buildocrat Property Technologies Ltd</name></author>{entries}
</feed>
""")

    def write_sitemap_robots(self):
        urls = "".join(f"\n  <url><loc>{BASE}/{p}</loc><lastmod>{self.upd}</lastmod><changefreq>weekly</changefreq><priority>{pr}</priority></url>" for p, pr in self.pages)
        self.out("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}\n</urlset>\n')
        bots = ["Googlebot", "Bingbot", "Google-Extended", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "anthropic-ai",
                "PerplexityBot", "Perplexity-User", "Applebot", "Applebot-Extended", "CCBot", "meta-externalagent", "Amazonbot", "DuckAssistBot", "cohere-ai", "YouBot", "MistralAI-User"]
        self.out("robots.txt", "# Buildocrat Rate Book: search engines and AI assistants are welcome to crawl, index and cite this site.\n"
                 + "".join(f"\nUser-agent: {b}\nAllow: /\n" for b in bots) + "\nUser-agent: *\nAllow: /\n\n" + f"Sitemap: {BASE}/sitemap.xml\n")

    def write_404(self):
        doc = f"""<!doctype html>
<html lang="en-NG"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page not found | Buildocrat Rate Book</title><meta name="robots" content="noindex">
<link rel="stylesheet" href="{BASE}/assets/site.css"></head>
<body><div class="wrap"><header class="sitehead"><div class="brandbar"><a class="wordmark" href="{BASE}/">Build<span>ocrat</span></a><span class="brandtag">Nigeria Construction Rate Book</span></div>{self.nav(BASE + '/')}</header>
<main class="static"><h1>Page not found</h1><p>The page may have moved. Try the <a href="{BASE}/">interactive rate book</a>, <a href="{BASE}/prices/">material prices</a> or <a href="{BASE}/rates/">BoQ rates</a>.</p></main></div></body></html>
"""
        self.out("404.html", doc)

    def og_image(self):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            return False
        def font(size, bold=True):
            for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                       "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
                if os.path.exists(fp): return ImageFont.truetype(fp, size)
            return ImageFont.load_default()
        W, H = 1200, 630
        im = Image.new("RGB", (W, H), (12, 106, 76)); d = ImageDraw.Draw(im)
        d.text((64, 52), "Build", font=font(46), fill="white"); bw = d.textlength("Build", font=font(46))
        d.text((64 + bw, 52), "ocrat", font=font(46), fill=(213, 235, 226))
        d.text((64, 128), "Nigeria Construction Rate Book", font=font(54), fill="white")
        d.text((64, 196), f"Prices as at {self.date_long}  ·  updated weekly", font=font(26, False), fill=(213, 235, 226))
        cards = [("M-CEM-01", "Cement, 50kg bag"), ("M-STL-01", "Iron rods, per tonne"), ("M-BLK-01", "9\" block"), ("M-FUE-01", "Diesel, per litre")]
        x0, y0, cw, ch, gap = 64, 290, 256, 170, 16
        for i, (c, lab) in enumerate(cards):
            x = x0 + i * (cw + gap)
            d.rectangle([x, y0, x + cw, y0 + ch], fill=(255, 255, 255))
            d.text((x + 18, y0 + 20), lab, font=font(22, False), fill=(86, 101, 94))
            txt = naira(self.E.rate(c)); fs = 40
            while fs > 22 and d.textlength(txt, font=font(fs)) > cw - 36: fs -= 2
            d.text((x + 18, y0 + 70), txt, font=font(fs), fill=(21, 32, 27))
        d.text((64, 520), f"{len(self.D['items'])} BoQ unit rates · {len(self.D['resources'])} materials · labour · plant hire · 12 locations", font=font(24, False), fill="white")
        d.text((64, 562), "rates.buildocrat.store", font=font(26), fill="white")
        im.save(os.path.join(self.root, "og.png"), optimize=True)
        return True

    def home_inserts(self, bung):
        """Pre-rendered content for the interactive home page (so crawlers without JavaScript see it)."""
        f = (1, 1, 1)
        watch = ""
        WL = self.D["meta"].get("watchLabels", {})
        for c in self.D["meta"]["watch"]:
            r = self.R[c]
            watch += f'<li><span class="k">{e(WL.get(c, r["d"]))}</span><span class="v">{naira(self.E.rate(c))}</span></li>'
        by_sec = {}
        for it in self.D["items"]:
            by_sec.setdefault(it["s"], []).append(it)
        rows = ""
        for s in sorted(by_sec):
            rows += f'<tr class="sec"><td colspan="8">{e(s)}</td></tr>'
            for it in sorted(by_sec[s], key=lambda x: x["c"]):
                r = self.E.item(it, f)
                rows += (f'<tr><td class="hm"></td><td class="code hm">{it["c"]}</td><td><a href="{self.item_path[it["c"]]}">{e(it["d"])}</a></td><td>{e(it["u"])}</td>'
                         f'<td class="n hm">{naira(r["m"])}</td><td class="n hm">{naira(r["l"])}</td><td class="n hm">{naira(r["p"])}</td><td class="n net">{naira(r["net"])}</td></tr>')
        view = ('<div class="tablebox"><table><thead><tr><th class="hm"></th><th class="hm">Code</th><th>Description</th><th>Unit</th><th class="n hm">Materials</th><th class="n hm">Labour</th>'
                f'<th class="n hm">Plant</th><th class="n">Net rate</th></tr></thead><tbody>{rows}</tbody></table></div>')
        facts = "; ".join(f"{e(self.R[h['primary']]['d'])} {naira(self.E.rate(h['primary']))} per {u(self.R[h['primary']]['u'])}" for h in HUBS[:6])
        summary = (f'<p class="herofact">A typical 140 m² three-bedroom bungalow costs about '
                   f'<a href="guides/cost-to-build-3-bedroom-bungalow/">{naira(bung["total"])}</a> to build in Abuja this week, or {naira(bung["total"]/BUNGALOW_GFA)} per m².</p>')
        lk = lambda h: f'<li><a href="prices/{h["slug"]}/"><b>{e(h["name"])}</b><small>{naira(self.E.rate(h["primary"]))} per {u(self.R[h["primary"]]["u"])}</small></a></li>'
        links = "".join(lk(h) for h in HUBS if not h["primary"].startswith("M-EQ-"))
        eqlinks = "".join(lk(h) for h in HUBS if h["primary"].startswith("M-EQ-"))
        locl = "".join(f'<li><a href="locations/{slug(n.replace("(FCT)", "").replace("(Osun)", "osun"))}/"><b>{e(n)}</b><small>Construction costs</small></a></li>' for n, *_ in self.locs)
        browse = f"""<section class="browse" aria-label="Browse the rate book">
    <h2>Browse the rate book</h2>
    <ul class="linkgrid">
      <li><a href="prices/"><b>All prices</b><small>{len(self.D['resources'])} materials, tools and machines</small></a></li>
      <li><a href="rates/"><b>All BoQ unit rates</b><small>{len(self.D['items'])} rates with build-ups</small></a></li>
      <li><a href="labour/"><b>Labour rates</b><small>{len(self.D['labour'])} trades and staff grades</small></a></li>
      <li><a href="plant/"><b>Plant and equipment hire</b><small>{len(self.D['plant'])} machines</small></a></li>
      <li><a href="guides/cost-to-build-3-bedroom-bungalow/"><b>Cost to build a bungalow</b><small>{naira(bung['total'])}</small></a></li>
      <li><a href="methodology/"><b>Methodology</b><small>How the rates are built</small></a></li>
      <li><a href="updates/"><b>Weekly updates</b><small>What changed</small></a></li>
      <li><a href="data/"><b>Download the data</b><small>CSV and JSON, CC BY 4.0</small></a></li>
    </ul>
    <h2>Building material prices</h2><ul class="linkgrid">{links}</ul>
    <h2>Construction equipment prices</h2><ul class="linkgrid">{eqlinks}</ul>
    <h2>Costs by location</h2><ul class="linkgrid">{locl}</ul>
  </section>"""
        return watch, view, summary, browse

    def site_css(self, template):
        m = re.search(r"<style>(.*?)</style>", template, re.S)
        self.out("assets/site.css", m.group(1).strip() + "\n" + EXTRA_CSS)

    def build_all(self, template):
        self.site_css(template)
        self.pages.append(("", "1.0"))
        self.build_prices_index(); self.build_hubs()
        self.build_rates_index(); self.build_rate_pages()
        self.build_labour(); self.build_plant(); self.build_locations()
        bung = self.build_guide()
        self.build_method(); self.build_about(); self.build_updates(); self.build_data(); self.build_privacy()
        self.write_csvs(); self.write_llms(bung); self.write_feed(); self.write_404()
        self.write_sitemap_robots()
        self.og_image()
        key = self.cfg.get("indexnow_key")
        if key: self.out(f"{key}.txt", key)
        return bung
