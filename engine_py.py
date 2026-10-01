"""Python port of engine.js - used to pre-render crawlable pages. Must match engine.js exactly."""


class Engine:
    def __init__(self, data):
        self.d = data
        self.P = data["params"]
        self.R = {}
        for r in data["resources"]:
            self.R[r["c"]] = dict(r, kind="M")
        for l in data["labour"]:
            self.R[l["c"]] = dict(l, kind="L", u="h", w=0)
        for p in data["plant"]:
            self.R[p["c"]] = dict(p, kind="P", w=0)
        self._cache = {}

    def _mat(self, code, key):
        r = self.R[code]
        if "k" in r:
            k = r["k"]
            if key in ("lo", "hi") and k.get("s"):
                return self._mat(k["b"], "r") * k["f"] * (1 - k["s"] if key == "lo" else 1 + k["s"])
            return self._mat(k["b"], key) * k["f"]
        return r[key]

    def lab_day(self, l, which="r"):
        P = self.P
        if l["cat"] == "Staff":
            mult = 0.75 if which == "lo" else 1.3 if which == "hi" else 1
            return l["mon"] * mult / P["dpm"] * (1 + P["staffOncost"])
        w = l["lo"] if which == "lo" else l["hi"] if which == "hi" else l["day"]
        return w * (1 + P["craftUplift"])

    def plant_parts(self, p, which="r"):
        dry = p["lo"] if which == "lo" else p["hi"] if which == "hi" else p["dry"]
        fuel = p["lpd"] * self.rate(p["fuel"]) * (1 + self.P["lube"]) if p.get("fuel") else 0
        op = self.lab_day(self.R[p["op"]]) if p.get("op") else 0
        return {"dry": dry, "fuel": fuel, "op": op, "total": dry + fuel + op}

    def rate(self, code, which="r"):
        key = (code, which)
        if key in self._cache:
            return self._cache[key]
        r = self.R[code]
        if r["kind"] == "M":
            v = self._mat(code, which)
        elif r["kind"] == "L":
            v = self.lab_day(r, which) / self.P["hrs"]
        else:
            v = self.plant_parts(r, which)["total"]
        self._cache[key] = v
        return v

    def item(self, it, f=(1, 1, 1)):
        lines = []
        for t, code, q in it["l"]:
            r = self.R[code]
            w = (r.get("w") or 0) if t == "M" else 0
            fx = f[0] if t == "M" else f[1] if t == "L" else f[2]
            rt = self.rate(code) * fx
            lines.append({"t": t, "code": code, "d": r["d"], "u": r["u"], "q": q, "w": w, "rate": rt, "cost": q * (1 + w) * rt})
        s = lambda t: sum(x["cost"] for x in lines if x["t"] == t)
        m, l, p = s("M"), s("L"), s("P")
        return {"lines": lines, "m": m, "l": l, "p": p, "net": m + l + p}

    def markup(self):
        P = self.P
        return (1 + P["oh"]) * (1 + P["cont"]) * (1 + P["profit"]) * (1 + P["vat"])
