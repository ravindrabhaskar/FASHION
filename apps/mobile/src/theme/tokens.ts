/**
 * FashionXP design tokens — premium fashion identity.
 * Dark editorial base with warm gold accents; fashion-forward, not generic.
 */
export const colors = {
  // Base
  ink: '#0B0B0F',
  inkElevated: '#141419',
  inkCard: '#1B1B22',
  inkBorder: '#2A2A33',

  // Text
  textPrimary: '#F5F1EA',
  textSecondary: '#A8A29B',
  textMuted: '#6E6862',

  // Accent — warm champagne gold (fashion house feel)
  gold: '#C9A96E',
  goldSoft: 'rgba(201, 169, 110, 0.16)',
  blush: '#D9A5A0',
  sage: '#9CAF88',

  // Feedback
  success: '#7FB069',
  danger: '#E06C5A',
  warning: '#D9B36A',

  // Surfaces on light contexts
  white: '#FFFFFF',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radii = {
  sm: 10,
  md: 16,
  lg: 24,
  pill: 999,
} as const;

export const typography = {
  display: { fontSize: 32, fontWeight: '700' as const, letterSpacing: -0.5 },
  h1: { fontSize: 26, fontWeight: '700' as const, letterSpacing: -0.3 },
  h2: { fontSize: 20, fontWeight: '600' as const },
  h3: { fontSize: 16, fontWeight: '600' as const },
  body: { fontSize: 15, fontWeight: '400' as const, lineHeight: 22 },
  small: { fontSize: 13, fontWeight: '400' as const, lineHeight: 18 },
  micro: { fontSize: 11, fontWeight: '500' as const, letterSpacing: 0.6 },
};

export const shadow = {
  card: {
    shadowColor: '#000000',
    shadowOpacity: 0.35,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 6 },
    elevation: 6,
  },
};
