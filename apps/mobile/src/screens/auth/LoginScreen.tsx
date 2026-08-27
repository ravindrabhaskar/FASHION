import React, { useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Input } from '@/components/ui';
import { colors, spacing, typography } from '@/theme/tokens';
import { useAuth } from '@/state/auth';
import { useI18n } from '@/i18n';
import { ApiError } from '@/api/client';
import { authApi } from '@/api/endpoints';
import type { RootStackParamList } from '@/navigation/types';

export default function LoginScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { signIn, signInWithOtp, signInWithProvider } = useAuth();
  const { t } = useI18n();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState<'password' | 'otp'>('password');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [devCode, setDevCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setError('');
    setLoading(true);
    try {
      if (mode === 'password') {
        await signIn(email.trim().toLowerCase(), password);
      } else {
        await signInWithOtp(phone.trim(), code.trim());
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not sign in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const sendCode = async () => {
    setError('');
    setLoading(true);
    try {
      const result = await authApi.requestOtp(phone.trim());
      setDevCode(result.dev_code ?? '');
      setOtpSent(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not send the code.');
    } finally {
      setLoading(false);
    }
  };

  const social = async (provider: 'google' | 'apple') => {
    setError('');
    setLoading(true);
    try {
      const token = await getProviderToken(provider);
      if (!token) {
        setError(
          `${provider === 'google' ? 'Google' : 'Apple'} sign-in needs a client id configured in .env (see EXPO_PUBLIC_GOOGLE_CLIENT_ID).`,
        );
        return;
      }
      await signInWithProvider(provider, token);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : `${provider} sign-in failed.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: spacing.xxl }}>
        <Text style={styles.brand}>FashionXP</Text>
        <Text style={styles.tagline}>{t('auth.tagline')}</Text>

        <View style={{ marginTop: spacing.xxl }}>
          {mode === 'password' ? (
            <>
              <Input
                autoCapitalize="none"
                keyboardType="email-address"
                onChangeText={setEmail}
                placeholder={t('auth.email')}
                value={email}
              />
              <Input
                onChangeText={setPassword}
                placeholder={t('auth.password')}
                secureTextEntry
                value={password}
              />
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <Button label={t('auth.sign_in')} loading={loading} onPress={submit} style={{ marginTop: spacing.md }} />
              <Button
                label="Switch to SMS login"
                variant="ghost"
                onPress={() => { setMode('otp'); setError(''); }}
                style={{ marginTop: spacing.sm }}
              />
            </>
          ) : (
            <>
              <Input
                keyboardType="phone-pad"
                onChangeText={setPhone}
                placeholder={t('auth.phone')}
                value={phone}
              />
              {otpSent ? (
                <>
                  <Input
                    keyboardType="number-pad"
                    onChangeText={setCode}
                    placeholder={t('auth.otp_code')}
                    value={code}
                  />
                  {devCode ? (
                    <Text style={styles.devHint}>Dev code (DEBUG build): {devCode}</Text>
                  ) : null}
                  <Button
                    label={t('auth.verify')}
                    loading={loading}
                    onPress={submit}
                    style={{ marginTop: spacing.md }}
                  />
                </>
              ) : null}
              {!otpSent ? (
                <Button
                  label={t('auth.send_code')}
                  loading={loading}
                  onPress={sendCode}
                  style={{ marginTop: spacing.md }}
                />
              ) : null}
              <Button
                label="Send code again"
                variant="ghost"
                disabled={!otpSent}
                onPress={() => { setOtpSent(false); setCode(''); setError(''); }}
                style={{ marginTop: spacing.sm }}
              />
              <Button
                label="Use email & password instead"
                variant="ghost"
                onPress={() => { setMode('password'); setError(''); }}
                style={{ marginTop: spacing.sm }}
              />
            </>
          )}

          <Text style={styles.or}>or</Text>

          <Button label={t('auth.google')} variant="gold" onPress={() => social('google')} style={{ marginTop: spacing.sm }} />
          <Button label={t('auth.apple')} variant="ghost" onPress={() => social('apple')} style={{ marginTop: spacing.md }} />
          <Button
            label={t('auth.create_account')}
            variant="ghost"
            onPress={() => navigation.navigate('Register')}
            style={{ marginTop: spacing.md }}
          />
          <Text style={styles.footnote}>
            Demo (after backend seeding): aisha@demo.com / demo-pass-123
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

async function getProviderToken(provider: 'google' | 'apple'): Promise<string | null> {
  if (provider === 'google') {
    const clientId = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) return null;
    try {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const AuthSession = require('expo-auth-session');
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const WebBrowser = require('expo-web-browser');
      WebBrowser.maybeCompleteAuthSession();
      const request = AuthSession.createAuthRequest(
        {
          clientId,
          scopes: ['openid', 'email', 'profile'],
          responseType: 'id_token',
          nonce: Math.random().toString(36).slice(2),
        },
        {
          // eslint-disable-next-line no-empty
          discovery: {
            authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
            tokenEndpoint: 'https://oauth2.googleapis.com/token',
          },
        },
      );
      const result = await request.promptAsync();
      if (result?.type === 'success' && result.params?.id_token) {
        return result.params.id_token;
      }
    } catch {
      return null;
    }
    return null;
  }
  // Apple requires an iOS native build (expo-apple-authentication).
  if (Platform.OS !== 'ios') return null;
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const AppleAuthentication = require('expo-apple-authentication');
    const { identityToken } = await AppleAuthentication.signInAsync({
      requestedScopes: [AppleAuthentication.AppleAuthenticationScope.FULL_NAME, AppleAuthentication.AppleAuthenticationScope.EMAIL],
    });
    return identityToken ?? null;
  } catch {
    return null;
  }
}

const styles = StyleSheet.create({
  brand: {
    ...typography.display,
    color: colors.gold,
    fontSize: 40,
    marginTop: spacing.xxl * 3,
    textAlign: 'center',
  },
  devHint: { ...typography.small, color: colors.gold, marginBottom: spacing.sm, textAlign: 'center' },
  error: { ...typography.small, color: colors.danger, marginBottom: spacing.sm, textAlign: 'center' },
  footnote: {
    ...typography.small,
    color: colors.textMuted,
    marginTop: spacing.xl,
    textAlign: 'center',
  },
  or: { ...typography.micro, color: colors.textMuted, marginVertical: spacing.lg, textAlign: 'center' },
  tagline: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
  wrap: { backgroundColor: colors.ink, flex: 1, padding: spacing.xl },
});