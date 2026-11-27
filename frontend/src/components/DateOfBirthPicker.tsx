import { useState } from "react";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";

interface DateOfBirthPickerProps {
  value: string; // "" or "YYYY-MM-DD"
  onChange: (value: string) => void;
}

const MIN_AGE = 18;
const MAX_AGE = 100;

function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

function parseValue(value: string): { day?: number; month?: number; year?: number } {
  if (!value) return {};
  const [year, month, day] = value.split("-").map(Number);
  return { year, month, day };
}

export default function DateOfBirthPicker({ value, onChange }: DateOfBirthPickerProps) {
  const { language } = useLanguage();
  const t = authTranslations[language];

  // Each field keeps its own state so a partial selection (e.g. only the
  // month picked) is never lost — onChange to the parent only fires once
  // all three are set and form a valid date.
  const initial = parseValue(value);
  const [day, setDay] = useState<number | undefined>(initial.day);
  const [month, setMonth] = useState<number | undefined>(initial.month);
  const [year, setYear] = useState<number | undefined>(initial.year);

  const now = new Date();
  const maxYear = now.getFullYear() - MIN_AGE; // oldest allowed = 18 today
  const minYear = now.getFullYear() - MAX_AGE;
  const years = Array.from({ length: maxYear - minYear + 1 }, (_, i) => maxYear - i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const dayCount = year && month ? daysInMonth(year, month) : 31;
  const days = Array.from({ length: dayCount }, (_, i) => i + 1);

  function update(part: "day" | "month" | "year", raw: string) {
    const num = Number(raw);
    const nextDay = part === "day" ? num : day;
    const nextMonth = part === "month" ? num : month;
    const nextYear = part === "year" ? num : year;

    setDay(nextDay);
    setMonth(nextMonth);
    setYear(nextYear);

    if (nextDay && nextMonth && nextYear) {
      const clampedDay = Math.min(nextDay, daysInMonth(nextYear, nextMonth));
      const iso = `${nextYear}-${String(nextMonth).padStart(2, "0")}-${String(clampedDay).padStart(2, "0")}`;
      onChange(iso);
    }
  }

  return (
    <div className="dob-picker">
      <select className="input" value={day ?? ""} onChange={(e) => update("day", e.target.value)}>
        <option value="" disabled>
          {t.day}
        </option>
        {days.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>
      <select className="input" value={month ?? ""} onChange={(e) => update("month", e.target.value)}>
        <option value="" disabled>
          {t.month}
        </option>
        {months.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
      <select className="input" value={year ?? ""} onChange={(e) => update("year", e.target.value)}>
        <option value="" disabled>
          {t.year}
        </option>
        {years.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
    </div>
  );
}
