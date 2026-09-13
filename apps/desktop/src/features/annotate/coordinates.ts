import type { PageSize } from "../../services/preview";
import type { Annotation } from "./types";

/** Maps a pointer event's screen position onto SVG viewBox coordinates,
 * using the SVG's own current transform — correct regardless of how the
 * element is actually scaled/laid out on screen, no manual pixel math. */
export function screenPointToSvgPoint(svg: SVGSVGElement, clientX: number, clientY: number) {
  const point = svg.createSVGPoint();
  point.x = clientX;
  point.y = clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: clientX, y: clientY };
  const transformed = point.matrixTransform(ctm.inverse());
  return { x: transformed.x, y: transformed.y };
}

/** Converts one editor-space annotation into the flat option shape the
 * `annotate` engine tool expects, flipping Y into PDF's bottom-left origin
 * using that annotation's own page size. */
export function toEngineOptions(annotation: Annotation, pageSize: PageSize): Record<string, unknown> {
  const { id: _id, ...rest } = annotation;
  void _id;

  switch (annotation.type) {
    case "text":
      // The click point is treated as the text's top-left, but reportlab's
      // drawString positions the baseline - shift down by an approximate
      // ascent so the rendered text lands close to where it was placed.
      return {
        ...rest,
        y: pageSize.height - annotation.y - annotation.fontSize * 0.8,
      };
    case "rectangle":
      return {
        ...rest,
        y: pageSize.height - annotation.y - annotation.height,
      };
    case "line":
      return {
        ...rest,
        y1: pageSize.height - annotation.y1,
        y2: pageSize.height - annotation.y2,
      };
  }
}
