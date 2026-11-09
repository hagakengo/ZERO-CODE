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


test("missing approval scope is shown as unverified, never as a denial", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /selected\.approvalScope\?\.trim\(\) \|\| "未確認（承認根拠未取得）"/);
  assert.doesNotMatch(details, /未確認（承認なし）/);
});

test("approval evidence is independent for script, integration, MASTER and video QC", () => {
  const types = fs.readFileSync(path.join(canvasDir, "types.ts"), "utf8");
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  for (const key of ["scriptContent", "integratedFile", "masterAdoption", "videoQc"]) {
    assert.match(types, new RegExp(`\\b${key}\\?: ApprovalEvidence`));
    assert.match(details, new RegExp(`"${key}"`));
  }
  assert.match(details, /UNVERIFIED（根拠未取得）/);
  assert.match(details, /selected\.approvalEvidence\?\.\[key\]/);
});

test("project scope distinguishes current anime from legacy project", () => {
  const types = fs.readFileSync(path.join(canvasDir, "types.ts"), "utf8");
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  for (const scope of ["CURRENT_ANIME", "LEGACY_YEN_ZERO", "OS", "UNVERIFIED"]) {
    assert.ok(types.includes(`"${scope}"`), scope);
  }
  assert.match(details, /selected\.projectScope \?\? "UNVERIFIED"/);
});

test("APPROVED display requires both evidence ID and approval scope", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /evidence\.status === "APPROVED"/);
  assert.match(details, /!evidence\.evidenceId\?\.trim\(\)/);
  assert.match(details, /!evidence\.approvalScope\?\.trim\(\)/);
  assert.match(details, /UNVERIFIED（APPROVED根拠不足）/);
});

test("CUT boundary states are optional and unknown states remain UNVERIFIED", () => {
  const types = fs.readFileSync(path.join(canvasDir, "types.ts"), "utf8");
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(types, /startState\?: CutBoundaryState/);
  assert.match(types, /endState\?: CutBoundaryState/);
  assert.match(details, /boundaryText\(cut\.startState\)/);
  assert.match(details, /boundaryText\(cut\.endState\)/);
  assert.match(details, /UNVERIFIED（状態未記録）/);
});

test("CUT boundary comparator never treats missing information as a match", () => {
  const comparator = fs.readFileSync(path.join(canvasDir, "continuity.ts"), "utf8");
  assert.match(comparator, /status: "UNVERIFIED"/);
  assert.match(comparator, /status: "MISMATCH"/);
  assert.match(comparator, /status: "MATCH"/);
  assert.match(comparator, /if \(!previousEnd \|\| !nextStart\)/);
  assert.match(comparator, /if \(!before \|\| !after\)/);
  assert.match(comparator, /if \(mismatches\.length\)/);
  assert.match(comparator, /if \(missing\.length\)/);
});

test("CUT comparison UI labels synthetic order and does not assert canonical continuity", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /compareCutBoundaries\(previousCut\.cutDetails\?\.endState, cut\.startState\)/);
  assert.match(details, /明示された前CUT参照のみ/);
  assert.match(details, /前CUT参照・順序根拠・資料適用範囲のいずれかが未確認/);
});

test("CUT comparator runtime: match, mismatch, missing and partial states", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "continuity.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const compare = exports.compareCutBoundaries;
  const complete = { characterPosition: "左", pose: "立つ", facing: "右", props: "なし", camera: "固定", evidenceId: "TEST-EVIDENCE-001" };
  assert.equal(compare(complete, { ...complete }).status, "MATCH");
  assert.equal(compare({ ...complete, evidenceId: undefined }, { ...complete }).status, "UNVERIFIED");
  assert.equal(compare({ ...complete }, { ...complete, evidenceId: " " }).status, "UNVERIFIED");
  assert.equal(compare(complete, { ...complete, facing: "左" }).status, "MISMATCH");
  const mismatchWithoutEvidence = compare({ ...complete, evidenceId: undefined }, { ...complete, facing: "左" });
  assert.equal(mismatchWithoutEvidence.status, "MISMATCH");
  assert.ok(mismatchWithoutEvidence.reasons.some((reason) => reason.includes("根拠IDが未記録")));
  assert.ok(mismatchWithoutEvidence.reasons.some((reason) => reason.includes("向き")));
  assert.equal(compare({ ...complete, pose: " 立つ " }, complete).status, "MATCH");
  assert.equal(compare(undefined, complete).status, "UNVERIFIED");
  assert.equal(compare({ pose: "立つ" }, { pose: "立つ" }).status, "UNVERIFIED");
  assert.equal(compare({ pose: "立つ" }, { pose: "座る" }).status, "MISMATCH");
});

test("CUT MATCH display never claims video QC approval", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /5項目の文字列一致（根拠IDの実在性・映像QCは未検証）/);
});

test("CUT comparison is blocked unless project scopes are known and identical", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /previousCut\?\.projectScope && selected\.projectScope/);
  assert.match(details, /previousCut\.projectScope === selected\.projectScope/);
  assert.match(details, /previousCut\.projectScope !== "UNVERIFIED"/);
  assert.match(details, /sameVerifiedScope && previousCut && cut/);
});

test("CUT sequence is never inferred from sample array order", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  const types = fs.readFileSync(path.join(canvasDir, "types.ts"), "utf8");
  assert.match(types, /previousCutId\?: string/);
  assert.match(types, /sequenceEvidenceId\?: string/);
  assert.match(details, /cut\?\.previousCutId/);
  assert.match(details, /cut\?\.sequenceEvidenceId\?\.trim\(\)/);
  assert.match(details, /previousCut\.id !== selected\.id/);
  assert.match(details, /previousCut\.cutDetails\?\.sceneId === cut\.sceneId/);
  assert.match(details, /previousCut\.cutDetails\?\.scriptId === cut\.scriptId/);
  assert.match(details, /sequenceVerified && sameVerifiedScope/);
  assert.doesNotMatch(details, /sameSceneCuts|cutIndex/);
});

test("CUT detail exposes predecessor and sequence evidence without claiming source verification", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /前CUT参照ID/);
  assert.match(details, /CUT順序の根拠ID/);
  assert.match(details, /cut\.previousCutId\?\.trim\(\)/);
  assert.match(details, /cut\.sequenceEvidenceId\?\.trim\(\)/);
  assert.match(details, /参照先未検証/);
});
