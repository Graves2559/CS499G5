import { useRef, useState } from "react";
import { Upload, ChevronDown, FileText } from "lucide-react";
import type { InputType } from "../types";

type InputPanelProps = {
  input: InputType;
  text: string;
  activeFile: File | null;
  imageUrl: string;
  error: string;
  status: string;
  canRun: boolean;
  onTypeChange: (type: InputType) => void;
  onTextChange: (text: string) => void;
  onFileChange: (file?: File) => void;
  onRemoveFile: () => void;
  onImageError: () => void;
  onRun: () => void;
};

export default function InputPanel({ input, text, activeFile, imageUrl, error, status, canRun, onTypeChange, onTextChange, onFileChange, onRemoveFile, onImageError, onRun }: InputPanelProps) {
  const picker = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  return (<section className="panel" aria-labelledby="input-title">
          <div className="panel-heading"><h1 id="input-title">Input</h1><div className="select-wrap"><select aria-label="Input type" value={input} onChange={e => { onTypeChange(e.target.value as InputType); setDragging(false); }}><option>Image</option><option>Texts</option><option>PDF</option></select><ChevronDown size={16} /></div></div>
          <div className="input-body">
            <input key={input} ref={picker} className="file-picker" type="file" accept={input === "PDF" ? "application/pdf,.pdf" : "image/png,image/jpeg"} aria-label={input === "PDF" ? "Choose a PDF" : "Choose an image"} onChange={e => { onFileChange(e.target.files?.[0]); e.target.value = ""; }} />
            {input === "Texts" ? <textarea className="text-input" aria-label="Text to copy" value={text} onChange={e => onTextChange(e.target.value)} placeholder="Type or paste your text here..." /> : <div className={`image-area${dragging ? " dragging" : ""}`} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false); }} onDrop={e => { e.preventDefault(); setDragging(false); onFileChange(e.dataTransfer.files[0]); }}>
              {activeFile ? <>
                {input === "Image" ? <img className="image-preview" src={imageUrl || undefined} alt={`Preview of ${activeFile.name}`} onError={onImageError} /> : <div className="pdf-input-card"><FileText size={44} strokeWidth={1.3} /><span>{activeFile.name}</span><small>Click Run, then select PDF in Output.</small></div>}
                <div className="image-details"><span>{activeFile.name}</span><div><button className="pill" onClick={() => picker.current?.click()}>Replace</button><button className="pill" onClick={onRemoveFile}>Remove</button></div></div>
              </> : <button className="dropzone" onClick={() => picker.current?.click()}><Upload size={20} strokeWidth={1.5} /><span>Drop {input === "PDF" ? "a PDF" : "an image"} here, or click to browse</span><small>{input === "PDF" ? "PDF up to 25MB" : "PNG, JPG up to 10MB"}</small></button>}
            </div>}
            {error && <p role="alert" className="upload-error">{error}</p>}
            <p className="run-status" role="status">{status}</p>
            <div className="actions"><button className="run-button" disabled={!canRun} onClick={onRun}>Run</button></div>
          </div>
        </section>);
}
