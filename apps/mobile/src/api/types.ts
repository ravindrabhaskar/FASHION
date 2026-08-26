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
