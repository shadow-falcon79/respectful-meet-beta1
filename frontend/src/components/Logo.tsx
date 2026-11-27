import logoIcon from "../assets/logo-icon.png";
import logoFull from "../assets/logo.png";

interface LogoProps {
  variant?: "icon" | "full";
  height?: number;
}

export default function Logo({ variant = "full", height = 40 }: LogoProps) {
  const src = variant === "icon" ? logoIcon : logoFull;
  return <img src={src} alt="Respectful Meet" style={{ height, width: "auto" }} />;
}
