#!/usr/bin/env python3
"""Build the existing landing page and focused, static informational pages."""
from pathlib import Path
from html import escape
from copy import deepcopy
import re,json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
# Always write UTF-8 with LF so the build is identical on Windows, macOS and Linux.
def W(path,text):path.write_text(text,encoding='utf-8',newline='\n')
BASE='https://guaratickets.com.br'
HOME=(ROOT/'src/home.html').read_text(encoding='utf-8')
DATE='2026-11-23'
SRC=ROOT/'src'
# Rates live in data/taxas.json so changing a number never means editing code.
TAXAS=json.loads((ROOT/'data/taxas.json').read_text(encoding='utf-8'))
def check_taxas(t):
 """Stop the build with a plain message if the rates file is inconsistent."""
 def erro(msg):raise SystemExit('data/taxas.json: '+msg)
 faixas=t['alimentacao_refeicao']
 limites=[f['ate_reais'] for f in faixas]
 if limites[-1] is not None or None in limites[:-1]:erro('só a última faixa deve ter "ate_reais": null.')
 if limites[:-1]!=sorted(set(limites[:-1])):erro('os limites das faixas devem ser crescentes e sem repetição.')
 for taxa in [f['taxa'] for f in faixas]+[t['outros_beneficios'],t['cartao_credito']]:
  if not 0<taxa<100:erro(f'a taxa {taxa} precisa estar entre 0 e 100.')
check_taxas(TAXAS)
def minify(text):
 """Small, safe minifier: drops comments and the whitespace around braces and semicolons."""
 text=re.sub(r'/\*.*?\*/','',text,flags=re.S)
 text=re.sub(r'\s+',' ',text)
 return re.sub(r' ?([{};]) ?',r'\1',text).replace(';}','}').strip()
css=minify((SRC/'site.css').read_text(encoding='utf-8'))
cssname='site-'+hashlib.sha256(css.encode()).hexdigest()[:10]+'.css'
W(OUT/'assets'/cssname,css)
# The stylesheet name carries a content hash; drop older builds so dist never ships orphans.
for old in (OUT/'assets').glob('site-*.css'):
 if old.name!=cssname:old.unlink()
# Scripts are served as written, except that the __TAXAS__ placeholder in simulador.js becomes data/taxas.json.
def inject_taxas(js):
 if js.count('__TAXAS__')!=1:raise SystemExit('src/simulador.js: o marcador __TAXAS__ deve aparecer exatamente uma vez.')
 return js.replace('__TAXAS__',json.dumps(TAXAS,ensure_ascii=False,separators=(',',':')))
W(OUT/'assets/simulador.js',inject_taxas((SRC/'simulador.js').read_text(encoding='utf-8')))
W(OUT/'assets/navegacao.js',(SRC/'navegacao.js').read_text(encoding='utf-8'))
org=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',HOME,re.S)[1])
org['image']=BASE+'/assets/compartilhamento-guara.png'
org['description']='Atendimento de VR, vale-alimentação, vale-refeição e cartões de benefícios com Israel, proprietário do Guará Mix, no Jardim Umarizal/Campo Limpo, São Paulo. Região sul, centro e zona oeste da capital.'
WA_ICON=re.search(r'(<svg class="wa-icon".*?</svg>)',HOME,re.S)[1]
WA='https://wa.me/5511940240988'
def wa(label='Falar com Israel',cls='btn',message=None):
 from urllib.parse import quote
 href=WA+('?text='+quote(message) if message else '')
 return f'<a class="{cls}" href="{href}" target="_blank" rel="noopener">{escape(label)} {WA_ICON}</a>'
