export type CanvasStatus = "DRAFT" | "APPROVED" | "HOLD" | "NOT_FOUND" | "UNVERIFIED";
export type CanvasNodeKind = "SCRIPT" | "SCENE" | "CUT" | "CHARACTER" | "ASSET";
export type Point = { x: number; y: number };

// Separate evidence states prevent a script approval from implying MASTER or video approval.
export type ProjectScope = "CURRENT_ANIME" | "LEGACY_YEN_ZERO" | "OS" | "UNVERIFIED";
export type ApprovalEvidenceStatus = "UNVERIFIED" | "DRAFT" | "REVIEWED" | "APPROVED" | "NOT_APPLICABLE";
export type ApprovalEvidence = {
  status: ApprovalEvidenceStatus;
  evidenceId?: string;
  approvalScope?: string;
};
export type CanvasApprovalEvidence = {
  scriptContent?: ApprovalEvidence;
  integratedFile?: ApprovalEvidence;
  masterAdoption?: ApprovalEvidence;
  videoQc?: ApprovalEvidence;
};

export type CutDetails = {
  sceneId: string;
  scriptId: string;
  purpose: string;
  action: string;
  camera: string;
  sound: string;
  continuity: string;
  timing: string;
  qc: CanvasStatus;
};

export type CanvasNode = {
  id: string;
  kind: CanvasNodeKind;
  title: string;
  status: CanvasStatus;
  sourceId: string;
  projectScope?: ProjectScope;
  approvalEvidence?: CanvasApprovalEvidence;
  sourceVersion?: string;
  sourcePath?: string;
  approvalScope?: string;
  description: string;
  initialPosition: Point;
  cutDetails?: CutDetails;
};

export type CanvasEdge = {
  id: string;
  source: string;
  target: string;
  label: "CONTAINS" | "APPEARS_IN" | "REFERENCES";
  status: "DRAFT" | "UNVERIFIED";
};
