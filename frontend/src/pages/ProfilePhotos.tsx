import { useEffect, useRef, useState } from "react";
import SubPageHeader from "../components/SubPageHeader";
import { deleteProfilePhoto, getMyProfile, setPrimaryProfilePhoto, uploadProfilePhoto, type ProfilePhoto } from "../api/profile";

export default function ProfilePhotos() {
  const [photos, setPhotos] = useState<ProfilePhoto[]>([]);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  async function refresh() {
    const profile = await getMyProfile();
    setPhotos(profile.photos);
  }
  useEffect(() => { refresh().catch((e) => setError(e.message)); }, []);

  async function handleAdd(file?: File) {
    if (!file) return;
    setError("");
    try { await uploadProfilePhoto(file); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to upload photo"); }
  }

  async function handleRemove(id: string) {
    setError("");
    try { await deleteProfilePhoto(id); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to remove photo"); }
  }

  async function handlePrimary(id: string) {
    setError("");
    try { await setPrimaryProfilePhoto(id); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to set primary photo"); }
  }

  return (
    <section className="page">
      <SubPageHeader title="My photos" backTo="/profile" />
      <p style={{ margin: "12px 0" }}>Up to 3 profile photos. JPG, PNG or WebP, maximum 8 MB each.</p>
      {error && <p role="alert">{error}</p>}
      <input ref={inputRef} hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; void handleAdd(f); }} />
      <div className="photo-grid">
        {photos.map((photo) => (
          <div key={photo.id} className="photo-tile" style={{ backgroundImage: `url(${photo.url})` }}>
            {photo.is_primary && <span className="photo-tile__primary">Primary</span>}
            <button className="photo-tile__remove" onClick={() => void handleRemove(photo.id)} aria-label="Remove photo">✕</button>
            {!photo.is_primary && <button className="btn btn-primary" style={{ position: "absolute", bottom: 8, left: 8 }} onClick={() => void handlePrimary(photo.id)}>Set primary</button>}
          </div>
        ))}
        {photos.length < 3 && <button className="photo-tile photo-tile--add" onClick={() => inputRef.current?.click()}>+ Add</button>}
      </div>
    </section>
  );
}