links=[('/', 'Início'),('/vender-vr/','VR e cartões'),('/vale-refeicao/','Vale-refeição'),('/vale-alimentacao/','Vale-alimentação'),('/taxas/','Taxas e simulador'),('/como-funciona/','Como funciona'),('/atendimento-sao-paulo/','Atendimento em São Paulo'),('/duvidas/','Dúvidas'),('/sobre/','Quem atende')]
header=re.search(r'<header>.*?</header>',HOME,re.S)[0]
menu='<details class="mobile-menu"><summary>Menu</summary><nav aria-label="Navegação pelo site">'+''.join(f'<a href="{u}">{t}</a>'for u,t in links)+'</nav></details>'
header=header.replace('</nav></header>',menu+'</nav></header>')
footer=re.search(r'<footer>.*?</footer>',HOME,re.S)[0]
flinks=links[1:]+[('/condicoes/','Condições do atendimento'),('/privacidade/','Privacidade')]
footer=footer.replace('</footer>','<nav class="wrap site-links" aria-label="Informações e páginas do site">'+''.join(f'<a href="{u}">{t}</a>'for u,t in flinks)+'</nav><p class="wrap footer-legal">© 2026 Guará Tickets</p></footer>')
fixed=re.search(r'<a class="btn mobile-contact".*?</a>',HOME,re.S)[0]
# Mensagem que já vem preenchida nos botões de WhatsApp do topo e do botão fixo do celular.
# Deixe '' para abrir a conversa em branco.
DEFAULT_WA_MESSAGE='Olá! Vi o site da Guará Tickets e quero consultar o valor dos meus cartões.'
if DEFAULT_WA_MESSAGE:
 from urllib.parse import quote
 bare=f'href="{WA}"';filled=f'href="{WA}?text={quote(DEFAULT_WA_MESSAGE)}"'
 header=header.replace(bare,filled);fixed=fixed.replace(bare,filled)
headbase=HOME[HOME.index('<head>')+6:HOME.index('</head>')]
headbase=re.sub(r'<script type="application/ld\+json">.*?</script>','',headbase,flags=re.S)
def schema(path,title):
 url=BASE+path
 graph=[deepcopy(org),{'@type':'WebSite','@id':BASE+'/#website','url':BASE+'/','name':'Guará Tickets','inLanguage':'pt-BR','publisher':{'@id':org['@id']}},{'@type':'WebPage','@id':url+'#pagina','url':url,'name':title,'inLanguage':'pt-BR','isPartOf':{'@id':BASE+'/#website'},'about':{'@id':org['@id']}}]
 if path!='/':graph.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Início','item':BASE+'/'},{'@type':'ListItem','position':2,'name':title.split(' | ')[0],'item':url}]})
 return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,separators=(',',':'))+'</script>'
def head(path,title,desc,noindex=False):
 h=re.sub(r'<title>.*?</title>','<title>'+escape(title)+'</title>',headbase,flags=re.S)
 for attr,val in [('name="description"',desc),('property="og:title"',title),('property="og:description"',desc),('name="twitter:title"',title),('name="twitter:description"',desc),('property="og:url"',BASE+path)]:
  h=re.sub(r'(<meta '+re.escape(attr)+r' content=")[^"]*(">)',lambda m:m[1]+escape(val,quote=True)+m[2],h)
 h=re.sub(r'(<link rel="canonical" href=")[^"]*(">)',lambda m:m[1]+BASE+path+m[2],h)
 h+='<meta name="robots" content="'+('noindex,follow'if noindex else'index,follow,max-image-preview:large')+'">\n'
 h+=f'<link rel="stylesheet" href="/assets/{cssname}">\n'
 return '<head>'+h+(''if noindex else schema(path,title))+'</head>'
def layout(path,title,desc,main,hascalc=False,noindex=False):
 scripts='<script src="/assets/navegacao.js" defer></script>'
 if hascalc:scripts+='<script src="/assets/simulador.js" defer></script>'
 return '<!doctype html><html lang="pt-BR">'+head(path,title,desc,noindex)+'<body><a class="skip-link" href="#conteudo">Pular para o conteúdo</a>'+header+'<main id="conteudo">'+main+'</main>'+footer+fixed+scripts+'</body></html>'
