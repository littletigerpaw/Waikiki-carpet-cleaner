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

  it('uploads several photos one request at a time and returns the final task', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(201, { id: 5, photos: [1] }))
      .mockResolvedValueOnce(jsonResponse(201, { id: 5, photos: [1, 2] }))
    const files = [new File(['a'], 'a.png', { type: 'image/png' }), new File(['b'], 'b.png', { type: 'image/png' })]
    const task = await api.uploadPhotos(5, files)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect((fetchMock.mock.calls[1][1].body as FormData).get('photos')).toBeInstanceOf(File)
    expect(task.photos).toHaveLength(2)
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
    await expect(api.uploadPhotos(1, [new File(['x'], 'big.png', { type: 'image/png' })])).rejects.toThrow(/4 MB/)
  })
})

describe('assetUrl', () => {
  it('keeps absolute URLs (Firebase Storage) unchanged', () => {
    const url = 'https://firebasestorage.googleapis.com/v0/b/app/o/task-photos%2Fa.jpg?alt=media&token=t'
    expect(assetUrl(url)).toBe(url)
  })
  it('leaves relative API paths relative in dev', () => {
    expect(assetUrl('/api/uploads/abc.png')).toBe('/api/uploads/abc.png')
  })
})
