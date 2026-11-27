import { ShieldCheck } from "lucide-react";
import SubPageHeader from "../components/SubPageHeader";

export default function ProfileVerify() {
  return <section className="page"><SubPageHeader title="Verify your profile" backTo="/profile" /><div className="card text-center" style={{ marginTop: 12 }}><ShieldCheck size={36} color="var(--color-accent)" style={{ marginBottom: 8 }} /><h2 style={{ fontSize: "1.1rem", marginBottom: 6 }}>Profile verification</h2><p>Identity verification is intentionally not simulated. The production verification provider must be configured before users can submit verification.</p></div></section>;
}
