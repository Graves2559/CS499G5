// Frontend architecture check: the dependency rule (imports only point inward). Run with `npm run check:architecture`.
//
//   domain  <-  application  <-  infrastructure / components  <-  page.tsx (composition)
//
// domain          pure rules: imports only other domain files and types.ts, and no packages at all
// application     hooks and ports: domain + types (+ react); never infrastructure, components or page
// infrastructure  fetch/browser code: implements the application ports; never components, hooks or page
// hooks           UI-only hooks: domain, application, types
// components      rendering: domain, application, hooks, types, and the browser download helper;
//                 never infrastructure/api (the network)
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "app");

const rules = {
  domain: { layers: ["domain", "types"], packages: [] },
  application: { layers: ["domain", "application", "types"], packages: ["react"] },
  infrastructure: { layers: ["domain", "application", "infrastructure", "types"], packages: [] },
  hooks: { layers: ["domain", "application", "hooks", "types"], packages: ["react"] },
  components: { layers: ["domain", "application", "hooks", "components", "types", "infrastructure/download"], packages: ["react", "lucide-react"] },
};

function* sourceFiles(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* sourceFiles(path);
    else if (/\.(ts|tsx)$/.test(name)) yield path;
  }
}

// "domain/files.ts" -> "domain"; "types.ts" -> "types"; "infrastructure/download.ts" -> "infrastructure/download"
function layerOf(path) {
  const parts = relative(root, path).replace(/\.(ts|tsx)$/, "").split("/");
  return parts.length === 1 ? parts[0] : parts[0] === "infrastructure" ? `infrastructure/${parts[1]}` : parts[0];
}

// A rule entry such as "infrastructure/download" allows only that file; a plain layer name allows the whole layer.
const allowed = (rule, target) =>
  rule.layers.some(layer => target === layer || (!layer.includes("/") && target.startsWith(`${layer}/`)));

const problems = [];
let checked = 0;
for (const file of sourceFiles(root)) {
  const from = relative(root, file).split("/")[0];
  const rule = rules[from];
  if (!rule) continue; // page.tsx and main.tsx are the composition code and may import anything
  checked++;
  const text = readFileSync(file, "utf8");
  for (const [, spec] of text.matchAll(/(?:from|import)\s+["']([^"']+)["']/g)) {
    if (spec.startsWith(".")) {
      const target = layerOf(resolve(dirname(file), spec));
      if (!allowed(rule, target)) problems.push(`${relative(root, file)} (${from}) imports ${spec}  -> ${target}`);
    } else if (!rule.packages.includes(spec) && !spec.endsWith(".css")) {
      problems.push(`${relative(root, file)} (${from}) imports package "${spec}"`);
    }
  }
}

if (problems.length) {
  console.error(`Architecture violations:\n  ${problems.join("\n  ")}`);
  process.exit(1);
}
console.log(`Architecture OK (${checked} files checked)`);
