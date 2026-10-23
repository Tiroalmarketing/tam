#!/usr/bin/env python3
"""SEO crawler for a single site.

Crawls internal links + sitemaps + WordPress REST API, records the HTTP status
of every URL without following redirects, and reports where each redirected or
broken URL is linked from. Writes crawl.json and REPORT.md to --out.
"""
import argparse
import collections
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, urlunparse, urlencode

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Mobile Safari/537.36 TAM-SEO-Audit")
SKIP_EXT = re.compile(r"\.(jpe?g|png|gif|webp|svg|ico|pdf|mp4|webm|mov|zip|css|js|woff2?|ttf|eot|xml)$", re.I)

# URLs to check explicitly: old URLs, redirected blog posts, backlink targets, Ads landing, etc.
CHECK_PATHS = [
    "/", "/accueil-2/", "/le-centre/", "/contact/",
    "/epilation-laser-perpignan/", "/epilation-definitive/", "/epilation-laser-3-en-1/",
    "/lumiere-pulsee-focalisee/", "/epilation-laser/",
    "/detatouage-perpignan/", "/detatouage/",
    "/electrolyse-perpignan/", "/thermolyse-perpignan/", "/electrolyse/",
    "/body-sculpt/", "/body-sculpt-perpignan/", "/traitement-de-la-peau/",
    "/blog/", "/category/blog/", "/categorie/blog/", "/category/blog/page/2/",
    "/blog/centre-epilation-laser/",
    "/blog/epilation-perpignan-guide-complet-pour-une-peau-douce-et-soignee/",
    "/epilation-perpignan-guide-complet-pour-une-peau-douce-et-soignee/",
    "/blog/quand-se-raser-avant-epilation-lumiere-pulsee/",
    "/blog/lumiere-pulsse-ou-laser-pour-epilation-definitive/",
    "/blog/depilation-laser-et-types-de-peau-comment-choisir-la-bonne-methode/",
    "/blog/combien-de-seance-pour-epilation-laser/",
    "/blog/a-partir-de-quel-age-epilation-laser/",
    "/blog/eliminer-les-taches-pigmentaires-avec-depilinea-solutions-avancees-pour-un-teint-uniforme/",
    "/blog/depilation-laser-chez-depilinea-resultats-durables-et-sans-douleur/",
    "/blog/les-avantages-a-long-terme-de-la-depilation-laser/",
    "/blog/traitement-de-lacne-chez-depilinea-solutions-efficaces-pour-une-peau-plus-saine/",
    "/blog/pourquoi-opter-pour-la-depilation-laser-les-cles-dune-peau-parfaite/",
    "/les-differentes-methodes-depilation-disponibles-a-perpignan/",
    "/pourquoi-opter-pour-la-depilation-laser-les-cles-dune-peau-parfaite/",
    "/eliminer-les-taches-pigmentaires-avec-depilinea-solutions-avancees-pour-un-teint-uniforme/",
    "/depilation-laser-chez-depilinea-resultats-durables-et-sans-douleur/",
    "/robots.txt", "/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml",
    "/feed/", "/?s=epilation", "/author/admin/", "/wp-login.php",
]
HOST_VARIANTS = ["http://{h}/", "http://www.{h}/", "https://www.{h}/", "https://{h}/index.php"]
PSI_PATHS = ["/", "/epilation-laser-perpignan/", "/detatouage-perpignan/",
             "/electrolyse-perpignan/", "/body-sculpt/"]


def norm(url):
    p = urlparse(url)
    path = p.path or "/"
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", p.query, ""))


