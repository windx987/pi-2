# TypeScript for the workshop

Pi is written in TypeScript, and so are the exercises. This page covers the TypeScript you need to read Pi's code and write the four tools. The four PDFs in this directory are the official cheat sheets from [typescriptlang.org/cheatsheets](https://www.typescriptlang.org/cheatsheets); this page says which parts of them matter here.

## What TypeScript is

TypeScript is JavaScript with types. The types are checked before the code runs and removed when it runs:

```typescript
function lineCount(text: string): number {
	return text.split("\n").length;
}

lineCount(42); // TypeScript: Argument of type 'number' is not assignable to parameter of type 'string'.
```

Remove `: string` and `: number` and what is left is the JavaScript that runs. Two consequences follow:

1. **Nothing checks types while Pi runs.** Pi loads your extension with `jiti`, which strips the types and runs the JavaScript. A type error does not stop it from loading. Run the checker yourself (next section).
2. **Types cannot check data from outside.** The model's tool arguments arrive as JSON at run time, after the types are gone. That is why a tool declares a JSON Schema: Pi validates the arguments against it before it calls your `execute()`.

## Check your code

```bash
npx tsc --noEmit -p education/tsconfig.json   # type-checks the exercises only
npm run check                                 # the whole repository, including the exercises
```

`--noEmit` means "check only, write no JavaScript". An editor with TypeScript support (VS Code, for example) shows the same errors as you type, and the type of any name when you hover over it.

## Read the starter through its types

Every exercise starter has the same shape. Here is exercise 01, shortened, with what each line means:

```typescript
import { Type } from "typebox";                                          // a value: used at run time
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent"; // `type`: removed at run time

const readTool = defineTool({
	name: "read",
	parameters: Type.Object({                                             // a JSON Schema, built at run time
		path: Type.String(),
		offset: Type.Optional(Type.Number()),
	}),

	async execute(_toolCallId, params, _signal, _onUpdate, ctx) {        // `async`: returns a Promise
		params.path;    // string
		params.offset;  // number | undefined
		ctx.cwd;        // string
		return { content: [{ type: "text", text: "..." }], details: undefined };
	},
});

export default function (pi: ExtensionAPI) {                            // a type annotation on a parameter
	pi.registerTool(readTool);
}
```

- **One schema, two uses.** `Type.Object(...)` builds a JSON Schema object that Pi validates the model's arguments against at run time. `defineTool` also turns that schema into a TypeScript type with TypeBox's `Static`, so `params` is typed as `{ path: string; offset?: number }` without you writing that type. Add a field to the schema and `params` gains it.
- **Inferred types.** `execute`'s parameters have no annotations: TypeScript knows them from `defineTool`'s definition. Hover over `ctx` to see everything it offers.
- **`type` imports.** `type ExtensionAPI` is only a type, so the import disappears from the JavaScript. This repository requires the `type` keyword for such imports.
- **Unused parameters.** A leading underscore (`_toolCallId`) marks a parameter the function does not use.
- **`async` and `await`.** `execute` is `async`, so it returns a `Promise` of its result. Inside it, `await readFile(path, "utf8")` waits for the file without blocking Pi.

## Handle optional values

`offset?: number` means the property may be missing, so its type is `number | undefined`. TypeScript does not let you use it as a number until you rule out `undefined`. Ruling out a type in a union this way is called narrowing:

```typescript
const start = params.offset ?? 1;               // ?? : use 1 when offset is undefined (or null)

if (params.limit !== undefined) {
	lines = lines.slice(0, params.limit);       // here limit is number
}
```

The same narrowing works on errors. In a `catch` block the error's type is `unknown`, because JavaScript can throw any value:

```typescript
try {
	text = await readFile(path, "utf8");
} catch (error) {
	const message = error instanceof Error ? error.message : String(error);
	throw new Error(`Could not read ${params.path}: ${message}`);
}
```

## Rules in this repository

The repository's `tsconfig.base.json` turns on three settings that affect what you write:

| Setting | What it means for you |
|---|---|
| `strict` | Full checking: `undefined` must be handled, parameters need a known type |
| `erasableSyntaxOnly` | Only TypeScript that can be removed without changing the JavaScript: no `enum`, `namespace`, or parameter properties (`constructor(public x: number)`) |
| `verbatimModuleSyntax` | Imports that bring in only types must say `type` |

Avoid `any`: it turns checking off for that value. When you do not know a type, use `unknown` and narrow it.

## The cheat sheets

| Cheat sheet | Read it for | Where the workshop needs it |
|---|---|---|
| [Types](TypeScript%20Types.pdf) | Object types, union types (`"a" \| "b"`), optional fields, `typeof` and `ReturnType` | Reading `ToolDefinition` and the tool result types in Pi |
| [Control Flow Analysis](TypeScript%20Control%20Flow%20Analysis.pdf) | Narrowing with `if`, `typeof`, `instanceof`, `in`, discriminated unions | Optional parameters, caught errors; Pi's message and event types are discriminated unions on `type` or `role` |
| [Interfaces](TypeScript%20Interfaces.pdf) | Describing object shapes, built-in types, generics such as `Array<string>` and `Promise<T>` | Reading `ExtensionAPI` and `ExtensionContext` in `packages/coding-agent/src/core/extensions/types.ts` |
| [Classes](TypeScript%20Classes.pdf) | Fields, `private`, `#private`, `implements` | Reading `AgentSession` and `Agent`. The exercises need no classes. Its "Parameter Properties" are not allowed here (see above) |

Start with Types and Control Flow Analysis; they cover everything the exercises use.

## Try it

1. Open `education/exercises/01-read/starter.ts` and add `params.path.toFixed();` inside `execute`.
2. Run `npx tsc --noEmit -p education/tsconfig.json`. TypeScript reports that `toFixed` does not exist on type `string`.
3. Change it to `params.offset.toFixed();`. Now it reports that `params.offset` is possibly `undefined`.
4. Change it to `(params.offset ?? 1).toFixed();`. The error goes away. Remove the line.
