export type Role = 'USER' | 'CREATOR' | 'DESIGNER' | 'BRAND' | 'MODERATOR' | 'ADMIN' | 'SUPER_ADMIN';

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  role: Role;
  status: string;
  avatar: string;
  onboarding_completed_at: string | null;
  onboarding_completed: boolean;
}

export interface ColorSwatch {
  name: string;
  hex: string;
  role: 'primary' | 'secondary' | 'accent' | 'neutral';
}

export interface GarmentSpec {
  category: string;
  description: string;
  color?: string;
  fabric?: string;
  pattern?: string;
  details?: string[];
}

export interface OutfitComponent {
  slot: string;
  item: GarmentSpec;
}

export interface RecommendationResult {
  headline: string;
  explanation: string;
  occasion_fit_notes?: string;
  palette: ColorSwatch[];
  outfit_components: OutfitComponent[];
  accessories: string[];
  footwear_note?: string;
  budget_total_inr?: number | null;
  budget_allocation?: { component: string; amount_inr: number }[];
  styling_tips?: string[];
  confidence?: number;
  alternatives?: string[];
}

export interface DesignState {
  garment_type: string;
  base_color: string;
  accent_color: string;
  fabric: string;
  sleeve_style: string;
  collar_neckline: string;
  length: string;
  pattern: string;
  embroidery_level: 'none' | 'subtle' | 'moderate' | 'heavy';
  traditional_modern_balance: number;
  formality: number;
  weather_suitability: string;
  target_budget_inr: number | null;
  accessories: string[];
  notes: string;
}

export interface Outfit {
  id: string;
  source: 'STYLIST' | 'DESIGNER' | 'CUSTOMIZE' | 'WARDROBE';
  status: 'QUEUED' | 'GENERATING' | 'COMPLETED' | 'FAILED';
  title: string;
  occasion: string;
  budget_inr: number | null;
  recommendation: RecommendationResult;
  design_state: Partial<DesignState> & { wardrobe_item_ids?: string[] };
  image: string;
  image_prompt: string;
  version: number;
  saved: boolean;
  failed_reason: string;
  created_at: string;
}

export interface Occasion {
  slug: string;
  label: string;
  description: string;
  formality: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  changes: string[];
  design_version: number | null;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  occasion: string;
  budget_inr: number | null;
  design_state: Partial<DesignState>;
  messages: ChatMessage[];
  updated_at: string;
}

export interface StyleProfile {
  preferred_styles: string[];
  favorite_colors: string[];
  avoided_colors: string[];
  fit_preference: string;
  budget_min: number | null;
  budget_max: number | null;
  clothing_preferences: Record<string, unknown>;
  common_occasions: string[];
  traditional_modern_balance: number;
  completion: number;
}

export interface Entitlements {
  tier: string | null;
  is_paid: boolean;
  ai_text_daily_limit: number;
  ai_image_monthly_limit: number;
  max_saved_looks: number;
  wardrobe_item_limit: number;
  designer_chat_enabled: boolean;
}

export type WardrobeCategory =
  | 'tops'
  | 'bottoms'
  | 'dresses'
  | 'outerwear'
  | 'footwear'
  | 'accessories'
  | 'ethnic'
  | 'other';

export interface WardrobeItem {
  id: string;
  name: string;
  category: WardrobeCategory;
  category_label?: string;
  status: 'PENDING' | 'READY' | 'FAILED';
  color_primary: string;
  color_hex: string;
  favorite: boolean;
  times_worn: number;
  last_worn_at: string | null;
  image: string;
  fabric?: string;
  pattern?: string;
  formality?: number;
  seasons?: string[];
  occasion_slugs?: string[];
  style_tags?: string[];
  notes?: string;
  archived?: boolean;
  created_at: string;
}

export interface DailySuggestion {
  date: string;
  city: string;
  weather: { temp_c: number; condition: string; is_mock: boolean; source: string } | null;
  occasion: string;
  headline: string;
  tips: string[];
  closet_outfit: {
    recommendation: RecommendationResult;
    items: Pick<WardrobeItem, 'id' | 'name' | 'category' | 'color_primary' | 'color_hex' | 'image'>[];
  } | null;
}

