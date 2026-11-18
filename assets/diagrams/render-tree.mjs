// Renders <name>.txt to <name>.svg: a file tree with an aligned explanation column.
// Usage: node render-tree.mjs [name], default project-structure.
import { readFileSync, writeFileSync } from "node:fs";

const dir = import.meta.dirname;
const name = process.argv[2] ?? "project-structure";
const colors = {
	d: { path: "#1a2b45", note: "#1a2b45" },
	w: { path: "#b03a37", note: "#4a1a18" },
	c: { path: "#2f5a96", note: "#1a2b45" },
	o: { path: "#6b7280", note: "#6b7280" },
};
const legend = [
	["w", "workshop: where you work"],
	["c", "core: read this code"],
	["o", "other: outside the workshop path"],
];

const rows = readFileSync(`${dir}/${name}.txt`, "utf-8")
	.split("\n")
	.filter((line) => line && !line.startsWith("#"))
	.map((line) => {
		const role = line[0];
		const [path, note = ""] = line.slice(2).split(" -- ");
		return { role, path, note };
	});

const fontSize = 14;
const charWidth = 9.1; // advance of a 14px monospace glyph, with room for wider fonts such as Menlo
const lineHeight = 24;
const pad = 24;
const noteX = pad + Math.max(...rows.map((row) => [...row.path].length)) * charWidth + 32;
const legendWidth = legend.reduce((sum, [, label]) => sum + 18 + label.length * charWidth + 28, 0) - 28;
const width = Math.ceil(Math.max(noteX + Math.max(...rows.map((row) => [...row.note].length)) * charWidth, pad + legendWidth) + pad);
const legendY = pad + rows.length * lineHeight + 20;
const height = legendY + 24 + pad;

const escape = (text) => text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const lines = rows.map((row, i) => {
	const y = pad + (i + 1) * lineHeight - 6;
	const branch = row.path.match(/^[│├└─\s]*/)[0];
	const name = row.path.slice(branch.length);
	// One text run, so the browser places the name right after the branch glyphs.
	const parts = [
		`<text x="${pad}" y="${y}"><tspan fill="#9aa7b8">${escape(branch)}</tspan><tspan fill="${colors[row.role].path}" font-weight="600">${escape(name)}</tspan></text>`,
	];
	if (row.note) parts.push(`<text x="${noteX}" y="${y}" fill="${colors[row.role].note}">${escape(row.note)}</text>`);
	return parts.join("");
});
let legendX = pad;
const legendItems = legend.map(([role, label]) => {
	const item = `<rect x="${legendX}" y="${legendY}" width="12" height="12" rx="2" fill="${colors[role].path}"/><text x="${legendX + 18}" y="${legendY + 11}" fill="#4b5563">${escape(label)}</text>`;
	legendX += 18 + label.length * charWidth + 28;
	return item;
});

const svg = `<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace" font-size="${fontSize}">
<rect width="100%" height="100%" fill="#ffffff"/>
${lines.join("\n")}
<line x1="${pad}" y1="${legendY - 12}" x2="${width - pad}" y2="${legendY - 12}" stroke="#e5e7eb"/>
${legendItems.join("\n")}
</svg>
`;
writeFileSync(`${dir}/${name}.svg`, svg);
