# Depilinea (depilinea.fr) — Hallazgos verificados y correcciones

Rastreo del 23/10/2026: 65 URLs, 28 páginas HTML, WordPress REST API (11 páginas, 10 posts),
sitemap Yoast (18 URLs), cabeceras HTTP con curl, Lighthouse móvil en 3 páginas.
Detalle completo en `REPORT.md`; datos en `crawl.json` y `lighthouse/`.

Stack: WordPress + Divi + Yoast, GTM-WT42BRXZ, Joinchat (WhatsApp), TablePress, edge cache activo.

## Prioridad 1 — corregir ya

| # | Problema | Evidencia | Corrección |
|---|---|---|---|
| 1 | La 301 de la landing de Ads **pierde `gclid` y UTM** | `/epilation-laser-3-en-1/?gclid=TEST&utm_source=google` → 301 a `/epilation-laser-perpignan/` sin parámetros | Cambiar la URL final de los anuncios a `/epilation-laser-perpignan/` (o la landing `/epilation-laser-perpignan-rdv-gratuit/`) y configurar la redirección para que conserve el query string |
| 2 | Backlink local *follow* apunta a un 404 | bip-perpignan.fr → `/epilation-perpignan-guide-complet-pour-une-peau-douce-et-soignee/` = **404** (el post vive en `/blog/…` y este redirige a la landing) | 301 de esa URL sin `/blog/` → `/epilation-laser-perpignan/` |
| 3 | Détatouage anuncia "suspendu pour la période estivale… dès l'automne" en pleno otoño | Texto en `/detatouage-perpignan/`, con tabla de precios (30–160 €) y 9 enlaces a Planity | Decidir con la clienta (requisito médico en Francia) y actualizar el mensaje; si no se ofrece, quitar los CTA de reserva y poner un aviso claro |
| 4 | Schema de reseñas duplicado e inconsistente en todas las páginas | 2–3 bloques `LocalBusiness` por página; `AggregateRating` 4,5/110 (con coma decimal, inválido) y 4.5/123; los mismos 6 `Review` repetidos en todo el sitio | Un solo `LocalBusiness` (home/contacto) sin reseñas propias; quitar los bloques duplicados del resto |

## Prioridad 2 — redirecciones y URLs antiguas

Estado real de las URLs del histórico (GSC, hoja ON-PAGE, linkbuilding):

| URL | Estado | Acción |
|---|---|---|
| `/epilation-definitive/` | 301 → `/epilation-laser-perpignan/` | OK |
| `/epilation-laser-3-en-1/` | 301 → `/epilation-laser-perpignan/` | OK, pero ver punto 1 |
| `/lumiere-pulsee-focalisee/` | 301 → `/epilation-laser-perpignan/` | OK |
| `/blog/centre-epilation-laser/` | 301 → `/epilation-laser-perpignan/` | OK |
| `/blog/epilation-perpignan-guide-complet-…/` | 301 → `/epilation-laser-perpignan/` | OK |
| `/detatouage/` | 301 → `/detatouage-perpignan/` | OK |
| `/pourquoi-opter-…`, `/eliminer-les-taches-…`, `/depilation-laser-chez-depilinea-…` (sin `/blog/`) | 301 → versión `/blog/` | OK |
| `/epilation-perpignan-guide-complet-…/` (sin `/blog/`) | **404** | 301 → `/epilation-laser-perpignan/` (punto 2) |
| `/les-differentes-methodes-depilation-disponibles-a-perpignan/` | **404** | 301 → `/epilation-laser-perpignan/` |
| `/blog/` | **404** (aunque todos los posts cuelgan de `/blog/…`) | 301 → `/categorie/blog/` |
| `/category/blog/`, `/category/blog/page/2/` | **404** | 301 → `/categorie/blog/` |
| `/accueil-2/` | 404 | OK (borrador eliminado) |
| `https://www.` e `/index.php` | 301 → `https://depilinea.fr/` | OK |
| `http://` | no comprobable desde el entorno de auditoría | Verificar a mano que hace 301 a https |

Ningún enlace interno apunta a redirecciones ni a 404, y el sitemap no tiene URLs con problemas.

## Prioridad 3 — on-page y enlazado interno

- **Title de la home sin "Perpignan" ni servicio**: "Centre Laser Spécialisé - DEPILINEA". Propuesta: "Épilation laser Perpignan | Centre laser spécialisé - DEPILINEA".
- **`/electrolyse-perpignan/`**: el title y el H1 dicen "Thermolyse" y la consulta que posiciona es "electrolyse perpignan" (pos. 5,5, CTR 12%). Propuesta: "Électrolyse & thermolyse Perpignan - DEPILINEA".
- `/le-centre/` y `/contact/` con titles genéricos; `/contact/` con 283 palabras.
- **Sin enlaces contextuales entre servicios**: `/electrolyse-perpignan/`, `/body-sculpt/`, `/detatouage-perpignan/` y `/le-centre/` no tienen ningún enlace interno en el contenido. Todo pasa por el menú (anchors repetidos ×26).
- `/epilation-laser-perpignan/` recibe 320 enlaces, todos de menú. El post con más impresiones (`/blog/quand-se-raser-…`) le da un único enlace contextual; los 4 posts antiguos solo reciben enlaces desde la categoría.
- Logo con alt "logo depilinea en negro" en las 26 páginas; 4 imágenes sin alt por página (plantilla).
- `/categorie/blog/` sin H1. La página de autor tiene una meta description de plantilla: "Découvrez l'univers créatif de [Nom de l'auteur]…" (noindex, pero visible).
- 11 titles de más de 60 caracteres (posts) y 10 meta descriptions de más de 160.
- `/epilation-laser-perpignan-rdv-gratuit/`: noindex/nofollow, huérfana y fuera del sitemap. Correcto si es la landing de Ads.
- Enlace a Facebook (`/DepilineaFrance/`) da 400 a bots; revisar a mano.

## Prioridad 4 — rendimiento (Lighthouse móvil, laboratorio)

| Página | Perf. | LCP | TBT | CLS | Peso |
|---|---|---|---|---|---|
| Home | 56 | 8,9 s | 390 ms | 0,016 | 1,4 MB |
| /epilation-laser-perpignan/ | 63 | 7,5 s | 190 ms | 0,008 | 1,3 MB |
| /detatouage-perpignan/ | 72 | 4,1 s | 160 ms | 0,023 | 0,7 MB |

Acciones: imagen hero (LCP) con preload y `fetchpriority=high`, sin lazy-load; lazy-load del resto (546 KB ahorrables en la landing); `width`/`height` en imágenes; política de caché para los estáticos (30+ recursos); preconnect a los orígenes externos; quitar `user-scalable=no` del viewport (accesibilidad).
