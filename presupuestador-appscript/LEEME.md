# INGAS — Presupuestador (Apps Script)

Web app público donde la gente arma su pedido de trabajos de gas y lo envía.
Los precios los define el cliente (INGAS) en una planilla de Google; las
solicitudes caen en una hoja para que las vea.

## Archivos
- **Codigo.gs** — backend (crea la planilla, sirve el web app, lee precios, guarda solicitudes).
- **Index.html** — interfaz del presupuestador.
- **appsscript.json** — manifiesto (zona horaria, permisos, acceso público).

## Puesta en marcha (una sola vez)
1. Entrá a https://script.google.com → **Nuevo proyecto**.
2. Creá un archivo HTML llamado exactamente **Index** y pegá el contenido de `Index.html`.
   Pegá `Codigo.gs` en el archivo de código. (Opcional: activá el manifiesto
   en *Configuración del proyecto → Mostrar appsscript.json* y pegá su contenido.)
3. En el selector de funciones elegí **inicializar** y tocá **Ejecutar**.
   Autorizá los permisos. Esto crea la planilla **“INGAS — Presupuestador (datos)”**
   con tres hojas:
   - **Precios** → el cliente carga el valor de cada trabajo (columna *Precio*).
   - **Config** → mes de referencia, IVA, WhatsApp, email de avisos, mensaje,
     y *Mostrar precios al público* (SÍ/NO).
   - **Solicitudes** → cada pedido que envía la gente.
   En **Registro de ejecución** aparece el **link de la planilla** (guardalo).
4. **Implementar → Nueva implementación → Aplicación web**
   - *Ejecutar como:* Yo
   - *Quién tiene acceso:* Cualquier usuario
   - Copiá la **URL del web app**: esa es la que se comparte / se enlaza desde el sitio.

## Uso
- **El cliente** edita la hoja *Precios* para actualizar valores (cada mes).
  Puede desactivar un trabajo con la casilla *Activo*. Los cambios se reflejan
  solos (no hay que volver a publicar).
- **La gente** entra a la URL, elige los trabajos y cantidades, ve un estimado
  (si *Mostrar precios al público* = SÍ) y envía la solicitud con sus datos.
- **Las solicitudes** quedan en la hoja *Solicitudes*. Si cargás un correo en
  *Config → Email de avisos*, además te llega un mail por cada pedido.

## Notas
- Si ponés *Mostrar precios al público* = **NO**, la app oculta los montos y
  solo recopila el pedido para que INGAS cotice.
- El estimado es de referencia: no incluye IVA, movilidad, ayudante ni viáticos
  (así lo aclara la pantalla).
- El logo se toma de `https://damianm1121.github.io/INGAS/incas-logo-estatico.png`.
  Si cambia la URL del sitio, actualizá esa línea en `Index.html`.
