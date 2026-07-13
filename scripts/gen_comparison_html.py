"""Vygeneruje porovnávací HTML: číslo otázky | odpověď z PDF | odpověď z appky | shoda."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pdfplumber
from tests.test_all_answers_vs_pdf import _detect, PDF_PATH

OUT = ROOT / "docs" / "porovnani.html"
SECTIONS = {"pravo": "Právo", "provadeci_predpisy": "Prováděcí předpisy",
            "jine_predpisy": "Jiné předpisy", "nauka_o_zbranich": "Nauka o zbraních",
            "zdravotni_minimum": "Zdravotnické minimum"}

qs = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
qs.sort(key=lambda x: x["pdf_number"])
pdf = pdfplumber.open(PDF_PATH)

rows = []
match = mismatch = undet = 0
for q in qs:
    n = q["pdf_number"]
    app = q["correct"]
    pdf_ans = _detect(pdf, n, q["source_page"] - 1)
    if pdf_ans is None:
        undet += 1
        state = "undet"
    elif pdf_ans == app:
        match += 1
        state = "ok"
    else:
        mismatch += 1
        state = "bad"
    rows.append({"n": n, "s": q.get("section") or "?", "pdf": pdf_ans or "—",
                 "app": app, "st": state, "q": q["question"][:70], "img": bool(q.get("image"))})
pdf.close()

payload = json.dumps({"rows": rows, "sections": SECTIONS,
                      "sum": {"total": len(rows), "match": match, "mismatch": mismatch, "undet": undet}},
                     ensure_ascii=False)
print(f"total={len(rows)} match={match} mismatch={mismatch} undet={undet}")

HTML = r"""
<title>Pro Zbroják — porovnání odpovědí: PDF vs aplikace</title>
<style>
  :root{--bg:#f7f9fb;--surface:#fff;--text:#111827;--muted:#5b6472;--border:#e3e8ef;
    --accent:#1e40af;--ok:#15803d;--ok-bg:#ecfdf3;--bad:#b91c1c;--bad-bg:#fef2f2;--warn:#b45309;--warn-bg:#fffbeb;--chip:#eef2f7;}
  @media(prefers-color-scheme:dark){:root{--bg:#0e131c;--surface:#161d29;--text:#e6e9ef;--muted:#98a2b3;
    --border:#28313f;--accent:#7ea2ff;--ok:#5ee08a;--ok-bg:#0d2a1b;--bad:#f87171;--bad-bg:#2a1113;--warn:#fbbf24;--warn-bg:#2a2109;--chip:#212a38;}}
  :root[data-theme="dark"]{--bg:#0e131c;--surface:#161d29;--text:#e6e9ef;--muted:#98a2b3;--border:#28313f;--accent:#7ea2ff;--ok:#5ee08a;--ok-bg:#0d2a1b;--bad:#f87171;--bad-bg:#2a1113;--warn:#fbbf24;--warn-bg:#2a2109;--chip:#212a38;}
  :root[data-theme="light"]{--bg:#f7f9fb;--surface:#fff;--text:#111827;--muted:#5b6472;--border:#e3e8ef;--accent:#1e40af;--ok:#15803d;--ok-bg:#ecfdf3;--bad:#b91c1c;--bad-bg:#fef2f2;--warn:#b45309;--warn-bg:#fffbeb;--chip:#eef2f7;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;line-height:1.4}
  .wrap{max-width:1000px;margin:0 auto;padding:0 14px}
  header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 90%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--border)}
  .hin{max-width:1000px;margin:0 auto;padding:14px}
  h1{font-size:1.1rem;margin:0 0 10px}
  .cards{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px}
  .stat{border:1px solid var(--border);border-radius:10px;padding:8px 14px;background:var(--surface);min-width:120px}
  .stat .v{font-size:1.5rem;font-weight:800;font-variant-numeric:tabular-nums;line-height:1}
  .stat .l{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:3px}
  .stat.ok .v{color:var(--ok)} .stat.bad .v{color:var(--bad)} .stat.warn .v{color:var(--warn)}
  .ctrl{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
  input{padding:9px 12px;border:1px solid var(--border);border-radius:9px;background:var(--surface);color:var(--text);font-size:.95rem}
  input:focus{outline:2px solid var(--accent);border-color:var(--accent)}
  .toggle{font-size:.8rem;padding:8px 12px;border:1px solid var(--border);border-radius:9px;background:var(--surface);color:var(--text);cursor:pointer}
  .toggle[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
  main{padding:16px 0 60px}
  table{width:100%;border-collapse:collapse;font-size:.9rem}
  th{position:sticky;top:0;text-align:left;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);
     padding:8px 10px;border-bottom:2px solid var(--border);background:var(--bg)}
  td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}
  .n{font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap}
  .ans{font-weight:800;font-variant-numeric:tabular-nums;text-align:center;width:1.6em;border-radius:5px;display:inline-block;padding:1px 7px}
  .a-pdf{background:var(--chip)}
  tr.ok .a-app{background:var(--ok-bg);color:var(--ok)}
  tr.bad .a-app{background:var(--bad-bg);color:var(--bad)}
  tr.bad{background:var(--bad-bg)}
  tr.undet .a-pdf{background:var(--warn-bg);color:var(--warn)}
  .m{text-align:center;font-weight:800}
  tr.ok .m{color:var(--ok)} tr.bad .m{color:var(--bad)} tr.undet .m{color:var(--warn)}
  .qt{color:var(--muted);font-size:.82rem}
  .sec{font-size:.7rem;color:var(--muted);white-space:nowrap}
  .tblwrap{overflow-x:auto;border:1px solid var(--border);border-radius:12px;background:var(--surface)}
  @media(max-width:600px){.qt,.sec{display:none} }
</style>
<header><div class="hin">
  <h1>Porovnání odpovědí — oficiální PDF MV ČR vs aplikace</h1>
  <div class="cards" id="cards"></div>
  <div class="ctrl">
    <input id="q" type="search" placeholder="Skoč na číslo otázky…" inputmode="numeric" style="width:180px">
    <button class="toggle" id="only" aria-pressed="false">Jen neshody</button>
  </div>
</div></header>
<main><div class="wrap"><div class="tblwrap"><table>
  <thead><tr><th>Č.</th><th>PDF</th><th>Appka</th><th>Shoda</th><th>Oblast</th><th>Otázka</th></tr></thead>
  <tbody id="tb"></tbody></table></div></div></main>
<script id="data" type="application/json">__DATA__</script>
<script>
  const D=JSON.parse(document.getElementById('data').textContent);
  const s=D.sum;
  document.getElementById('cards').innerHTML=
    `<div class="stat"><div class="v">${s.total}</div><div class="l">otázek</div></div>`+
    `<div class="stat ok"><div class="v">${s.match}</div><div class="l">shodných ✓</div></div>`+
    `<div class="stat ${s.mismatch?'bad':''}"><div class="v">${s.mismatch}</div><div class="l">neshod</div></div>`+
    (s.undet?`<div class="stat warn"><div class="v">${s.undet}</div><div class="l">nedetekováno</div></div>`:'');
  const tb=document.getElementById('tb');
  let onlyBad=false, q='';
  const esc=x=>x.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
  function render(){
    let r=D.rows;
    if(onlyBad) r=r.filter(x=>x.st!=='ok');
    if(q) r=r.filter(x=>String(x.n).startsWith(q));
    tb.innerHTML=r.map(x=>{
      const sym=x.st==='ok'?'✓':x.st==='bad'?'✗':'?';
      return `<tr class="${x.st}"><td class="n">${x.n}</td>`+
        `<td><span class="ans a-pdf">${x.pdf}</span></td>`+
        `<td><span class="ans a-app">${x.app}</span></td>`+
        `<td class="m">${sym}</td>`+
        `<td class="sec">${D.sections[x.s]||x.s}</td>`+
        `<td class="qt">${esc(x.q)}${x.img?' 🖼':''}</td></tr>`;
    }).join('');
  }
  document.getElementById('q').addEventListener('input',e=>{q=e.target.value.replace(/\D/g,'');render();});
  document.getElementById('only').addEventListener('click',e=>{onlyBad=!onlyBad;e.target.setAttribute('aria-pressed',onlyBad);render();});
  render();
</script>
"""
OUT.write_text(HTML.replace("__DATA__", payload), encoding="utf-8")
print("Zapsáno:", OUT, OUT.stat().st_size, "B")
