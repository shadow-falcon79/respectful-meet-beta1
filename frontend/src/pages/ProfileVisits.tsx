import SubPageHeader from "../components/SubPageHeader";

export default function ProfileVisits() {
  return <section className="page"><SubPageHeader title="Who visited you" backTo="/profile" /><div className="card text-center" style={{ marginTop: 12 }}><h2 style={{ fontSize: "1rem", marginBottom: 6 }}>Visit history is not enabled yet</h2><p>There are no simulated visitors in the beta. This screen will show real visits once the backend visit-tracking module is enabled.</p></div></section>;
}
