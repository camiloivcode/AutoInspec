# Sistema de diseño — AutoInspec

Este documento existe para que un cambio de UI no rompa la coherencia visual sin querer. Cada decisión de aquí sale del tema del producto, no de una preferencia estética; si vas a apartarte de alguna, que sea a propósito.

---

## Identidad: señalización vial

AutoInspec es una herramienta de inspección vehicular que se usa en campo, con el celular, muchas veces al aire libre. El vocabulario visual sale de ahí: **las señales de tránsito colombianas**.

Eso da tres cosas gratis que una plantilla genérica no da: un código de color que la gente ya sabe leer, una tipografía que literalmente pertenece al tema, y una lógica de materialidad (cómo se construye una placa de señal) que reemplaza a las sombras suaves de siempre.

---

## Color

### Los tres tokens semánticos

En señalización el color **es** código, no adorno. Los tres tokens tienen significado fijo y no se usan por fuera de él:

| Token | Significado | Uso |
|---|---|---|
| `signal` (verde) | guiar | acciones primarias, progreso, éxito, posición cubierta |
| `plate` (amarillo) | advertir | atención, confianza media, y **la placa del vehículo** |
| `stop` (rojo) | prohibir | destructivo, error |

Nunca uses `plate` porque "queda bien ahí". Si un elemento no advierte de nada, no es amarillo.

El amarillo tiene además un papel de marca: la placa particular colombiana es negro sobre amarillo, y el chip `.plate-chip` la reproduce tal cual. Es el ancla de identidad del sistema, y por eso es **el único sitio donde el amarillo aparece a plena saturación**.

### Neutros

La escala neutra (`bg`, `surface`, `border`, `fg`) es gris asfalto casi puro, definida como variables CSS en `src/index.css` y expuesta a Tailwind en `tailwind.config.js`. Es deliberadamente neutra: el verde debe ser el único croma de la pantalla.

Las variables cambian con el tema, así que **no hace falta escribir `dark:` para colores de superficie o texto**. Solo se necesita `dark:` en los tintes de croma.

### La regla que gobierna todo

> **El croma marca estado. El neutro sostiene la superficie.**

Los hexadecimales de señalización reales (MUTCD) están hechos para señales reflectivas al aire libre. En una pantalla retroiluminada, y rellenando áreas grandes, saturan y cansan. Por eso las escalas de este proyecto están rebajadas respecto al original (`#00693E` → `#427F65`), pero sobre todo por eso **el croma se aplica como acento, no como relleno**:

| Haz esto | No esto |
|---|---|
| Superficie neutra + borde o icono de color | Tarjeta entera pintada de verde |
| Badge en tinte `50` con texto `700` y borde `200` | Badge en relleno `500` sólido |
| Mosaico de icono en tinte `50` con el icono en `600` | Mosaico de 64px en `500` sólido |
| Toast neutro con barra lateral de color | Toast a sangre en verde/rojo/amarillo |
| Solo el paso activo del wizard relleno | Los cuatro segmentos rellenos |

Las excepciones —los únicos sitios con croma pleno— son el **botón primario**, el **chip de placa** y el **paso activo** del indicador. Están contadas a propósito.

Esta regla no es teórica: se violó en el commit `6aa69d2` y se corrigió en `1b9469c`. Si algo empieza a verse recargado, casi siempre es porque una superficie grande se pintó de color.

---

## Forma

**Escala de radios, bloqueada.** No inventes valores intermedios:

| Token | Valor | Para |
|---|---|---|
| `rounded-plate` | 12px | tarjetas, botones, inputs, modales |
| `rounded-chip` | 6px | badges, chips, botones de icono |
| `rounded-full` | pill | indicadores de estado, puntos |

**La keyline.** Una señal real es un rectángulo redondeado con una línea interior separada del borde. La clase `.plate` lo reproduce: `border` es el canto de la placa y un `box-shadow: inset` hace de keyline. Esto sustituye a las sombras suaves — el sistema no usa elevación difusa.

> Ojo: la keyline debe derivarse del token de borde. En su primera versión se calculaba contra el fondo de la página, lo que la dejaba blanca sobre blanco en tema claro; el detalle no se veía nunca.

**Sin gradientes.** Las señales no tienen degradados.

---

## Tipografía

**Overpass** para todo, **Overpass Mono** para datos.

Overpass es un derivado directo de *Highway Gothic*, la tipografía de las señales viales del US DOT. No es una elección estética: es la tipografía del tema.

Va **autohospedada** con `@fontsource`, importando solo el subset latino desde `src/main.tsx`. Nada de `<link>` a Google Fonts: el primer render no debe depender de una CDN externa cuando la app se usa en campo con mala conexión, ni dentro de Docker.

La monoespaciada se reserva para **datos**: placa, conteos, tamaños de archivo, nombres de archivo, números de posición. Los rótulos y botones van en mayúsculas con `tracking` amplio, como la leyenda de una señal.

---

## Primitivos (`src/components/ui/`)

Toda la UI se construye sobre estos. **No repliques sus estilos con Tailwind suelto** — si necesitas una variante nueva, añádela al primitivo.

| Componente | Notas |
|---|---|
| `Button` | variantes `primary` / `secondary` / `ghost` / `danger`, tamaños `sm` / `md` / `lg`, estado `loading`. `iconOnly` **exige `aria-label` por tipos** |
| `Card` | `Card` / `CardHeader` / `CardBody`, sobre la clase `.plate` |
| `Field` | input con label asociado, `hint`, `error` y `aria-describedby` generados |
| `Select` | sobre Radix Select, tamaños `sm` / `md` |
| `Badge` | tonos `success` / `warning` / `neutral`, siempre en tinte |
| `Modal` | sobre Radix Dialog: focus trap, Esc y restauración de foco incluidos |
| `Skeleton` | `Skeleton` y `SkeletonCard` |
| `EmptyState` | icono + título + descripción + acción |
| `Spinner` | tamaños `sm` / `md` / `lg` |

### El tamaño va por prop, nunca por `className`

`clsx` **no deduplica utilidades de Tailwind en conflicto**. Si un componente ya trae `px-4` y le pasas `px-2.5` por `className`, las dos clases acaban en el atributo y gana la que Tailwind emita después en el CSS — no la que pasaste.

Fue un bug real: el `Select` dentro de `PhotoCard` nunca fue compacto. Por eso el tamaño es una prop con su mapa de clases, como en `Button`. Si necesitas otro tamaño, añádelo al mapa.

---

## Accesibilidad

Es parte del sistema, no un extra:

- **Contraste AA verificado** en claro y oscuro. Blanco sobre `signal-500` da 4.71:1; si cambias la escala de verde, vuelve a medirlo — es el par que está más al límite.
- **Botones de icono sin etiqueta visible exigen `aria-label`**, forzado por los tipos de `Button`.
- **Nada de funcionalidad solo en hover.** En táctil no existe el hover: las acciones deben ser alcanzables sin él.
- **Modales sobre Radix**, para no reimplementar focus trap ni manejo de Esc.
- **`prefers-reduced-motion`** anula las animaciones en `index.css`.
- El tema oscuro se aplica **antes de la hidratación** con un script en `index.html`, para que no haya destello blanco.

---

## Al añadir UI nueva

1. ¿Existe ya un primitivo? Úsalo.
2. ¿El color que vas a poner significa guiar, advertir o prohibir? Si no, va neutro.
3. ¿Estás rellenando un área grande de croma? Casi seguro va tinte, no sólido.
4. Radio: `plate` o `chip`, nada más.
5. Comprueba el resultado a 375px y en tema oscuro antes de darlo por bueno.
