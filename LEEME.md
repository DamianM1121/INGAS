# Logo INCAS animado para encabezado web

Animación del logo con **fondo transparente**: el color o degradado de tu encabezado se ve a través.
Las letras **aparecen** una por una, la **A-llama se enciende** desde la base y después el **fuego queda vivo** en bucle infinito.

Vista previa en vivo (temporal): <https://8080-iyff0tgv5chd3p76zne4f-5eab2a4e.us4.manus.computer/demo-encabezado.html>

---

## Archivos

| Archivo | Tamaño | Peso | Qué es |
|---|---|---|---|
| `incas-logo-intro.webp` | 640×240 · 2,48 s | 486 KB | Aparición de letras + encendido del fuego. Se reproduce **una sola vez**. |
| `incas-logo-fuego-loop.webp` | 640×240 · 2 s | 329 KB | Solo el fuego, **bucle perfecto** (empalme sin salto). Es lo que queda en el encabezado. |
| `incas-logo.webp` | 640×240 · 4,48 s | 806 KB | Todo en uno, bucle infinito (la aparición se repite cada 4,48 s). |
| `incas-logo-estatico.png` | 640×240 | 38 KB | Versión fija, sin animación, con el borde corregido. |
| `demo-encabezado.html` | — | — | Página de prueba con los tres fondos y el código para copiar. |
| `generar-animacion.py` | — | — | Script que genera todo desde `image.png` (por si querés ajustar tiempos o colores). |

---

## Uso recomendado (dos capas, sin JavaScript)

Abajo el fuego en bucle infinito, arriba la intro que se desvanece sola a los 2,48 s.
El fuego nunca se detiene y el empalme es perfecto porque la intro termina exactamente en la fase 0 del bucle.

```html
<div class="logo">
  <img class="logo-fire"  src="incas-logo-fuego-loop.webp" width="640" height="240"
       alt="INCAS — Instalaciones internas, industriales y domiciliarias">
  <img class="logo-intro" src="incas-logo-intro.webp" width="640" height="240"
       alt="" aria-hidden="true">
</div>
```

```css
.logo{
  position:relative;
  display:inline-block;
  width:clamp(190px,32vw,290px);   /* ajustá el ancho a gusto */
  line-height:0;
}
.logo img{display:block;width:100%;height:auto}

.logo-intro{
  position:absolute;inset:0;pointer-events:none;
  animation:logoIntroOut .3s linear 2.48s forwards;   /* 2,48 s = duración de la intro */
}
@keyframes logoIntroOut{to{opacity:0}}
```

> Si preferís una sola imagen: `<img src="incas-logo.webp" width="640" height="240" alt="INCAS — Instalaciones internas, industriales y domiciliarias">`

---

## Detalles técnicos

- **Formato:** WebP animado con canal alfa (24 bits + alfa). Soporte: Chrome, Edge, Firefox, Safari 14+ (macOS Big Sur / iOS 14) y Android. Pesa 30–60 % menos que el GIF equivalente y no tiene bordes dentados.
- **Fondo:** transparente real. No hay caja blanca ni fondo de ningún color.
- **Bucle de fuego:** 2 s a 25 fps. El ruido que deforma la llama es periódico, por eso el cierre del bucle no da salto.
- **Borde corregido:** el PNG original traía un halo claro de 1 px alrededor de las letras y las llamas (artefacto típico de quitar el fondo con una herramienta automática). Se recalculó el color y el alfa de esos píxeles, así que sobre fondo oscuro ya no aparece la línea clara.
- **Cómo está hecho el fuego:** el logo se separó en capas (letras I, N, C, S · llama azul marino que forma la A · llama cian grande · gota cian interna · subtítulo). A las llamas se les aplica un campo de desplazamiento suave que crece hacia la punta (la base queda anclada), más un pulso de brillo, una lengua de luz que sube y un resplandor cian que late detrás. Las letras entran con desvanecido + leve subida, escalonadas de izquierda a derecha.

---

## Dos cosas a tener en cuenta

1. **Subtítulo sobre fondo oscuro.** "Instalaciones internas, industriales y domiciliarias" es gris muy oscuro (#1B1B1B) y sobre un encabezado oscuro casi no se lee (se ve en la demo con el fondo "Oscuro"). Si tu encabezado es oscuro, se puede generar la versión con el subtítulo en blanco — o con las letras en blanco y el fuego a color.
2. **Peso.** Los 640×240 son la resolución nativa del logo (queda nítido hasta pantallas retina). Si necesitás aligerarlo, se puede bajar a 480×180 o 320×120, o acortar el bucle de fuego.

---

## Regenerar o ajustar

```bash
python3 generar-animacion.py       # necesita image.png en la misma carpeta, Pillow, numpy y ffmpeg
```

Parámetros útiles al principio del script:

| Constante | Qué controla |
|---|---|
| `FPS` | fotogramas por segundo (25) |
| `T_LOOP` | duración del bucle de fuego en segundos (2.0) |
| `IGNITE_T` | cuándo se enciende el fuego dentro de la intro (0.48 s) |
| `ALPHA_BITS` | precisión del canal alfa (6 bits = mismo aspecto, ~30 % menos de peso) |
| `QFINAL` | calidad de compresión WebP (78) |

Los tiempos de aparición de cada letra están en la función `frame()`, en el diccionario `times`.
