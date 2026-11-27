import { useRef, type ClipboardEvent, type KeyboardEvent } from "react";

interface OtpInputProps {
  value: string;
  onChange: (value: string) => void;
  onComplete?: (value: string) => void;
  hasError?: boolean;
}

const LENGTH = 6;

export default function OtpInput({ value, onChange, onComplete, hasError }: OtpInputProps) {
  const inputsRef = useRef<Array<HTMLInputElement | null>>([]);
  const digits = value.split("").concat(Array(LENGTH).fill("")).slice(0, LENGTH);

  function updateDigit(index: number, raw: string) {
    const digit = raw.replace(/\D/g, "").slice(-1);
    const next = digits.slice();
    next[index] = digit;
    const joined = next.join("");
    onChange(joined);

    if (digit && index < LENGTH - 1) {
      inputsRef.current[index + 1]?.focus();
    }
    const allFilled = next.every((d) => d !== "");
    if (allFilled) {
      onComplete?.(joined);
    }
  }

  function handleKeyDown(index: number, event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    const pasted = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, LENGTH);
    if (pasted) {
      event.preventDefault();
      onChange(pasted.padEnd(LENGTH, "").slice(0, LENGTH).replace(/\s/g, ""));
      const targetIndex = Math.min(pasted.length, LENGTH - 1);
      inputsRef.current[targetIndex]?.focus();
      if (pasted.length === LENGTH) {
        onComplete?.(pasted);
      }
    }
  }

  return (
    <div className="otp-input" role="group" aria-label="Verification code">
      {digits.map((digit, index) => (
        <input
          key={index}
          ref={(el) => {
            inputsRef.current[index] = el;
          }}
          className={`otp-digit ${hasError ? "input-error" : ""}`}
          inputMode="numeric"
          autoComplete={index === 0 ? "one-time-code" : "off"}
          maxLength={1}
          value={digit}
          onChange={(e) => updateDigit(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={handlePaste}
          aria-label={`Digit ${index + 1}`}
        />
      ))}
    </div>
  );
}
