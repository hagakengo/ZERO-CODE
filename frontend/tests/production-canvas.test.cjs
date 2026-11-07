const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const canvasDir = path.join(__dirname, "..", "app", "production", "canvas");
const dataSource = fs.readFileSync(path.join(canvasDir, "test-data.ts"), "utf8");
const sourceFiles = fs.readdirSync(canvasDir).filter((name) => /\.(ts|tsx)$/.test(name));
const allSource = sourceFiles.map((name) => fs.readFileSync(path.join(canvasDir, name), "utf8")).join("\n");

const nodeSection = dataSource.match(/sampleNodes[\s\S]*?\] as const;/)?.[0] ?? "";
const edgeSection = dataSource.match(/sampleEdges[\s\S]*?\] as const;/)?.[0] ?? "";
const nodeIds = [...nodeSection.matchAll(/id: "([^"]+)"/g)].map((match) => match[1]);
const edgeIds = [...edgeSection.matchAll(/id: "([^"]+)"/g)].map((match) => match[1]);
const edgeSources = [...edgeSection.matchAll(/source: "([^"]+)"/g)].map((match) => match[1]);
const edgeTargets = [...edgeSection.matchAll(/target: "([^"]+)"/g)].map((match) => match[1]);

test("test node and edge identifiers are unique", () => {
  assert.equal(new Set(nodeIds).size, nodeIds.length);
  assert.equal(new Set(edgeIds).size, edgeIds.length);
});

test("every edge endpoint references a test node", () => {
  const known = new Set(nodeIds);
  for (const endpoint of [...edgeSources, ...edgeTargets]) assert.ok(known.has(endpoint), endpoint);
});

test("all required node kinds and safety states are represented", () => {
  for (const kind of ["SCRIPT", "SCENE", "CUT", "CHARACTER", "ASSET"]) assert.match(nodeSection, new RegExp(`kind: "${kind}"`));
  for (const status of ["DRAFT", "HOLD", "NOT_FOUND", "UNVERIFIED"]) assert.match(nodeSection, new RegExp(`status: "${status}"`));
});

test("canvas stays isolated from APIs, databases and external writes", () => {
  assert.doesNotMatch(allSource, /\bfetch\s*\(/);
  assert.doesNotMatch(allSource, /XMLHttpRequest|axios|DATABASE_URL|NEXT_PUBLIC_API_URL/);
  assert.match(allSource, /READ ONLY · TEST DATA/);
});
