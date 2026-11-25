import { assetUrl } from '../api/client'
import type { TaskPhoto } from '../types'

interface Props {
  photos: TaskPhoto[]
  onDelete?: (photo: TaskPhoto) => void
}

/** Thumbnail grid. Click a photo to open it full size in a new tab. */
export default function PhotoGallery({ photos, onDelete }: Props) {
  if (photos.length === 0) return <p className="muted small">No photos yet.</p>

  return (
    <div className="gallery">
      {photos.map((p) => (
        <div key={p.id} className="thumb">
          <a href={assetUrl(p.url)} target="_blank" rel="noreferrer">
            <img src={assetUrl(p.url)} alt={`Photo uploaded by ${p.uploaded_by ?? 'employee'}`} loading="lazy" />
          </a>
          {onDelete && (
            <button
              type="button"
              className="thumb-delete"
              aria-label="Delete photo"
              onClick={() => onDelete(p)}
            >
              ×
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
