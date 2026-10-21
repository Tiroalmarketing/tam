# Landing «Migración web» · Guía de montaje paso a paso

Tiempo estimado: 30–40 minutos. Nada queda visible hasta el paso 7.

## Archivos de esta carpeta

| Archivo | Para qué sirve |
|---|---|
| `plantilla-elementor-migracion-web.json` | La landing completa para importar en Elementor |
| `cf7-formulario-hero.txt` | Código del formulario corto (arriba de la página) |
| `cf7-formulario-contacto.txt` | Código del formulario completo (final de la página) |
| `logo-almark.svg`, `logo-grupalia.webp` | Logos de clientes. Ya van incrustados en la plantilla; los archivos son por si los quieres en la biblioteca de medios |

---

## Paso 0 · Copia de seguridad
SiteGround → Site Tools → Seguridad → Copias de seguridad → **Crear copia**. Es un minuto y te cubre ante cualquier imprevisto.

---

## Paso 1 · Crear los dos formularios en Contact Form 7

### 1A. Formulario del hero
1. **Contacto → Añadir nuevo**. Título: `Migración web – Hero`.
2. Pestaña **Formulario**: borra todo y pega el contenido de `cf7-formulario-hero.txt`.
3. Pestaña **Correo electrónico**:
   - **Para:** `info@tiroalmarketing.com`
   - **De:** `Tiro al Marketing <wordpress@tiroalmarketing.com>` (tiene que ser una dirección de tu dominio o el email puede acabar en spam)
   - **Asunto:** `Migración web (hero): [web-actual]`
   - **Cabeceras adicionales:** `Reply-To: [your-email]`
   - **Cuerpo del mensaje:**
     ```
     Nueva solicitud desde la landing de migración web.

     Formulario: [origen]
     Email: [your-email]
     Web actual: [web-actual]
     Qué va a cambiar: [tipo-migracion]
     Resultado del test de riesgo: [riesgo-test]

     --
     Enviado desde [_url] el [_date] a las [_time]
     ```
4. **Guardar**. Arriba aparece el shortcode, por ejemplo `[contact-form-7 id="a1b2c3d" title="Migración web – Hero"]`. **Cópialo** en un bloc de notas.

### 1B. Formulario de contacto
1. **Contacto → Añadir nuevo**. Título: `Migración web – Contacto`.
2. Pestaña **Formulario**: pega el contenido de `cf7-formulario-contacto.txt`.
3. Pestaña **Correo electrónico**: igual que el anterior, pero con:
   - **Asunto:** `Migración web: [your-name] – [web-actual]`
   - **Cuerpo del mensaje:**
     ```
     Nueva solicitud desde la landing de migración web.

     Formulario: [origen]
     Nombre: [your-name]
     Email: [your-email]
     Teléfono: [your-phone]
     Web actual: [web-actual]
     Tipo de migración: [tipo-migracion]
     Fecha prevista: [fecha-prevista]
     Resultado del test de riesgo: [riesgo-test]

     --
     Enviado desde [_url] el [_date] a las [_time]
     ```
4. **Guardar** y copia también este shortcode.

> El campo «Resultado del test de riesgo» se rellena solo si el visitante usa el test de la página antes de enviar. Si no lo usa, llega vacío.

---

## Paso 2 · Importar la plantilla en Elementor
1. **Plantillas → Plantillas guardadas** (en algunas versiones: *Elementor → Plantillas*).
2. Botón **Importar plantillas** (arriba) → elige `plantilla-elementor-migracion-web.json` → **Importar ahora**.
3. Aparecerá en la lista como **«Migración web – Tiro al Marketing»**.

---

## Paso 3 · Crear la página
1. **Páginas → Añadir nueva**.
2. Título: `Migración web sin perder posicionamiento SEO`.
3. Enlace permanente (slug): `migracion-web`. Página superior: **ninguna**.
4. **Ajustes de Kadence** de la página: copia los mismos que tiene la página de abogados (ancho completo, título oculto, sin espaciado vertical del contenido). Si no los recuerdas, abre la de abogados en otra pestaña y compáralos.
5. **Guardar borrador** (no publiques todavía) → **Editar con Elementor**.

---

## Paso 4 · Insertar la plantilla
1. En el lienzo vacío pulsa el icono de **carpeta** («Añadir plantilla»).
2. Pestaña **Mis plantillas** → «Migración web – Tiro al Marketing» → **Insertar**.
3. Si pregunta por importar los ajustes de página, elige **No**.

---

## Paso 5 · Pegar los formularios
La plantilla tiene dos widgets **Shortcode** con un texto provisional:

