/**
 * Shrink a photo in the browser before uploading.
 *
 * Phone photos are often 3–8 MB, but Vercel rejects uploads over 4.5 MB.
 * Resizing to at most 2000px and saving as JPEG keeps them around 300–800 KB,
 * which is still plenty sharp for "is this unit clean?" and much faster on mobile
 * data. It also drops hidden EXIF data such as GPS location.
 *
 * If the browser can't decode the file (e.g. HEIC in Chrome), the original is
 * returned unchanged and the server decides whether to accept it.
 */
export const MAX_DIMENSION = 2000
const JPEG_QUALITY = 0.85

export async function compressImage(file: File): Promise<File> {
  if (typeof createImageBitmap !== 'function' || !file.type.startsWith('image/') || file.type === 'image/gif') {
    return file
  }

  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
    const scale = Math.min(1, MAX_DIMENSION / Math.max(bitmap.width, bitmap.height))
    const width = Math.round(bitmap.width * scale)
    const height = Math.round(bitmap.height * scale)

    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    if (!ctx) return file
    ctx.drawImage(bitmap, 0, 0, width, height)
    bitmap.close()

    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY))
    if (!blob || blob.size >= file.size) return file // already small: keep the original

    const name = file.name.replace(/\.[^.]+$/, '') + '.jpg'
    return new File([blob], name, { type: 'image/jpeg', lastModified: file.lastModified })
  } catch {
    return file
  }
}
