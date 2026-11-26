import { describe, expect, it } from 'vitest'
import { compressImage } from './image'

describe('compressImage', () => {
  it('returns the original file when the browser cannot decode images (e.g. tests, old browsers)', async () => {
    const file = new File(['data'], 'photo.png', { type: 'image/png' })
    expect(await compressImage(file)).toBe(file)
  })

  it('leaves non-image files alone', async () => {
    const file = new File(['data'], 'notes.txt', { type: 'text/plain' })
    expect(await compressImage(file)).toBe(file)
  })
})