class Crawler:
    def __init__(self, site, max_pages, delay):
        self.site = site.rstrip("/")
        self.host = urlparse(site).netloc.lower()
        self.bare = self.host[4:] if self.host.startswith("www.") else self.host
        self.max_pages = max_pages
        self.delay = delay
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
        self.res = {}          # url -> fetch record
        self.pages = {}        # url -> parsed page data
        self.inlinks = collections.defaultdict(list)  # target -> [{source, anchor, zone, rel}]
        self.sitemap_urls = {}  # url -> lastmod
        self.sitemap_files = []
        self.wp = {}           # type -> [items]
        self.external = collections.defaultdict(list)
        self.errors = []

    def internal(self, url):
        h = urlparse(url).netloc.lower()
        return h in (self.bare, "www." + self.bare)

    def fetch(self, url, method="GET"):
        if url in self.res:
            return self.res[url]
        rec = {"url": url}
        try:
            t = time.time()
            r = self.s.request(method, url, allow_redirects=False, timeout=25)
            rec.update(status=r.status_code, ms=int((time.time() - t) * 1000),
                       location=urljoin(url, r.headers["Location"]) if "Location" in r.headers else None,
                       ctype=r.headers.get("Content-Type", ""),
                       x_robots=r.headers.get("X-Robots-Tag"),
                       server=r.headers.get("Server"), size=len(r.content))
            rec["_body"] = r.text if re.search(r"text/|xml|json", rec["ctype"]) else None
        except requests.RequestException as e:
            rec.update(status="ERROR", error=str(e)[:200])
        self.res[url] = rec
        if self.delay:
            time.sleep(self.delay)
        return rec

    def chain(self, url):
        hops, cur, seen = [], url, set()
        while len(hops) < 10:
            rec = self.fetch(cur)
            hops.append({"url": cur, "status": rec.get("status")})
            loc = rec.get("location")
            if not (isinstance(rec.get("status"), int) and 300 <= rec["status"] < 400 and loc):
                break
            if loc in seen:
                hops.append({"url": loc, "status": "LOOP"})
                break
            seen.add(cur)
            cur = loc
        return hops

    # ---------- sitemaps ----------
    def load_sitemaps(self):
        robots = self.fetch(self.site + "/robots.txt")
        cands = []
        if robots.get("status") == 200 and robots.get("_body"):
            cands = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots["_body"])
        cands += [self.site + p for p in ("/sitemap_index.xml", "/sitemap.xml", "/wp-sitemap.xml")]
        done = set()
        queue = list(dict.fromkeys(cands))
        while queue:
            sm = queue.pop(0)
            if sm in done:
                continue
            done.add(sm)
            rec = self.fetch(sm)
            entry = {"url": sm, "status": rec.get("status"), "urls": 0}
            self.sitemap_files.append(entry)
            if rec.get("status") != 200 or not rec.get("_body"):
                continue
            try:
                root = ET.fromstring(rec["_body"].encode("utf-8"))
            except ET.ParseError as e:
                entry["error"] = str(e)
                continue
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root.findall(".//sm:sitemap/sm:loc", ns):
                queue.append(loc.text.strip())
            for u in root.findall(".//sm:url", ns):
                loc = u.find("sm:loc", ns)
                lm = u.find("sm:lastmod", ns)
                if loc is not None and loc.text:
                    self.sitemap_urls[norm(loc.text.strip())] = lm.text if lm is not None else None
                    entry["urls"] += 1

    # ---------- WordPress REST ----------
    def load_wp(self):
        for typ in ("pages", "posts", "categories", "tags", "media"):
            items, page = [], 1
            while page <= 10:
                q = {"per_page": 100, "page": page}
                if typ in ("pages", "posts"):
                    q["_fields"] = "id,link,slug,status,date,modified,title,parent"
                elif typ == "media":
                    q["_fields"] = "id,link,source_url,alt_text,mime_type"
                else:
                    q["_fields"] = "id,link,slug,count,name"
                url = f"{self.site}/wp-json/wp/v2/{typ}?{urlencode(q)}"
                try:
                    r = self.s.get(url, timeout=25)
                except requests.RequestException as e:
                    self.errors.append(f"wp {typ}: {e}")
                    break
                if r.status_code != 200:
                    self.errors.append(f"wp {typ}: HTTP {r.status_code}")
                    break
                try:
                    batch = r.json()
                except ValueError:
                    break
                if not isinstance(batch, list) or not batch:
                    break
                items += batch
                if len(batch) < 100:
                    break
                page += 1
            self.wp[typ] = items

    # ---------- page parsing ----------
    def parse(self, url, html):
        soup = BeautifulSoup(html, "lxml")
        d = {}
        d["lang"] = (soup.html.get("lang") if soup.html else None)
        d["title"] = soup.title.get_text(strip=True) if soup.title else None
        md = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        d["meta_description"] = md.get("content", "").strip() if md else None
        mr = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
        d["meta_robots"] = mr.get("content") if mr else None
        can = soup.find("link", rel=lambda v: v and "canonical" in v)
        d["canonical"] = urljoin(url, can["href"]) if can and can.get("href") else None
        gen = soup.find("meta", attrs={"name": "generator"})
        d["generator"] = gen.get("content") if gen else None
        d["h1"] = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
        d["h2"] = [h.get_text(" ", strip=True) for h in soup.find_all("h2")][:15]
        d["hreflang"] = [l.get("hreflang") for l in soup.find_all("link", hreflang=True)]
        types = []
        for sc in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(sc.string or "")
            except (ValueError, TypeError):
                types.append("INVALID_JSON")
                continue
            stack = [data]
            while stack:
                x = stack.pop()
                if isinstance(x, dict):
                    t = x.get("@type")
                    if t:
                        types += t if isinstance(t, list) else [t]
                    stack += list(x.values())
                elif isinstance(x, list):
                    stack += x
        d["schema_types"] = sorted(set(map(str, types)))
        low = html.lower()
        d["has_trustindex"] = "trustindex" in low
        d["mentions_suspendu"] = bool(re.search(r"suspendu|temporairement|pause", low))
        imgs = soup.find_all("img")
        d["img_total"] = len(imgs)
        d["img_no_alt"] = sum(1 for i in imgs if not (i.get("alt") or "").strip())
        for t in soup(["script", "style", "noscript"]):
            t.decompose()
        text = soup.get_text(" ", strip=True)
        d["word_count"] = len(text.split())
        ctas = {"tel": 0, "whatsapp": 0, "planity": 0}
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("tel:"):
                ctas["tel"] += 1
                continue
            if href.startswith(("mailto:", "javascript:", "#")):
                continue
            absu = urljoin(url, href)
            if "wa.me" in absu or "whatsapp" in absu:
                ctas["whatsapp"] += 1
            if "planity" in absu:
                ctas["planity"] += 1
            zone = "body"
            for anc in a.parents:
                if anc.name in ("header", "nav", "footer", "aside"):
                    zone = anc.name
                    break
                cls = " ".join(anc.get("class", [])) if hasattr(anc, "get") else ""
                if re.search(r"(^|[\s_-])(menu|nav|header)([\s_-]|$)", cls):
                    zone = "nav"
                    break
                if re.search(r"footer", cls):
                    zone = "footer"
                    break
            anchor = a.get_text(" ", strip=True) or (a.find("img").get("alt", "[img]") if a.find("img") else "")
            links.append({"href": absu.split("#")[0], "raw": href, "anchor": anchor[:120],
                          "rel": " ".join(a.get("rel", [])), "zone": zone})
        d["ctas"] = ctas
        d["links_out"] = len(links)
        return d, links

    def crawl(self):
        start = [self.site + "/"] + [self.site + p for p in CHECK_PATHS]
        queue = collections.deque(dict.fromkeys(start + list(self.sitemap_urls)))
        for typ in ("pages", "posts", "categories"):
            for it in self.wp.get(typ, []):
                if it.get("link"):
                    queue.append(norm(it["link"]))
        seen = set()
        while queue and len(self.pages) < self.max_pages:
            url = norm(queue.popleft())
            if url in seen:
                continue
            seen.add(url)
            rec = self.fetch(url)
            st = rec.get("status")
            if isinstance(st, int) and 300 <= st < 400 and rec.get("location"):
                loc = norm(rec["location"])
                if self.internal(loc) and loc not in seen:
                    queue.append(loc)
                continue
            if st != 200 or "html" not in rec.get("ctype", "") or not rec.get("_body"):
                continue
            if urlparse(url).query:
                continue  # status recorded, but parameter URLs are not inventoried
            data, links = self.parse(url, rec["_body"])
            self.pages[url] = data
            for l in links:
                tgt = norm(l["href"]) if l["href"].startswith("http") else None
                if not tgt:
                    continue
                if self.internal(tgt):
                    self.inlinks[tgt].append({"source": url, "anchor": l["anchor"], "zone": l["zone"],
                                              "rel": l["rel"], "raw": l["raw"]})
                    path = urlparse(tgt).path
                    if not SKIP_EXT.search(path) and tgt not in seen:
                        if not urlparse(tgt).query:
                            queue.append(tgt)
                        else:
                            # check status of query URLs but do not crawl them
                            self.fetch(tgt)
                else:
                    self.external[tgt].append({"source": url, "anchor": l["anchor"], "rel": l["rel"]})
        # status of internal targets that were not crawled (assets, query URLs)
        for tgt in list(self.inlinks):
            if tgt not in self.res:
                self.fetch(tgt, "HEAD" if SKIP_EXT.search(urlparse(tgt).path) else "GET")

    def check_external(self, limit=150):
        out = {}
        for i, tgt in enumerate(self.external):
            if i >= limit:
                break
            try:
                r = self.s.head(tgt, allow_redirects=True, timeout=15)
                st = r.status_code
                if st in (403, 405, 501):
                    r = self.s.get(tgt, allow_redirects=True, timeout=15, stream=True)
                    st = r.status_code
                out[tgt] = st
            except requests.RequestException as e:
                out[tgt] = "ERROR: " + str(e)[:80]
        return out

    def psi(self):
        out = {}
        key = os.environ.get("PSI_KEY")
        for p in PSI_PATHS:
            q = {"url": self.site + p, "strategy": "mobile", "category": "performance"}
            if key:
                q["key"] = key
            try:
                r = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urlencode(q),
                                 timeout=120)
                j = r.json()
            except (requests.RequestException, ValueError) as e:
                out[p] = {"error": str(e)[:200]}
                continue
            if "error" in j:
                out[p] = {"error": j["error"].get("message", "")[:200]}
                continue
            lh = j.get("lighthouseResult", {})
            au = lh.get("audits", {})
            field = j.get("loadingExperience", {}).get("metrics", {})
            out[p] = {
                "score": round(lh.get("categories", {}).get("performance", {}).get("score", 0) * 100),
                "LCP": au.get("largest-contentful-paint", {}).get("displayValue"),
                "CLS": au.get("cumulative-layout-shift", {}).get("displayValue"),
                "TBT": au.get("total-blocking-time", {}).get("displayValue"),
                "FCP": au.get("first-contentful-paint", {}).get("displayValue"),
                "page_weight": au.get("total-byte-weight", {}).get("displayValue"),
                "field_LCP_ms": field.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile"),
                "field_INP_ms": field.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile"),
                "field_CLS": field.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile"),
                "field_overall": j.get("loadingExperience", {}).get("overall_category"),
            }
        return out


