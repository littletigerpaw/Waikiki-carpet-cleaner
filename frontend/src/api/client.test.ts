import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, assetUrl } from './client'

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

describe('api client', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock)
    fetchMock.mockReset()
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends the saved token as a Bearer header', async () => {
    localStorage.setItem('token', 'abc')
    fetchMock.mockResolvedValue(jsonResponse(200, []))
    await api.myTasks()
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/employee/tasks')
    expect(init.headers.Authorization).toBe('Bearer abc')
    expect(init.headers['Content-Type']).toBe('application/json')
  })

  it('lets the browser set Content-Type for photo uploads', async () => {
    fetchMock.mockResolvedValue(jsonResponse(201, {}))
    await api.uploadPhotos(5, [new File(['x'], 'a.png', { type: 'image/png' })])
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/employee/tasks/5/photos')
    expect(init.body).toBeInstanceOf(FormData)
    expect(init.headers['Content-Type']).toBeUndefined()
  })

  it('throws ApiError with the server message', async () => {
    fetchMock.mockResolvedValue(jsonResponse(400, { error: 'Missing fields: address' }))
    await expect(api.createTask({} as never)).rejects.toEqual(new ApiError('Missing fields: address', 400))
  })

  it('logs out on 401 when a token was sent', async () => {
    localStorage.setItem('token', 'expired')
    const assign = vi.fn()
    vi.stubGlobal('location', { ...window.location, assign })
    fetchMock.mockResolvedValue(jsonResponse(401, { error: 'Session expired' }))

    await expect(api.myTasks()).rejects.toBeInstanceOf(ApiError)
    expect(localStorage.getItem('token')).toBeNull()
    expect(assign).toHaveBeenCalledWith('/login')
  })

  it('gives a friendly message for uploads that are too large', async () => {
    fetchMock.mockResolvedValue(new Response('Too large', { status: 413 }))
    await expect(api.uploadPhotos(1, [])).rejects.toThrow(/10 MB/)
  })
})

describe('assetUrl', () => {
  it('keeps absolute URLs (Cloudinary) unchanged', () => {
    expect(assetUrl('https://res.cloudinary.com/x/photo.jpg')).toBe('https://res.cloudinary.com/x/photo.jpg')
  })
  it('leaves relative API paths relative in dev', () => {
    expect(assetUrl('/api/uploads/abc.png')).toBe('/api/uploads/abc.png')
  })
})
