import { useState, type Dispatch, type SetStateAction } from "react";
import { Plus, ChevronDown, Download, BookOpen } from "lucide-react";
import type { OutputType } from "../types";
import { useFileUrl } from "../hooks/useFileUrl";
import { saveDownload } from "../utils/download";

type OutputPanelProps = {
  outputType: OutputType;
  setOutputType: Dispatch<SetStateAction<OutputType>>;
  summary: string;
  outputImage: File | null;
  outputPdf: File | null;
  word: string;
  setWord: Dispatch<SetStateAction<string>>;
};

export default function OutputPanel({ outputType, setOutputType, summary, outputImage, outputPdf, word, setWord }: OutputPanelProps) {
  const outputImageUrl = useFileUrl(outputImage);
  const outputPdfUrl = useFileUrl(outputPdf);
  const [defineNotice, setDefineNotice] = useState("");

  function downloadPdf() {
    if (outputPdf) saveDownload(outputPdf, outputPdf.name);
  }

  return (<section className="panel output-panel" aria-labelledby="output-title">
          <div className="panel-heading"><h2 id="output-title">Output</h2><div className="select-wrap"><select aria-label="Output type" value={outputType} onChange={e => { setOutputType(e.target.value as OutputType); setWord(""); }}><option>Summary</option><option>Image</option><option>PDF</option></select><ChevronDown size={16} /></div></div>
          <div className="output-body result-body">
            {outputType === "Summary" ? <>
              <div className="summary-layout">
                <textarea className="text-input summary-text" aria-label="Summary output" readOnly value={summary}
                  placeholder="Enter text on the left and click Run."
                  onBlur={e => { if (!(e.relatedTarget instanceof Element) || !e.relatedTarget.closest(".definition-side")) setWord(""); }}
                  onSelect={e => {
                    const field = e.currentTarget;
                    setWord(field.value.slice(field.selectionStart, field.selectionEnd).trim());
                    setDefineNotice("");
                  }} />
                {word && <aside className="definition-side" aria-label="Definition panel">
                  <h3><BookOpen size={16} />Define</h3>
                  <p className="selected-word">{word}</p>
                  <button className="pill" onMouseDown={e => e.preventDefault()} onClick={() => setDefineNotice("Definitions are not connected yet.")}>Define</button>
                  {defineNotice && <p className="muted-copy" role="status">{defineNotice}</p>}
                </aside>}
              </div>
            </> : outputType === "Image" && outputImage && outputImageUrl ? <><div className="output-media"><img src={outputImageUrl} alt={`Output: ${outputImage.name}`} /></div><p className="output-filename">{outputImage.name}</p></> : outputType === "PDF" && outputPdf && outputPdfUrl ? <>
              <object className="pdf-viewer" data={outputPdfUrl} type="application/pdf" aria-label={`PDF preview: ${outputPdf.name}`}><p>This browser cannot preview this PDF. Use Download PDF below.</p></object>
              <div className="pdf-download"><span>{outputPdf.name}</span><button className="pill" type="button" onClick={downloadPdf}><Download size={15} />Download PDF</button></div>
            </> : <div className="media-empty empty-state"><span className="empty-icon"><Plus size={20} strokeWidth={1.5} /></span><p>Upload {outputType === "PDF" ? "a PDF" : "an image"} on the left,<br />then click Run to show it here.</p></div>}
          </div>
        </section>);
}
