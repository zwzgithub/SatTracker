#!/usr/bin/env python3
"""Fetch CelesTrak GP groups as OMM-CSV and write classic 3-line TLE files (tle/<group>.txt).

Why CSV→TLE instead of FORMAT=tle:
  * TLE catalog field is 5 chars; CelesTrak omits objects with NORAD ID > 99999 from FORMAT=tle.
    We encode those in Alpha-5 (A0000 = 100000 … Z9999 = 339999), which satellite.js parses fine.
  * CSV is ~5x smaller than JSON (CelesTrak caps downloads at ~100 MB/day/IP).
CelesTrak allows one download per group per 2 h per IP; on 403 (or any failure) we fall back to
the copy already published on the Pages site so a deploy never loses data.
Usage: fetch_tle.py <out_dir> [previous_site_base_url]
"""
import csv, io, math, sys, time, urllib.request
from datetime import datetime, timezone

GROUPS = ["starlink", "oneweb", "qianfan", "hulianwang", "kuiper", "gps-ops", "glo-ops", "galileo", "beidou",
          "iridium-NEXT", "globalstar", "orbcomm", "planet", "spire", "geo", "stations", "amateur", "visual"]
UA = "constellation-tracker-pwa mirror (GitHub Actions; 1 fetch/group/4h)"
ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ"          # Alpha-5: I and O are skipped → A=10 … Z=33

def get(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def checksum(line):
    return sum(int(c) if c.isdigit() else (1 if c == "-" else 0) for c in line[:68]) % 10

def catnum(n):
    n = int(n)
    if n < 100000: return f"{n:05d}"
    hi, lo = divmod(n, 10000)
    return ALPHA[hi - 10] + f"{lo:04d}"

def exp_field(x):                     # TLE "assumed decimal" exponent format, 8 chars: ±MMMMM±E
    x = float(x)
    if x == 0: return " 00000+0"
    e = math.floor(math.log10(abs(x))) + 1
    m = round(abs(x) / 10 ** e * 1e5)
    if m >= 100000: m //= 10; e += 1
    return ("-" if x < 0 else " ") + f"{m:05d}" + ("-" if e < 0 else "+") + str(abs(e))[-1]

def ndot_field(x):                    # ±.NNNNNNNN, 10 chars
    x = float(x); s = f"{abs(x):.8f}"
    return ("-" if x < 0 else " ") + s[s.index("."):]

def omm_to_tle(r):
    ep = datetime.fromisoformat(r["EPOCH"].replace("Z", "")).replace(tzinfo=timezone.utc)
    y0 = datetime(ep.year, 1, 1, tzinfo=timezone.utc)
    doy = 1 + (ep - y0).total_seconds() / 86400.0
    oid = r.get("OBJECT_ID", "") or ""
    intl = (oid[2:4] + oid[5:]) if len(oid) >= 6 and oid[4] == "-" else ""
    cat, cls = catnum(r["NORAD_CAT_ID"]), (r.get("CLASSIFICATION_TYPE") or "U")[:1]
    l1 = (f"1 {cat}{cls} {intl:<8s} {ep.year % 100:02d}{doy:012.8f} {ndot_field(r['MEAN_MOTION_DOT'])} "
          f"{exp_field(r['MEAN_MOTION_DDOT'])} {exp_field(r['BSTAR'])} 0 {int(r.get('ELEMENT_SET_NO') or 999) % 10000:4d}")
    ecc = f"{float(r['ECCENTRICITY']):.7f}"[2:]
    l2 = (f"2 {cat} {float(r['INCLINATION']):8.4f} {float(r['RA_OF_ASC_NODE']) % 360:8.4f} {ecc} "
          f"{float(r['ARG_OF_PERICENTER']) % 360:8.4f} {float(r['MEAN_ANOMALY']) % 360:8.4f} "
          f"{float(r['MEAN_MOTION']):11.8f}{int(float(r.get('REV_AT_EPOCH') or 0)) % 100000:5d}")
    assert len(l1) == 68 and len(l2) == 68, (l1, l2)
    return f"{r['OBJECT_NAME'].strip()}\n{l1}{checksum(l1)}\n{l2}{checksum(l2)}\n"

def csv_to_tle(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "MEAN_MOTION" not in rows[0]: raise ValueError(text[:160].strip())
    return "".join(omm_to_tle(r) for r in rows), len(rows)

def main():
    out = sys.argv[1]; prev = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else ""
    import os; os.makedirs(out, exist_ok=True)
    for g in GROUPS:
        dst = f"{out}/{g}.txt"
        try:
            tle, n = csv_to_tle(get(f"https://celestrak.org/NORAD/elements/gp.php?GROUP={g}&FORMAT=csv"))
            open(dst, "w").write(tle); print(f"fresh  {g:13s} {n:6d}")
        except Exception as e:
            try:
                txt = get(f"{prev}/tle/{g}.txt") if prev else ""
                if "\n1 " not in txt: raise ValueError("no previous copy")
                open(dst, "w").write(txt); print(f"kept   {g:13s} (CelesTrak: {str(e)[:90]})")
            except Exception as e2:
                print(f"MISS   {g:13s} {str(e)[:90]} / {e2}")
        time.sleep(2)

if __name__ == "__main__":
    main()
