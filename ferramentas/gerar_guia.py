"""Gera o guia da trilha prática (guia_pdf/guia_trilha.html -> Guia_de_Estudos.pdf) a partir das missões.

Uso (na raiz):  .venv\\Scripts\\python.exe ferramentas\\gerar_guia.py   (precisa do Microsoft Edge)
"""
import html
import importlib.util
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
E = html.escape


def carregar(arq):
    spec = importlib.util.spec_from_file_location(arq.stem, arq)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


linhas, total = [], 0
for arq in sorted((RAIZ / "ferramentas" / "missoes").glob("cap*.py")):
    m = carregar(arq)
    n = int(re.search(r"\d+", arq.stem).group())
    passos = sum(1 for p in m.PASSOS if p[0] in ("tarefa", "arquivo"))
    modulos = [p[2] for p in m.PASSOS if p[0] == "arquivo"]
    total += passos
    linhas.append(f"<tr><td>{n}</td><td><b>{E(m.TITULO)}</b><br><span class='p'>{re.sub(r'`([^`]+)`', r'<code>\1</code>', E(m.ENTREGA.replace('PKG/', '')))}</span></td>"
                  f"<td>{passos}</td><td><code>{'<br>'.join(E(x) for x in modulos) or '-'}</code></td></tr>")

CSS = """
@page{size:A4;margin:16mm 15mm 18mm 15mm}html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Segoe UI",Calibri,Arial,sans-serif;color:#1f2933;font-size:11pt;line-height:1.55;margin:0}
.pg{break-after:page}.capa{height:250mm;display:flex;flex-direction:column;justify-content:center;
background:linear-gradient(160deg,#2f2a6b,#2f7d6d);color:#fff;border-radius:10px;padding:0 16mm}
.capa .tag{letter-spacing:.2em;text-transform:uppercase;font-size:10pt;opacity:.85}
.capa h1{font-size:30pt;margin:4mm 0 2mm;line-height:1.15}.capa h2{font-weight:400;font-size:15pt;color:#fff;border:0;margin:0 0 10mm}
.capa .lema{font-size:13pt;border-left:4px solid #9fe0c9;padding-left:5mm;max-width:145mm}
h2{color:#2f2a6b;font-size:18pt;margin:0 0 4mm;padding-bottom:2mm;border-bottom:2px solid #e6eef6}
h3{color:#2f2a6b;font-size:13pt;margin:6mm 0 2mm}code{font-family:Consolas,monospace;font-size:9.3pt;background:#f2f5f8;padding:0 4px;border-radius:3px}
kbd{border:1px solid #c9d2db;border-bottom-width:2px;border-radius:4px;padding:0 5px;font-size:9.5pt}
.passo{display:flex;gap:4mm;margin:0 0 3.5mm;break-inside:avoid}.n{flex:0 0 9mm;height:9mm;border-radius:50%;background:#2f2a6b;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700}
.box{border-radius:7px;padding:3mm 5mm;margin:3mm 0;break-inside:avoid}.dica{background:#e8f5ee;border-left:4px solid #2e7d5b}.aviso{background:#fff5df;border-left:4px solid #a86b00}
table{border-collapse:collapse;width:100%;font-size:9.8pt;margin:2mm 0}th{background:#2f2a6b;color:#fff;text-align:left;padding:2mm}
td{padding:1.6mm 2mm;border-bottom:1px solid #e3e8ee;vertical-align:top}tr:nth-child(even) td{background:#f7f9fb}.p{color:#5b6b7a;font-size:9pt}
.linha{display:flex;gap:3mm;margin:2mm 0}.min{flex:0 0 22mm;font-weight:700;color:#2f7d6d}
"""

