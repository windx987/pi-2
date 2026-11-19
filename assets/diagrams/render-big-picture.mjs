// Renders big-picture.svg: the original Pi's path from a prompt to a tool call, each step next to its code.
// The code is quoted from earendil-works/pi at cead615b4, the workshop baseline; "…" marks lines left out.
import { writeFileSync } from "node:fs";

const packages = {
	"coding-agent": { color: "#2f5a96", fill: "#eef3fa", label: "packages/coding-agent" },
	agent: { color: "#6d4bb3", fill: "#f3effa", label: "packages/agent" },
	ai: { color: "#2f7d5b", fill: "#edf7f2", label: "packages/ai" },
	tools: { color: "#b03a37", fill: "#fbefee", label: "coding-agent/src/core/tools" },
};

// A line starting with "@@ " names the file the following lines come from.
const steps = [
	{
		pkg: "coding-agent",
		title: "Interactive mode",
		text: "The terminal app. Waits for your input and hands it to the session. Renders every event the session emits while the answer streams in.",
		code: [
			"@@ packages/coding-agent/src/modes/interactive/interactive-mode.ts",
			"// Main interactive loop",
			"while (true) {",
			"  const userInput = await this.getUserInput();",
			"  try {",
			"    await this.session.prompt(userInput);",
			"  } catch (error: unknown) {",
		],
	},
	{
		pkg: "coding-agent",
		title: "AgentSession",
		text: "The center of the application. Turns your text into messages and starts the agent. At startup it creates the built-in tools and declares them to the model.",
		code: [
			"@@ packages/coding-agent/src/core/agent-session.ts",
			"async prompt(text: string, options?: PromptOptions): Promise<void> {",
			"  …",
			"  await this.agent.prompt(messages);",
			"…",
			"const baseToolDefinitions = this._baseToolsOverride",
			"  ? …",
			"  : createAllToolDefinitions(this._cwd, {",
			"      read: { autoResizeImages },",
			"      bash: { commandPrefix: shellCommandPrefix, shellPath },",
			"    });",
			"…",
			"this.agent.state.tools = declared;",
		],
	},
	{
		pkg: "agent",
		title: "Agent loop",
		text: "Asks the model for an answer, runs the tool calls in it, adds the results, and asks again. Stops when an answer has no tool calls.",
		code: [
			"@@ packages/agent/src/agent-loop.ts",
			"while (hasMoreToolCalls || pendingMessages.length > 0) {",
			"  …",
			"  const message = await streamAssistantResponse(currentContext, config, signal, emit, streamFunction);",
			"  …",
			'  const toolCalls = message.content.filter((c) => c.type === "toolCall");',
			"  hasMoreToolCalls = false;",
			"  if (toolCalls.length > 0) {",
			"    const executedToolBatch =",
			'      message.stopReason === "length"',
			"        ? await failToolCallsFromTruncatedMessage(toolCalls, emit)",
			"        : await executeToolCalls(currentContext, message, config, signal, emit);",
		],
	},
	{
		pkg: "coding-agent",
		title: "streamFn and ModelRuntime",
		text: "The loop does not know any provider. It calls the streamFn the session gave it, which sends the request through ModelRuntime: model routing and API keys.",
		code: [
			"@@ packages/agent/src/agent-loop.ts",
			"const response = await streamFunction(config.model, llmContext, {",
			"@@ packages/coding-agent/src/core/sdk.ts",
			"streamFn: async (model, context, options) => {",
			"  const requestOptions = buildRequestOptions(options);",
			"  …",
			"  return modelRuntime.streamSimple(model, context, requestOptions);",
			"},",
		],
	},
	{
		pkg: "ai",
		title: "Provider → LLM",
		text: "pi-ai converts the messages and tool schemas to the provider's format, sends the request, and converts the streamed answer back: text, thinking, tool calls.",
		code: [
			"@@ packages/ai/src/api/openai-completions.ts",
			"const params: OpenAI.Chat.Completions.ChatCompletionCreateParamsStreaming = {",
			"…",
			"params.tools = convertTools(transcriptTools.requestTools, compat);",
			"…",
			"const { data: openaiStream, response } = await retryProviderRequest(",
			"  () => client.chat.completions.create(params, requestOptions).withResponse(),",
		],
	},
	{
		pkg: "agent",
		title: "Validate, then ask extensions",
		text: "The model's arguments are checked against the tool's JSON Schema. Then extensions see the call (the tool_call event) and can block it.",
		code: [
			"@@ packages/agent/src/agent-loop.ts",
			"const preparedToolCall = prepareToolCallArguments(tool, toolCall);",
			"const validatedArgs = validateToolArguments(tool, preparedToolCall);",
			"if (config.beforeToolCall) {",
			"  const beforeResult = await config.beforeToolCall(",
			"    {",
			"      assistantMessage,",
			"      toolCall,",
			"      args: validatedArgs,",
		],
	},
	{
		pkg: "tools",
		title: "Built-in tool runs",
		badge: "removed in pi/2: you build it",
		text: "The loop calls the tool's execute(). In the original Pi this is read, write, edit, bash, grep, find or ls. In the workshop, your extension's execute() runs here.",
		code: [
			"@@ packages/agent/src/agent-loop.ts",
			"const result = await prepared.tool.execute(",
			"  prepared.toolCall.id,",
			"  prepared.args as never,",
			"  signal,",
			"@@ packages/coding-agent/src/core/tools/read.ts",
			'name: "read",',
			"…",
			"async execute(",
			"  _toolCallId,",
			"  { path, offset, limit }: { path: string; offset?: number; limit?: number },",
			"  …",
			"const absolutePath = await resolveReadPathAsync(path, ctx?.cwd || cwd);",
		],
	},
	{
		pkg: "agent",
		title: "Result back to the model",
		text: "The result joins the conversation, so the model sees it on the next turn. The session saves every finished message to the session file.",
		code: [
			"@@ packages/agent/src/agent-loop.ts",
			"for (const result of toolResults) {",
			"  currentContext.messages.push(result);",
			"@@ packages/coding-agent/src/core/agent-session.ts",
			"// Regular LLM message - persist as SessionMessageEntry",
			"entryId = this.sessionManager.appendMessage(event.message);",
		],
	},
];