1. **Hero** (tarjeta oscura de la derecha): haz clic en el widget que pone `PEGA-AQUI-ID-FORM-HERO` y sustituye todo su contenido por el shortcode del paso 1A.
2. **Contacto** (última sección): sustituye `PEGA-AQUI-ID-FORM-CONTACTO` por el shortcode del paso 1B.

---

## Paso 6 · Revisar antes de publicar
1. **Vista previa** (icono del ojo). El editor de Elementor no ejecuta el código de los widgets HTML, así que el test de riesgo solo funciona en la vista previa.
2. Revisa en **escritorio, tablet y móvil**: modo responsive de Elementor o tu propio móvil con el enlace de vista previa.
3. Comprueba que:
   - Las «pastillas» de ¿Qué vas a cambiar? cambian a rojo al pulsarlas.
   - El test de riesgo cambia de nivel al marcar casillas.
   - Los botones de WhatsApp abren el chat con el mensaje «Hola, quiero valorar la migración de mi web».
   - Los botones «Pedir presupuesto» bajan al formulario final.

---

## Paso 7 · SEO (Yoast) y publicación
1. En la página (editor de WordPress), caja **Yoast SEO**:
   - **Frase clave:** `migración web`
   - **Frases clave relacionadas** (si tienes Yoast Premium): `consultoría de migración web`, `migración de página web`
   - **Título SEO:** `Migración Web sin Perder Posicionamiento SEO | Tiro al Marketing`
   - **Meta descripción:** `Consultoría de migración web para cambiar de web, CMS o dominio sin perder posiciones: redirecciones URL a URL y seguimiento 90 días. Desde 300 €.`
   - Pestaña **Avanzado → Título de la miga de pan:** `Migración web`
2. **Publicar**.
3. **Purgar caché:** SiteGround Optimizer → *Purgar caché* (o el botón de la barra superior de WordPress).

> No hace falta añadir datos estructurados en Yoast: la plantilla ya incluye el schema `Service` (con precio desde 300 €) y `FAQPage` en el widget de la FAQ, enlazados con la organización que genera Yoast.

---

## Paso 8 · Pruebas después de publicar
1. **Envía los dos formularios** con tu email y comprueba que llegan a `info@tiroalmarketing.com` con todos los campos.
2. **GTM → Vista previa** (contenedor `GTM-PVX2KRVD`) sobre la página:
   - Envío de formulario → `envio_formulario`. Clic en WhatsApp → `clic_whatsapp`. Clic en «Llamar ahora» → `clic_llamar`.
   - Primer uso del test de riesgo → evento `test_riesgo_migracion` en la capa de datos. Para enviarlo a GA4, crea un activador de *Evento personalizado* `test_riesgo_migracion` y una etiqueta *Evento de GA4* con el mismo nombre.
3. **Valida el schema** en https://validator.schema.org con la URL de la página.
4. **Search Console → Inspección de URLs** → `https://tiroalmarketing.com/migracion-web/` → **Solicitar indexación**.

---

## Paso 9 · Enlazado interno (clave para que posicione)
1. **Menú principal:** dentro de SEO, añade «Migración web».
2. **Home:** añade una tarjeta en el bloque de servicios enlazando a la nueva página.
3. **`/diseno-web-seo/`:** un párrafo del tipo «¿Ya tienes web? La rediseñamos sin perder tu posicionamiento» con enlace (anchor: *rediseño web sin perder SEO*).
4. **`/servicio-auditoria-seo/`:** en «Qué incluye», enlace con anchor *auditoría previa a una migración*.
5. **Formularios generales de la web** (home y `/contacto/`): añade la opción «Migración web» al desplegable de servicio.

---

## Cómo editar textos más adelante
- **Titulares, párrafos y botones** son widgets nativos de Elementor: haz clic y edita.
- **Tarjetas, proceso, test, precios, tabla, opiniones y FAQ** están en widgets **HTML**. Ábrelos y edita el texto entre etiquetas.
- **Si cambias una pregunta o respuesta de la FAQ**, cámbiala también en el bloque `<script type="application/ld+json">` del mismo widget, para que el schema coincida con lo que se ve.
- **Los estilos** están en el primer widget HTML del hero, el que contiene `<style>`. Todas las clases empiezan por `tmw-`, así que no afectan al resto de la web.

## Pendiente
- **Caso de éxito de migración:** cuando lo tengas preparado, pásame los datos y te doy el bloque para insertarlo entre «Opiniones» y la FAQ.
- **IVA:** confirma si los precios (300 € y 450 €) llevan IVA incluido. Si no, conviene añadir «+ IVA» en la nota bajo los precios y en la FAQ.
