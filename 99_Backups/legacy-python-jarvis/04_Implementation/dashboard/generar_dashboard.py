"""
Genera un panel HTML local con el estado real de JARVIS -- tablero de
contenido y pendientes internos. Pensado para abrir en el navegador (doble
clic sobre el .html generado), no para publicar en ningún sitio: lee
directamente jarvis.db, así que solo tiene sentido corriéndolo en este
mismo ordenador.

Se corre a mano cuando se quiera un dato actualizado:

    python 04_Implementation/dashboard/generar_dashboard.py
"""

import html
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE / "memory_engine"))

import memory_engine as me  # noqa: E402

SALIDA_PATH = Path(__file__).parent / "panel.html"


def _recorte(texto: str, n: int = 160) -> str:
    texto = (texto or "").strip()
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def _tarjeta_decision(d: dict) -> str:
    confianza = d.get("confidence")
    etiqueta_confianza = (f'<span class="tag">confianza: {html.escape(confianza)}</span>'
                           if confianza else "")
    return f"""
    <div class="decision">
      <p class="decision-motivo">{html.escape(_recorte(d.get("reason", ""), 220))}</p>
      <p class="decision-meta">{d.get("created_at", "")[:10]} {etiqueta_confianza}</p>
    </div>"""


def _fila_conocimiento(k: dict) -> str:
    return (f'<tr><td>{html.escape(_recorte(k.get("name", ""), 70))}</td>'
            f'<td>{html.escape(k.get("topic", "") or "")}</td>'
            f'<td class="num">{k.get("created_at", "")[:10]}</td></tr>')


def generar() -> Path:
    tareas_contenido = me.list_tasks(business_line="contenido_afiliados")
    por_fase: dict[str, int] = {}
    for t in tareas_contenido:
        fase = t.get("business_phase") or "(sin fase)"
        por_fase[fase] = por_fase.get(fase, 0) + 1
    orden_fases = ["idea", "produccion", "borrador_listo", "publicado"]
    filas_fase = "".join(
        f'<tr><td>{fase}</td><td class="num">{por_fase.get(fase, 0)}</td></tr>'
        for fase in orden_fases if por_fase.get(fase, 0) or fase in por_fase
    )
    if not filas_fase:
        filas_fase = '<tr><td colspan="2" class="muted">Sin tareas de contenido todavía.</td></tr>'

    decisiones = me.pending_decisions()
    tarjetas_decision = "".join(_tarjeta_decision(d) for d in decisiones[:20])
    if not tarjetas_decision:
        tarjetas_decision = '<p class="muted">Sin decisiones pendientes.</p>'

    conocimiento = me.list_knowledge()
    filas_conocimiento = "".join(_fila_conocimiento(k) for k in conocimiento[:20])
    if not filas_conocimiento:
        filas_conocimiento = '<tr><td colspan="3" class="muted">Sin conocimiento guardado todavía.</td></tr>'

    html_doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Panel JARVIS</title>
<style>
:root{{
  --bg:#0f1319; --surface:#161c25; --surface-2:#1e2530; --border:#2a3341;
  --text:#e6e9ef; --text-dim:#97a2b3; --text-faint:#5f6b7d;
  --accent:#e0a458; --accent-bg:rgba(224,164,88,0.1);
  --good:#4fae8b; --bad:#d1584a;
  --mono:'Consolas','SF Mono',ui-monospace,monospace;
  --sans:-apple-system,'Segoe UI',sans-serif;
}}
*{{box-sizing:border-box;}}
body{{background:var(--bg);color:var(--text);font-family:var(--sans);margin:0;padding:32px 20px 80px;}}
.wrap{{max-width:920px;margin:0 auto;}}
header{{padding-bottom:24px;border-bottom:1px solid var(--border);margin-bottom:32px;}}
.eyebrow{{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin:0 0 8px;}}
h1{{font-family:var(--mono);font-size:28px;margin:0 0 6px;}}
.sub{{color:var(--text-dim);font-size:14px;margin:0;}}
h2{{font-family:var(--mono);font-size:17px;margin:0 0 14px;color:var(--text);}}
section{{margin-bottom:36px;}}
.muted{{color:var(--text-faint);font-size:13px;margin:0;}}
.tbl-wrap{{border:1px solid var(--border);border-radius:10px;overflow:hidden;}}
table.full{{width:100%;border-collapse:collapse;font-size:14px;}}
table.full th{{text-align:left;font-family:var(--mono);font-size:11px;text-transform:uppercase;color:var(--text-faint);padding:10px 16px;background:var(--surface-2);}}
table.full td{{padding:10px 16px;border-top:1px solid var(--border);color:var(--text-dim);}}
table.full td.num{{font-family:var(--mono);color:var(--text);}}
.decisiones-wrap{{display:flex;flex-direction:column;gap:2px;}}
.decision{{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:6px;padding:12px 16px;margin-bottom:8px;}}
.decision-motivo{{margin:0 0 6px;font-size:14px;color:var(--text);}}
.decision-meta{{margin:0;font-size:11px;color:var(--text-faint);font-family:var(--mono);display:flex;gap:10px;align-items:center;}}
.tag{{background:var(--accent-bg);color:var(--accent);border-radius:4px;padding:1px 8px;font-size:10.5px;}}
footer{{margin-top:40px;padding-top:16px;border-top:1px solid var(--border);color:var(--text-faint);font-size:12px;font-family:var(--mono);}}
</style>
</head>
<body>
<div class="wrap">

<header>
  <p class="eyebrow">Panel local -- generado en este ordenador</p>
  <h1>JARVIS</h1>
  <p class="sub">Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')} (hora local)</p>
</header>

<section>
  <h2>Contenido / afiliados -- tablero</h2>
  <div class="tbl-wrap">
    <table class="full">
      <thead><tr><th>Fase</th><th>Tareas</th></tr></thead>
      <tbody>{filas_fase}</tbody>
    </table>
  </div>
</section>

<section>
  <h2>Decisiones pendientes ({len(decisiones)})</h2>
  <div class="decisiones-wrap">
    {tarjetas_decision}
  </div>
</section>

<section>
  <h2>Conocimiento reciente ({len(conocimiento)})</h2>
  <div class="tbl-wrap">
    <table class="full">
      <thead><tr><th>Nota</th><th>Tema</th><th>Fecha</th></tr></thead>
      <tbody>{filas_conocimiento}</tbody>
    </table>
  </div>
</section>

<footer>Generado por 04_Implementation/dashboard/generar_dashboard.py -- correr a mano para actualizar.</footer>

</div>
</body>
</html>"""

    SALIDA_PATH.write_text(html_doc, encoding="utf-8")
    return SALIDA_PATH


if __name__ == "__main__":
    ruta = generar()
    print(f"Panel generado: {ruta}")
