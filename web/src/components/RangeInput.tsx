interface Props {
  label: string;
  value: number; // 0..1
  min?: number;
  max?: number;
  step?: number;
  onChange: (v: number) => void;
}

export function RangeInput({ label, value, min = 0, max = 1, step = 0.05, onChange }: Props) {
  return (
    <label className="block">
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-[12.5px] font-medium text-body">{label}</span>
        <span className="font-heading text-[13px] tnum text-iris">{Math.round(value * 100)}%</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-iris"
        aria-label={label}
      />
    </label>
  );
}
