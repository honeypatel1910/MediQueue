import { afterEach, describe, expect, test, vi } from 'vitest';
import { apiFetch, postJson } from '../app/api';

describe('frontend API helper', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('apiFetch sends JSON headers and same-origin credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true, value: 42 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const result = await apiFetch<{ ok: boolean; value: number }>('/api/example');

    expect(result).toEqual({ ok: true, value: 42 });
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/example',
      expect.objectContaining({
        credentials: 'same-origin',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      }),
    );
  });

  test('apiFetch throws the backend error message for an unsuccessful response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: false, error: 'Access denied' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(apiFetch('/api/protected')).rejects.toThrow('Access denied');
  });

  test('postJson sends a POST request with a JSON body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await postJson('/api/login', { email: 'patient@example.com', password: 'Secret123!' });

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'patient@example.com', password: 'Secret123!' }),
      }),
    );
  });
});