// ---- Social -------------------------------------------------------------------

export interface SocialPost {
  id: string;
  user_id: string;
  user_name: string;
  user_avatar: string;
  caption: string;
  occasion: string;
  image: string;
  like_count: number;
  comment_count: number;
  saved_count: number;
  liked: boolean;
  saved: boolean;
  item_tags: { id: string; label: string; position: number }[];
  created_at: string;
}

export interface SocialComment {
  id: string;
  user_id: string;
  user_name: string;
  text: string;
  created_at: string;
}

export interface FeedPage {
  count: number;
  results: SocialPost[];
  has_more: boolean;
}

export interface PublicProfile {
  id: string;
  full_name: string;
  avatar: string;
  bio: string;
  follower_count: number;
  following_count: number;
  post_count: number;
  is_following: boolean;
  recent_posts: SocialPost[];
}

// ---- FashionXP / Gamification -------------------------------------------------

export interface XPDashboard {
  total_xp: number;
  level: string;
  level_number: number;
  next_threshold: number;
  progress_percent: number;
  earned_today: number;
  daily_cap: number;
  badges: XPBadge[];
  recent_transactions: XPTransaction[];
}

export interface XPBadge {
  code: string;
  name: string;
  icon: string;
  awarded_at: string;
}

export interface XPTransaction {
  amount: number;
  reason: string;
  balance_after: number;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  user_name: string;
  user_avatar: string;
  total_xp: number;
  level: string;
}

export interface Challenge {
  id: string;
  slug: string;
  title: string;
  description: string;
  occasion_slug: string;
  hashtag: string;
  starts_at: string;
  ends_at: string;
  xp_reward: number;
  status: 'UPCOMING' | 'LIVE' | 'CLOSED';
  enrolled: boolean;
  my_score: number | null;
  entry_count: number;
}

export interface Reward {
  code: string;
  name: string;
  description: string;
  cost_xp: number;
  stock: number;
  partner: string;
  affordable: boolean;
}

export interface Redemption {
  id: string;
  reward: string;
  reward_name: string;
  cost_xp: number;
  status: string;
  created_at: string;
}

// ---- Marketplace --------------------------------------------------------------

export interface Product {
  id: string;
  title: string;
  description: string;
  category: string;
  price_inr: number;
  sale_price_inr: number | null;
  city: string;
  fabric: string;
  colors: string[];
  is_customizable: boolean;
  ready_to_ship: boolean;
  in_stock: boolean;
  seller_type: string;
  seller_user_id: string;
  seller_name: string;
  image: string;
  variants: ProductVariant[];
}

export interface ProductVariant {
  id: string;
  name: string;
  value: string;
  price_delta_inr: number;
  stock: number;
}

export type SearchResult = Product & { relevance: number };

export interface QuoteRequest {
  id: string;
  brief: string;
  budget_inr: number | null;
  status: string;
  designer: { slug: string; studio_name: string } | null;
  product_title: string;
  offers: QuoteOffer[];
  created_at: string;
}

export interface QuoteOffer {
  id: string;
  price_inr: number;
  timeline_days: number;
  notes: string;
  status: string;
}

// ---- Orders -------------------------------------------------------------------

export interface Order {
  id: string;
  title: string;
  status: string;
  quantity: number;
  amount_inr: number;
  variant_snapshot: Record<string, string>;
  product_id: string | null;
  seller_user_id: string;
  seller_name: string;
  customer_name: string;
  shipping_address: Record<string, unknown>;
  notes: string;
  created_at: string;
  events?: OrderEvent[];
}

export interface OrderEvent {
  from_status: string;
  to_status: string;
  note: string;
  created_at: string;
}

// ---- Buyer-Seller Chat --------------------------------------------------------

