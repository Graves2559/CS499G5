import { useState, type Dispatch, type SetStateAction, type RefObject } from "react";
import { X } from "lucide-react";
import type { Preferences, FileEntry } from "../types";
import FilesView from "./FilesView";

type SettingsModalProps = {
  dialogRef: RefObject<HTMLDialogElement | null>;
  preferences: Preferences;
  onChange: Dispatch<SetStateAction<Preferences>>;
  entries: FileEntry[];
  setEntries: Dispatch<SetStateAction<FileEntry[]>>;
};

export default function SettingsModal({ dialogRef, preferences, onChange, entries, setEntries }: SettingsModalProps) {
  return (<dialog ref={dialogRef} className="settings-dialog" aria-labelledby="settings-title" onClick={e => {
      if (e.target !== e.currentTarget) return;
      const rect = e.currentTarget.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) dialogRef.current?.close();
    }}>
      <header className="settings-header"><h2 id="settings-title">Settings</h2><button className="icon-button" aria-label="Close settings" onClick={() => dialogRef.current?.close()}><X size={21} /></button></header>
      <SettingsContent preferences={preferences} onChange={onChange} entries={entries} setEntries={setEntries} />
    </dialog>);
}

function SettingsContent({ preferences, onChange, entries, setEntries }: {
  preferences: Preferences;
  onChange: Dispatch<SetStateAction<Preferences>>;
  entries: FileEntry[];
  setEntries: Dispatch<SetStateAction<FileEntry[]>>;
}) {
  const [section, setSection] = useState("General");
  const [billingNotice, setBillingNotice] = useState("");
  const sections = ["General", "Files", "Appearance", "Performance", "Payment"];
  return <div className="settings-layout">
    <nav className="settings-nav" aria-label="Settings sections">

      {sections.map(name => <button key={name} type="button" aria-current={section === name ? "page" : undefined} onClick={() => setSection(name)}>{name}</button>)}
    </nav>
    <section className={`settings-content${section === "Files" ? " files-settings-content" : ""}`} aria-label={`${section} settings`}>
      {section === "Files" && <FilesView entries={entries} setEntries={setEntries} />}
      {section === "General" && <>
        <h3>General</h3>
        <p className="muted-copy">Encryption and conversion are not connected yet.</p>
        <div className="preference-row"><div><label htmlFor="image-video-encryption">Image &amp; video encryption</label></div><input id="image-video-encryption" className="preference-checkbox" type="checkbox" checked={preferences.encryption} onChange={e => onChange(current => ({ ...current, encryption: e.target.checked }))} /></div>
        <div className="preference-row"><div><label htmlFor="lossless-conversion">Lossless format conversion</label></div><input id="lossless-conversion" className="preference-checkbox" type="checkbox" checked={preferences.lossless} onChange={e => onChange(current => ({ ...current, lossless: e.target.checked }))} /></div>
      </>}
      {section === "Appearance" && <>
        <h3>Background color</h3>
        <div className="color-options">{[{ name: "Midnight", color: "#0b0610" }, { name: "Charcoal", color: "#15171c" }, { name: "Ocean", color: "#071d2a" }, { name: "Plum", color: "#29142c" }].map(({ name, color }) => <button key={name} aria-pressed={preferences.background === color} onClick={() => onChange(current => ({ ...current, background: color }))}><span style={{ background: color }} />{name}</button>)}</div>
        <label className="custom-color">Custom color <input type="color" aria-label="Custom background color" value={preferences.background} onChange={e => onChange(current => ({ ...current, background: e.target.value }))} /><span>{preferences.background.toUpperCase()}</span></label>
        <p className="muted-copy section-space">Changes reset on refresh.</p>
      </>}
      {section === "Performance" && <>
        <h3>Performance</h3><p className="muted-copy">Token usage is not connected yet.</p>
        <div className="token-counts"><div><span>Input tokens</span><strong>—</strong></div><div><span>Output tokens</span><strong>—</strong></div><div><span>Total tokens</span><strong>—</strong></div></div>
        <h4>Recent token usage</h4><div className="table-scroll"><table className="details-table"><thead><tr><th>Request</th><th>Input</th><th>Output</th><th>Total</th></tr></thead><tbody><tr><td colSpan={4} className="table-empty">No token usage recorded.</td></tr></tbody></table></div>
      </>}
      {section === "Payment" && <>
        <h3>Payment</h3>
        <div className="payment-method"><div><h4>Current payment method</h4><p>No payment method added.</p></div><button className="pill" onClick={() => setBillingNotice("Payments are not connected yet.")}>Add payment method</button></div>
        {billingNotice && <p className="status-note" role="status">{billingNotice}</p>}
        <h4 className="section-space">Billing history</h4><div className="table-scroll"><table className="details-table"><thead><tr><th>Date</th><th>Description</th><th>Amount</th><th>Status</th></tr></thead><tbody><tr><td colSpan={4} className="table-empty">No billing history yet.</td></tr></tbody></table></div>
      </>}
    </section>
  </div>;
}
