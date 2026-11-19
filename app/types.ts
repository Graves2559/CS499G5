export type InputType = "Image" | "Texts" | "PDF";
export type OutputType = "Summary" | "Image" | "PDF";

export type FileEntry = {
  id: string;
  parentId: string | null;
  name: string;
  kind: "folder" | "file";
  description: string;
  file?: File;
  text?: string;
  mimeType?: string;
  size?: number;
  favorite?: boolean;
  dateModified?: string;
};

export type Preferences = {
  encryption: boolean;
  lossless: boolean;
  background: string;
};
