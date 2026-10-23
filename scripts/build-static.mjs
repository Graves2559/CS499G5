import fs from "node:fs/promises";
import ts from "typescript";
import { build } from "rolldown";

await fs.mkdir("dist", { recursive: true });

await build({
  input: "app/main.tsx",
  platform: "browser",
  plugins: [{
    name: "typescript",
    transform(code, id) {
      if (!/\.tsx?$/.test(id) || id.includes("node_modules")) return null;
      return {
        code: ts.transpileModule(code, {
          fileName: id,
          compilerOptions: {
            jsx: ts.JsxEmit.ReactJSX,
            module: ts.ModuleKind.ESNext,
            target: ts.ScriptTarget.ES2022,
          },
        }).outputText,
        map: null,
      };
    },
  }],
  output: { file: "dist/app.js", format: "esm", minify: true },
});

await fs.writeFile("dist/style.css", await fs.readFile("app/globals.css", "utf8"));
await fs.copyFile("public/favicon.svg", "dist/favicon.svg");
await fs.writeFile(
  "dist/index.html",
  '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="An image and text summary workspace."><title>ClosedAI</title><link rel="icon" href="/favicon.svg"><link rel="stylesheet" href="/style.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>',
);

console.log("Website built successfully.");
