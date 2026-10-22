# Página «Diseño web SEO» · Guía de montaje paso a paso

Se sustituye el contenido de la página que ya existe (`/diseno-web-seo/`). Así se conservan la URL, su historial en Google y los enlaces internos. Tiempo estimado: 40 minutos.

## Archivos de esta carpeta

| Archivo | Para qué sirve |
|---|---|
| `plantilla-elementor-diseno-web-seo.json` | La página completa para importar en Elementor |
| `cf7-formulario-hero.txt` | Formulario corto (arriba de la página) |
| `cf7-formulario-contacto.txt` | Formulario completo (final de la página) |
| `portfolio-depilinea.webp`, `portfolio-la-voz-de-lili.webp`, `portfolio-almark.webp` | Imágenes del portfolio, ya optimizadas (24–45 KB cada una) |

---

## Paso 0 · Copia de seguridad
1. SiteGround → Copias de seguridad → **Crear copia**.
2. Abre `/diseno-web-seo/` con Elementor → flecha junto a **Actualizar** → **Guardar como plantilla** → nombre `Diseño web SEO – versión antigua`. Si algo sale mal, la recuperas en un clic.

## Paso 1 · Subir las imágenes del portfolio
1. **Medios → Añadir nuevo** y sube los tres archivos `.webp` **sin cambiarles el nombre**.
2. Abre una de ellas y copia su URL. Debe ser `https://tiroalmarketing.com/wp-content/uploads/2026/10/portfolio-depilinea.webp`.
   - **Si coincide** (año 2026, mes 10), no hay que hacer nada más.
   - **Si no coincide** (por ejemplo, si las subes otro mes), en el paso 5 abre el widget HTML del portfolio y cambia `/2026/10/` por la carpeta correcta en las tres imágenes.

## Paso 2 · Crear los dos formularios en Contact Form 7

### 2A. `Diseño web – Hero`
1. **Contacto → Añadir nuevo**. Título: `Diseño web – Hero`.
2. Pestaña **Formulario**: pega `cf7-formulario-hero.txt`.
3. Pestaña **Correo electrónico**:
   - **Para:** `info@tiroalmarketing.com`
   - **De:** `Tiro al Marketing <wordpress@tiroalmarketing.com>`
   - **Asunto:** `Diseño web (hero): [tipo-web]`
   - **Cabeceras adicionales:** `Reply-To: [your-email]`
   - **Cuerpo:**
     ```
     Nueva solicitud desde la página de diseño web SEO.

     Formulario: [origen]
     Email: [your-email]
     Web actual: [web-actual]
     Qué necesita: [tipo-web]
     Calculadora: [calculadora]

     --
     Enviado desde [_url] el [_date] a las [_time]
     ```
4. Pestaña **Configuración adicional**: `acceptance_as_validation: on`
5. **Guardar** y copia el shortcode.

### 2B. `Diseño web – Contacto`
Igual que el anterior, con:
- **Formulario:** `cf7-formulario-contacto.txt`
- **Asunto:** `Diseño web: [your-name] – [tipo-web]`
- **Cuerpo:**
  ```
  Nueva solicitud desde la página de diseño web SEO.

  Formulario: [origen]
  Nombre: [your-name]
  Email: [your-email]
  Teléfono: [your-phone]
  Web actual: [web-actual]
  Qué necesita: [tipo-web]
  Calculadora: [calculadora]

  --
  Enviado desde [_url] el [_date] a las [_time]
  ```
- **Configuración adicional:** `acceptance_as_validation: on`

> El campo «Calculadora» llega relleno si el visitante usa la calculadora antes de enviar, por ejemplo: «Tienda online · 6 a 10 páginas · Blog · orientativo desde 700 € + IVA».

## Paso 3 · Importar la plantilla
**Plantillas → Plantillas guardadas → Importar plantillas**. Asegúrate de estar en **Plantillas del sitio**, no en la nube. Elige `plantilla-elementor-diseno-web-seo.json` → **Importar ahora**.

## Paso 4 · Sustituir el contenido de la página
1. Abre `/diseno-web-seo/` con **Editar con Elementor**.
2. Selecciona y **borra todas las secciones** actuales (ya tienes la copia del paso 0).
3. Icono de **carpeta** → **Mis plantillas** → «Diseño web SEO – Tiro al Marketing» → **Insertar**. Si pregunta por los ajustes de página, elige **No**.

## Paso 5 · Pegar los formularios
- Widget con `PEGA-AQUI-ID-FORM-HERO` → shortcode del paso 2A.
- Widget con `PEGA-AQUI-ID-FORM-CONTACTO` → shortcode del paso 2B.

## Paso 6 · Revisar en la vista previa
El editor de Elementor no ejecuta el código de los widgets HTML, así que la calculadora solo funciona en la **vista previa**. Comprueba en escritorio y móvil:
- La calculadora cambia el precio al elegir **Tienda online** (700 €).
- Las tres imágenes del portfolio se ven.
- Las pastillas de «¿Qué necesitas?» del formulario se marcan en rojo.

## Paso 7 · SEO (Yoast) y publicación
- **Frase clave:** `diseño web seo`
- **Título SEO:** `Diseño Web SEO para Empresas | Webs que Captan Clientes`
- **Meta descripción:** `Diseño web SEO para empresas: arquitectura orientada a negocio, textos incluidos y validación en cada fase. Entrega en 3–4 semanas. Desde 450 € + IVA.`
- **Avanzado → Título de la miga de pan:** `Diseño web SEO`

Pulsa **Actualizar** y purga la caché de SiteGround Optimizer.

## Paso 8 · Medición en GTM (opcional)
El primer uso de la calculadora envía el evento `calculadora_diseno_web` a la capa de datos. Para verlo en GA4: activador de **Evento personalizado** `calculadora_diseno_web` + etiqueta **Evento de GA4** con el mismo nombre.

## Paso 9 · Evitar que el blog compita con esta página
El artículo `/blog/diseno-web-seo-guia-completa/` también aparece en Google para «diseño web seo».
1. Cambia su **título SEO** a uno informativo: `Cómo hacer un diseño web SEO: guía paso a paso`.
2. En su primer párrafo, añade un enlace a `/diseno-web-seo/` con el texto *diseño web SEO para tu empresa*.

La página de servicio ya enlaza al artículo desde el bloque «¿Qué es el diseño web SEO?».

## Paso 10 · Precios de la calculadora (cuando los tengas)
Ahora la calculadora suma solo el precio base y muestra «Se valora en el presupuesto» en tamaños y extras. Para que sume importes, abre el widget HTML de la calculadora y, al principio del `<script>`, cambia `precio:null` por el importe en euros sin IVA (por ejemplo `precio:150`). `precio:0` muestra «Incluido».

## Cómo editar textos más adelante
- **Titulares, párrafos y botones:** widgets nativos de Elementor.
- **Portfolio, calculadora, proceso, precios, tabla, opiniones y FAQ:** widgets HTML.
- **Si cambias una pregunta de la FAQ**, cámbiala también en el bloque `<script type="application/ld+json">` del mismo widget.
