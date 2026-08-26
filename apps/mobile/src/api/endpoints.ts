import { api, tokenStore } from './client';
import type {
  ConversationDetail,
  DailySuggestion,
  DesignState,
  Entitlements,
  Occasion,
  Outfit,
  RecommendationResult,
  StyleProfile,
  User,
  WardrobeCategory,
  WardrobeItem,
} from './types';

export const authApi = {
  register: (email: string, fullName: string, password: string) =>
    api.post<{ access: string; refresh: string; user: User }>('/auth/register', {
      email,
      full_name: fullName,
      password,
      device_name: 'mobile',
    }),
  login: (email: string, password: string) =>
    api.post<{ access: string; refresh: string; user: User }>('/auth/login', {
      email,
      password,
      device_name: 'mobile',
    }),
  me: () => api.get<User>('/auth/me'),
  logoutAll: () => api.post<{ sessions_revoked: boolean }>('/auth/logout-all'),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<{ changed: boolean }>('/auth/password/change', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
  deleteAccount: async (password: string) => {
    await api.post('/auth/delete-account', { password });
    await tokenStore.clear();
  },
};

export const profileApi = {
  getStyleProfile: () => api.get<StyleProfile>('/profile/style'),
  patchStyleProfile: (patch: Partial<StyleProfile>) => api.patch<StyleProfile>('/profile/style', patch),
  onboardingStatus: () =>
    api.get<{
      completed: boolean;
      completion_percent: number;
      steps: { key: string; done: boolean }[];
    }>('/profile/onboarding-status'),
};

export const fashionApi = {
  occasions: () => api.get<Occasion[]>('/fashion/occasions'),
  analyzePhoto: (photoUri: string, occasion?: string, notes?: string) => {
    const form = new FormData();
    // React Native FormData file shape.
    form.append('photo', {
      uri: photoUri,
      name: 'look.jpg',
      type: 'image/jpeg',
    } as unknown as Blob);
    if (occasion) form.append('occasion', occasion);
    if (notes) form.append('notes', notes);
    return api.post<{ analysis: RecommendationResult | Record<string, unknown> }>(
      '/fashion/analyze',
      form,
    );
  },
  recommend: (input: { occasion?: string; budget_inr?: number; notes?: string }) =>
    api.post<Outfit>('/fashion/recommend', input),
  outfits: (savedOnly = false) =>
    api.get<{ count: number; results: Outfit[] }>(`/fashion/outfits${savedOnly ? '?saved=true' : ''}`),
  outfit: (id: string) => api.get<Outfit>(`/fashion/outfits/${id}`),
  saveOutfit: (id: string) => api.post<Outfit>(`/fashion/outfits/${id}/save`),
  deleteOutfit: (id: string) => api.delete<void>(`/fashion/outfits/${id}`),
  generateImage: (outfitId?: string) =>
    api.post<Outfit>('/outfits/generate', outfitId ? { outfit_id: outfitId } : {}),
};

export const designerApi = {
  conversations: () => api.get<{ id: string; title: string; updated_at: string }[]>(
    '/fashion/designer/conversations',
  ),
  createConversation: (input: { occasion?: string; budget_inr?: number; opening_request?: string }) =>
    api.post<ConversationDetail>('/fashion/designer/conversations', input),
  conversation: (id: string) => api.get<ConversationDetail>(`/fashion/designer/conversations/${id}`),
  sendMessage: (id: string, message: string) =>
    api.post<ConversationDetail>(`/fashion/designer/conversations/${id}/messages`, { message }),
  materialize: (id: string) => api.post<Outfit>(`/fashion/designer/conversations/${id}/materialize`),
  archive: (id: string) => api.delete<void>(`/fashion/designer/conversations/${id}`),
};

export const plansApi = {
  entitlements: () => api.get<Entitlements>('/plans/entitlements'),
};

export const wardrobeApi = {
  items: (filter?: { category?: WardrobeCategory; favorite?: boolean }) => {
    const params = new URLSearchParams();
    if (filter?.category) params.set('category', filter.category);
    if (filter?.favorite) params.set('favorite', 'true');
    const qs = params.toString();
    return api.get<{ count: number; results: WardrobeItem[] }>(
      `/wardrobe/items${qs ? `?${qs}` : ''}`,
    );
  },
  addItem: (photoUri: string, opts?: { category?: string; notes?: string }) => {
    const form = new FormData();
    form.append('photo', {
      uri: photoUri,
      name: 'piece.jpg',
      type: 'image/jpeg',
    } as unknown as Blob);
    if (opts?.category) form.append('category', opts.category);
    if (opts?.notes) form.append('notes', opts.notes);
    return api.post<WardrobeItem>('/wardrobe/items', form);
  },
  updateItem: (id: string, patch: Partial<Pick<WardrobeItem, 'name' | 'category' | 'favorite' | 'archived' | 'notes'>>) =>
    api.patch<WardrobeItem>(`/wardrobe/items/${id}`, patch),
  deleteItem: (id: string) => api.delete<void>(`/wardrobe/items/${id}`),
  markWorn: (id: string) => api.post<WardrobeItem>(`/wardrobe/items/${id}/worn`),
  styleFromCloset: (input: { occasion?: string; budget_inr?: number }) =>
    api.post<{ outfit: Outfit; items: WardrobeItem[] }>('/wardrobe/closet/recommend', input),
  daily: () => api.get<DailySuggestion>('/wardrobe/daily'),
};

export type { DesignState };
