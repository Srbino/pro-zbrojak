"""Diagnostika — ověří v PROHLÍŽEČI, že se načte každý obrázek.

Server umí říct jen to, že soubor odešle. Jestli ho prohlížeč doopravdy
vykreslí, se z logu poznat nedá — a přesně tam vznikl spor o „rozbité
obrázky", kde `curl` vracel 200 a uživatel viděl prázdné místo.

Kontrola běží čistě na klientovi. Skript se proto vkládá přes
`ui.add_body_html`, ne přes `ui.html`: značka `<script>` vložená do
`innerHTML` se v prohlížeči nespustí. Díky tomu funguje i tehdy, když je
spojení s aplikací rozbité — což je právě situace, kdy je potřeba.
"""
from __future__ import annotations

import json

from nicegui import ui

from src.auth import require_login
from src.db.questions import load_questions
from src.ui.layout import page_shell

SKRIPT = """
<script>
(function () {
  var seznam = %s;

  // Kontejnery normálně vykreslí NiceGUI na svém místě. Když je spojení
  // rozbité, nepřijdou vůbec — tak si je skript po chvíli vyrobí sám na
  // konci stránky. Jinak by diagnostika selhala právě tehdy, kdy je třeba.
  var pokusu = 0;
  function start() {
    var mrizka = document.getElementById('zp-diag-mrizka');
    var souhrn = document.getElementById('zp-diag-souhrn');
    if ((!mrizka || !souhrn) && pokusu++ < 25) { return setTimeout(start, 200); }
    if (!souhrn) {
      souhrn = document.createElement('div');
      souhrn.id = 'zp-diag-souhrn';
      souhrn.className = 'zp-card zp-mb-md';
      souhrn.style.margin = '1rem';
      document.body.appendChild(souhrn);
    }
    if (!mrizka) {
      mrizka = document.createElement('div');
      mrizka.id = 'zp-diag-mrizka';
      mrizka.className = 'zp-diag-grid';
      mrizka.style.margin = '1rem';
      document.body.appendChild(mrizka);
    }

    var hotovo = 0, ok = 0, chybne = [];

    function dopsat() {
      if (hotovo < seznam.length) {
        souhrn.textContent = 'Kontroluji… ' + hotovo + ' / ' + seznam.length;
        return;
      }
      souhrn.innerHTML = (chybne.length === 0
        ? '<b>Všech ' + ok + ' obrázků se načetlo.</b> Problém není v obrázcích.'
        : '<b>' + chybne.length + ' z ' + seznam.length + ' se NENAČETLO:</b><br>'
          + chybne.map(function (c) { return 'otázka ' + c.n + ' → ' + c.src; }).join('<br>'))
        + '<div style="margin-top:.5rem;opacity:.7;font-size:.75rem">'
        + navigator.userAgent + '</div>';
    }

    seznam.forEach(function (polozka) {
      var obal = document.createElement('div');
      obal.className = 'zp-diag-item';
      var img = new Image();
      img.alt = String(polozka.n);
      img.onload = function () {
        hotovo++;
        if (img.naturalWidth > 0) { ok++; obal.className += ' ok'; }
        else { chybne.push(polozka); obal.className += ' bad'; }
        dopsat();
      };
      img.onerror = function () {
        hotovo++; chybne.push(polozka); obal.className += ' bad'; dopsat();
      };
      img.src = polozka.src;
      obal.appendChild(img);
      var p = document.createElement('span');
      p.textContent = polozka.n;
      obal.appendChild(p);
      mrizka.appendChild(obal);
    });
    dopsat();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
</script>
"""


@ui.page("/diagnostika")
def diagnostika_page():
    user = require_login()
    if user is None:
        return

    obrazky = [
        {"n": q["pdf_number"], "src": "/" + q["image"]}
        for q in sorted(load_questions(), key=lambda x: x["pdf_number"])
        if q.get("image")
    ]
    # Skript patří do těla dokumentu — z innerHTML by se nespustil.
    ui.add_body_html(SKRIPT % json.dumps(obrazky, ensure_ascii=False))

    with page_shell("Diagnostika", active_path="/settings"):
        ui.label("Diagnostika obrázků").classes("zp-display")
        ui.label(
            f"Stránka zkusí v tomhle prohlížeči načíst všech {len(obrazky)} obrázků "
            "a vypíše, které selhaly. Kontrola nepotřebuje spojení s aplikací, takže "
            "funguje i při výpadku — pošli výsledek i s údajem o prohlížeči dole."
        ).classes("zp-body zp-prose zp-mb-md")

        ui.html('<div id="zp-diag-souhrn" class="zp-card zp-mb-md">Spouštím kontrolu…</div>'
                '<div id="zp-diag-mrizka" class="zp-diag-grid"></div>')

        with ui.element("div").classes("zp-card zp-mt-lg"):
            ui.label("Co běží na serveru").classes("zp-h3 zp-mb-sm")
            ui.label(
                "Podrobnosti vrací /healthz — verze aplikace i NiceGUI, cesta "
                "socketu a počty otázek a obrázků."
            ).classes("zp-body-sm zp-mb-sm")
            ui.link("Otevřít /healthz", "/healthz", new_tab=True).classes("zp-law-ref-link")