corpo = f"""
<section class="pg capa"><div class="tag">Guia de estudos · trilha prática</div>
<h1>AI Engineering</h1><h2>Chip Huyen (edição em inglês) — da teoria ao assistente completo</h2>
<p class="lema">Menos leitura, mais construção: cada capítulo é uma missão que acrescenta uma peça ao assistente de
suporte da Nimbus. No fim você terá avaliação, RAG, agente, guardrails, cache, roteador e monitoramento, tudo escrito por você.</p></section>

<section class="pg"><h2>1. Como a trilha funciona</h2>
<div class="passo"><div class="n">1</div><div><b>Missão</b>: o topo de cada caderno diz o que você vai construir e por quê.</div></div>
<div class="passo"><div class="n">2</div><div><b>Leitura essencial (opcional)</b>: só as seções que importam, com a página do PDF em inglês. Leia quando um passo gerar dúvida, não antes.</div></div>
<div class="passo"><div class="n">3</div><div><b>Passos</b>: uma explicação curta e uma célula vazia. Digite, rode com <kbd>Shift</kbd>+<kbd>Enter</kbd> e veja o resultado.</div></div>
<div class="passo"><div class="n">4</div><div><b>Módulos do projeto</b>: os passos com <code>%%writefile</code> gravam arquivos em <code>meu_assistente/</code>. Os capítulos seguintes importam esses arquivos, então faça na ordem.</div></div>
<div class="passo"><div class="n">5</div><div><b>Gabarito</b> em <code>resolvidos/</code>, com o mesmo passo pronto. Travou por mais de 10 minutos? Olhe, entenda e digite de novo sem copiar.</div></div>
<h3>Custos e modo simulado</h3>
<p>Os passos chamam modelos reais pelo OpenRouter, e a maioria custa frações de centavo (veja <code>gasto()</code>). Para testar sem gastar, rode o Jupyter com a variável <code>IA_FAKE=1</code>: as respostas são falsas, mas têm o mesmo formato. Os números do modo simulado <b>não</b> refletem a qualidade dos modelos.</p>
<div class="box aviso">Os capítulos 3, 4, 8 e 10 usam o modelo forte como juiz, e cada avaliação completa faz algumas dezenas de chamadas. Ainda é barato, mas acompanhe o <code>gasto()</code>.</div>
<h3>Primeira vez</h3>
<div class="passo"><div class="n">1</div><div>Abra o VS Code pelo atalho <b>Projetos e Estudos</b> e entre na pasta do AI Engineering.</div></div>
<div class="passo"><div class="n">2</div><div>Abra <code>praticar/cap01_…ipynb</code>, clique em <b>Select Kernel</b> e escolha o <b>.venv</b> desta pasta.</div></div>
<div class="passo"><div class="n">3</div><div>Rode a Preparação. Deve aparecer <i>Pronto. Modelo: openai/gpt-4o-mini | modo simulado: False</i>.</div></div>
</section>

<section class="pg"><h2>2. Mapa da trilha ({total} passos)</h2>
<table><tr><th>Cap.</th><th>Missão e entrega</th><th>Passos</th><th>Módulos</th></tr>{''.join(linhas)}</table></section>

<section class="pg"><h2>3. Rotina de 60 minutos</h2>
<div class="linha"><div class="min">0–5 min</div><div>Rode a Preparação e releia o Fechamento da última sessão.</div></div>
<div class="linha"><div class="min">5–45 min</div><div>Faça 2 a 4 passos. Antes de rodar, escreva numa linha o que você espera que aconteça e compare com o resultado.</div></div>
<div class="linha"><div class="min">45–55 min</div><div>Mude um parâmetro e veja o efeito: temperatura, k da busca, limiar do cache, a rubrica do juiz...</div></div>
<div class="linha"><div class="min">55–60 min</div><div>Preencha o Fechamento e faça commit + Sync no VS Code.</div></div>
<h3>Para ir além (desafios)</h3>
<ul><li>Rode o capítulo 4 e o 10 sem o modo simulado e guarde os números: esse é o seu "antes e depois".</li>
<li>Troque o <code>MODELO</code> por um modelo aberto do OpenRouter e compare a nota por dólar.</li>
<li>Escreva 10 perguntas reais sobre a Nimbus e acrescente ao conjunto de avaliação.</li>
<li>Coloque o <code>Assistente</code> atrás de uma API FastAPI com streaming. O curso RAG agêntico de produção mostra como.</li></ul>
<div class="box dica">A versão anterior (sobre a tradução em português) continua em <code>versao_anterior_pt/</code>, com o seu progresso.</div>
</section>
"""

saida = RAIZ / "guia_pdf" / "guia_trilha.html"
saida.parent.mkdir(exist_ok=True)
saida.write_text(f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Guia AI Engineering</title>'
                 f"<style>{CSS}</style></head><body>{corpo}</body></html>", encoding="utf-8")
pdf = RAIZ / "Guia_de_Estudos.pdf"
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
import tempfile
perfil = tempfile.mkdtemp(prefix="edge_guia_")      # perfil separado: funciona mesmo com o Edge aberto
subprocess.run([edge, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", saida.as_uri()], check=True, capture_output=True, timeout=120)
print("Guia gerado:", pdf, pdf.exists())