def md_escape(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")


def report(c, ext_status, psi, variants, out):
    L = []
    w = L.append
    site_p = urlparse(c.site)

    def rel(u):
        p = urlparse(u)
        if (p.scheme, p.netloc) != (site_p.scheme, site_p.netloc):
            return u
        return p.path + ("?" + p.query if p.query else "")
    w(f"# Auditoría técnica {c.bare} — {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}\n")
    status_count = collections.Counter(str(r.get("status")) for r in c.res.values())
    w(f"URLs comprobadas: **{len(c.res)}** · Páginas HTML 200 rastreadas: **{len(c.pages)}** · "
      f"URLs en sitemap: **{len(c.sitemap_urls)}**\n")
    w("Estados: " + ", ".join(f"`{k}`: {v}" for k, v in sorted(status_count.items())) + "\n")
    if c.errors:
        w("Avisos: " + "; ".join(c.errors) + "\n")

    w("\n## 1. Variantes de host / protocolo\n")
    w("| Origen | Cadena |\n|---|---|")
    for v, ch in variants.items():
        w(f"| {v} | " + " → ".join(f"{h['url']} ({h['status']})" for h in ch) + " |")

    def where(u):
        srcs = c.inlinks.get(u, [])
        insm = "sí" if u in c.sitemap_urls else "no"
        if not srcs:
            return insm, "— (sin enlaces internos)"
        grp = collections.defaultdict(set)
        for s in srcs:
            grp[s["zone"]].add((rel(s["source"]), s["anchor"]))
        parts = []
        for z, items in grp.items():
            items = sorted(items)
            sample = "; ".join(f"{p} «{md_escape(a)[:40]}»" for p, a in items[:6])
            more = f" (+{len(items) - 6})" if len(items) > 6 else ""
            parts.append(f"**{z}** ×{len(items)}: {sample}{more}")
        return insm, "<br>".join(parts)

    w("\n## 2. Redirecciones internas (3xx) y dónde están enlazadas\n")
    w("| URL | Cadena | ¿En sitemap? | Enlazada desde |\n|---|---|---|---|")
    n = 0
    for u, r in sorted(c.res.items()):
        st = r.get("status")
        if isinstance(st, int) and 300 <= st < 400 and c.internal(u):
            ch = c.chain(u)
            insm, src = where(u)
            w(f"| {rel(u)} | " + " → ".join(f"{h['status']}" for h in ch) + f" → {rel(ch[-1]['url'])} | {insm} | {src} |")
            n += 1
    if not n:
        w("| — | ninguna | | |")

    w("\n## 3. Errores 4xx / 5xx / sin respuesta enlazados o en sitemap\n")
    w("(Las URLs comprobadas a mano que dan 404 sin enlaces están en la sección 4.)\n")
    w("| URL | Estado | ¿En sitemap? | Enlazada desde |\n|---|---|---|---|")
    n = 0
    for u, r in sorted(c.res.items()):
        st = r.get("status")
        if not (c.inlinks.get(u) or u in c.sitemap_urls):
            continue
        if (st == "ERROR" or (isinstance(st, int) and st >= 400)) and c.internal(u):
            insm, src = where(u)
            w(f"| {rel(u)} | {st} | {insm} | {src} |")
            n += 1
    if not n:
        w("| — | ninguno | | |")

    w("\n## 4. URLs revisadas explícitamente\n")
    w("| Ruta | Estado | Destino final | Indexable | Enlaces internos |\n|---|---|---|---|---|")
    for p in CHECK_PATHS:
        u = norm(c.site + p)
        ch = c.chain(u)
        fin = ch[-1]["url"]
        pg = c.pages.get(norm(fin))
        idx = "—"
        if pg is not None:
            nofollow_idx = "noindex" in (pg.get("meta_robots") or "").lower() or \
                           "noindex" in (c.res.get(norm(fin), {}).get("x_robots") or "").lower()
            can = pg.get("canonical")
            idx = "NO (noindex)" if nofollow_idx else ("NO (canonical → " + rel(can) + ")" if can and norm(can) != norm(fin) else "sí")
        w(f"| {p} | {' → '.join(str(h['status']) for h in ch)} | {rel(fin) if fin != u else ''} | {idx} | {len(c.inlinks.get(u, []))} |")

    w("\n## 5. Sitemaps\n")
    for s in c.sitemap_files:
        w(f"- {s['url']} → {s['status']} ({s['urls']} URLs){' ' + s.get('error', '') if s.get('error') else ''}")
    bad = []
    for u in c.sitemap_urls:
        r = c.res.get(u, {})
        pg = c.pages.get(u)
        why = []
        if r.get("status") != 200:
            why.append(f"estado {r.get('status')}")
        if pg and "noindex" in (pg.get("meta_robots") or "").lower():
            why.append("noindex")
        if pg and pg.get("canonical") and norm(pg["canonical"]) != u:
            why.append("canonical a " + rel(pg["canonical"]))
        if why:
            bad.append((u, why))
    w(f"\nURLs del sitemap con problemas: **{len(bad)}**")
    for u, why in bad:
        w(f"- {rel(u)} — {', '.join(why)}")

    w("\n## 6. Inventario de páginas indexables (HTML 200)\n")
    w("| URL | Title (long.) | Meta desc. (long.) | H1 | Canonical | Robots | Palabras | Inlinks | Schema |\n|---|---|---|---|---|---|---|---|---|")
    for u, d in sorted(c.pages.items()):
        can = d.get("canonical")
        cs = "self" if can and norm(can) == u else (rel(can) if can else "FALTA")
        h1 = " / ".join(d["h1"]) if d["h1"] else "FALTA"
        w(f"| {rel(u)} | {md_escape(d['title'])} ({len(d['title'] or '')}) | "
          f"{md_escape((d['meta_description'] or 'FALTA')[:90])} ({len(d['meta_description'] or '')}) | "
          f"{md_escape(h1)[:90]}{' ⚠️' + str(len(d['h1'])) + ' H1' if len(d['h1']) > 1 else ''} | {cs} | "
          f"{d.get('meta_robots') or ''} | {d['word_count']} | {len(c.inlinks.get(u, []))} | {', '.join(d['schema_types'])} |")

    w("\n## 7. Problemas on-page detectados\n")
    titles = collections.defaultdict(list)
    descs = collections.defaultdict(list)
    h1s = collections.defaultdict(list)
    for u, d in c.pages.items():
        if d.get("title"):
            titles[d["title"].strip().lower()].append(rel(u))
        if d.get("meta_description"):
            descs[d["meta_description"].strip().lower()].append(rel(u))
        for h in d["h1"]:
            h1s[h.strip().lower()].append(rel(u))
    def dup(name, m):
        items = [(k, v) for k, v in m.items() if len(v) > 1]
        w(f"\n**{name} duplicados:** {len(items)}")
        for k, v in items:
            w(f"- «{md_escape(k)[:80]}» → {', '.join(v)}")
    dup("Titles", titles)
    dup("Meta descriptions", descs)
    dup("H1", h1s)
    for label, f in [("Sin meta description", lambda d: not d.get("meta_description")),
                     ("Sin H1", lambda d: not d["h1"]),
                     ("Varios H1", lambda d: len(d["h1"]) > 1),
                     ("Title > 60 caracteres", lambda d: len(d.get("title") or "") > 60),
                     ("Meta description > 160", lambda d: len(d.get("meta_description") or "") > 160),
                     ("Menos de 300 palabras", lambda d: d["word_count"] < 300),
                     ("noindex", lambda d: "noindex" in (d.get("meta_robots") or "").lower()),
                     ("Canonical a otra URL o ausente", None),
                     ("Imágenes sin alt", lambda d: d["img_no_alt"] > 0),
                     ("Widget Trustindex", lambda d: d["has_trustindex"]),
                     ("Menciona suspendu/temporairement/pause", lambda d: d["mentions_suspendu"])]:
        if f is None:
            lst = [rel(u) for u, d in c.pages.items() if not d.get("canonical") or norm(d["canonical"]) != u]
        else:
            lst = [rel(u) + (f" ({d['img_no_alt']}/{d['img_total']})" if label == "Imágenes sin alt" else "")
                   for u, d in c.pages.items() if f(d)]
        w(f"\n**{label}:** {len(lst)}" + ("\n- " + "\n- ".join(sorted(lst)) if lst else ""))

    # internal links pointing to non-200, http, or utm
    w("\n## 8. Enlaces internos a corregir\n")
    w("| Página origen | Zona | Anchor | Enlaza a | Estado destino |\n|---|---|---|---|---|")
    n = 0
    for tgt, srcs in sorted(c.inlinks.items()):
        st = c.res.get(tgt, {}).get("status")
        issue = st != 200 or (tgt.startswith("http://") and c.site.startswith("https://")) or "utm_" in tgt or urlparse(tgt).netloc.startswith("www.") != c.host.startswith("www.")
        if not issue:
            continue
        for s in srcs:
            w(f"| {rel(s['source'])} | {s['zone']} | {md_escape(s['anchor'])[:50]} | {s['raw'][:90]} | {st} |")
            n += 1
    if not n:
        w("| — | | | ninguno | |")

    w("\n## 9. Páginas huérfanas (publicadas en WordPress o en sitemap pero sin enlaces internos)\n")
    known = set(c.sitemap_urls)
    for typ in ("pages", "posts"):
        for it in c.wp.get(typ, []):
            if it.get("link"):
                known.add(norm(it["link"]))
    orphans = [u for u in sorted(known) if not c.inlinks.get(u) and u != norm(c.site + "/")]
    w(f"Total: **{len(orphans)}**")
    for u in orphans:
        w(f"- {rel(u)} (estado {c.res.get(u, {}).get('status')}{', en sitemap' if u in c.sitemap_urls else ''})")

    w("\n## 10. Contenido publicado en WordPress (REST API)\n")
    for typ in ("pages", "posts"):
        items = c.wp.get(typ, [])
        w(f"\n**{typ}: {len(items)}**\n")
        if items:
            w("| ID | Slug | URL | Modificado | Estado HTTP | Inlinks |\n|---|---|---|---|---|---|")
            for it in sorted(items, key=lambda x: x.get("link", "")):
                u = norm(it.get("link", ""))
                w(f"| {it.get('id')} | {it.get('slug')} | {rel(u)} | {(it.get('modified') or '')[:10]} | "
                  f"{c.res.get(u, {}).get('status')} | {len(c.inlinks.get(u, []))} |")
    cats = c.wp.get("categories", [])
    if cats:
        w("\n**Categorías:** " + ", ".join(f"{x.get('name')} ({x.get('count')}) {rel(x.get('link', ''))}" for x in cats))

    w("\n## 11. Enlazado interno hacia páginas de negocio\n")
    for p in ["/", "/epilation-laser-perpignan/", "/epilation-definitive/", "/epilation-laser-3-en-1/",
              "/detatouage-perpignan/", "/electrolyse-perpignan/", "/body-sculpt/", "/traitement-de-la-peau/"]:
        u = norm(c.site + p)
        srcs = c.inlinks.get(u, [])
        pages_src = {s["source"] for s in srcs}
        body = [s for s in srcs if s["zone"] == "body"]
        anchors = collections.Counter(s["anchor"].lower() for s in srcs)
        w(f"\n**{p}** — {len(srcs)} enlaces desde {len(pages_src)} páginas ({len(body)} contextuales en body)")
        w("Anchors: " + ", ".join(f"«{md_escape(a)[:40]}» ×{k}" for a, k in anchors.most_common(12)))
        if body:
            w("Contextuales desde: " + ", ".join(sorted({rel(s['source']) for s in body})))

    w("\n## 12. CTAs por página (tel / WhatsApp / Planity)\n")
    w("| URL | tel | WhatsApp | Planity |\n|---|---|---|---|")
    for u, d in sorted(c.pages.items()):
        ct = d["ctas"]
        w(f"| {rel(u)} | {ct['tel']} | {ct['whatsapp']} | {ct['planity']} |")

    w("\n## 13. Enlaces externos rotos\n")
    broken = {k: v for k, v in ext_status.items() if not (isinstance(v, int) and v < 400)}
    w(f"Comprobados: {len(ext_status)} · con error: **{len(broken)}**")
    for k, v in broken.items():
        srcs = ", ".join(sorted({rel(s['source']) for s in c.external[k]}))[:200]
        w(f"- {k} → {v} (desde {srcs})")

    w("\n## 14. PageSpeed Insights (móvil)\n")
    w("| URL | Score | LCP | CLS | TBT | FCP | Peso | Campo LCP ms | Campo INP ms | Campo CLS | Campo global |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for p, v in psi.items():
        if "error" in v:
            w(f"| {p} | error: {md_escape(v['error'])[:80]} |||||||||| ")
        else:
            w(f"| {p} | {v['score']} | {v['LCP']} | {v['CLS']} | {v['TBT']} | {v['FCP']} | {v['page_weight']} | "
              f"{v['field_LCP_ms']} | {v['field_INP_ms']} | {v['field_CLS']} | {v['field_overall']} |")

    gens = {d.get("generator") for d in c.pages.values() if d.get("generator")}
    w("\n## 15. Stack\n")
    w(f"Generator: {', '.join(gens) or '—'} · Server: {c.res.get(norm(c.site + '/'), {}).get('server')}")
    w(f"\nrobots.txt:\n```\n{(c.res.get(c.site + '/robots.txt', {}).get('_body') or '')[:1500]}\n```")

    with open(os.path.join(out, "REPORT.md"), "w") as f:
        f.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-pages", type=int, default=800)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--no-psi", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    c = Crawler(a.site, a.max_pages, a.delay)
    c.load_sitemaps()
    c.load_wp()
    c.crawl()
    variants = {v.format(h=c.bare): c.chain(v.format(h=c.bare)) for v in HOST_VARIANTS}
    ext = c.check_external()
    psi = {} if a.no_psi else c.psi()
    report(c, ext, psi, variants, a.out)
    dump = {"fetch": {u: {k: v for k, v in r.items() if k != "_body"} for u, r in c.res.items()},
            "pages": c.pages, "inlinks": c.inlinks, "sitemap_urls": c.sitemap_urls,
            "sitemap_files": c.sitemap_files, "wp": c.wp, "external_status": ext, "psi": psi,
            "variants": variants, "errors": c.errors}
    with open(os.path.join(a.out, "crawl.json"), "w") as f:
        json.dump(dump, f, ensure_ascii=False, indent=1, default=str)
    print(f"done: {len(c.res)} urls, {len(c.pages)} pages")


if __name__ == "__main__":
    sys.exit(main())
