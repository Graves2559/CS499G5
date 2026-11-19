import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { Upload, ChevronDown, FileText, Settings } from "lucide-react";
import type { InputType, ProcessingOptions } from "../types";

type InputPanelProps = {
  input: InputType;
  text: string;
  activeFile: File | null;
  imageUrl: string;
  error: string;
  status: string;
  canRun: boolean;
  processingOptions: ProcessingOptions;
  onProcessingOptionsChange: Dispatch<SetStateAction<ProcessingOptions>>;
  onTypeChange: (type: InputType) => void;
  onTextChange: (text: string) => void;
  onFileChange: (file?: File) => void;
  onRemoveFile: () => void;
  onImageError: () => void;
  onRun: () => void;
};

export default function InputPanel({ input, text, activeFile, imageUrl, error, status, canRun, processingOptions, onProcessingOptionsChange, onTypeChange, onTextChange, onFileChange, onRemoveFile, onImageError, onRun }: InputPanelProps) {
  const picker = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [tab, setTab] = useState<"document" | "prompt">("document");
  const documentTab = useRef<HTMLButtonElement>(null);
  const promptTab = useRef<HTMLButtonElement>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const processingSettings = useRef<HTMLDivElement>(null);
  const settingsButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!settingsOpen) return;
    const closeOutside = (event: PointerEvent) => {
      if (!processingSettings.current?.contains(event.target as Node)) setSettingsOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSettingsOpen(false);
        settingsButton.current?.focus();
      }
    };
    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [settingsOpen]);

  function editPrompt(value: string) {
    onProcessingOptionsChange(current => ({ ...current, prompt: value }));
  }

  return (<section className="panel" aria-labelledby="input-title">
          <div className="panel-heading">
            <h1 id="input-title">Input</h1>
            <div className="input-heading-controls">
              <div className="select-wrap"><select aria-label="Input type" value={input} onChange={e => { onTypeChange(e.target.value as InputType); setDragging(false); }}><option>Image</option><option>Texts</option><option>PDF</option></select><ChevronDown size={16} /></div>
              <div className="processing-settings" ref={processingSettings} onBlur={e => {
                if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setSettingsOpen(false);
              }}>
                <button ref={settingsButton} className="processing-settings-button" type="button" aria-label="OCR and LLM settings" title="OCR and LLM settings" aria-expanded={settingsOpen} aria-controls="processing-settings-panel" onClick={() => setSettingsOpen(open => !open)}><Settings size={18} /></button>
                {settingsOpen && <div id="processing-settings-panel" className="processing-popover" role="group" aria-labelledby="processing-settings-title">
                  <h2 id="processing-settings-title">Processing</h2>
                  <label><span>OCR<small>Extract text from images</small></span><input type="checkbox" checked={processingOptions.ocr} onChange={e => onProcessingOptionsChange(current => ({ ...current, ocr: e.target.checked }))} /></label>
                  <label><span>LLM<small>Use a prompt to generate a response</small></span><input type="checkbox" checked={processingOptions.llm} onChange={e => onProcessingOptionsChange(current => ({ ...current, llm: e.target.checked }))} /></label>
                </div>}
              </div>
            </div>
          </div>
          <div className="input-tabs" role="tablist" aria-label="Input and prompt" onKeyDown={e => {
            if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
            e.preventDefault();
            const next = e.key === "Home" ? "document" : e.key === "End" ? "prompt" : tab === "document" ? "prompt" : "document";
            setTab(next);
            (next === "document" ? documentTab : promptTab).current?.focus();
          }}>
            <button ref={documentTab} id="document-tab" type="button" role="tab" aria-selected={tab === "document"} aria-controls="document-panel" tabIndex={tab === "document" ? 0 : -1} onClick={() => setTab("document")}>Document</button>
            <button ref={promptTab} id="prompt-tab" type="button" role="tab" aria-selected={tab === "prompt"} aria-controls="prompt-panel" tabIndex={tab === "prompt" ? 0 : -1} onClick={() => setTab("prompt")}>Prompt</button>
          </div>
          <div className="input-body">
            <div id="document-panel" className="input-content" role="tabpanel" aria-labelledby="document-tab" hidden={tab !== "document"}>
            <input key={input} ref={picker} className="file-picker" type="file" accept={input === "PDF" ? "application/pdf,.pdf" : "image/png,image/jpeg"} aria-label={input === "PDF" ? "Choose a PDF" : "Choose an image"} onChange={e => { onFileChange(e.target.files?.[0]); e.target.value = ""; }} />
            {input === "Texts" ? <textarea className="text-input" aria-label="Text to copy" value={text} onChange={e => onTextChange(e.target.value)} placeholder="Type or paste your text here..." /> : <div className={`image-area${dragging ? " dragging" : ""}`} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false); }} onDrop={e => { e.preventDefault(); setDragging(false); onFileChange(e.dataTransfer.files[0]); }}>
              {activeFile ? <>
                {input === "Image" ? <img className="image-preview" src={imageUrl || undefined} alt={`Preview of ${activeFile.name}`} onError={onImageError} /> : <div className="pdf-input-card"><FileText size={44} strokeWidth={1.3} /><span>{activeFile.name}</span><small>Click Run, then select PDF in Output.</small></div>}
                <div className="image-details"><span>{activeFile.name}</span><div><button className="pill" onClick={() => picker.current?.click()}>Replace</button><button className="pill" onClick={onRemoveFile}>Remove</button></div></div>
              </> : <button className="dropzone" onClick={() => picker.current?.click()}><Upload size={20} strokeWidth={1.5} /><span>Drop {input === "PDF" ? "a PDF" : "an image"} here, or click to browse</span><small>{input === "PDF" ? "PDF up to 25MB" : "PNG, JPG up to 10MB"}</small></button>}
            </div>}
            </div>
            <div id="prompt-panel" className="input-content prompt-content" role="tabpanel" aria-labelledby="prompt-tab" hidden={tab !== "prompt"}>
              <label htmlFor="custom-prompt">Prompt</label>
              <textarea id="custom-prompt" className="text-input prompt-text" value={processingOptions.prompt} onChange={e => editPrompt(e.target.value)} placeholder="Write your instructions here..." />
            </div>
            {error && <p role="alert" className="upload-error">{error}</p>}
            <p className="run-status" role="status">{status}</p>
            <div className="actions processing-actions">
              <div className="run-options">
                <label><input type="checkbox" checked={processingOptions.pdf} onChange={e => onProcessingOptionsChange(current => ({ ...current, pdf: e.target.checked }))} aria-describedby="export-format" />PDF</label>
                <span id="export-format" className="export-format" aria-live="polite">Output file: {processingOptions.pdf ? ".pdf" : ".txt"}</span>
              </div>
              <button className="run-button" disabled={!canRun} onClick={onRun}>Run</button>
            </div>
          </div>
        </section>);
}
