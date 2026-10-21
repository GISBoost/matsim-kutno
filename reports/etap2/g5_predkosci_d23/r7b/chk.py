import re,subprocess,sys
D="reports/etap2/g5_predkosci_d23/r7b"
for run,pl in [("g5r7b_25pct_s4711","r7b"),("g5r7b_25pct_s1","r7b"),("g5r7b_25pct_s2","r7b"),("g5r7bp1_25pct_s4711","r7bp1"),("g5r7bp2_25pct_s4711","r7bp2")]:
    s=open(f"{D}/plans_{pl}.log",encoding="utf-8",errors="replace").read()
    t=int(re.search(r"t.o (\d+);",s).group(1)); c=int(re.search(r"ci.kie (\d+)",s).group(1)); n=7478+t+c
    o=subprocess.run(["uv","run","python","pipeline/check_events.py",f"output/{run}/output_events.xml.zst","--expect-car-legs",str(n)],capture_output=True,text=True).stdout
    open(f"{D}/check_{run}.json","w").write(o)
    print(run,n,'"ok": true' in o, re.search(r'"stuck": (\d+)',o).group(1))
