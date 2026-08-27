import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { i18nApi, profileApi } from '@/api/endpoints';
import type { LanguageCode } from '@/api/types';

const LOCALE_KEY = 'fashionxp.locale';

export const LANGUAGES: Record<LanguageCode, string> = {
  en: 'English',
  hi: 'हिन्दी (Hindi)',
  bn: 'বাংলা (Bengali)',
  ta: 'தமிழ் (Tamil)',
  te: 'తెలుగు (Telugu)',
  mr: 'मराठी (Marathi)',
  gu: 'ગુજરાતી (Gujarati)',
  kn: 'ಕನ್ನಡ (Kannada)',
  ur: 'اردو (Urdu)',
};

// Local English fallback so the app never renders bare keys offline.
const EN_FALLBACK: Record<string, string> = {
  'action.save': 'Save',
  'action.cancel': 'Cancel',
  'action.back': 'Back',
  'action.send': 'Send',
  'action.share': 'Share',
  'action.edit': 'Edit',
  'action.delete': 'Delete',
  'action.retry': 'Try again',
  'action.continue': 'Continue',
  'auth.sign_in': 'Sign in',
  'auth.create_account': 'Create account',
  'auth.email': 'Email',
  'auth.password': 'Password',
  'auth.phone': 'Phone number',
  'auth.otp_code': 'Enter the 6-digit code',
  'auth.send_code': 'Send code',
  'auth.verify': 'Verify & sign in',
  'auth.google': 'Continue with Google',
  'auth.apple': 'Continue with Apple',
  'auth.sms': 'Sign in with SMS',
  'auth.tagline': 'Your personal AI fashion designer.',
  'nav.home': 'Home',
  'nav.social': 'Social',
  'nav.stylist': 'Stylist',
  'nav.shop': 'Shop',
  'nav.wardrobe': 'Wardrobe',
  'nav.profile': 'Profile',
  'home.trending': 'Trending now',
  'home.custom_quotes': 'Custom quotes',
  'home.earn_xp': 'Earn XP & rewards',
  'home.my_looks': 'My saved looks',
  'home.chat': 'AI Designer chat',
  'mp.title': 'Marketplace',
  'mp.buy_now': 'Buy now',
  'mp.request_quote': 'Request custom quote',
  'mp.chat_seller': 'Chat with seller',
  'mp.sell': 'Sell your designs',
  'mp.my_products': 'My products',
  'wd.title': 'Wardrobe',
  'wd.add_item': 'Add item',
  'wd.daily_pick': "Today's pick",
  'pf.language': 'Language',
  'pf.orders': 'My orders',
  'pf.quotes': 'Custom quotes',
  'pf.brands': 'Brands',
  'pf.creators': 'Creators & campaigns',
  'xp.title': 'FashionXP',
  'xp.leaderboard': 'Leaderboard',
  'xp.challenges': 'Challenges',
  'xp.rewards': 'Rewards',
  'nx.empty': 'No notifications yet',
  'tr.header': "What's trending",
  'tr.colors': 'Colours in demand',
  'tr.fabrics': 'Fabrics trending',
  'tr.categories': 'Top categories',
  'tr.locations': 'Trending cities',
};

interface I18nState {
  locale: string;
  supported: Record<string, string>;
  t: (key: string) => string;
  setLocale: (locale: string) => Promise<void>;
}

const I18nContext = createContext<I18nState>(null as unknown as I18nState);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState('en');
  const [supported, setSupported] = useState<Record<string, string>>(LANGUAGES);
  const stringsRef = React.useRef<Record<string, string>>({ ...EN_FALLBACK });

  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem(LOCALE_KEY);
        const preferred = stored ?? 'en';
        setLocaleState(preferred);
        const data = await i18nApi.strings(preferred);
        stringsRef.current = { ...EN_FALLBACK, ...data.strings };
        setSupported(data.supported ?? LANGUAGES);
      } catch {
        stringsRef.current = { ...EN_FALLBACK };
      }
    })();
  }, []);

  const t = useCallback((key: string) => stringsRef.current[key] ?? EN_FALLBACK[key] ?? key, []);
  const setLocale = useCallback(async (next: string) => {
    setLocaleState(next);
    await AsyncStorage.setItem(LOCALE_KEY, next);
    try {
      const data = await i18nApi.strings(next);
      stringsRef.current = { ...EN_FALLBACK, ...data.strings };
      setSupported(data.supported ?? LANGUAGES);
      void profileApi.patchMe({ language: next }).catch(() => undefined);
    } catch {
      stringsRef.current = { ...EN_FALLBACK };
    }
  }, []);

  const value = useMemo<I18nState>(() => ({ locale, supported, t, setLocale }), [locale, supported, t, setLocale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}