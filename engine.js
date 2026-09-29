/* Rate engine: recomputes every resource and composite rate from the base data. */
function buildEngine(DATA) {
  const P = DATA.params;
  const R = {};
  DATA.resources.forEach(r => { R[r.c] = Object.assign({ kind: "M" }, r); });
  DATA.labour.forEach(l => { R[l.c] = Object.assign({ kind: "L", u: "h", w: 0 }, l); });
  DATA.plant.forEach(p => { R[p.c] = Object.assign({ kind: "P", w: 0 }, p); });
  const cache = {};
  function mat(code, key) {
    const r = R[code];
    if (r.k) return mat(r.k.b, key) * r.k.f;
    return r[key];
  }
  function labDay(l, which) {
    if (l.cat === "Staff") {
      const mult = which === "lo" ? 0.75 : which === "hi" ? 1.3 : 1;
      return l.mon * mult / P.dpm * (1 + P.staffOncost);
    }
    const w = which === "lo" ? l.lo : which === "hi" ? l.hi : l.day;
    return w * (1 + P.craftUplift);
  }
  function plantParts(p, which) {
    const dry = which === "lo" ? p.lo : which === "hi" ? p.hi : p.dry;
    const fuel = p.fuel ? p.lpd * rate(p.fuel) * (1 + P.lube) : 0;
    const op = p.op ? labDay(R[p.op]) : 0;
    return { dry, fuel, op, total: dry + fuel + op };
  }
  function rate(code, which) {
    which = which || "r";
    const key = code + "|" + which;
    if (key in cache) return cache[key];
    const r = R[code];
    if (!r) throw new Error("Unknown resource " + code);
    let v;
    if (r.kind === "M") v = mat(code, which);
    else if (r.kind === "L") v = labDay(r, which) / P.hrs;
    else v = plantParts(r, which).total;
    cache[key] = v;
    return v;
  }
  function item(it) {
    const lines = it.l.map(([t, code, q]) => {
      const r = R[code];
      const w = t === "M" ? (r.w || 0) : 0;
      const rt = rate(code);
      return { t, code, d: r.d, u: r.u, q, w, rate: rt, cost: q * (1 + w) * rt };
    });
    const sum = t => lines.filter(x => x.t === t).reduce((a, x) => a + x.cost, 0);
    const m = sum("M"), l = sum("L"), p = sum("P");
    return { lines, m, l, p, net: m + l + p };
  }
  function reset() { for (const k in cache) delete cache[k]; }
  return { R, rate, item, labDay, plantParts, reset };
}
if (typeof module !== "undefined") module.exports = { buildEngine };
