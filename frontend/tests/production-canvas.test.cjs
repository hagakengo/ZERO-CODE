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
  assert.match(details, /previousCut\.cutDetails\?\.previousCutId !== selected\.id/);
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

test("CUT predecessor cycle detector handles self, reciprocal, long cycles and broken links", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "cut-sequence.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const detect = exports.hasPredecessorCycle;
  const cut = (id, previousCutId) => ({
    id, kind: "CUT", cutDetails: { previousCutId },
  });
  assert.equal(detect("a", [cut("a", "a")]), true);
  assert.equal(detect("a", [cut("a", "b"), cut("b", "a")]), true);
  assert.equal(detect("a", [cut("a", "b"), cut("b", "c"), cut("c", "a")]), true);
  assert.equal(detect("a", [cut("a", "b"), cut("b", "c"), cut("c", "d"), cut("d", "b")]), true);
  assert.equal(detect("a", [cut("a", "b"), cut("b", "c"), cut("c", undefined)]), false);
  assert.equal(detect("a", [cut("a", "missing")]), false);
  assert.equal(detect("a", [cut("a", "b"), { id: "b", kind: "SCENE" }]), false);
});

test("CUT detail blocks cyclic predecessors and does not equate no-cycle with approval", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /hasPredecessorCycle\(selected\.id, nodes\)/);
  assert.match(details, /!ambiguousNodeIds && !noncanonicalPredecessor && !cycleDetected && !brokenPredecessor && !inconsistentPredecessor && cut\?\.sequenceEvidenceId/);
  assert.match(details, /循環未検出（順序の正当性は未検証）/);
  assert.match(details, /INVALID（前CUT参照に循環あり・比較停止）/);
});

test("CUT predecessor chain reports missing CUT references at any depth", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "cut-sequence.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const broken = exports.hasBrokenPredecessorReference;
  const cut = (id, previousCutId) => ({ id, kind: "CUT", cutDetails: { previousCutId } });
  assert.equal(broken("a", [cut("a", "missing")]), true);
  assert.equal(broken("a", [cut("a", "b"), cut("b", "missing")]), true);
  assert.equal(broken("a", [cut("a", "b"), { id: "b", kind: "SCENE" }]), true);
  assert.equal(broken("a", [cut("a", "b"), cut("b", undefined)]), false);
  assert.equal(broken("a", [cut("a", "b"), cut("b", "a")]), false);
  assert.equal(broken("missing", []), true);
});

test("CUT detail blocks missing predecessor links and labels uncertainty", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /hasBrokenPredecessorReference\(selected\.id, nodes\)/);
  assert.match(details, /!ambiguousNodeIds && !noncanonicalPredecessor && !cycleDetected && !brokenPredecessor && !inconsistentPredecessor/);
  assert.match(details, /参照先CUTが見つからない・比較停止/);
  assert.match(details, /欠落参照未検出（根拠の実在性は未検証）/);
});

test("approval evidence display never implies that an APPROVED ID was independently verified", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /APPROVED（参照先・承認権限未検証）/);
  assert.match(details, /UNVERIFIED（APPROVED根拠不足）/);
});

test("CUT predecessor chain rejects cross-project, scene and script context at any depth", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "cut-sequence.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const inconsistent = exports.hasInconsistentPredecessorContext;
  const cut = (id, previousCutId, scope = "CURRENT_ANIME", scene = "s1", script = "p1") => ({
    id, kind: "CUT", projectScope: scope, cutDetails: { previousCutId, sceneId: scene, scriptId: script },
  });
  assert.equal(inconsistent("a", [cut("a", "b"), cut("b", "c"), cut("c", undefined)]), false);
  assert.equal(inconsistent("a", [cut("a", "b"), cut("b", "c"), cut("c", undefined, "LEGACY_YEN_ZERO")]), true);
  assert.equal(inconsistent("a", [cut("a", "b"), cut("b", "c"), cut("c", undefined, "CURRENT_ANIME", "s2")]), true);
  assert.equal(inconsistent("a", [cut("a", "b"), cut("b", "c"), cut("c", undefined, "CURRENT_ANIME", "s1", "p2")]), true);
  assert.equal(inconsistent("a", [cut("a", undefined, "UNVERIFIED")]), true);
  assert.equal(inconsistent("missing", []), true);
});

