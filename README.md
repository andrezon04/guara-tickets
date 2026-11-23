<div align="center">

# Guará Tickets

Site institucional com páginas sobre vale-alimentação e vale-refeição, simulador de valores e atendimento via WhatsApp.

<img alt="HTML" src="https://img.shields.io/badge/HTML-1a1b27?style=flat-square" />
<img alt="CSS" src="https://img.shields.io/badge/CSS-1a1b27?style=flat-square" />
<img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-1a1b27?style=flat-square" />
<img alt="Python" src="https://img.shields.io/badge/Python-1a1b27?style=flat-square" />

**Site institucional**

</div>

---

## Funcionalidades

- Páginas sobre cartões, taxas, condições e dúvidas frequentes.
- Simulador de valores e atalhos para atendimento via WhatsApp.
- Páginas estáticas com sitemap e metadados por rota.

## Como executar

Rode `python -m http.server 8000 --directory dist` na raiz do repositório e abra [localhost:8000](http://localhost:8000).

## Como reconstruir

Depois de editar qualquer arquivo em `src/` ou `scripts/build-pages.py`, rode `python scripts/build-pages.py` e em seguida `python scripts/validate-pages.py` (o validador precisa de `pip install lxml`).

## Organização

- `src/home.html` contém o HTML da página inicial, do cabeçalho e do rodapé.
- `src/site.css` é a folha de estilo única; `src/simulador.js` e `src/navegacao.js` são os scripts.
- `scripts/` reúne o manifesto de páginas, o gerador e o validador.
- `dist/` contém as páginas e os recursos prontos para servir.
- O site é publicado no Cloudflare Workers em [guaratickets.com.br](https://guaratickets.com.br), a partir da pasta `dist/`, a cada push na `main`.
- `dist/_headers` (gerado pelo build) define o cache dos recursos e os cabeçalhos de segurança.