def hero(title,intro,label):return f'<section class="page-hero"><div class="wrap"><nav class="breadcrumb" aria-label="Caminho da página"><a href="/">Início</a><span aria-hidden="true">/</span><span>{escape(label)}</span></nav><h1>{title}</h1><p class="intro">{intro}</p></div></section>'
def sidebar():return '<aside class="info-panel"><h2>Fale com Israel</h2><p>Zona sul, centro e zona oeste de SP. Agende com no mínimo 3 dias de antecedência. Pagamento via Pix.</p>'+wa('Falar no WhatsApp')+'<nav class="related-links" aria-label="Continue sua consulta"><a href="/taxas/">Ver taxas e simular</a><a href="/como-funciona/">Como funciona</a></nav></aside>'
def prose(body):return '<section class="page-body"><div class="wrap reading-layout"><div class="prose">'+body+'</div>'+sidebar()+'</div></section>'
def extract(id):return re.search(r'<section[^>]*id="'+re.escape(id)+r'".*?</section>',HOME,re.S)[0]
# The simulator ticket is marked in the source so the home hero and /taxas/ share one copy.
SIM=re.search(r'<!--sim:start-->(.*?)<!--sim:end-->',HOME,re.S)[1].strip()
faq=re.findall(r'<details>.*?</details>',extract('duvidas'),re.S)
examples='''<div class="table-scroll"><table class="example-table"><caption>Exemplos para alimentação e refeição</caption><thead><tr><th scope="col">Valor bruto</th><th scope="col">Taxa</th><th scope="col">Desconto</th><th scope="col">Você recebe</th></tr></thead><tbody><tr><td>R$ 1.000,00</td><td>17%</td><td>R$ 170,00</td><td>R$ 830,00</td></tr><tr><td>R$ 1.500,00</td><td>16%</td><td>R$ 240,00</td><td>R$ 1.260,00</td></tr><tr><td>R$ 2.500,00</td><td>15%</td><td>R$ 375,00</td><td>R$ 2.125,00</td></tr></tbody></table></div>'''
PAGES={}
# Breadcrumbs use the short menu names so they fit on one line on phones.
SHORT=dict(links)|{'/condicoes/':'Condições','/privacidade/':'Privacidade'}
def page(slug,title,h1,intro,body):PAGES['/'+slug+'/']={'title':title+' | Guará Tickets','h1':h1,'desc':intro,'main':hero(h1,intro,SHORT['/'+slug+'/'])+prose(body),'calc':False}
page('vender-vr','VR em São Paulo: modalidades, taxas e consulta','VR em São Paulo: consulte sua modalidade e o valor a receber','Veja as informações para consultar VR Alimentação e VR Refeição com Israel. Atendimento na região sul, centro e zona oeste de São Paulo.', '''<h2>Primeiro, identifique a modalidade do cartão</h2><p>VR é uma das bandeiras apresentadas pela Guará Tickets. Na consulta, informe se o cartão é de alimentação ou refeição. A bandeira e a modalidade ajudam Israel a confirmar a disponibilidade e as condições do atendimento.</p><p>Também são mencionadas Ticket, Alelo e Pluxee. Não existe aprovação automática pelo site: a confirmação é feita pelo WhatsApp.</p><h2>O que informar na primeira mensagem</h2><ol><li>Nome da bandeira e modalidade do cartão.</li><li>Valor que pretende consultar em cada cartão e o total.</li><li>Região de São Paulo e data pretendida para o atendimento.</li></ol><p>Você não precisa inserir número de cartão, senha ou código de segurança no site. O simulador pede somente o tipo de benefício e o valor.</p><h2>Como o total define a taxa</h2><p>Para alimentação e refeição, as faixas anunciadas são 17% até R$ 1.000,00; 16% de R$ 1.000,01 a R$ 2.000,00; e 15% acima de R$ 2.000,00. A faixa é aplicada ao valor total, e não somente à parte que ultrapassa o limite.</p><p>Por exemplo, R$ 1.500,00 correspondem à faixa de 16%: o desconto é de R$ 240,00 e o recebimento estimado é de R$ 1.260,00. <a href="/taxas/">Veja outros exemplos e use o simulador.</a></p><h2>Agendamento e local</h2><p>Agende com pelo menos 3 dias de antecedência. A base do atendimento é o Guará Mix, no Jardim Umarizal/Campo Limpo. A cobertura é somente região sul, centro e zona oeste da capital. Atendimento no local do cliente tem taxa de motoboy combinada à parte.</p><h2>Continue pela modalidade</h2><ul><li><a href="/vale-refeicao/">Informações sobre vale-refeição.</a></li><li><a href="/vale-alimentacao/">Informações sobre vale-alimentação e soma de cartões.</a></li><li><a href="/condicoes/">Condições comerciais e confirmação antes do atendimento.</a></li></ul>''')
page('vale-refeicao','Vale-refeição em São Paulo: cartões e atendimento','Vale-refeição: cartões, taxas e atendimento em São Paulo','Consulte sua modalidade de vale-refeição, entenda o cálculo do valor líquido e saiba o que combinar antes do atendimento.', '''<h2>Vale-refeição e bandeira são informações diferentes</h2><p>O nome da bandeira, como VR, Ticket, Alelo ou Pluxee, identifica a marca do cartão. A modalidade informa se o benefício é de refeição ou alimentação. Na primeira consulta, envie as duas informações para Israel confirmar o atendimento.</p><p>Vale-refeição é normalmente associado a refeições prontas. Se o seu cartão tem mais de uma modalidade, informe qual saldo deseja consultar; não presuma que todos os saldos ou produtos de uma mesma marca têm as mesmas condições.</p><h2>O cálculo usa o valor bruto informado</h2><p>A faixa da taxa anunciada depende do total dos cartões de alimentação e refeição. Em um total de R$ 1.000,00, a taxa é 17%, equivalente a R$ 170,00, e o valor estimado a receber é R$ 830,00. Se o total for R$ 1.500,00, a faixa passa a 16%, com estimativa de R$ 1.260,00 recebidos.</p><p><a href="/taxas/">Confira a tabela completa e faça sua própria simulação.</a> A estimativa não substitui a confirmação das condições pelo WhatsApp.</p><h2>Checklist antes de sair de casa</h2><ul><li>Confirme a disponibilidade para a bandeira e modalidade.</li><li>Combine valor bruto, desconto e valor líquido.</li><li>Agende com pelo menos 3 dias de antecedência e confirme o local.</li><li>Se o atendimento for até você, confirme a taxa de motoboy.</li><li>Combine o recebimento, que é somente via Pix.</li></ul><h2>Quem responde e qual é a cobertura?</h2><p>Israel, proprietário do Guará Mix, realiza o atendimento. Estamos no Jardim Umarizal/Campo Limpo e atendemos somente a região sul, o centro e a zona oeste de São Paulo — SP.</p><p>Para outra modalidade, consulte a página de <a href="/vale-alimentacao/">vale-alimentação</a>. Para entender o fluxo completo, veja <a href="/como-funciona/">como funciona o atendimento</a>.</p>''')
page('vale-alimentacao','Vale-alimentação em SP: soma dos cartões e taxas','Vale-alimentação: entenda o total dos cartões e as taxas','Veja como organizar sua consulta de vale-alimentação e calcular a estimativa considerando vários cartões no mesmo atendimento.', '''<h2>Informe o saldo da modalidade correta</h2><p>Vale-alimentação é normalmente associado à compra de gêneros alimentícios. Se o seu cartão também tem outras modalidades ou saldos, identifique qual deles está consultando. O nome da bandeira sozinho não define todas as condições.</p><p>VR, Ticket, Alelo e Pluxee são as bandeiras apresentadas para alimentação e refeição. A disponibilidade da modalidade precisa ser confirmada com Israel pelo WhatsApp.</p><h2>Como funciona a soma de cartões</h2><p>Para a tabela de alimentação e refeição, o que define a faixa é o valor total dos cartões do atendimento. Você pode informar os valores separados para facilitar a conferência.</p><p>Exemplo: um cartão de R$ 600,00 e outro de R$ 700,00 totalizam R$ 1.300,00. Esse total está na faixa de 16%. O desconto estimado é de R$ 208,00 e o valor líquido é de R$ 1.092,00.</p><p>A tabela é: 17% até R$ 1.000,00; 16% de R$ 1.000,01 a R$ 2.000,00; 15% acima de R$ 2.000,00. <a href="/taxas/">Abra o simulador para conferir outro total.</a></p><h2>O que confirmar no agendamento</h2><p>Confirme a bandeira, a modalidade, o valor bruto e o valor líquido com Israel. As taxas anunciadas consideram agendamento com pelo menos 3 dias de antecedência. Sem agendamento, a taxa é maior e deve ser consultada.</p><p>O pagamento é somente via Pix. Atendimento no local do cliente tem taxa de motoboy, combinada antes. A cobertura é somente região sul, centro e zona oeste de São Paulo.</p><h2>Outros benefícios têm outra condição</h2><p>iFood, Swile, Flash e Caju aparecem no grupo de outros benefícios, com taxa anunciada de 15% e disponibilidade sujeita à modalidade. Não misture esse grupo com a tabela de alimentação e refeição sem confirmar com Israel.</p><p>Leia as <a href="/condicoes/">condições do atendimento</a> e as informações de <a href="/vale-refeicao/">vale-refeição</a> se essa for a modalidade do seu cartão.</p>''')
page('como-funciona','Como funciona: consulta, agendamento e Pix','Como funciona o atendimento da Guará Tickets','Da primeira conversa com Israel à confirmação do valor e do local: veja o que combinar em cada etapa.', '''<h2>1. Faça a consulta pelo WhatsApp</h2><p>O atendimento é realizado por Israel, proprietário do Guará Mix. Informe a bandeira, a modalidade e o valor pretendido. Se tiver vários cartões, informe os valores de cada um e o total.</p><p>Para organizar o atendimento, informe também sua região de São Paulo e a data desejada. O site não tem cadastro nem pagamento online.</p><h2>2. Confirme a taxa e o valor líquido</h2><p>Antes de agendar, confirme quanto será passado, quanto será descontado e quanto você receberá. O <a href="/taxas/">simulador</a> ajuda a estimar os valores de alimentação, refeição e outros benefícios, mas a confirmação é feita no atendimento.</p><p>Na modalidade de cartão de crédito, a taxa anunciada de 15% é descontada do valor bruto. R$ 1.000,00 passados correspondem a R$ 150,00 de taxa e R$ 850,00 recebidos. Condições do cartão devem ser combinadas com Israel.</p><h2>3. Agende com pelo menos 3 dias de antecedência</h2><p>Combine data, horário e local. As taxas da página consideram esse agendamento. Sem agendamento, a taxa é maior e deve ser consultada antes.</p><p>A base é o Jardim Umarizal/Campo Limpo. Atendemos somente a região sul, o centro e a zona oeste da capital. Se o atendimento for até você, confirme separadamente a disponibilidade e a taxa de motoboy.</p><h2>4. Confira os valores no atendimento</h2><p>Confira os valores combinados e o canal de recebimento. O pagamento é feito no ato, somente via Pix.</p><h2>O que o site não solicita</h2><p>O simulador não solicita número de cartão, senha, código de segurança, foto de documento ou dados bancários. Ele precisa apenas da categoria e do valor para calcular a estimativa.</p><p><a href="/condicoes/">Leia as condições comerciais</a> e <a href="/privacidade/">saiba como os dados do simulador e dos links são usados</a>.</p>''')
page('atendimento-sao-paulo','Atendimento em São Paulo: Campo Limpo e regiões','Atendimento em São Paulo: região sul, centro e zona oeste','Nossa base fica no Jardim Umarizal, na região do Campo Limpo. Consulte a disponibilidade com Israel antes de agendar.', '''<h2>Onde fica a base do atendimento?</h2><p>O atendimento é realizado por Israel, proprietário do Guará Mix, no Jardim Umarizal, região do Campo Limpo, São Paulo — SP.</p><p>O ponto exato e o horário do atendimento devem ser combinados pelo WhatsApp. Confirme o ponto de atendimento e o horário com Israel antes de se deslocar.</p><h2>Quais regiões são atendidas?</h2><ul><li>Região sul de São Paulo.</li><li>Centro de São Paulo.</li><li>Zona oeste de São Paulo.</li></ul><p>Não há uma lista fechada de bairros. Informe sua localização para combinar o atendimento dentro dessas regiões. A cobertura anunciada se limita à capital de São Paulo.</p><h2>Vocês vão até o cliente?</h2><p>Há atendimento no local do cliente com taxa de motoboy. A disponibilidade e o valor são combinados antes pelo WhatsApp. Esse custo deve ser confirmado separadamente do desconto aplicado ao valor dos cartões.</p><h2>Qual é a antecedência?</h2><p>Agende com no mínimo 3 dias de antecedência. As taxas apresentadas consideram agendamento; sem agendamento, a taxa é maior e precisa ser consultada.</p><h2>O que informar ao combinar o local?</h2><p>Envie a região, o ponto pretendido e a data desejada junto com a bandeira, modalidade e valor dos cartões. Israel confirma se é possível realizar o atendimento e quais são as condições.</p><p>Veja <a href="/como-funciona/">o passo a passo</a> e <a href="/taxas/">a tabela de taxas</a> antes de agendar.</p>''')
page('sobre','Quem atende: Israel e Guará Mix','Guará Tickets: atendimento com Israel, do Guará Mix','Conheça a relação entre o nome Guará Tickets, este site e o atendimento realizado no Jardim Umarizal/Campo Limpo.', '''<h2>Quem realiza o atendimento?</h2><p>Israel, proprietário do Guará Mix, é o responsável pelo atendimento divulgado neste site. A Guará Tickets é a marca usada aqui para apresentar as informações sobre cartões, taxas, simulação e agendamento.</p><h2>Qual é a relação com o mercado?</h2><p>A base informada para o atendimento é o Guará Mix, no Jardim Umarizal, na região do Campo Limpo, capital de São Paulo. Os nomes aparecem juntos para deixar claro quem atende e onde está a base da operação.</p><h2>Como falar com Israel?</h2><p>O contato divulgado é <a href="tel:+5511940240988">(11) 94024-0988</a>. Use o WhatsApp para confirmar modalidade do cartão, valores, local e condições antes do agendamento.</p><h2>Quais informações estão disponíveis?</h2><p>O site reúne <a href="/taxas/">taxas e exemplos de cálculo</a>, <a href="/como-funciona/">etapas do atendimento</a> e <a href="/atendimento-sao-paulo/">regiões atendidas</a>. As informações comerciais estão sujeitas a confirmação, como indicado na página de <a href="/condicoes/">condições</a>.</p><p>Use o contato divulgado no site para esclarecer dúvidas e confirmar o combinado antes do atendimento.</p>''')
page('condicoes','Condições: taxas, Pix e agendamento','Condições informadas para o atendimento','Confira as condições comerciais divulgadas pela Guará Tickets e o que precisa ser combinado diretamente com Israel.', '''<h2>Confirmação antes do atendimento</h2><p>O site apresenta informações e estimativas. Bandeira, modalidade, disponibilidade, valores e condições devem ser confirmados com Israel pelo WhatsApp antes de agendar. Não há contratação, aprovação ou pagamento automático pelo site.</p><h2>Alimentação e refeição</h2><p>A taxa considera o valor total dos cartões do atendimento: 17% até R$ 1.000,00; 16% de R$ 1.000,01 a R$ 2.000,00; e 15% acima de R$ 2.000,00. <a href="/taxas/">Veja a tabela e os exemplos.</a></p><h2>Outros benefícios e cartão de crédito</h2><p>A taxa anunciada para outros benefícios é 15%, sujeita à modalidade e confirmação. Para cartão de crédito, os 15% são descontados do valor bruto passado: R$ 1.000,00 de bruto resultam em R$ 850,00 líquidos.</p><p>O desconto descrito no site não explica, por si só, condições de parcelamento, vencimentos ou encargos do cartão. Confirme as condições completas com Israel antes do atendimento. Confirme todos os valores e condições antes de concordar com o atendimento.</p><h2>Agendamento</h2><p>As taxas apresentadas consideram agendamento com no mínimo 3 dias de antecedência. Sem agendamento, a taxa é maior e deve ser consultada. Valores anunciados estão sujeitos a alteração; confirme antes de combinar o atendimento.</p><h2>Pagamento e deslocamento</h2><p>O pagamento é feito no ato, somente via Pix. Atendimento no local do cliente tem taxa de motoboy, com disponibilidade e valor combinados previamente. A cobertura é somente região sul, centro e zona oeste da capital de São Paulo.</p><h2>Contato e ajustes no combinado</h2><p>Para dúvidas ou para alterar o que foi combinado, fale com Israel no WhatsApp <a href="https://wa.me/5511940240988" target="_blank" rel="noopener">(11) 94024-0988</a>. Combine previamente com Israel como proceder se precisar alterar ou cancelar o atendimento.</p>''')
page('privacidade','Privacidade: simulador, WhatsApp e atendimento','Como os dados são usados neste site','Este aviso descreve o funcionamento atual do simulador, dos links de contato e dos serviços externos usados para acessar o atendimento.', '''<h2>Dados inseridos no simulador</h2><p>O simulador solicita a categoria do cartão e um valor. O cálculo é executado no navegador, sem um formulário de cadastro ou envio automático para um banco de dados próprio do site.</p><p>Não há campos para número de cartão, senha, código de segurança, CPF, foto de documento ou chave Pix. Não insira essas informações no campo de valor.</p><h2>Ao abrir o WhatsApp</h2><p>Alguns botões abrem um link para o WhatsApp com uma mensagem preenchida. No botão da simulação, essa mensagem pode conter a categoria, o valor bruto, a taxa estimada e o valor líquido. Ao abrir o link, essas informações passam a integrar a navegação para o serviço externo.</p><p>Revise a mensagem antes de enviá-la ao contato. A conversa e o tratamento de dados no WhatsApp também seguem as práticas da plataforma. <a href="https://www.whatsapp.com/legal/privacy-policy" target="_blank" rel="noopener">Consulte a política de privacidade do WhatsApp.</a></p><h2>Dados técnicos da navegação</h2><p>O site é hospedado na Vercel. A hospedagem pode tratar registros técnicos e usar recursos de segurança, como dados de conexão e cookies necessários ao funcionamento. Isso é diferente dos valores usados localmente no simulador.</p><p>O código atual do site não inclui formulário de cadastro, pixel publicitário ou ferramenta própria de análise de visitantes. Se novos recursos de coleta forem adicionados, este aviso deve ser atualizado.</p><h2>Contato sobre dados do atendimento</h2><p>Para perguntas ou solicitações relacionadas às informações que você enviou durante o atendimento, fale com Israel pelo WhatsApp <a href="https://wa.me/5511940240988" target="_blank" rel="noopener">(11) 94024-0988</a>, identificando sua solicitação. Não envie documentos ou dados de cartão apenas para usar o simulador.</p><p>Este aviso descreve os recursos atuais do site. Condições específicas de guarda e tratamento dos dados da conversa devem ser esclarecidas com o responsável pelo atendimento.</p>''')
PAGES['/taxas/']={'title':'Taxas e simulador de cartões em São Paulo | Guará Tickets','h1':'Taxas dos cartões e simulador do valor a receber','desc':'Confira as faixas de 17%, 16% e 15%, entenda o desconto sobre o valor bruto e simule quanto recebe após a taxa.','main':hero('Taxas dos cartões e simulador do valor a receber','Confira a tabela anunciada, veja exemplos e faça uma estimativa antes de confirmar o atendimento com Israel.','Taxas e simulador')+extract('taxas')+'<section class="sim-band"><div class="wrap">'+SIM+'</div></section><section class="page-body"><div class="wrap"><div class="prose"><h2>Como o desconto é calculado?</h2><p>Valor líquido = valor bruto − (valor bruto × taxa ÷ 100). Para alimentação e refeição, o total dos cartões define uma única faixa, aplicada a todo o valor informado.</p>'+examples+'<h2>O que o simulador não inclui?</h2><p>O simulador usa as taxas anunciadas com agendamento. Ele não inclui a taxa de motoboy nem uma eventual taxa maior para atendimento sem agendamento. Esses valores são confirmados com Israel.</p><h2>Exemplo de cartão de crédito</h2><p>A taxa anunciada nessa modalidade é 15% do valor bruto: R$ 1.000,00 passados resultam em R$ 150,00 de desconto e R$ 850,00 recebidos. O simulador acima não confirma as condições do cartão de crédito.</p><p>Leia as <a href="/condicoes/">condições do atendimento</a> e veja <a href="/como-funciona/">como agendar</a>.</p></div></div></section>','calc':True}
PAGES['/duvidas/']={'title':'Dúvidas sobre cartões, taxas e atendimento | Guará Tickets','h1':'Dúvidas sobre cartões, taxas e atendimento','desc':'Respostas sobre modalidades, cálculo, agendamento de 3 dias, Pix e atendimento em São Paulo com Israel.','main':hero('Dúvidas sobre cartões, taxas e atendimento','Abra as perguntas para conferir informações sobre a consulta, os valores e o agendamento.','Dúvidas')+prose('<h2>Cartões, valores e atendimento</h2>'+''.join(faq)+'<h2>Quer conferir um exemplo?</h2><p>Veja a página de <a href="/taxas/">taxas e simulação</a>. Para informações sobre os dados da simulação e links de contato, consulte <a href="/privacidade/">privacidade</a>.</p>'),'calc':False}
main=re.search(r'<main>(.*?)</main>',HOME,re.S)[1].replace('<!--sim:start-->','').replace('<!--sim:end-->','').strip()
# Keep the landing FAQ concise; all questions remain on /duvidas/.
home_questions={'Como funciona o cartão de crédito com recebimento via Pix?','Posso somar mais de um cartão?','Quais regiões vocês atendem?','Preciso agendar antes?'}
main=re.sub(r'<details>.*?</details>',lambda m:m[0] if re.search(r'<summary>(.*?)</summary>',m[0],re.S)[1] in home_questions else '',main,flags=re.S)
ht='Vender VR, vale-refeição e alimentação em SP | Guará Tickets'
hd='Consulte VR, vale-refeição e vale-alimentação em São Paulo. Confira taxas, simule o valor e agende com Israel no Jardim Umarizal/Campo Limpo.'
W(OUT/'index.html',layout('/',ht,hd,main,True))
for path,entry in PAGES.items():
 folder=OUT/path.strip('/');folder.mkdir(parents=True,exist_ok=True)
 W(folder/'index.html',layout(path,entry['title'],entry['desc'],entry['main'],entry['calc']))
