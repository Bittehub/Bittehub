"""Rapports : un résumé texte (pour la réunion d'équipe) et un tableau de bord HTML autonome."""
import html
import json

from . import mesures


# Consignés dans le journal, mais trop fréquents pour un rapport.
BRUIT = ("ordres", "statu_quo", "pause_prolongee")


def _pct(x):
    return "%+.1f %%" % (x * 100)


def synthese(etat):
    ref = [v for _, v in etat["reference"]["historique"]]
    eq = [v for _, v in etat["equipe"]["historique"]]
    lignes = []
    for n, a in etat["agents"].items():
        vals = [v for _, v in a["historique"]]
        m = mesures.resume(vals) if len(vals) > 1 else mesures.resume([a["capital_initial"]] * 2)
        lignes.append({
            "agent": n, "strategie": a["strategie"], "role": a["role"], "generation": a["generation"],
            "en_pause": a["en_pause"], "valeur": vals[-1] if vals else a["capital_initial"],
            "parametres": a["parametres"], **m,
            "correlation_reference": mesures.correlation(mesures.rendements(vals), mesures.rendements(ref)),
        })
    return {
        "debut": etat["debut"], "au": etat["au"], "source": etat["source_donnees"],
        "jours": len(eq), "equipe": mesures.resume(eq), "reference": mesures.resume(ref),
        "reference_ticker": etat["reference"]["ticker"],
        "valeur_equipe": eq[-1] if eq else etat["equipe"]["capital"],
        "valeur_reference": ref[-1] if ref else etat["reference"]["capital"],
        "agents": lignes,
    }


def markdown(etat, evenements_recents, savoir):
    s = synthese(etat)
    out = ["# Rapport de l'équipe au %s" % s["au"], ""]
    if s["source"] == "synthetique":
        out += ["> **DONNÉES SYNTHÉTIQUES.** Test de mécanique uniquement : ces chiffres ne disent rien "
                "de la rentabilité réelle.", ""]
    out += ["%d jours de cotation depuis le %s. Mode papier." % (s["jours"], s["debut"]), "",
            "| | Valeur | Rendement | Annualisé | Vol | Sharpe | Drawdown max |",
            "|---|---:|---:|---:|---:|---:|---:|"]

    def row(nom, v, m):
        return "| %s | %s $ | %s | %s | %.1f %% | %.2f | %.1f %% |" % (
            nom, "{:,.0f}".format(v).replace(",", " "), _pct(m["rendement"]), _pct(m["annualise"]),
            m["vol"] * 100, m["sharpe"], m["drawdown_max"] * 100)

    out.append(row("**Équipe**", s["valeur_equipe"], s["equipe"]))
    out.append(row("Référence %s" % s["reference_ticker"], s["valeur_reference"], s["reference"]))
    for a in s["agents"]:
        out.append(row("%s%s (gén. %d)" % (a["agent"], " ⏸" if a["en_pause"] else "", a["generation"]), a["valeur"], a))
    out += ["", "## Réglages actuels", ""]
    for a in s["agents"]:
        out.append("- **%s** (%s) : %s" % (a["agent"], a["strategie"],
                                            ", ".join("%s=%s" % kv for kv in a["parametres"].items())))
    out += ["", "## Événements récents", ""]
    notables = [e for e in evenements_recents if e["type"] not in BRUIT][-30:]
    out += ["- %s · %s" % (e["date"], e.get("texte", e["type"])) for e in notables] or ["- Rien de notable."]
    out += ["", "## Derniers éléments du savoir partagé", ""]
    out += ["- %s · %s" % (l["date"], l["texte"]) for l in savoir[-15:]] or ["- Vide pour l'instant."]
    return "\n".join(out) + "\n"


