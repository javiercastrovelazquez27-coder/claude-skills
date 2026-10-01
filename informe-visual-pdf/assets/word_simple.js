// Word acompañante del informe: una o dos hojas, sin gráficas.
// DATOS FICTICIOS. Copia a la carpeta de trabajo junto a logo.png, cambia DATOS y corre:
//   node word_simple.js   (si falla require('docx'): npm install docx)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat, Footer, PageNumber,
} = require("docx");

const NB = " "; // espacio duro: "1 400" y "65 %" no se parten de línea

const DATOS = {
  salida: "Informe.docx",
  color: "0075A2",          // color principal de la marca, sin #
  fuente: "Calibri",
  logo: { archivo: "logo.png", ancho: 150, alto: 58 },   // respeta la proporción del PNG
  titulo: "Nombre del informe",
  subtitulo: "Tema · 1 de julio de 2026",
  pie: "Área · Empresa",
  // Párrafo inicial: texto plano y {b: "..."} para negritas.
  resumen: ["En el semestre se cobraron ", { b: `$94${NB}mil` }, ". Hay ", { b: `$18${NB}mil` }, " vencidos."],
  tabla: {
    anchos: [3000, 3360, 3000],          // suman 9360 = carta con márgenes de 1"
    encabezado: ["Concepto", "Detalle", "Monto"],
    filas: [["Cobrado", "Enero a junio", `$94${NB}000`], ["Vencido", "Más de 30 días", `$18${NB}000`]],
    total: ["Total", "", `$112${NB}000`],
    nota: "Cifras al 30 de junio.",
  },
  secciones: [
    { titulo: "Lo que hay que saber", vinetas: [[{ b: "Hallazgo: " }, "consecuencia, con su número."]] },
    { titulo: "Qué hacer", parrafo: ["Acción concreta, con verbo y objeto."] },
  ],
};

const runs = (partes) => [].concat(partes).map((x) =>
  typeof x === "string" ? new TextRun(x) : new TextRun({ text: x.b, bold: true }));
const borde = { style: BorderStyle.SINGLE, size: 4, color: "C8C8C8" };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };
const ultima = DATOS.tabla.anchos.length - 1;
const celda = (t, i, { head = false, bold = false } = {}) => new TableCell({
  width: { size: DATOS.tabla.anchos[i], type: WidthType.DXA }, borders: bordes,
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  shading: head ? { type: ShadingType.CLEAR, fill: DATOS.color, color: "auto" } : undefined,
  children: [new Paragraph({
    alignment: i === ultima ? AlignmentType.RIGHT : AlignmentType.LEFT,
    children: [new TextRun({ text: t, bold: head || bold, color: head ? "FFFFFF" : undefined })],
  })],
});
const fila = (cols, opts) => new TableRow({
  tableHeader: !!(opts && opts.head), children: cols.map((c, i) => celda(c, i, opts)),
});
const h = (t) => new Paragraph({ spacing: { before: 280, after: 100 },
  children: [new TextRun({ text: t, bold: true, size: 26, color: DATOS.color })] });

const cuerpo = [
  new Paragraph({ spacing: { after: 240 }, children: [new ImageRun({ type: "png",
    data: fs.readFileSync(path.join(__dirname, DATOS.logo.archivo)),
    transformation: { width: DATOS.logo.ancho, height: DATOS.logo.alto } })] }),
  new Paragraph({ spacing: { after: 60 },
    children: [new TextRun({ text: DATOS.titulo, bold: true, size: 40, color: DATOS.color })] }),
  new Paragraph({ spacing: { after: 280 }, children: [new TextRun({ text: DATOS.subtitulo, color: "5B6B75" })] }),
  new Paragraph({ spacing: { after: 240 }, children: runs(DATOS.resumen) }),
  new Table({
    width: { size: DATOS.tabla.anchos.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: DATOS.tabla.anchos,
    rows: [fila(DATOS.tabla.encabezado, { head: true }), ...DATOS.tabla.filas.map((f) => fila(f)),
      ...(DATOS.tabla.total ? [fila(DATOS.tabla.total, { bold: true })] : [])],
  }),
  new Paragraph({ spacing: { before: 80, after: 120 },
    children: [new TextRun({ text: DATOS.tabla.nota, size: 18, color: "687782" })] }),
];
for (const sec of DATOS.secciones) {
  cuerpo.push(h(sec.titulo));
  if (sec.parrafo) cuerpo.push(new Paragraph({ spacing: { after: 120 }, children: runs(sec.parrafo) }));
  for (const v of sec.vinetas || []) {
    cuerpo.push(new Paragraph({ numbering: { reference: "vinetas", level: 0 }, spacing: { after: 60 }, children: runs(v) }));
  }
}

const doc = new Document({
  title: DATOS.titulo,
  styles: { default: { document: { run: { font: DATOS.fuente, size: 22 } } } },
  numbering: { config: [{ reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 1260, bottom: 1260, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: `${DATOS.pie} · `, size: 16, color: "687782" }),
      new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "687782" })] })] }) },
    children: cuerpo,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(path.join(__dirname, DATOS.salida), buf);
  console.log(path.join(__dirname, DATOS.salida));
});
