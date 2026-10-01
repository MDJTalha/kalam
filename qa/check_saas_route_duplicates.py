import re, collections, pathlib
p = pathlib.Path(r"C:\Projects\CorpLMS\apps\api\app\api\routes\saas_commercial.py")
t = p.read_text(encoding="utf-8")
rows = []
for m in re.finditer(r'@router\.(get|post|patch)\("([^"]+)"', t):
    rows.append((m.group(1).upper(), m.group(2), t.count("\n", 0, m.start()) + 1))
counts = collections.Counter((a,b) for a,b,_ in rows)
dupes = [(a,b,[n for x,y,n in rows if x==a and y==b]) for (a,b),k in counts.items() if k > 1]
if dupes:
    for a,b,lines in dupes:
        print(a, b, "->", ",".join(map(str, lines)))
else:
    print("NO_DUPLICATES")
