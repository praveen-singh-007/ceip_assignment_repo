interface SegmentedControlProps<T extends string> {
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}

export default function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
}: SegmentedControlProps<T>) {
  return (
    <div className="inline-flex rounded-full border border-platinum-700 bg-alabaster_grey-800 p-1">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            value === option.value
              ? "bg-black-500 text-white-500"
              : "text-charcoal-400 hover:text-black-500"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
