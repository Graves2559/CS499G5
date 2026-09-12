import fs from 'node:fs/promises';
import ts from 'typescript';
import { build } from 'rolldown';
await fs.mkdir('work',{recursive:true});
await fs.mkdir('dist',{recursive:true});
const source=await fs.readFile('app/page.tsx','utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
await fs.writeFile('work/App.js',compiled);
await fs.writeFile('work/entry.js',`import {createRoot} from 'react-dom/client'; import {jsx} from 'react/jsx-runtime'; import App from './App.js'; createRoot(document.getElementById('root')).render(jsx(App,{}));`);
await build({input:'work/entry.js',platform:'browser',output:{file:'dist/app.js',format:'esm',minify:true}});
await fs.writeFile('dist/style.css',(await fs.readFile('app/globals.css','utf8')).replace('@import "tailwindcss";',''));
await fs.copyFile('public/favicon.svg','dist/favicon.svg');
await fs.writeFile('dist/index.html','<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="An image and text summary workspace."><title>ClosedAI</title><link rel="icon" href="/favicon.svg"><link rel="stylesheet" href="/style.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>');
console.log('React prototype built successfully.');

