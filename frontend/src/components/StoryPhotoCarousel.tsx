import { useState } from "react";

export default function StoryPhotoCarousel({ photos }: { photos: string[] }) {
  const [index, setIndex] = useState(0);

  function next() {
    setIndex((i) => Math.min(i + 1, photos.length - 1));
  }
  function prev() {
    setIndex((i) => Math.max(i - 1, 0));
  }

  return (
    <>
      <div className="story-dots">
        {photos.map((_, i) => (
          <span key={i} className={`story-dot ${i === index ? "active" : ""} ${i < index ? "seen" : ""}`} />
        ))}
      </div>
      <div className="story-photo" style={{ backgroundImage: `url(${photos[index]})` }}>
        <button className="story-tap-zone story-tap-zone--left" aria-label="Previous photo" onClick={prev} />
        <button className="story-tap-zone story-tap-zone--right" aria-label="Next photo" onClick={next} />
      </div>
    </>
  );
}