def tableau_de_bord(etat, evenements_recents, savoir, titre="Équipe de trading"):
    s = synthese(etat)
    dates = [d for d, _ in etat["equipe"]["historique"]]
    series = {
        "equipe": [v for _, v in etat["equipe"]["historique"]],
        "reference": [v for _, v in etat["reference"]["historique"]],
        "agents": {n: [v for _, v in a["historique"]] for n, a in etat["agents"].items()},
    }
    payload = json.dumps({"dates": dates, "series": series, "synthese": s,
                          "evenements": [e for e in evenements_recents if e["type"] not in BRUIT][-40:],
                          "savoir": savoir[-20:]}, ensure_ascii=False).replace("</", "<\\/")
    return GABARIT.replace("__TITRE__", html.escape(titre)).replace("__DATA__", payload)


GABARIT = r"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITRE__</title>
<style>
:root{color-scheme:light;--bg:#f7f7f5;--surface:#fcfcfb;--border:#e4e3df;--grid:#ecebe7;--text:#0b0b0b;--text2:#52514e;--muted:#7a7974;
--s1:#2a78d6;--ref:#8a8984;--good:#0ca30c;--critical:#d03b3b;--warn-bg:#fff4d6;--warn-text:#6b4a00}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#121211;--surface:#1a1a19;--border:#2e2e2b;--grid:#262624;
--text:#f0efec;--text2:#c3c2b7;--muted:#8f8e88;--s1:#3987e5;--ref:#8f8e88;--warn-bg:#3a2d0a;--warn-text:#f5d27a}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#121211;--surface:#1a1a19;--border:#2e2e2b;--grid:#262624;
--text:#f0efec;--text2:#c3c2b7;--muted:#8f8e88;--s1:#3987e5;--ref:#8f8e88;--warn-bg:#3a2d0a;--warn-text:#f5d27a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 12px}.sub{color:var(--text2);margin:0 0 16px}
.banner{background:var(--warn-bg);color:var(--warn-text);border-radius:8px;padding:10px 14px;margin:12px 0;font-weight:600}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px}
.tile .k{color:var(--text2);font-size:13px}.tile .v{font-size:24px;font-weight:650;font-variant-numeric:tabular-nums}
.tile .d{font-size:13px;color:var(--text2);font-variant-numeric:tabular-nums}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px;position:relative}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--text2);margin-bottom:6px}
.legend i{display:inline-block;width:14px;height:2px;vertical-align:middle;margin-right:6px}
.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}
.grid4 h3{font-size:14px;margin:0}.grid4 .meta{font-size:12px;color:var(--text2);margin:0 0 6px}
svg{display:block;width:100%;height:auto;overflow:visible}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:6px 8px;font-size:12px;
box-shadow:0 2px 8px rgba(0,0,0,.12);display:none;white-space:nowrap;font-variant-numeric:tabular-nums;z-index:2}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;border-bottom:1px solid var(--border);text-align:right}th:first-child,td:first-child{text-align:left}
th{color:var(--text2);font-weight:600}ul{padding-left:18px;margin:0}li{margin:4px 0}.date{color:var(--muted);font-variant-numeric:tabular-nums}
.pause{color:var(--critical);font-weight:600}
</style></head><body><main>
<h1>__TITRE__</h1><p class="sub" id="sub"></p><div id="banner"></div>
<div class="tiles" id="tiles"></div>
<h2>Équipe contre référence</h2>
<div class="card"><div class="legend" id="leg-main"></div><div id="main-chart"></div></div>
<h2>Chaque agent</h2><p class="sub">Ligne bleue : l'agent. Ligne grise : la référence, ramenée à son capital de départ.</p>
<div class="grid4" id="agents"></div>
<h2>Tableau</h2><div class="card scroll"><table id="table"></table></div>
<h2>Événements récents</h2><div class="card"><ul id="events"></ul></div>
<h2>Savoir partagé</h2><div class="card"><ul id="savoir"></ul></div>
</main>
<script>
const D=__DATA__;const S=D.synthese;
const fmt$=v=>new Intl.NumberFormat('fr-FR',{maximumFractionDigits:0}).format(v)+' $';
const pct=v=>(v>=0?'+':'')+(v*100).toFixed(1).replace('.',',')+' %';
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
document.getElementById('sub').textContent=`Du ${S.debut||'—'} au ${S.au||'—'} · ${S.jours} jours de cotation · mode papier · données : ${S.source}`;
if(S.source==='synthetique')document.getElementById('banner').innerHTML='<div class="banner">Données synthétiques : test de la mécanique uniquement. Ces chiffres ne disent rien de la rentabilité réelle.</div>';
const tiles=[['Valeur équipe',fmt$(S.valeur_equipe),pct(S.equipe.rendement)],['Référence '+S.reference_ticker,fmt$(S.valeur_reference),pct(S.reference.rendement)],
['Écart équipe − référence',pct(S.equipe.rendement-S.reference.rendement).replace(' %',' pts'),'sur la période'],['Drawdown max équipe',(S.equipe.drawdown_max*100).toFixed(1).replace('.',',')+' %','référence : '+(S.reference.drawdown_max*100).toFixed(1).replace('.',',')+' %'],
['Sharpe équipe',S.equipe.sharpe.toFixed(2).replace('.',','),'référence : '+S.reference.sharpe.toFixed(2).replace('.',',')]];
document.getElementById('tiles').innerHTML=tiles.map(t=>`<div class="tile"><div class="k">${esc(t[0])}</div><div class="v">${esc(t[1])}</div><div class="d">${esc(t[2])}</div></div>`).join('');

