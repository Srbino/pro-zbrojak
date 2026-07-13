"""Vygeneruje čitelnou HTML stránku se všemi otázkami (správná odpověď zeleně)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "otazky.html"

SECTIONS = {
    "pravo": "Právo",
    "provadeci_predpisy": "Prováděcí předpisy",
    "jine_predpisy": "Jiné předpisy",
    "nauka_o_zbranich": "Nauka o zbraních a střelivu",
    "zdravotni_minimum": "Zdravotnické minimum",
}
ORDER = list(SECTIONS.keys())

qs = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
data = [{
    "n": q["pdf_number"],
    "s": q.get("section") or "unknown",
    "q": q["question"],
    "o": q["options"],
    "c": q["correct"],
    "img": bool(q.get("image")),
} for q in sorted(qs, key=lambda x: x["pdf_number"])]

counts = {}
for d in data:
    counts[d["s"]] = counts.get(d["s"], 0) + 1

payload = json.dumps({"q": data, "sections": SECTIONS, "order": ORDER, "counts": counts},
                     ensure_ascii=False)

HTML = """
<title>Pro Zbroják — všech 837 otázek</title>
<style>
  :root{
    --bg:#f7f9fb; --surface:#ffffff; --surface2:#f1f4f8; --text:#111827; --muted:#5b6472;
    --border:#e3e8ef; --accent:#1e40af; --accent-soft:#e8edfb;
    --ok:#15803d; --ok-bg:#ecfdf3; --ok-border:#16a34a;
    --chip:#eef2f7; --chip-text:#425065;
    --maxw:920px;
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#0e131c; --surface:#161d29; --surface2:#1b2331; --text:#e6e9ef; --muted:#98a2b3;
      --border:#28313f; --accent:#7ea2ff; --accent-soft:#1a2740;
      --ok:#5ee08a; --ok-bg:#0d2a1b; --ok-border:#2f9e5c;
      --chip:#212a38; --chip-text:#aab4c4;
    }
  }
  :root[data-theme="dark"]{
    --bg:#0e131c; --surface:#161d29; --surface2:#1b2331; --text:#e6e9ef; --muted:#98a2b3;
    --border:#28313f; --accent:#7ea2ff; --accent-soft:#1a2740;
    --ok:#5ee08a; --ok-bg:#0d2a1b; --ok-border:#2f9e5c; --chip:#212a38; --chip-text:#aab4c4;
  }
  :root[data-theme="light"]{
    --bg:#f7f9fb; --surface:#ffffff; --surface2:#f1f4f8; --text:#111827; --muted:#5b6472;
    --border:#e3e8ef; --accent:#1e40af; --accent-soft:#e8edfb;
    --ok:#15803d; --ok-bg:#ecfdf3; --ok-border:#16a34a; --chip:#eef2f7; --chip-text:#425065;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    line-height:1.5;-webkit-font-smoothing:antialiased}
  .wrap{max-width:var(--maxw);margin:0 auto;padding:0 16px}
  header{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 88%,transparent);
    backdrop-filter:blur(8px);border-bottom:1px solid var(--border)}
  .head-in{max-width:var(--maxw);margin:0 auto;padding:14px 16px}
  .title{font-size:1.15rem;font-weight:700;letter-spacing:-.01em;margin:0 0 2px}
  .sub{font-size:.8rem;color:var(--muted);margin:0 0 12px}
  .search{width:100%;padding:11px 14px;font-size:1rem;border:1px solid var(--border);
    border-radius:10px;background:var(--surface);color:var(--text)}
  .search:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
  .filters{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
  .chip{font-size:.78rem;padding:5px 11px;border-radius:999px;border:1px solid var(--border);
    background:var(--surface);color:var(--chip-text);cursor:pointer;white-space:nowrap;
    font-variant-numeric:tabular-nums}
  .chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
  main{padding:20px 0 64px}
  .sec-h{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
    color:var(--accent);margin:26px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:12px;
    padding:16px 16px 12px;margin-bottom:12px}
  .meta{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
  .num{font-variant-numeric:tabular-nums;font-weight:700;font-size:.82rem;color:#fff;
    background:var(--accent);border-radius:6px;padding:2px 8px}
  .tag{font-size:.72rem;color:var(--chip-text);background:var(--chip);border-radius:5px;padding:2px 7px}
  .tag.img{color:var(--accent);background:var(--accent-soft)}
  .qtext{font-weight:600;font-size:1.02rem;margin:0 0 10px;text-wrap:pretty}
  .opt{display:flex;gap:9px;padding:9px 11px;border:1px solid var(--border);border-radius:8px;
    margin-bottom:6px;background:var(--surface);font-size:.94rem}
  .opt .k{font-weight:700;color:var(--muted);flex:none;width:1.1em}
  .opt.ok{background:var(--ok-bg);border-color:var(--ok-border);color:var(--ok)}
  .opt.ok .k{color:var(--ok)}
  .opt.ok::after{content:"✓";margin-left:auto;color:var(--ok);font-weight:800;flex:none}
  .count{font-size:.78rem;color:var(--muted);font-variant-numeric:tabular-nums}
  .empty{text-align:center;color:var(--muted);padding:48px 0}
  mark{background:var(--accent-soft);color:inherit;border-radius:3px;padding:0 1px}
  @media (max-width:520px){ .qtext{font-size:.98rem} .card{padding:14px} }
</style>

<header>
  <div class="head-in">
    <h1 class="title">Pro Zbroják — všech 837 otázek</h1>
    <p class="sub">Oficiální katalog MV ČR · <span class="count" id="shown"></span> · správná odpověď <span style="color:var(--ok);font-weight:700">zeleně ✓</span></p>
    <input class="search" id="q" type="search" placeholder="Hledej podle čísla nebo textu otázky…" aria-label="Hledat">
    <div class="filters" id="filters"></div>
  </div>
</header>
<main><div class="wrap" id="list"></div></main>

<script id="data" type="application/json">__DATA__</script>
<script>
  const D = JSON.parse(document.getElementById('data').textContent);
  const list = document.getElementById('list');
  const shown = document.getElementById('shown');
  const filters = document.getElementById('filters');
  let activeSec = 'all', query = '';

  const secChips = [['all','Vše',D.q.length], ...D.order.map(k=>[k,D.sections[k],D.counts[k]||0])];
  filters.innerHTML = secChips.map(([k,l,c])=>
    `<button class="chip" data-sec="${k}" aria-pressed="${k==='all'}">${l} <span style="opacity:.6">${c}</span></button>`).join('');
  filters.addEventListener('click',e=>{
    const b=e.target.closest('.chip'); if(!b)return;
    activeSec=b.dataset.sec;
    [...filters.children].forEach(c=>c.setAttribute('aria-pressed', c===b));
    render();
  });
  document.getElementById('q').addEventListener('input',e=>{query=e.target.value.trim().toLowerCase();render();});

  const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
  function hl(s){ if(!query) return esc(s);
    const i=s.toLowerCase().indexOf(query); if(i<0) return esc(s);
    return esc(s.slice(0,i))+'<mark>'+esc(s.slice(i,i+query.length))+'</mark>'+esc(s.slice(i+query.length)); }

  function render(){
    let items=D.q.filter(x=>activeSec==='all'||x.s===activeSec);
    if(query) items=items.filter(x=>String(x.n)===query||x.q.toLowerCase().includes(query));
    shown.textContent=items.length+' zobrazeno';
    if(!items.length){list.innerHTML='<p class="empty">Nic nenalezeno.</p>';return;}
    let html='', lastSec=null;
    for(const x of items){
      if(x.s!==lastSec && activeSec==='all'){html+=`<h2 class="sec-h">${D.sections[x.s]||x.s}</h2>`;lastSec=x.s;}
      const opts=['A','B','C'].map(k=>
        `<div class="opt ${k===x.c?'ok':''}"><span class="k">${k}</span><span>${esc(x.o[k]||'')}</span></div>`).join('');
      html+=`<article class="card"><div class="meta"><span class="num">č. ${x.n}</span>`+
        `<span class="tag">${D.sections[x.s]||x.s}</span>`+
        (x.img?'<span class="tag img">🖼 obrázek v aplikaci</span>':'')+
        `</div><p class="qtext">${hl(x.q)}</p>${opts}</article>`;
    }
    list.innerHTML=html;
  }
  render();
</script>
"""

OUT.write_text(HTML.replace("__DATA__", payload), encoding="utf-8")
print("Zapsáno:", OUT, "-", OUT.stat().st_size, "bytů,", len(data), "otázek")
