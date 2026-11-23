// Renders <name>.txt to <name>.svg: a file tree with an aligned explanation column, rows grouped into
// tinted sections. Usage: node render-tree.mjs [name], default python-structure.
import { readFileSync, writeFileSync } from "node:fs";

const dir = import.meta.dirname;
const name = process.argv[2] ?? "python-structure";
// The colors of Pi's packages: coding-agent blue, agent purple, ai green, your code red.
const colors = {
	d: { path: "#1a2b45", note: "#1a2b45" },
	a: { path: "#2f5a96", note: "#1a2b45" },
	l: { path: "#6d4bb3", note: "#1a2b45" },
	m: { path: "#2f7d5b", note: "#1a2b45" },
	w: { path: "#b03a37", note: "#4a1a18" },
	r: { path: "#b7791f", note: "#4a3510" },
	o: { path: "#6b7280", note: "#6b7280" },
};
const legend = [
	["a", "app: terminal, session, models"],
	["l", "agent loop"],
	["m", "talks to the model"],
	["w", "where you work"],
	["r", "read and run"],
	["o", "outside the workshop"],
];
// Section bands: a tint and a label color, chosen by the first role in the section.
const bands = {
	a: { fill: "#f4f7fc", label: "#2f5a96" },
	w: { fill: "#fcf3f3", label: "#b03a37" },
	r: { fill: "#fcf7ec", label: "#b7791f" },
	o: { fill: "#f6f7f8", label: "#6b7280" },
};

const rows = [];
let section = null;
for (const line of readFileSync(`${dir}/${name}.txt`, "utf-8").split("\n")) {
	if (line.startsWith("## ")) {
		section = { label: line.slice(3), first: rows.length };
		continue;
	}
	if (!line || line.startsWith("#")) continue;
	const [path, note = ""] = line.slice(2).split(" -- ");
	rows.push({ role: line[0], path, note, section });
}

const fontSize = 14;
const charWidth = 9.1; // advance of a 14px monospace glyph, with room for wider fonts such as Menlo
const lineHeight = 24;
const pad = 24;
const labelSize = 11;
const noteX = pad + Math.max(...rows.map((row) => [...row.path].length)) * charWidth + 32;
const notesEnd = noteX + Math.max(...rows.map((row) => [...row.note].length)) * charWidth;
const labels = [...new Set(rows.map((row) => row.section).filter(Boolean))];
const labelWidth = Math.max(0, ...labels.map((s) => s.label.length * 7.4)) + 24;
const legendItemWidth = ([, label]) => 18 + label.length * charWidth + 28;
const legendRows = [legend.slice(0, 3), legend.slice(3)];
const legendWidth = Math.max(...legendRows.map((items) => items.reduce((sum, item) => sum + legendItemWidth(item), 0) - 28));
const width = Math.ceil(Math.max(notesEnd + 24 + labelWidth, pad + legendWidth) + pad);
const legendY = pad + rows.length * lineHeight + 22;
const height = legendY + legendRows.length * 24 + pad;

const escape = (text) => text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

// Section bands behind their rows, with the label at the right.
const bandShapes = labels.map((s) => {
	const members = rows.filter((row) => row.section === s);
	const top = pad + rows.indexOf(members[0]) * lineHeight + 3;
	const h = members.length * lineHeight - 3; // a small gap between neighbouring bands
	const band = bands[members[0].role] ?? bands.o;
	return [
		`<rect x="${pad - 10}" y="${top}" width="${width - 2 * pad + 20}" height="${h}" rx="8" fill="${band.fill}"/>`,
		`<text x="${width - pad}" y="${top + 17}" text-anchor="end" fill="${band.label}" font-family="-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="${labelSize}" font-weight="700" letter-spacing="0.6">${escape(s.label.toUpperCase())}</text>`,
	].join("");
});

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

const legendItems = legendRows.flatMap((items, r) => {
	let x = pad;
	const y = legendY + r * 24;
	return items.map((item) => {
		const [role, label] = item;
		const out = `<rect x="${x}" y="${y}" width="12" height="12" rx="2" fill="${colors[role].path}"/><text x="${x + 18}" y="${y + 11}" fill="#4b5563">${escape(label)}</text>`;
		x += legendItemWidth(item);
		return out;
	});
});

const svg = `<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace" font-size="${fontSize}">
<rect width="100%" height="100%" fill="#ffffff"/>
${bandShapes.join("\n")}
${lines.join("\n")}
<line x1="${pad}" y1="${legendY - 12}" x2="${width - pad}" y2="${legendY - 12}" stroke="#e5e7eb"/>
${legendItems.join("\n")}
</svg>
`;
writeFileSync(`${dir}/${name}.svg`, svg);
