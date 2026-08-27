import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { api, tokenStore } from '@/api/client';
import { authApi } from '@/api/endpoints';
import type { User } from '@/api/types';
import { colors } from '@/theme/tokens';
import { registerPushDevice } from '@/state/push';

interface AuthState {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, fullName: string, password: string) => Promise<void>;
  signInWithOtp: (phone: string, code: string, fullName?: string) => Promise<void>;
  signInWithProvider: (provider: 'google' | 'apple', idToken: string) => Promise<void>;
  signOutAll: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState>(null as unknown as AuthState);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const persistSession = useCallback((access: string, refresh: string, nextUser: User) => {
    // fire-and-forget persistence
    void tokenStore.save(access, refresh);
    setUser(nextUser);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const access = await tokenStore.getAccess();
        if (!access) return;
        const me = await authApi.me();
        setUser(me);
        void registerPushDevice();
      } catch {
        await tokenStore.clear();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      signIn: async (email, password) => {
        const data = await authApi.login(email, password);
        persistSession(data.access, data.refresh, data.user);
        void registerPushDevice();
      },
      signUp: async (email, fullName, password) => {
        const data = await authApi.register(email, fullName, password);
        persistSession(data.access, data.refresh, data.user);
        void registerPushDevice();
      },
      signInWithOtp: async (phone, code, fullName) => {
        const data = await authApi.loginWithOtp(phone, code, fullName);
        persistSession(data.access, data.refresh, data.user);
        void registerPushDevice();
      },
      signInWithProvider: async (provider, idToken) => {
        const data = await authApi.socialLogin(provider, idToken);
        persistSession(data.access, data.refresh, data.user);
        void registerPushDevice();
      },
      signOutAll: async () => {
        try {
          await authApi.logoutAll();
        } catch {
          /* best-effort */
        }
        await tokenStore.clear();
        setUser(null);
      },
      refreshUser: async () => setUser(await authApi.me()),
    }),
    [user, loading, persistSession],
  );

  if (loading) {
    return (
      <View style={{ alignItems: 'center', backgroundColor: colors.ink, flex: 1, justifyContent: 'center' }}>
        <ActivityIndicator color={colors.gold} size="large" />
      </View>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

// Re-exported for screens that need direct fetches with credentials.
export { api };
