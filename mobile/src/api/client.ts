/** Mobile transport only. The existing FastAPI service remains the source of truth. */
export type Role = "owner" | "editor" | "viewer";
export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string | null;
  email_verified?: boolean;
  subscription_plan?: string;
  is_admin?: boolean;
  is_demo?: boolean;
}
export interface Memory {
  id: number;
  title?: string | null;
  content: string;
  event_date?: string | null;
  created_at: string;
  contributor_name?: string | null;
  status: string;
}
export interface Media {
  id: number;
  memorial_id: number;
  media_type: string;
  file_name: string;
  file_url?: string | null;
  mime_type?: string | null;
  created_at: string;
}
export interface Memorial {
  id: number;
  name: string;
  description?: string | null;
  gender?: "male" | "female" | null;
  maiden_name?: string | null;
  birth_date?: string | null;
  death_date?: string | null;
  owner_id?: number;
  cover_photo_id?: number | null;
  cover_photo_url?: string | null;
  is_public: boolean;
  current_user_role?: Role | null;
  media?: Media[];
  memories?: Memory[];
  memories_count?: number;
  media_count?: number;
}
export interface Relationship {
  id: number;
  related_memorial_id: number;
  related_memorial_name?: string | null;
  relationship_type: string;
  custom_label?: string | null;
}
export interface TimelineItem {
  id: number;
  year: number;
  date_label: string;
  type: string;
  title?: string | null;
  content?: string | null;
  media_id?: number | null;
}
export interface ChatResponse {
  answer: string;
  audio_url?: string | null;
  audio_error?: string | null;
  sources: string[];
  suggest_memory?: boolean;
}
export interface UploadFile {
  uri: string;
  name: string;
  mimeType?: string;
  type?: string;
  file?: Blob;
}
export interface TokenStore {
  get(): Promise<string | null>;
  set(token: string): Promise<void>;
  clear(): Promise<void>;
}
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function normalizeBaseUrl(value: string): string {
  let url: URL;
  try {
    url = new URL(value.trim());
  } catch {
    throw new Error(
      "Укажите полный адрес сервера, например https://example.com/api/v1",
    );
  }
  if (
    !["https:", "http:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash
  )
    throw new Error("Некорректный адрес сервера");
  const host = url.hostname;
  const local =
    host === "localhost" ||
    host === "127.0.0.1" ||
    host === "[::1]" ||
    /^10\./.test(host) ||
    /^192\.168\./.test(host) ||
    /^172\.(1[6-9]|2\d|3[01])\./.test(host);
  if (url.protocol !== "https:" && !local)
    throw new Error("Для удалённого сервера требуется HTTPS");
  url.pathname = url.pathname.replace(/\/+$/, "") || "/api/v1";
  return url.toString().replace(/\/$/, "");
}

export class MobileApi {
  private token: string | null = null;
  private baseUrl: string;
  private revision = 0;
  private guestId = `mobile-${Date.now()}-${Math.random().toString(36).slice(2, 14)}`;
  onUnauthorized?: () => void;
  constructor(
    baseUrl: string,
    private store: TokenStore,
    private fetcher: typeof fetch = (input, init) => fetch(input, init),
  ) {
    this.baseUrl = normalizeBaseUrl(baseUrl);
  }
  async hydrate() {
    this.token = await this.store.get();
  }
  getBaseUrl() {
    return this.baseUrl;
  }
  hasSession() {
    return !!this.token;
  }
  setGuestId(value: string) {
    if (/^[a-zA-Z0-9-]{16,64}$/.test(value)) this.guestId = value;
  }
  getGuestId() {
    return this.guestId;
  }
  async setBaseUrl(url: string) {
    const next = normalizeBaseUrl(url);
    if (next !== this.baseUrl) {
      await this.logout();
      this.baseUrl = next;
    }
  }
  async logout() {
    this.revision++;
    this.token = null;
    await this.store.clear();
  }
  private async request<T>(
    path: string,
    init: RequestInit = {},
    authenticated = true,
  ): Promise<T> {
    const revision = this.revision;
    const token = authenticated ? this.token : null;
    const headers = new Headers(init.headers);
    headers.set("X-Lang", "ru");
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (init.body && !(init.body instanceof FormData))
      headers.set("Content-Type", "application/json");
    const controller = new AbortController();
    const timeout = setTimeout(
      () => controller.abort(),
      path.includes("/avatar/chat")
        ? 120000
        : path.includes("/upload")
          ? 120000
          : 30000,
    );
    let response: Response;
    try {
      response = await this.fetcher(`${this.baseUrl}${path}`, {
        ...init,
        headers,
        signal: controller.signal,
      });
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError")
        throw new ApiError(
          "Сервер не ответил вовремя. Проверьте соединение и повторите.",
          0,
        );
      throw new ApiError(
        "Не удалось связаться с сервером. Проверьте интернет и адрес сервера.",
        0,
      );
    } finally {
      clearTimeout(timeout);
    }
    if (revision !== this.revision)
      throw new ApiError("Сессия изменилась. Откройте страницу заново.", 401);
    if (!response.ok) {
      if (response.status === 401 && token) {
        await this.logout();
        this.onUnauthorized?.();
      }
      let message = `Ошибка запроса (${response.status})`;
      try {
        const data = await response.json();
        if (typeof data.detail === "string") message = data.detail;
        else if (Array.isArray(data.detail))
          message = data.detail
            .map((item: { msg?: string }) => item.msg || "")
            .join("\n");
      } catch {
        /* No JSON error body. */
      }
      throw new ApiError(message, response.status);
    }
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }
  async login(email: string, password: string) {
    const result = await this.request<{ access_token: string; user: User }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
      false,
    );
    await this.store.set(result.access_token);
    this.token = result.access_token;
    return result.user;
  }
  startGoogle(challenge: string) {
    return this.request<{
      attempt_id: string;
      authorization_url: string;
      expires_in: number;
    }>(
      "/auth/mobile/google/start",
      { method: "POST", body: JSON.stringify({ challenge }) },
      false,
    );
  }
  async completeGoogle(attempt_id: string, verifier: string, code: string) {
    const result = await this.request<{ access_token: string; user: User }>(
      "/auth/mobile/google/exchange",
      { method: "POST", body: JSON.stringify({ attempt_id, verifier, code }) },
      false,
    );
    await this.store.set(result.access_token);
    this.token = result.access_token;
    return result.user;
  }
  register(
    username: string,
    email: string,
    password: string,
    fullName?: string,
  ) {
    return this.request<User>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify({
          username,
          email,
          password,
          full_name: fullName || undefined,
        }),
      },
      false,
    );
  }
  me() {
    return this.request<User>("/auth/me");
  }
  async listMemorials() {
    // Legacy list includes all public pages. Keep "My pages" restricted to actual ACL.
    const pages = await this.request<Memorial[]>("/memorials/");
    const own: Memorial[] = [];
    for (let offset = 0; offset < pages.length; offset += 4) {
      const batch = await Promise.all(
        pages.slice(offset, offset + 4).map(async (page) => {
          try {
            const detail = await this.getMemorial(page.id);
            return detail.current_user_role
              ? { ...page, current_user_role: detail.current_user_role }
              : null;
          } catch (error) {
            if (error instanceof ApiError && [403, 404].includes(error.status))
              return null;
            throw error;
          }
        }),
      );
      own.push(
        ...batch.filter(
          (page): page is Memorial & { current_user_role: Role } =>
            page !== null,
        ),
      );
    }
    return own;
  }
  getMemorial(id: number) {
    return this.request<Memorial>(`/memorials/${id}`);
  }
  createMemorial(data: {
    name: string;
    description?: string;
    maiden_name?: string | null;
    gender?: "male" | "female" | null;
    birth_date?: string | null;
    death_date?: string | null;
    is_public?: boolean;
  }) {
    return this.request<Memorial>("/memorials/", {
      method: "POST",
      body: JSON.stringify({ ...data, language: "ru" }),
    });
  }
  updateMemorial(
    id: number,
    data: Partial<
      Pick<
        Memorial,
        "name" | "description" | "is_public" | "birth_date" | "death_date" | "maiden_name" | "gender"
      >
    >,
  ) {
    return this.request<Memorial>(`/memorials/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }
  listMemories(id: number) {
    return this.request<Memory[]>(`/memorials/${id}/memories`);
  }
  createMemory(
    id: number,
    data: { title?: string; content: string; event_date?: string },
  ) {
    return this.request<Memory>(`/memorials/${id}/memories`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
  updateMemory(id:number, memoryId:number, data:{title?:string;content:string;event_date?:string|null}) {
    return this.request<Memory>(`/memorials/${id}/memories/${memoryId}`,{method:"PATCH",body:JSON.stringify(data)});
  }
  deleteMemory(id:number,memoryId:number) {
    return this.request<void>(`/memorials/${id}/memories/${memoryId}`,{method:"DELETE"});
  }
  submitPublicMemory(
    id: number,
    data: { title?: string; content: string; contributor_name: string },
  ) {
    return this.request<Memory>(`/memorials/${id}/memories/public`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
  listMedia(id: number) {
    return this.request<Media[]>(`/memorials/${id}/media`);
  }
  async uploadMedia(id: number, file: UploadFile) {
    const form = new FormData();
    if (file.file) form.append("file", file.file, file.name);
    else
      form.append("file", {
        uri: file.uri,
        name: file.name,
        type: file.mimeType || file.type || "application/octet-stream",
      } as unknown as Blob);
    return this.request<Media>(`/memorials/${id}/media/upload`, {
      method: "POST",
      body: form,
    });
  }
  getRelationships(id: number) {
    return this.request<Relationship[]>(
      `/family/memorials/${id}/relationships`,
    );
  }
  getTimeline(id: number) {
    return this.request<TimelineItem[]>(`/memorials/${id}/timeline`);
  }
  getPendingMemories(id: number) {
    return this.request<Memory[]>(`/memorials/${id}/memories/pending`);
  }
  approveMemory(id: number, memoryId: number) {
    return this.request<Memory>(
      `/memorials/${id}/memories/${memoryId}/approve`,
      { method: "POST" },
    );
  }
  rejectMemory(id: number, memoryId: number) {
    return this.request<void>(`/memorials/${id}/memories/${memoryId}/reject`, {
      method: "POST",
    });
  }
  savedAnswers(id: number) {
    return this.request<SavedAnswer[]>(`/featured-answers/memorials/${id}/saved`);
  }
  guestAnswers(id: number) {
    return this.request<GuestAnswer[]>(`/featured-answers/memorials/${id}/guest`);
  }
  revoiceAnswer(id: number, row: SavedAnswer) {
    return this.request<ChatResponse & {audio_preview_id?: string; answer_cache_id?: number}>(`/ai/avatar/chat`, {method: "POST", body: JSON.stringify({...(row.audio_variants.find(v => v.key === row.audio_variant)?.generation_settings || row.generation_settings), memorial_id: id, question: row.question, include_audio: true, regenerate_audio: true, include_family_memories: false})});
  }
  chooseAudio(cacheId: number, previewId: string, accept: boolean) {
    return this.request(`/ai/avatar/audio-preview/${cacheId}/${previewId}`, {method: "POST", body: JSON.stringify({accept})});
  }
  selectAnswer(cacheId: number, publish: boolean, audioVariant: string | null, position: number) {
    return this.request(`/featured-answers/saved/${cacheId}`, {method: "PUT", body: JSON.stringify({publish_to_guests: publish, audio_variant: audioVariant, position})});
  }
  revokeInvite(token: string) {
    return this.request<void>(`/invites/${encodeURIComponent(token)}`, {method: "DELETE"});
  }
  async invite(id: number, chat = false) {
    type Invite = {invite_url: string; token: string; expires_at?: string | null; permissions: {add_memories?: boolean; chat?: boolean; view_media?: boolean}};
    const current = await this.request<Invite[]>(`/invites/memorials/${id}/list`);
    const existing = current.find(item => (!item.expires_at || new Date(item.expires_at) > new Date()) && item.permissions.add_memories === true && Boolean(item.permissions.chat) === chat && !item.permissions.view_media);
    return existing || this.request<Invite>(`/invites/memorials/${id}/create`, {method: "POST", body: JSON.stringify({expires_days: 30, permissions: {add_memories: true, chat, view_media: false}})});
  }
  chat(id: number, question: string, includeAudio = false, includeFamily = false) {
    return this.request<ChatResponse>(
      `/ai/avatar/chat?guest_id=${this.guestId}`,
      {
        method: "POST",
        body: JSON.stringify({
          memorial_id: id,
          question,
          include_audio: includeAudio,
          include_family_memories: includeFamily,
          use_persona: true,
          language: "ru",
        }),
      },
    );
  }
  mediaUrl(id: number) {
    return `${this.baseUrl}/media/${id}`;
  }
  mediaSource(id: number) {
    return {
      uri: this.mediaUrl(id),
      headers: this.token
        ? { Authorization: `Bearer ${this.token}` }
        : undefined,
    };
  }
  publicPageUrl(id: number) {
    return this.websiteUrl(`/m/${id}`);
  }
  websiteUrl(path = "") {
    let base = (process.env.EXPO_PUBLIC_WEB_URL || "https://vspomin.ai/app").replace(/\/$/, "");
    if (base === "https://vspomin.ai" || base === "https://www.vspomin.ai") base += "/app";
    return `${base}${path}`;
  }
  resolveMediaUrl(url: string) {
    return new URL(url, this.baseUrl + "/").toString();
  }
}

export interface GuestAnswer { id: number; question: string; answer: string; audio_url: string | null }
export interface SavedAnswer { generation_settings: Record<string, unknown>; cache_id: number; question: string; answer: string; sources: string[]; source_memory_ids: number[]; audio_variants: {key: string; audio_url: string; generation_settings?: Record<string, unknown>}[]; featured: boolean; stale: boolean; audio_variant: string | null; position: number | null }
