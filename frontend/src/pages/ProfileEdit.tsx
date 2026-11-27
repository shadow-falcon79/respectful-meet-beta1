import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import SubPageHeader from "../components/SubPageHeader";
import { getMyProfile, updateMyProfile, type Profile } from "../api/profile";

export default function ProfileEdit() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [about, setAbout] = useState("");
  const [interestsText, setInterestsText] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getMyProfile().then((p) => {
      setProfile(p);
      setAbout(p.bio ?? "");
      setInterestsText(p.interests.join(", "));
    }).catch((e) => setError(e.message));
  }, []);

  async function handleSave() {
    setError("");
    try {
      const updated = await updateMyProfile({
        bio: about,
        interests: interestsText.split(",").map((i) => i.trim()).filter(Boolean),
      });
      setProfile(updated);
      setSaved(true);
      setTimeout(() => navigate("/profile"), 600);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save changes");
    }
  }

  if (!profile) return <section className="page"><p className="text-center">{error || "Loading…"}</p></section>;

  return (
    <section className="page">
      <SubPageHeader title="Edit profile" backTo="/profile" />
      <div className="stack" style={{ marginTop: 16 }}>
        <div className="field"><label htmlFor="about">About you</label><textarea id="about" className="input" rows={4} value={about} onChange={(e) => setAbout(e.target.value)} /></div>
        <div className="field"><label htmlFor="interests">Interests (comma-separated)</label><textarea id="interests" className="input" rows={3} value={interestsText} onChange={(e) => setInterestsText(e.target.value)} /></div>
        {error && <p role="alert">{error}</p>}
        <button className="btn btn-primary" onClick={handleSave}>{saved ? "Saved ✓" : "Save changes"}</button>
      </div>
    </section>
  );
}