notfound=hero('Página não encontrada','O endereço pode ter mudado. Use os links abaixo para continuar sua consulta.','Página não encontrada')+prose('<h2>Continue pelo site</h2><nav class="related-links" aria-label="Páginas principais"><a href="/">Voltar ao início</a><a href="/taxas/">Ver taxas e simular</a><a href="/duvidas/">Ver dúvidas</a></nav>')
W(OUT/'404.html',layout('/404.html','Página não encontrada | Guará Tickets','Este endereço não corresponde a uma página do site.',notfound,noindex=True))
ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9');root=ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
for path in ['/',*PAGES.keys()]:
 item=ET.SubElement(root,'url');ET.SubElement(item,'loc').text=BASE+path;ET.SubElement(item,'lastmod').text=DATE
(OUT/'sitemap.xml').write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
W(OUT/'robots.txt','User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n')
# Cloudflare Workers static assets read security and cache headers from dist/_headers (vercel.json is not used there).
W(OUT/'_headers','''/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'

/assets/site-*.css
  Cache-Control: public, max-age=31536000, immutable

/assets/*.svg
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400

/assets/*.png
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400

/favicon.ico
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400

/favicon.svg
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400

/favicon-96.png
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400

/apple-touch-icon.png
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400
''')
# Minimal navigation data for verification, kept as source, not served as marketing content.
W(ROOT/'scripts/pages-manifest.json',json.dumps({'origin':BASE,'pages':['/',*PAGES.keys()],'stylesheet':'/assets/'+cssname},ensure_ascii=False,indent=2)+'\n')
print(f'Built home + {len(PAGES)} focused pages, shared CSS/JS, sitemap and 404.')
