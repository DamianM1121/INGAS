/***************************************************************************
 *  INGAS — Presupuestador (Apps Script Web App)
 *  --------------------------------------------------------------------
 *  PASOS:
 *   1) Pegá este archivo (Codigo.gs) y el Index.html en un proyecto nuevo
 *      de Apps Script (script.google.com → Nuevo proyecto).
 *   2) Ejecutá UNA vez la función  inicializar()  (menú Ejecutar).
 *      Autorizá los permisos. Eso crea la planilla con 3 hojas:
 *         • Precios      → el cliente carga los valores
 *         • Config       → ajustes (mes, IVA, WhatsApp, etc.)
 *         • Solicitudes  → acá caen los pedidos de la gente
 *      En el Registro de ejecución vas a ver el LINK de la planilla.
 *   3) Implementar → Nueva implementación → Aplicación web
 *         Ejecutar como: Yo
 *         Quién tiene acceso: Cualquier usuario
 *      Copiá la URL del web app: esa es la que usa la gente.
 *   4) Para actualizar precios, el cliente edita la hoja "Precios".
 ***************************************************************************/

const PROP_SS = 'INGAS_PRESU_SS_ID';

/* ====== Semilla del catálogo (listado Cámara, Sept 2026) ====== */
const SEED = [
  ['Instalaciones', [
    ['Instalación de gas — cañería epoxi, zanjeado', 'por mt'],
    ['Instalación de gas — cañería epoxi, canalizado', 'por mt'],
    ['Instalación de gas — cañería epoxi, aéreo y engrampado', 'por mt'],
    ['Instalación de gas — cañería epoxi, por boca', 'por boca'],
    ['Instalación de gas — cañería fusión, zanjeado', 'por mt'],
    ['Instalación de gas — cañería fusión, canalizado', 'por mt'],
    ['Instalación de gas — cañería fusión, aéreo y engrampado', 'por mt'],
    ['Instalación de gas — cañería fusión, por boca', 'por boca'],
    ['Instalación de leño', 'unidad'],
    ['Instalación de pantalla IR', 'unidad'],
    ['Instalación de calefactor sin salida', 'unidad'],
    ['Instalación de calefactor TBH', 'unidad'],
    ['Instalación de calefactor TBU (hasta 6 mts)', 'unidad'],
    ['Instalación de calefón instantáneo TN', 'unidad'],
    ['Instalación de calefón instantáneo T.B.', 'unidad'],
    ['Instalación de termotanque (por acumulación)', 'unidad'],
    ['Instalación de cocina doméstica', 'unidad'],
    ['Instalación de cocina industrial', 'unidad'],
    ['Instalación de anafe', 'unidad'],
    ['Instalación de horno en nicho', 'unidad'],
    ['Instalación de caldera', 'unidad']
  ]],
  ['Colocación / Limpieza', [
    ['Colocación de par de rejas de ventilación', 'par'],
    ['Limpieza de calefactor sin salida', 'unidad'],
    ['Limpieza de calefactor TBH', 'unidad'],
    ['Limpieza de calefactor TBU', 'unidad'],
    ['Limpieza de calefón instantáneo', 'unidad'],
    ['Limpieza de termotanque (por acumulación)', 'unidad']
  ]],
  ['Cambios / Conversión / Diafragmas / Termocuplas', [
    ['Cambio de termocupla de calefón', 'unidad'],
    ['Cambio de termocupla de cocina', 'unidad'],
    ['Cambio de termocupla de calefactor sin salida', 'unidad'],
    ['Cambio de termocupla de calefactor TB', 'unidad'],
    ['Cambio de diafragma de calentador de agua', 'unidad'],
    ['Conversión de artefacto de GLP a GN', 'unidad']
  ]],
  ['Planta reguladora / Medidor / Pruebas', [
    ['Armado de planta reguladora', 'unidad'],
    ['Colocación de medidor con regulador', 'unidad'],
    ['Prueba manométrica hasta 3 artefactos', 'unidad'],
    ['Prueba manométrica hasta 6 artefactos', 'unidad'],
    ['Detección de fuga de gas', 'unidad']
  ]],
  ['Trámites y otros', [
    ['Trámites completos (planos, fact, parcial, final) — 3 bocas', 'unidad'],
    ['Trámites completos (planos, fact, parcial, final) — 10 bocas', 'unidad'],
    ['Factibilidad', 'unidad'],
    ['Trámites para inspección parcial', 'unidad'],
    ['Trámites para inspección final', 'unidad'],
    ['Plano completo en AutoCAD', 'unidad'],
    ['Informe de conformidad para inmobiliarias', 'unidad'],
    ['Jornal de oficial gasista', 'jornal'],
    ['Jornal de ayudante gasista', 'jornal']
  ]]
];

