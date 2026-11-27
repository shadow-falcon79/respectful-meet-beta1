import type { ReactNode } from "react";
import Logo from "../components/Logo";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="auth-layout">
      <div className="auth-layout__logo">
        <Logo variant="icon" height={56} />
      </div>
      {children}
    </div>
  );
}
