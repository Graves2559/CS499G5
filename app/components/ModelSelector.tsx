import type { AIModel } from "../types";

type ModelSelectorProps = {
  models: AIModel[];
  selectedModel: string;
  onSelect: (modelId: string) => void;
};

export default function ModelSelector({ models, selectedModel, onSelect }: ModelSelectorProps) {
  const summarizers = models.filter(model => model.kind === "summarizer");

  return <section aria-label="Summary model">
    <p className="muted-copy">Summary model</p>
    <div className="model-buttons">
      {summarizers.map(model => <button
        className="pill"
        type="button"
        key={model.id}
        disabled={!model.available}
        aria-pressed={selectedModel === model.id}
        onClick={() => onSelect(model.id)}
      >
        {model.name}{!model.available && " (unavailable)"}
      </button>)}
    </div>
  </section>;
}
