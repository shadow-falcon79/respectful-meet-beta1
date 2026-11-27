import SubPageHeader from "../components/SubPageHeader";

export default function ProfileTelegram() {
  return <section className="page"><SubPageHeader title="Connect Telegram" backTo="/profile" /><div className="settings-card" style={{ marginTop: 16 }}><strong>Telegram connection is not configured.</strong><p style={{ marginTop: 8 }}>This beta does not create fake Telegram identities. A real bot/OAuth flow will be connected when the server credentials are provided.</p></div></section>;
}