const sans = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";
const mono = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace";
const pad = 32;
const loopX = 44; // the "next turn" arrow runs in this margin
const boxX = 76;
const boxW = 360;
const codeX = boxX + boxW + 36;
const codeSize = 12.5;
const codeChar = 7.53; // advance of a 12.5px monospace glyph
const codeLine = 19;
const fileLine = 24;
const codeW = Math.ceil(
	Math.max(...steps.flatMap((step) => step.code.filter((l) => !l.startsWith("@@ ")).map((l) => l.length))) * codeChar +
		32,
);
const width = codeX + codeW + pad;
const gap = 34;
const textLine = 19;
const wrapChars = 46;

const escape = (text) => text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

const wrap = (text) => {
	const lines = [""];
	for (const word of text.split(" ")) {
		const last = lines.length - 1;
		if (lines[last] && lines[last].length + 1 + word.length > wrapChars) lines.push(word);
		else lines[last] = lines[last] ? `${lines[last]} ${word}` : word;
	}
	return lines;
};

// Light syntax colors in GitHub's palette: comments, strings, keywords.
const keywords =
	/^(const|let|await|async|return|if|for|of|while|true|false|try|catch|new|as|never|unknown|void|string|number)$/;
const highlight = (line) => {
	const comment = line.indexOf("//");
	const code = comment === -1 ? line : line.slice(0, comment);
	const parts = code.split(/("[^"]*")/).flatMap((part) =>
		part.startsWith('"')
			? [`<tspan fill="#0a3069">${escape(part)}</tspan>`]
			: part
					.split(/(\b[A-Za-z_]+\b)/)
					.map((token) => (keywords.test(token) ? `<tspan fill="#cf222e">${token}</tspan>` : escape(token))),
	);
	if (comment !== -1) parts.push(`<tspan fill="#6e7781">${escape(line.slice(comment))}</tspan>`);
	return parts.join("");
};

const codeHeight = (code) => code.reduce((h, line) => h + (line.startsWith("@@ ") ? fileLine : codeLine), 0) + 20;
const boxHeight = (step) => 58 + (step.badge ? 26 : 0) + wrap(step.text).length * textLine + 14;