export interface ChatThread {
  id: string;
  subject: string;
  other_user_name: string;
  other_user_id: string;
  last_message: string;
  last_message_at: string;
  unread_count: number;
}

export interface ChatThreadMessage {
  id: string;
  sender_id: string;
  sender_name: string;
  body: string;
  read_at: string | null;
  created_at: string;
}

export interface ChatThreadDetail extends ChatThread {
  messages: ChatThreadMessage[];
}

// ---- Notifications ------------------------------------------------------------

export interface Notification {
  id: string;
  type: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

// ---- Designers ----------------------------------------------------------------

export interface DesignerProfile {
  id: string;
  user_id: string;
  slug: string;
  studio_name: string;
  tagline: string;
  city: string;
  specialities: string[];
  verified: boolean;
  is_accepting_custom_requests: boolean;
  product_count: number;
  bio?: string;
  experience_years?: number;
  products?: {
    id: string;
    title: string;
    price_inr: number;
    category: string;
    image: string;
    is_customizable: boolean;
  }[];
}

// ---- Payments -----------------------------------------------------------------

export interface PaymentInit {
  payment_id: string;
  provider: string;
  provider_order_id: string;
  amount_inr: number;
  status: string;
  confirm_url: string;
}

export interface PaymentConfirm {
  status: string;
  order_status: string;
}

// ---- Brands -------------------------------------------------------------------

export interface BrandProfile {
  id: string;
  slug: string;
  name: string;
  city: string;
  categories: string[];
  verified: boolean;
  product_count: number;
  about?: string;
  website?: string;
  products?: BrandProduct[];
}

export interface BrandProduct {
  id: string;
  title: string;
  price_inr: number;
  category: string;
  image: string;
}

// ---- Creators -----------------------------------------------------------------

export interface CreatorProfile {
  id: string;
  user_id: string;
  handle: string;
  niche: string;
  audience_size: number;
  is_eligible: boolean;
  stats: {
    posts_published?: number;
    likes_received?: number;
    comments_received?: number;
    saves_received?: number;
    engagement_rate?: number;
  };
  portfolio: {
    id: string;
    title: string;
    media_url: string;
    metrics: Record<string, unknown>;
  }[];
}

export interface CreatorEligibility {
  min_audience: number;
  min_posts: number;
  posts_published: number;
  qualifies: boolean;
}

// ---- Campaigns ----------------------------------------------------------------

export interface Campaign {
  id: string;
  title: string;
  brief: string;
  deliverables: string[];
  budget_inr: number;
  payout_inr: number | null;
  min_audience: number;
  status: string;
  brand_name: string;
  application_count: number;
  created_at: string;
  applications?: CampaignApplication[];
  my_application_status?: string | null;
}

export interface CampaignApplication {
  id: string;
  handle: string;
  audience_size: number;
  pitch: string;
  status: string;
  performance: Record<string, unknown>;
}

// ---- Reports ------------------------------------------------------------------

export interface Report {
  id: string;
  status: string;
}

// ---- Shop This Look ------------------------------------------------------------

export interface ShopThisLookComponent {
  id: string;
  label: string;
  position: number;
  product: Product | null;
  similar_products: Product[];
}

// ---- Phase 7: Trends, Multilingual, Try-on -------------------------------------

export type LanguageCode =
  | 'en' | 'hi' | 'bn' | 'ta' | 'te' | 'mr' | 'gu' | 'kn' | 'ur';

export interface TrendingEntry {
  value: string;
  count: number;
  label: string;
}

export interface TrendsResult {
  colors: TrendingEntry[];
  fabrics: TrendingEntry[];
  categories: TrendingEntry[];
  hashtags: TrendingEntry[];
  cities: TrendingEntry[];
  generated_at: string;
}

export interface I18nStrings {
  locale: string;
  supported: Record<string, string>;
  strings: Record<string, string>;
}

export interface TranslateResult {
  text: string;
  target: string;
  source: string;
  mode: string;
}

export interface OTPRequestResult {
  phone: string;
  expires_in_seconds: number;
  dev_code?: string;
}