test("CUT detail blocks cross-context predecessor chains", () => {
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /hasInconsistentPredecessorContext\(selected\.id, nodes\)/);
  assert.match(details, /!inconsistentPredecessor && cut\?\.sequenceEvidenceId/);
  assert.match(details, /参照チェーンの作品scope・SCENE・SCRIPT不一致・比較停止/);
});

test("duplicate CUT IDs and blank IDs block continuity resolution", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "cut-sequence.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const ambiguous = exports.hasAmbiguousNodeIds;
  const cut = (id) => ({ id, kind: "CUT" });
  assert.equal(ambiguous([cut("a"), cut("b")]), false);
  assert.equal(ambiguous([cut("a"), cut("a")]), true);
  assert.equal(ambiguous([cut("a"), cut(" ")]), true);
  assert.equal(ambiguous([cut("a"), cut(" a ")]), true);
  assert.equal(ambiguous([cut(" a ")]), true);
  assert.equal(ambiguous([cut("a "), cut("b")]), true);
  assert.equal(ambiguous([cut("a"), { id: "a", kind: "SCENE" }]), true);
  assert.equal(ambiguous([{ id: "a", kind: "SCENE" }, { id: "a", kind: "ASSET" }]), true);
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /hasAmbiguousNodeIds\(nodes\)/);
  assert.match(details, /!ambiguousNodeIds && !noncanonicalPredecessor && !cycleDetected/);
  assert.match(details, /ノードID重複または空欄・比較停止/);
});


test("node drag bounds keep cards within logical canvas for extreme pointer deltas", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "node-bounds.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const clamp = exports.clampNodePosition;
  const at = (x, y) => clamp({ x, y }, 1200, 800, 200, 120);
  for (const zoom of [0.5, 1, 2]) {
    const leftTop = at(100 + (-9999 / zoom), 100 + (-9999 / zoom));
    assert.equal(leftTop.x, 0);
    assert.equal(leftTop.y, 0);
    const rightBottom = at(100 + (9999 / zoom), 100 + (9999 / zoom));
    assert.equal(rightBottom.x, 1000);
    assert.equal(rightBottom.y, 680);
  }
  const interior = at(500, 300);
  assert.equal(interior.x, 500);
  assert.equal(interior.y, 300);
  // Assert against the actual dimensions used by the Canvas, not only synthetic fixtures.
  const actual = dataSource.match(/CANVAS_WIDTH = (\d+);[\s\S]*?CANVAS_HEIGHT = (\d+);[\s\S]*?NODE_WIDTH = (\d+);[\s\S]*?NODE_HEIGHT = (\d+);/);
  assert.ok(actual, "Canvas logical dimensions must be explicitly declared");
  const [canvasW, canvasH, nodeW, nodeH] = actual.slice(1).map(Number);
  const actualBottomRight = clamp({ x: 99999, y: 99999 }, canvasW, canvasH, nodeW, nodeH);
  assert.equal(actualBottomRight.x, canvasW - nodeW);
  assert.equal(actualBottomRight.y, canvasH - nodeH);
  const actualTopLeft = clamp({ x: -99999, y: -99999 }, canvasW, canvasH, nodeW, nodeH);
  assert.equal(actualTopLeft.x, 0);
  assert.equal(actualTopLeft.y, 0);
  const tinyCanvas = clamp({ x: 10, y: 10 }, 100, 100, 200, 120);
  assert.equal(tinyCanvas.x, 0);
  assert.equal(tinyCanvas.y, 0);
  const canvas = fs.readFileSync(path.join(canvasDir, "ProductionCanvas.tsx"), "utf8");
  assert.match(canvas, /clampNodePosition\(/);
  assert.match(canvas, /CANVAS_WIDTH, CANVAS_HEIGHT, NODE_WIDTH, NODE_HEIGHT/);
  assert.match(canvas, /setPositions\(\{ \.\.\.initialPositions \}\)/);
});

