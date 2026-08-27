import { api, tokenStore } from './client';
import type {
  BrandProduct,
  BrandProfile,
  Campaign,
  CampaignApplication,
  Challenge,
  ChatThread,
  ChatThreadDetail,
  ChatThreadMessage,
  ConversationDetail,
  CreatorEligibility,
  CreatorProfile,
  DailySuggestion,
  DesignState,
  DesignerProfile,
  Entitlements,
  FeedPage,
  I18nStrings,
  LeaderboardEntry,
  Notification,
  Occasion,
  Order,
  OTPRequestResult,
  Outfit,
  PaymentConfirm,
  PaymentInit,
  Product,
  PublicProfile,
  QuoteOffer,
  QuoteRequest,
  RecommendationResult,
  Redemption,
  Report,
  Reward,
  SearchResult,
  ShopThisLookComponent,
  SocialComment,
  SocialPost,
  StyleProfile,
  TranslateResult,
  TrendsResult,
  User,
  WardrobeCategory,
  WardrobeItem,
  XPDashboard,
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
  socialLogin: (provider: 'google' | 'apple', idToken: string) =>
    api.post<{ access: string; refresh: string; user: User }>('/auth/social', {
      provider,
      id_token: idToken,
      device_name: 'mobile',
    }),
  requestOtp: (phone: string) =>
    api.post<OTPRequestResult>('/auth/otp/request', { phone, purpose: 'login' }),
  loginWithOtp: (phone: string, code: string, fullName?: string) =>
    api.post<{ access: string; refresh: string; user: User }>('/auth/otp/verify', {
      phone,
      code,
      full_name: fullName,
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
  me: () => api.get<{ display_name: string; bio: string; city: string; language: string }>('/profile/me'),
  patchMe: (patch: { language?: string; display_name?: string; bio?: string; city?: string }) =>
    api.patch<{ display_name: string; bio: string; city: string; language: string }>('/profile/me', patch),
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
  trends: () => api.get<TrendsResult>('/fashion/trends'),
  tryon: (outfitId: string) =>
    api.post<Outfit>(`/fashion/outfits/${outfitId}/tryon`, {}),
};

export const aiApi = {
  transcribe: (audioUri: string, language = 'en') => {
    const form = new FormData();
    form.append('audio', { uri: audioUri, name: 'voice.m4a', type: 'audio/m4a' } as unknown as Blob);
    form.append('language', language);
    return api.post<{ text: string; language: string }>('/ai/transcribe', form);
  },
  translate: (text: string, target: string, source = 'en') =>
    api.post<TranslateResult>('/ai/translate', { text, target, source }),
};

export const i18nApi = {
  strings: (lang: string) => api.get<I18nStrings>(`/fashion/i18n/strings?lang=${lang}`),
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

// ---- Social -------------------------------------------------------------------

export const socialApi = {
  feed: (page = 1) => api.get<FeedPage>(`/social/feed?page=${page}`),
  posts: (params?: { user_id?: string; saved?: boolean; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.user_id) q.set('user_id', params.user_id);
    if (params?.saved) q.set('saved', 'true');
    if (params?.limit) q.set('limit', String(params.limit));
    const qs = q.toString();
    return api.get<{ count: number; results: SocialPost[] }>(`/social/posts${qs ? `?${qs}` : ''}`);
  },
  post: (id: string) => api.get<SocialPost>(`/social/posts/${id}`),
  createPost: (photoUri: string, opts?: { caption?: string; occasion?: string; outfit_id?: string; item_tags?: string[] }) => {
    const form = new FormData();
    form.append('photo', { uri: photoUri, name: 'post.jpg', type: 'image/jpeg' } as unknown as Blob);
    if (opts?.caption) form.append('caption', opts.caption);
    if (opts?.occasion) form.append('occasion', opts.occasion);
    if (opts?.outfit_id) form.append('outfit_id', opts.outfit_id);
    if (opts?.item_tags) form.append('item_tags', JSON.stringify(opts.item_tags));
    return api.post<SocialPost>('/social/posts', form);
  },
  deletePost: (id: string) => api.delete<void>(`/social/posts/${id}`),
  toggleLike: (id: string) => api.post<{ liked: boolean; like_count: number }>(`/social/posts/${id}/like`),
  toggleSave: (id: string) => api.post<{ saved: boolean }>(`/social/posts/${id}/save`),
  comments: (postId: string) => api.get<{ results: SocialComment[] }>(`/social/posts/${postId}/comments`),
  addComment: (postId: string, text: string) => api.post<SocialComment>(`/social/posts/${postId}/comments`, { text }),
  deleteComment: (commentId: string) => api.delete<void>(`/social/comments/${commentId}`),
  follow: (userId: string) => api.post<{ following: boolean }>(`/social/users/${userId}/follow`),
  publicProfile: (userId: string) => api.get<PublicProfile>(`/social/users/${userId}/profile`),
};

// ---- FashionXP / Gamification -------------------------------------------------

export const xpApi = {
  me: () => api.get<XPDashboard>('/social/xp/me'),
  leaderboard: (params?: { scope?: string; city?: string; challenge?: string }) => {
    const q = new URLSearchParams();
    if (params?.scope) q.set('scope', params.scope);
    if (params?.city) q.set('city', params.city);
    if (params?.challenge) q.set('challenge', params.challenge);
    const qs = q.toString();
    return api.get<{ scope: string; results: LeaderboardEntry[] }>(`/social/xp/leaderboard${qs ? `?${qs}` : ''}`);
  },
};

export const rewardsApi = {
  list: () => api.get<{ balance: number; results: Reward[] }>('/social/rewards'),
  redeem: (code: string) => api.post<{ id: string; status: string; cost_xp: number; balance_after: number }>(`/social/rewards/${code}/redeem`),
  redemptions: () => api.get<{ results: Redemption[] }>('/social/rewards/redemptions'),
};

export const challengesApi = {
  list: () => api.get<{ results: Challenge[] }>('/social/challenges'),
  detail: (id: string) => api.get<Challenge & { leaderboard: LeaderboardEntry[] }>(`/social/challenges/${id}`),
  enroll: (id: string, postId?: string) => api.post<{ challenge: string; score: number; qualified: boolean }>(`/social/challenges/${id}/enroll`, postId ? { post_id: postId } : {}),
};

// ---- Marketplace --------------------------------------------------------------

export const marketplaceApi = {
  products: (params?: { category?: string; city?: string; mine?: boolean; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.category) q.set('category', params.category);
    if (params?.city) q.set('city', params.city);
    if (params?.mine) q.set('mine', 'true');
    if (params?.limit) q.set('limit', String(params.limit));
    const qs = q.toString();
    return api.get<{ count: number; results: Product[] }>(`/marketplace/products${qs ? `?${qs}` : ''}`);
  },
  product: (id: string) => api.get<Product>(`/marketplace/products/${id}`),
  createProduct: (payload: {
    title: string;
    description?: string;
    price_inr: number;
    stock?: number;
    category?: string;
    fabric?: string;
    city?: string;
    colors?: string[];
    tags?: string[];
    is_customizable?: boolean;
    ready_to_ship?: boolean;
    variants?: { name: string; value: string; price_delta_inr?: number; stock?: number }[];
    photo?: { uri: string; name?: string; type?: string };
  }) => {
    if (payload.photo) {
      const form = new FormData();
      (Object.keys(payload) as (keyof typeof payload)[]).forEach((k) => {
        if (k === 'photo') return;
        const v = payload[k];
        if (Array.isArray(v)) v.forEach((item) => form.append(k, JSON.stringify(item)));
        else if (v !== undefined && v !== null) form.append(k, String(v));
      });
      form.append('photo', {
        uri: payload.photo.uri,
        name: payload.photo.name ?? 'photo.jpg',
        type: payload.photo.type ?? 'image/jpeg',
      } as unknown as Blob);
      return api.post<Product>('/marketplace/products', form);
    }
    return api.post<Product>('/marketplace/products', payload);
  },
  updateProduct: (id: string, patch: Record<string, unknown>) => {
    const photo = patch.photo as { uri: string; name?: string; type?: string } | undefined;
    if (photo) {
      const { photo: _photo, ...rest } = patch;
      const form = new FormData();
      (Object.keys(rest) as string[]).forEach((k) => {
        const v = rest[k];
        if (v !== undefined && v !== null) form.append(k, String(v));
      });
      form.append('photo', {
        uri: photo.uri,
        name: photo.name ?? 'photo.jpg',
        type: photo.type ?? 'image/jpeg',
      } as unknown as Blob);
      return api.patch<Product>(`/marketplace/products/${id}`, form);
    }
    return api.patch<Product>(`/marketplace/products/${id}`, patch);
  },
  deleteProduct: (id: string) => api.delete<void>(`/marketplace/products/${id}`),
  search: (query: string, opts?: { category?: string; city?: string; max_price?: number }) =>
    api.post<{ count: number; results: SearchResult[] }>('/marketplace/search', { query, ...opts }),
  buy: (productId: string, quantity = 1) =>
    api.post<Order>(`/marketplace/products/${productId}/buy`, { quantity }),
  shopThisLook: (postId: string) =>
    api.get<{ post_id: string; components: ShopThisLookComponent[] }>(`/marketplace/posts/${postId}/shop`),
};

// ---- Orders -------------------------------------------------------------------

export const ordersApi = {
  list: (scope: 'mine' | 'selling' = 'mine') =>
    api.get<{ count: number; results: Order[] }>(`/orders/?scope=${scope}`),
  detail: (id: string) => api.get<Order>(`/orders/${id}`),
  transition: (id: string, toStatus: string, note?: string) =>
    api.post<Order>(`/orders/${id}/transition`, { status: toStatus, note }),
};

// ---- Payments -----------------------------------------------------------------

export const paymentsApi = {
  initiate: (orderId: string, opts?: { provider?: string; idempotency_key?: string }) =>
    api.post<PaymentInit>('/payments/pay', { order_id: orderId, ...opts }),
  confirm: (paymentId: string) => api.post<PaymentConfirm>(`/payments/${paymentId}/confirm`),
};

// ---- Custom Quotes ------------------------------------------------------------

export const quotesApi = {
  list: (scope: 'mine' | 'incoming' = 'mine') =>
    api.get<{ results: QuoteRequest[] }>(`/marketplace/quotes?scope=${scope}`),
  create: (input: {
    brief: string;
    budget_inr?: number;
    designer_slug?: string;
    product_id?: string;
    outfit_id?: string;
  }) => api.post<QuoteRequest>('/marketplace/quotes', input),
  offers: (requestId: string) => api.get<{ results: QuoteOffer[] }>(`/marketplace/quotes/${requestId}/offers`),
  offer: (requestId: string, input: { price_inr: number; timeline_days?: number; notes?: string }) =>
    api.post<{ id: string; price_inr: number; timeline_days: number; status: string }>(
      `/marketplace/quotes/${requestId}/offers`, input),
  accept: (offerId: string) => api.post<Order>(`/marketplace/offers/${offerId}/accept`),
};

// ---- Buyer-Seller Chat --------------------------------------------------------

export const chatApi = {
  threads: (scope: 'buying' | 'selling' = 'buying') =>
    api.get<{ results: ChatThread[] }>(`/chat/?scope=${scope}`),
  createThread: (input: { seller_user_id: string; product_id?: string; order_id?: string; subject?: string }) =>
    api.post<ChatThreadDetail>('/chat/', input),
  thread: (id: string) => api.get<ChatThreadDetail>(`/chat/${id}/messages`),
  sendMessage: (threadId: string, body: string) =>
    api.post<ChatThreadMessage>(`/chat/${threadId}/messages`, { body }),
};

// ---- Notifications ------------------------------------------------------------

export const notificationsApi = {
  list: () => api.get<{ unread: number; results: Notification[] }>('/notifications/'),
  markRead: (id: string) => api.post<Notification>(`/notifications/${id}/read`),
  markAllRead: () => api.post<{ marked_read: number }>('/notifications/read'),
  registerDevice: (token: string, platform: 'android' | 'ios') =>
    api.post<{ registered: boolean; id: string }>('/notifications/devices', { token, platform }),
};

// ---- Designers ----------------------------------------------------------------

export const designersApi = {
  list: (params?: { city?: string; speciality?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.city) q.set('city', params.city);
    if (params?.speciality) q.set('speciality', params.speciality);
    if (params?.search) q.set('search', params.search);
    const qs = q.toString();
    return api.get<{ count: number; results: DesignerProfile[] }>(`/designers${qs ? `?${qs}` : ''}`);
  },
  detail: (slug: string) => api.get<DesignerProfile>(`/designers/${slug}`),
  me: () => api.get<DesignerProfile>('/designers/me'),
  register: (input: { studio_name: string; bio?: string; city?: string; specialities?: string[] }) =>
    api.post<DesignerProfile>('/designers/me', input),
};

// ---- Brands -------------------------------------------------------------------

export const brandsApi = {
  list: (params?: { city?: string }) => {
    const q = new URLSearchParams();
    if (params?.city) q.set('city', params.city);
    const qs = q.toString();
    return api.get<{ count: number; results: BrandProfile[] }>(`/brands${qs ? `?${qs}` : ''}`);
  },
  detail: (slug: string) => api.get<BrandProfile & { products: BrandProduct[] }>(`/brands/${slug}`),
  me: () => api.get<BrandProfile>('/brands/me'),
  register: (input: { slug: string; name: string; about?: string; website?: string; city?: string; categories?: string[] }) =>
    api.post<BrandProfile>('/brands/me', input),
};

// ---- Creators -----------------------------------------------------------------

export const creatorsApi = {
  me: () => api.get<CreatorProfile>('/creators/me'),
  register: (input: { handle: string; niche?: string; platforms?: Record<string, string>; audience_size?: number }) =>
    api.post<CreatorProfile>('/creators/me', input),
  eligibility: () => api.get<CreatorEligibility>('/creators/eligibility'),
  portfolio: (input: { title: string; media_url?: string; metrics?: Record<string, unknown> }) =>
    api.post<{ id: string; title: string }>('/creators/portfolio', input),
};

export const campaignsApi = {
  list: (scope: 'open' | 'mine' = 'open') =>
    api.get<{ count: number; results: Campaign[] }>(`/campaigns?scope=${scope}`),
  detail: (id: string) => api.get<Campaign>(`/campaigns/${id}`),
  create: (input: { title: string; brief: string; budget_inr?: number; deliverables?: string[]; min_audience?: number; payout_inr?: number }) =>
    api.post<Campaign>('/campaigns', input),
  apply: (campaignId: string, pitch: string) =>
    api.post<{ id: string; status: string }>(`/campaigns/${campaignId}/apply`, { pitch }),
  review: (applicationId: string, accept: boolean, performance?: Record<string, unknown>) =>
    api.post<{ id: string; status: string }>(`/campaigns/applications/${applicationId}/review`, { accept, performance }),
};

// ---- Social extras -------------------------------------------------------------

export const reportApi = {
  create: (input: { target_type: 'POST' | 'COMMENT' | 'USER'; target_id: string; reason: string; details?: string }) =>
    api.post<Report>('/social/reports', input),
};

export const aiMetadataApi = {
  suggest: (input: { seed?: string; occasion?: string }) =>
    api.post<{ suggested_caption: string; suggested_tags: string[] }>('/social/ai-metadata', input),
};

export type { DesignState };
