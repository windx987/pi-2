# Diagrams

The root README and the education pages show these diagrams as pre-rendered SVG, because GitHub's live Mermaid rendering lays them out poorly. Edit the `.mmd` source, then render it again:

```bash
npx -y @mermaid-js/mermaid-cli@11.4.0 -c mermaid.config.json -b white -i architecture.mmd -o architecture.svg
```

Run it from this directory, once per changed diagram. `mermaid.config.json` turns off HTML labels so the SVG uses plain text, which GitHub keeps when it displays an SVG as an image. The white background keeps the diagrams readable in GitHub's dark theme.

`big-picture.svg` puts code next to each step, which Mermaid cannot draw. Edit the steps in `render-big-picture.mjs` and run `node render-big-picture.mjs`. Its code is quoted from the baseline `cead615b4`; keep quotes exact.

`project-structure.svg` is a file tree, which Mermaid lays out poorly. Edit `project-structure.txt` and run `node render-tree.mjs` instead.
