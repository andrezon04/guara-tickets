#!/usr/bin/env python3
"""Verify published routes, canonical URLs, metadata and local link targets."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
from lxml import html,etree
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist'
manifest=json.loads((ROOT/'scripts/pages-manifest.json').read_text());base=manifest['origin']
errors=[];titles=set();descriptions=set();docs={}
def target_file(path):
 p=OUT/unquote(path).lstrip('/')
 return p/'index.html' if path.endswith('/') else p
for route in manifest['pages']:
 p=target_file(route);d=html.fromstring(p.read_text());docs[route]=d
 title=d.xpath('//title/text()');desc=d.xpath('//meta[@name="description"]/@content');canonical=d.xpath('//link[@rel="canonical"]/@href')
 if len(d.xpath('//h1'))!=1:errors.append(f'{route}: must have exactly one h1')
 if len(title)!=1 or title[0]in titles:errors.append(f'{route}: missing or duplicated title')
 if len(desc)!=1 or desc[0]in descriptions:errors.append(f'{route}: missing or duplicated description')
 titles.update(title);descriptions.update(desc)
 if canonical!=[base+route]:errors.append(f'{route}: invalid canonical {canonical}')
 if d.xpath('//meta[@name="robots" and contains(@content,"noindex")]'):errors.append(f'{route}: accidentally noindex')
 ids=d.xpath('//*[@id]/@id')
 if len(ids)!=len(set(ids)):errors.append(f'{route}: duplicated IDs')
 for node in d.xpath('//script[@type="application/ld+json"]'):
  data=json.loads(node.text);assert data.get('@context')=='https://schema.org'
  assert any(x.get('@type')=='WebPage'and x.get('url')==base+route for x in data['@graph'])
 for node in d.xpath('//img'):
  if 'alt'not in node.attrib or not node.get('width')or not node.get('height'):errors.append(f'{route}: image missing accessible name or geometry')
for route,d in docs.items():
 for node in d.xpath('//*[@href or @src]'):
  ref=node.get('href')or node.get('src');u=urlsplit(ref)
  if u.scheme in ('https','http','tel','mailto','data')or u.netloc:continue
  path=u.path or route
  if not path.startswith('/'):errors.append(f'{route}: non-root-relative reference {ref}');continue
  p=target_file(path)
  if not p.exists():errors.append(f'{route}: missing target {ref}');continue
  if u.fragment:
   dest=docs.get(path)
   if dest is None and p.suffix=='.html':dest=html.fromstring(p.read_text())
   if dest is not None and not dest.xpath('//*[@id=$id]',id=u.fragment):errors.append(f'{route}: missing anchor {ref}')
sm=etree.fromstring((OUT/'sitemap.xml').read_bytes());urls=sm.xpath('//*[local-name()="loc"]/text()')
if set(urls)!={base+x for x in manifest['pages']}:errors.append('Sitemap differs from published canonical pages')
if 'Disallow: /'in(OUT/'robots.txt').read_text():errors.append('robots.txt blocks indexing')
notfound=html.fromstring((OUT/'404.html').read_text());assert notfound.xpath('//meta[@name="robots" and contains(@content,"noindex")]')
assert 'google-site-verification'in(OUT/'index.html').read_text()
if errors:raise SystemExit('\n'.join(errors))
print(f'{len(docs)} pages passed: unique title/description/H1, canonical, JSON-LD, links/assets/anchors, sitemap, robots, image dimensions and 404 noindex.')