test("predecessor references reject whitespace and blank IDs without inferring chronology", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "cut-sequence.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const invalid = exports.hasNoncanonicalPredecessorReference;
  const cut = (id, predecessor) => ({
    id, kind: "CUT", projectScope: "CURRENT_ANIME",
    cutDetails: { sceneId: "s", scriptId: "p", previousCutId: predecessor },
  });
  const check = (ref) => invalid("b", [cut("a", undefined), cut("b", ref)]);
  assert.equal(check("a"), false);
  assert.equal(check(" a"), true);
  assert.equal(check("a "), true);
  assert.equal(check(" a "), true);
  assert.equal(check(" "), true);
  assert.equal(check(""), true);
  assert.equal(check("missing"), false); // Broken reference has a separate diagnostic.
  assert.equal(check("b"), false); // Cycle has a separate diagnostic.
  assert.equal(invalid("b", [cut("a", " b "), cut("b", "a")]), true);
  const details = fs.readFileSync(path.join(canvasDir, "NodeDetails.tsx"), "utf8");
  assert.match(details, /hasNoncanonicalPredecessorReference\(selected.id, nodes\)/);
  assert.match(details, /!ambiguousNodeIds && !noncanonicalPredecessor && !cycleDetected/);
  assert.match(details, /前CUT参照IDに空白・空欄あり・比較停止/);
});