function chart(el,series,{h=260,small=false}={}){
  const W=small?320:Math.max(320,Math.min(900,el.clientWidth||900)),H=small?150:(W<600?220:h),ml=small?8:56,mr=small?8:16,mt=10,mb=small?8:26;
  const n=D.dates.length;if(n<2){el.innerHTML='<p class="sub">Pas encore assez de jours pour tracer.</p>';return}
  let lo=Infinity,hi=-Infinity;series.forEach(s=>s.v.forEach(x=>{if(x<lo)lo=x;if(x>hi)hi=x}));const pad=(hi-lo)*.06||1;lo-=pad;hi+=pad;
  const X=i=>ml+(W-ml-mr)*i/(n-1),Y=v=>mt+(H-mt-mb)*(1-(v-lo)/(hi-lo));
  let g='';
  if(!small){for(let k=0;k<=4;k++){const v=lo+(hi-lo)*k/4,y=Y(v);g+=`<line x1="${ml}" x2="${W-mr}" y1="${y}" y2="${y}" stroke="var(--grid)"/><text x="${ml-6}" y="${y+4}" text-anchor="end" font-size="11" fill="var(--muted)">${new Intl.NumberFormat('fr-FR',{notation:'compact'}).format(v)}</text>`}
    [0,Math.floor(n/2),n-1].forEach(i=>{g+=`<text x="${X(i)}" y="${H-6}" text-anchor="${i===0?'start':i===n-1?'end':'middle'}" font-size="11" fill="var(--muted)">${D.dates[i]}</text>`})}
  series.forEach(s=>{g+=`<path d="${s.v.map((x,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(x).toFixed(1)).join('')}" fill="none" stroke="${s.c}" stroke-width="2" stroke-linejoin="round" ${s.dash?'stroke-dasharray="4 3"':''}/>`});
  g+=`<line class="x" y1="${mt}" y2="${H-mb}" stroke="var(--muted)" stroke-width="1" visibility="hidden"/>`;
  series.forEach((s,k)=>{g+=`<circle class="m${k}" r="4" fill="${s.c}" stroke="var(--surface)" stroke-width="2" visibility="hidden"/>`});
  el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(series.map(s=>s.n).join(', '))}">${g}<rect x="${ml}" y="0" width="${W-ml-mr}" height="${H}" fill="transparent"/></svg><div class="tip"></div>`;
  const svg=el.querySelector('svg'),tip=el.querySelector('.tip'),xl=svg.querySelector('.x');
  svg.addEventListener('pointermove',e=>{const r=svg.getBoundingClientRect(),px=(e.clientX-r.left)*W/r.width;
    const i=Math.max(0,Math.min(n-1,Math.round((px-ml)/(W-ml-mr)*(n-1))));xl.setAttribute('x1',X(i));xl.setAttribute('x2',X(i));xl.setAttribute('visibility','visible');
    series.forEach((s,k)=>{const m=svg.querySelector('.m'+k);m.setAttribute('cx',X(i));m.setAttribute('cy',Y(s.v[i]));m.setAttribute('visibility','visible')});
    tip.innerHTML=`<div class="date">${D.dates[i]}</div>`+series.map(s=>`<div><i style="display:inline-block;width:10px;height:2px;background:${s.c};vertical-align:middle;margin-right:6px"></i>${esc(s.n)} : <b>${fmt$(s.v[i])}</b></div>`).join('');
    tip.style.display='block';const er=el.getBoundingClientRect();let lx=e.clientX-er.left+12;if(lx+tip.offsetWidth>er.width)lx=e.clientX-er.left-tip.offsetWidth-12;
    tip.style.left=lx+'px';tip.style.top=(e.clientY-er.top-10)+'px'});
  svg.addEventListener('pointerleave',()=>{tip.style.display='none';xl.setAttribute('visibility','hidden');svg.querySelectorAll('circle').forEach(c=>c.setAttribute('visibility','hidden'))});
}
const main=[{n:'Équipe',v:D.series.equipe,c:'var(--s1)'},{n:'Référence '+S.reference_ticker,v:D.series.reference,c:'var(--ref)',dash:true}];
document.getElementById('leg-main').innerHTML=main.map(s=>`<span><i style="background:${s.c}"></i>${esc(s.n)}</span>`).join('');
chart(document.getElementById('main-chart'),main);
const ref0=D.series.reference[0]||1;
const ag=document.getElementById('agents');
S.agents.forEach(a=>{const v=D.series.agents[a.agent];const c=document.createElement('div');c.className='card';
  c.innerHTML=`<h3>${esc(a.agent)} ${a.en_pause?'<span class="pause">⏸ en pause</span>':''}</h3><p class="meta">${esc(a.strategie)} · génération ${a.generation} · ${pct(a.rendement)} · drawdown max ${(a.drawdown_max*100).toFixed(1).replace('.',',')} %</p><div></div>`;
  ag.appendChild(c);const cap=v[0]||1;chart(c.lastElementChild,[{n:a.agent,v,c:'var(--s1)'},{n:'Référence',v:D.series.reference.map(x=>x/ref0*cap),c:'var(--ref)',dash:true}],{small:true})});