/* ====== 1) Inicialización: crea la planilla de datos ====== */
function inicializar() {
  const props = PropertiesService.getScriptProperties();
  let ss;
  const prev = props.getProperty(PROP_SS);
  if (prev) {
    try { ss = SpreadsheetApp.openById(prev); } catch (e) { ss = null; }
  }
  if (!ss) ss = SpreadsheetApp.create('INGAS — Presupuestador (datos)');

  /* --- Hoja Precios --- */
  let sh = ss.getSheetByName('Precios') || ss.insertSheet('Precios', 0);
  sh.clear();
  sh.getRange(1, 1, 1, 6).setValues([['ID', 'Categoría', 'Actividad', 'Unidad', 'Precio', 'Activo']])
    .setFontWeight('bold').setBackground('#0F4573').setFontColor('#ffffff');
  const filas = [];
  let i = 1;
  SEED.forEach(function (g) {
    g[1].forEach(function (it) {
      filas.push(['IT' + ('000' + i).slice(-3), g[0], it[0], it[1], '', true]);
      i++;
    });
  });
  sh.getRange(2, 1, filas.length, 6).setValues(filas);
  sh.getRange(2, 5, filas.length, 1).setNumberFormat('"$"#,##0');
  sh.getRange(2, 6, filas.length, 1).insertCheckboxes();
  sh.setFrozenRows(1);
  sh.setColumnWidth(2, 220);
  sh.setColumnWidth(3, 380);
  sh.hideColumns(1);
  sh.autoResizeColumn(4);

  /* --- Hoja Config --- */
  let cf = ss.getSheetByName('Config') || ss.insertSheet('Config');
  cf.clear();
  cf.getRange(1, 1, 1, 2).setValues([['Parámetro', 'Valor']])
    .setFontWeight('bold').setBackground('#0F4573').setFontColor('#ffffff');
  cf.getRange(2, 1, 6, 2).setValues([
    ['Mes de referencia', 'Septiembre 2026'],
    ['Mostrar precios al público', 'SÍ'],
    ['IVA (%)', 21],
    ['WhatsApp (sin + ni 15)', '5492215618081'],
    ['Email de avisos', ''],
    ['Mensaje de bienvenida', 'Armá tu presupuesto estimado seleccionando los trabajos que necesitás. Te contactamos para confirmar el valor final.']
  ]);
  cf.setFrozenRows(1);
  cf.setColumnWidth(1, 240);
  cf.setColumnWidth(2, 420);

  /* --- Hoja Solicitudes --- */
  let so = ss.getSheetByName('Solicitudes') || ss.insertSheet('Solicitudes');
  if (so.getLastRow() === 0) {
    so.getRange(1, 1, 1, 11).setValues([[
      'Fecha', 'Nombre', 'Teléfono', 'Email', 'Dirección',
      'Detalle', 'Subtotal', 'Adicionales', 'IVA', 'Total', 'Estado'
    ]]).setFontWeight('bold').setBackground('#0F4573').setFontColor('#ffffff');
    so.setFrozenRows(1);
  }

  props.setProperty(PROP_SS, ss.getId());
  const url = ss.getUrl();
  Logger.log('✅ Planilla lista: ' + url);
  return url;
}

/* ====== Helpers ====== */
function getSS_() {
  const id = PropertiesService.getScriptProperties().getProperty(PROP_SS);
  if (!id) throw new Error('Ejecutá primero la función inicializar().');
  return SpreadsheetApp.openById(id);
}
function cfgMap_(ss) {
  const v = ss.getSheetByName('Config').getDataRange().getValues();
  v.shift();
  const m = {};
  v.forEach(function (r) { m[r[0]] = r[1]; });
  return m;
}

/* ====== 2) Servir el web app ====== */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('INGAS — Presupuestador')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/* ====== 3) Datos para la UI (catálogo + config) ====== */
function getDatos() {
  const ss = getSS_();
  const pv = ss.getSheetByName('Precios').getDataRange().getValues();
  pv.shift();
  const grupos = [], idx = {};
  pv.forEach(function (r) {
    const id = r[0], cat = r[1], act = r[2], uni = r[3], precio = r[4], activo = r[5];
    if (!act || activo === false) return;
    if (!(cat in idx)) { idx[cat] = grupos.length; grupos.push({ categoria: cat, items: [] }); }
    grupos[idx[cat]].items.push({ id: String(id), actividad: act, unidad: uni, precio: Number(precio) || 0 });
  });
  const c = cfgMap_(ss);
  return {
    grupos: grupos,
    mes: c['Mes de referencia'] || '',
    mostrarPrecios: String(c['Mostrar precios al público'] || 'SÍ').trim().toUpperCase().charAt(0) === 'S',
    iva: Number(c['IVA (%)']) || 0,
    whatsapp: String(c['WhatsApp (sin + ni 15)'] || '').replace(/\D/g, ''),
    mensaje: c['Mensaje de bienvenida'] || ''
  };
}

/* ====== 4) Registrar solicitud de la gente ====== */
function registrarSolicitud(data) {
  const ss = getSS_();
  const so = ss.getSheetByName('Solicitudes');
  so.appendRow([
    new Date(),
    data.nombre || '', data.telefono || '', data.email || '', data.direccion || '',
    data.detalle || '',
    Number(data.subtotal) || 0, Number(data.adicionales) || 0,
    Number(data.iva) || 0, Number(data.total) || 0,
    'Nuevo'
  ]);
  const email = cfgMap_(ss)['Email de avisos'];
  if (email) {
    try {
      MailApp.sendEmail(
        String(email),
        'Nueva solicitud de presupuesto — INGAS',
        'Contacto: ' + (data.nombre || '') + ' / ' + (data.telefono || '') + ' / ' + (data.email || '') +
        '\nDirección: ' + (data.direccion || '') + '\n\n' + (data.detalle || '')
      );
    } catch (e) { /* si no hay permiso de mail, se ignora */ }
  }
  return { ok: true };
}