let y = pad;
const out = [];
const boxes = [];
steps.forEach((step, i) => {
	const p = packages[step.pkg];
	const bh = boxHeight(step);
	const ch = codeHeight(step.code);
	const rowH = Math.max(bh, ch);
	const by = y;
	boxes.push({ y: by, h: bh });

	// The component box: step number, title, package, explanation.
	out.push(
		`<rect x="${boxX}" y="${by}" width="${boxW}" height="${bh}" rx="10" fill="${p.fill}" stroke="${p.color}" stroke-width="1.5"/>`,
	);
	out.push(`<circle cx="${boxX + 26}" cy="${by + 26}" r="13" fill="${p.color}"/>`);
	out.push(
		`<text x="${boxX + 26}" y="${by + 31}" text-anchor="middle" fill="#fff" font-family="${sans}" font-size="14" font-weight="700">${i + 1}</text>`,
	);
	out.push(
		`<text x="${boxX + 50}" y="${by + 31}" fill="#1a2b45" font-family="${sans}" font-size="16" font-weight="700">${escape(step.title)}</text>`,
	);
	out.push(
		`<text x="${boxX + 50}" y="${by + 50}" fill="${p.color}" font-family="${mono}" font-size="11.5">${escape(p.label)}</text>`,
	);
	let ty = by + 58;
	if (step.badge) {
		const bw = step.badge.length * 6.6 + 18;
		out.push(
			`<rect x="${boxX + 16}" y="${ty + 2}" width="${bw}" height="20" rx="10" fill="${p.color}"/><text x="${boxX + 16 + bw / 2}" y="${ty + 16}" text-anchor="middle" fill="#fff" font-family="${sans}" font-size="11.5" font-weight="600">${escape(step.badge)}</text>`,
		);
		ty += 26;
	}
	for (const line of wrap(step.text)) {
		ty += textLine;
		out.push(
			`<text x="${boxX + 16}" y="${ty - 4}" fill="#374151" font-family="${sans}" font-size="13.5">${escape(line)}</text>`,
		);
	}

	// The code card, joined to the box by a dashed line.
	out.push(
		`<line x1="${boxX + boxW}" y1="${by + 26}" x2="${codeX}" y2="${by + 26}" stroke="${p.color}" stroke-dasharray="4 4"/>`,
	);
	out.push(
		`<rect x="${codeX}" y="${by}" width="${codeW}" height="${ch}" rx="8" fill="#f6f8fa" stroke="#d0d7de"/>`,
	);
	let cy = by + 10;
	step.code.forEach((line, j) => {
		if (line.startsWith("@@ ")) {
			if (j > 0) out.push(`<line x1="${codeX}" y1="${cy + 2}" x2="${codeX + codeW}" y2="${cy + 2}" stroke="#d0d7de"/>`);
			cy += fileLine;
			out.push(
				`<text x="${codeX + 16}" y="${cy - 4}" fill="${p.color}" font-family="${mono}" font-size="11.5" font-weight="600">${escape(line.slice(3))}</text>`,
			);
		} else {
			cy += codeLine;
			// Indent by position, not by spaces: some SVG renderers collapse leading spaces.
			const indent = line.length - line.trimStart().length;
			out.push(
				`<text x="${(codeX + 16 + indent * codeChar).toFixed(1)}" y="${cy - 5}" fill="#1f2328">${highlight(line.trimStart())}</text>`,
			);
		}
	});

	y += rowH + gap;
});

// Arrows between the steps, down the middle of the boxes.
const arrowX = boxX + boxW / 2;
for (let i = 0; i + 1 < boxes.length; i++) {
	const from = boxes[i].y + boxes[i].h;
	const to = boxes[i + 1].y;
	out.push(
		`<line x1="${arrowX}" y1="${from}" x2="${arrowX}" y2="${to - 2}" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)"/>`,
	);
}

// The loop: from the last step back to the agent loop.
const last = boxes[boxes.length - 1];
const loopFrom = last.y + last.h / 2;
const loopTo = boxes[2].y + 26;
out.push(
	`<path d="M ${boxX} ${loopFrom} H ${loopX} V ${loopTo} H ${boxX - 2}" fill="none" stroke="#6d4bb3" stroke-width="1.8" marker-end="url(#arrowLoop)"/>`,
);
out.push(
	`<text transform="translate(${loopX - 8} ${(loopFrom + loopTo) / 2}) rotate(-90)" text-anchor="middle" fill="#6d4bb3" font-family="${sans}" font-size="13" font-weight="600">next turn, while the model calls tools</text>`,
);

// Legend.
const legendY = y + 4;
let legendX = boxX;
const legend = Object.values(packages).map((p) => {
	const item = `<rect x="${legendX}" y="${legendY}" width="12" height="12" rx="2" fill="${p.color}"/><text x="${legendX + 18}" y="${legendY + 11}" fill="#4b5563" font-family="${mono}" font-size="12">${escape(p.label)}</text>`;
	legendX += 18 + p.label.length * 7.23 + 28;
	return item;
});
legend.push(
	`<text x="${boxX}" y="${legendY + 36}" fill="#4b5563" font-family="${sans}" font-size="12.5">Code from earendil-works/pi at cead615b4, the workshop baseline. … marks lines left out.</text>`,
);
const height = legendY + 40 + pad;

const svg = `<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" font-family="${mono}" font-size="${codeSize}">
<defs>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280"/></marker>
<marker id="arrowLoop" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6d4bb3"/></marker>
</defs>
<rect width="100%" height="100%" fill="#ffffff"/>
${out.join("\n")}
${legend.join("\n")}
</svg>
`;
writeFileSync(`${import.meta.dirname}/big-picture.svg`, svg);
