// All coordinates here are in "editor space": the same scale as PDF points
// (so 1 unit = 1 pt), but with a top-down Y axis matching normal screen/SVG
// conventions — the opposite of a PDF page's own bottom-left-origin space.
// The flip to real PDF coordinates happens once, at submit time
// (see toEngineOptions in AnnotateWorkspace.tsx), so all the interactive
// editing logic can stay in one consistent, screen-natural coordinate system.

export type Tool = "select" | "text" | "rectangle" | "line";

interface BaseAnnotation {
  id: string;
  page: number;
  color: string;
}

export interface TextAnnotation extends BaseAnnotation {
  type: "text";
  x: number;
  y: number;
  text: string;
  fontSize: number;
}

export interface RectangleAnnotation extends BaseAnnotation {
  type: "rectangle";
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface LineAnnotation extends BaseAnnotation {
  type: "line";
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export type Annotation = TextAnnotation | RectangleAnnotation | LineAnnotation;