const rows=[['Équipe',S.valeur_equipe,S.equipe],['Référence '+S.reference_ticker,S.valeur_reference,S.reference],...S.agents.map(a=>[a.agent+(a.en_pause?' ⏸':''),a.valeur,a])];
document.getElementById('table').innerHTML='<tr><th></th><th>Valeur</th><th>Rendement</th><th>Annualisé</th><th>Vol</th><th>Sharpe</th><th>Drawdown max</th></tr>'+
rows.map(r=>`<tr><td>${esc(r[0])}</td><td>${fmt$(r[1])}</td><td>${pct(r[2].rendement)}</td><td>${pct(r[2].annualise)}</td><td>${(r[2].vol*100).toFixed(1).replace('.',',')} %</td><td>${r[2].sharpe.toFixed(2).replace('.',',')}</td><td>${(r[2].drawdown_max*100).toFixed(1).replace('.',',')} %</td></tr>`).join('');
const li=xs=>xs.length?xs.slice().reverse().map(e=>`<li><span class="date">${esc(e.date)}</span> · ${esc(e.texte||e.type)}</li>`).join(''):'<li>Rien pour l’instant.</li>';
document.getElementById('events').innerHTML=li(D.evenements);document.getElementById('savoir').innerHTML=li(D.savoir);
</script></body></html>
"""
