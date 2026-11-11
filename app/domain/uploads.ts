// Domain rules for what the user may choose as input. Pure: returns an error message, or null when the file is fine.
export type UploadKind = "Image" | "PDF";

export function uploadProblem(kind: UploadKind, candidate: File): string | null {
  if (kind === "PDF") {
    if (candidate.type !== "application/pdf" && !(candidate.type === "" && /\.pdf$/i.test(candidate.name))) return "Please choose a PDF file.";
    if (candidate.size > 25 * 1024 * 1024) return "Please choose a PDF no larger than 25MB.";
    return null;
  }
  if (!["image/png", "image/jpeg"].includes(candidate.type)) return "Please choose a PNG or JPG image.";
  if (candidate.size > 10 * 1024 * 1024) return "Please choose an image no larger than 10MB.";
  return null;
}