test("keyboard canvas controls preserve native arrows and clamp moved nodes", () => {
  const canvas = fs.readFileSync(path.join(canvasDir, "ProductionCanvas.tsx"), "utf8");
  const card = fs.readFileSync(path.join(canvasDir, "CanvasNodeCard.tsx"), "utf8");
  assert.match(canvas, /keyboardMoveDelta\(event\.key, event\.altKey, event\.ctrlKey, event\.metaKey, event\.shiftKey\)/);
  assert.match(canvas, /event\.target !== event\.currentTarget/);
  assert.match(canvas, /onKeyDown=\{panByKeyboard\}/);
  assert.match(canvas, /onKeyboardMove=\{moveNodeByKeyboard\}/);
  assert.match(canvas, /\[node\.id\]: clampNodePosition\(/);
  assert.match(canvas, /tabIndex=\{0\}/);
  assert.match(canvas, /位置変更は保存されません/);
  assert.match(card, /onKeyDown=\{\(event\) => onKeyboardMove\(event, node\)\}/);
  assert.match(card, /aria-keyshortcuts="Alt\+ArrowUp/);
});

test("keyboard move delta runtime: modifiers, arrows and native keys", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "keyboard-controls.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const move = exports.keyboardMoveDelta;
  const plain = (key) => move(key, false, false, false, false);
  assert.equal(plain("ArrowLeft"), null);
  assert.equal(move("ArrowLeft", true, true, false, false), null);
  assert.equal(move("ArrowLeft", true, false, true, false), null);
  assert.equal(move("ArrowLeft", true, false, false, true), null);
  assert.equal(move("Enter", true, false, false, false), null);
  for (const [key, x, y] of [["ArrowLeft", -16, 0], ["ArrowRight", 16, 0], ["ArrowUp", 0, -16], ["ArrowDown", 0, 16]]) {
    const result = move(key, true, false, false, false);
    assert.equal(result.x, x);
    assert.equal(result.y, y);
  }
});

test("direction buttons offer a shortcut-independent accessible fallback", () => {
  const canvas = fs.readFileSync(path.join(canvasDir, "ProductionCanvas.tsx"), "utf8");
  assert.match(canvas, /function moveSelectedNode\(/);
  assert.match(canvas, /function panWithButton\(/);
  assert.match(canvas, /\[selected\.id\]: clampNodePosition\(/);
  assert.match(canvas, /role="group" aria-label="選択中のノードを移動"/);
  assert.match(canvas, /role="group" aria-label="キャンバス表示位置を移動"/);
  for (const direction of ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"]) {
    assert.match(canvas, new RegExp('onClick=\\{\\(\\) => moveSelectedNode\\("' + direction + '"\\)\\}'));
    assert.match(canvas, new RegExp('onClick=\\{\\(\\) => panWithButton\\("' + direction + '"\\)\\}'));
  }
});

test("read-only Canvas route has no direct link into live Dashboard", () => {
  const page = fs.readFileSync(path.join(canvasDir, "page.tsx"), "utf8");
  assert.doesNotMatch(page, /href=["']\/["']/);
  assert.doesNotMatch(page, /<a\b/);
  assert.match(page, /Dashboardへの移動リンクなし/);
  assert.match(page, /READ ONLY · TEST DATA/);
  assert.match(page, /位置変更は保存されず/);
});

test("RESET cancels an in-flight pointer drag before restoring the view", () => {
  const canvas = fs.readFileSync(path.join(canvasDir, "ProductionCanvas.tsx"), "utf8");
  const reset = canvas.match(/function resetView\(\) \{([\s\S]*?)\n  \}/)?.[1] ?? "";
  assert.ok(reset, "resetView must exist");
  const cancelIndex = reset.indexOf("interaction.current = null");
  const restoreIndex = reset.indexOf("setPositions({ ...initialPositions })");
  assert.ok(cancelIndex >= 0 && restoreIndex > cancelIndex, "cancel pointer capture state before restoring positions");
  assert.match(reset, /setPan\(\{ x: 18, y: 18 \}\)/);
  assert.match(reset, /setZoom\(1\)/);
});

test("RESET restores the scroll origin of the focusable canvas viewport", () => {
  const canvas = fs.readFileSync(path.join(canvasDir, "ProductionCanvas.tsx"), "utf8");
  const reset = canvas.match(/function resetView\(\) \{([\s\S]*?)\n  \}/)?.[1] ?? "";
  assert.match(canvas, /ref=\{viewportRef\}\s+data-canvas-background/);
  assert.match(reset, /viewportRef\.current\?\.scrollTo\(\{ left: 0, top: 0, behavior: "instant" \}\)/);
});

test("pointer start guards reject secondary pointers, right clicks and concurrent drags", () => {
  const canvas = fs.readFileSync(path.join(canvasDir, "ProductionCanvas.tsx"), "utf8");
  const nodeStart = canvas.match(/function beginNodeDrag\([\s\S]*?\n  \}/)?.[0] ?? "";
  const panStart = canvas.match(/function beginPan\([\s\S]*?\n  \}/)?.[0] ?? "";
  assert.match(nodeStart, /!canBeginPointerInteraction\(event\.isPrimary, event\.button, Boolean\(interaction\.current\)\)/);
  assert.match(panStart, /!canBeginPointerInteraction\(event\.isPrimary, event\.button, Boolean\(interaction\.current\)\)/);
  assert.match(nodeStart, /setPointerCapture\(event\.pointerId\)/);
  assert.match(panStart, /setPointerCapture\(event\.pointerId\)/);
  assert.match(canvas, /!isActivePointer\(active\.pointerId, event\.pointerId\)/);
});

test("unexpected loss of pointer capture clears the matching active interaction", () => {
  const canvas = fs.readFileSync(path.join(canvasDir, "ProductionCanvas.tsx"), "utf8");
  assert.match(canvas, /onLostPointerCapture=\{endInteraction\}/);
  assert.match(canvas, /onPointerCancel=\{endInteraction\}/);
  const end = canvas.match(/function endInteraction\([\s\S]*?\n  \}/)?.[0] ?? "";
  assert.match(end, /isActivePointer\(interaction\.current\?\.pointerId \?\? null, event\.pointerId\)/);
  assert.match(end, /interaction\.current = null/);
});

test("Canvas verification route cannot silently gain persistence or external navigation", () => {
  const source = fs.readdirSync(canvasDir)
    .filter((name) => /\.(ts|tsx)$/.test(name))
    .map((name) => fs.readFileSync(path.join(canvasDir, name), "utf8"))
    .join("\n");
  for (const pattern of [
    /\b(?:localStorage|sessionStorage|indexedDB)\b/,
    /\b(?:WebSocket|EventSource|sendBeacon)\b/,
    /\b(?:useRouter|redirect|router\.push|router\.replace|window\.location)\b/,
    /\b(?:serverAction|use server)\b/,
  ]) {
    assert.doesNotMatch(source, pattern, "read-only test Canvas must not persist or navigate");
  }
  assert.match(dataSource, /TEST-SCRIPT-001/);
  assert.match(dataSource, /TEST-CUT-001/);
  assert.doesNotMatch(dataSource, /(?:https?:\/\/|\/api\/)/);
});


test("node bounds runtime clamps extreme positions and undersized canvas safely", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "node-bounds.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const clamp = exports.clampNodePosition;
  for (const [input, expected] of [
    [{ x: -999, y: -100 }, { x: 0, y: 0 }],
    [{ x: 9999, y: 9999 }, { x: 544, y: 528 }],
    [{ x: 160, y: 200 }, { x: 160, y: 200 }],
  ]) {
    const actual = clamp(input, 720, 620, 176, 92);
    assert.deepEqual({ x: actual.x, y: actual.y }, expected);
  }
  const tiny = clamp({ x: 100, y: 100 }, 100, 80, 176, 92);
  assert.deepEqual({ x: tiny.x, y: tiny.y }, { x: 0, y: 0 });
});


test("pointer ownership runtime: reject secondary, right-button and competing interactions", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "pointer-guards.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const canBegin = exports.canBeginPointerInteraction;
  const owns = exports.isActivePointer;
  assert.equal(canBegin(true, 0, false), true);
  for (const [primary, button, active] of [
    [false, 0, false], [true, 2, false], [true, 1, false],
    [true, 0, true], [false, 2, true],
  ]) assert.equal(canBegin(primary, button, active), false);
  assert.equal(owns(5, 5), true);
  assert.equal(owns(5, 6), false);
  assert.equal(owns(null, 5), false);
  assert.equal(owns(0, 0), true);
});


test("zoom runtime: bounded finite values, rounding and invalid input fallback", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "zoom-controls.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const clamp = exports.clampZoom;
  assert.equal(exports.MIN_ZOOM, 0.5);
  assert.equal(exports.MAX_ZOOM, 2);
  assert.equal(exports.ZOOM_STEP, 0.2);
  assert.equal(clamp(-100), 0.5);
  assert.equal(clamp(100), 2);
  assert.equal(clamp(1.234), 1.23);
  assert.equal(clamp(1), 1);
  for (const value of [NaN, Infinity, -Infinity]) assert.equal(clamp(value), 1);
  const canvas = fs.readFileSync(path.join(canvasDir, "ProductionCanvas.tsx"), "utf8");
  assert.match(canvas, /import \{ clampZoom, ZOOM_STEP \} from "\.\/zoom-controls"/);
  assert.match(canvas, /clampZoom\(value - ZOOM_STEP\)/);
  assert.match(canvas, /clampZoom\(value \+ ZOOM_STEP\)/);
});


test("node bounds runtime: malformed coordinates and dimensions remain finite", () => {
  const ts = require("typescript");
  const vm = require("node:vm");
  const source = fs.readFileSync(path.join(canvasDir, "node-bounds.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(compiled, { exports }, { timeout: 1000 });
  const clamp = exports.clampNodePosition;
  for (const position of [
    { x: NaN, y: Infinity }, { x: -Infinity, y: NaN },
    { x: Infinity, y: -Infinity },
  ]) {
    const result = clamp(position, 800, 600, 200, 72);
    assert.equal(result.x, 0);
    assert.equal(result.y, 0);
  }
  for (const dims of [
    [NaN, Infinity, 200, 72], [800, 600, NaN, Infinity],
    [-800, -600, 200, 72], [800, 600, -200, -72],
  ]) {
    const result = clamp({ x: 999, y: 999 }, ...dims);
    assert.equal(Number.isFinite(result.x), true);
    assert.equal(Number.isFinite(result.y), true);
    assert.equal(result.x >= 0 && result.y >= 0, true);
  }
});
