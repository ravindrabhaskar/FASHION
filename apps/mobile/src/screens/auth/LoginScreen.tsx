import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Input } from '@/components/ui';
import { colors, spacing, typography } from '@/theme/tokens';
import { useAuth } from '@/state/auth';
import { ApiError } from '@/api/client';
import type { RootStackParamList } from '@/navigation/types';

export default function LoginScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setError('');
    setLoading(true);
    try {
      await signIn(email.trim().toLowerCase(), password);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not sign in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Text style={styles.brand}>FashionXP</Text>
      <Text style={styles.tagline}>Your personal AI fashion designer.</Text>

      <View style={{ marginTop: spacing.xxl }}>
        <Input
          autoCapitalize="none"
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="Email"
          value={email}
        />
        <Input
          onChangeText={setPassword}
          placeholder="Password"
          secureTextEntry
          value={password}
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Button label="Sign in" loading={loading} onPress={submit} style={{ marginTop: spacing.md }} />
        <Button
          label="Create account"
          variant="ghost"
          onPress={() => navigation.navigate('Register')}
          style={{ marginTop: spacing.md }}
        />
        <Text style={styles.footnote}>
          Demo (after backend seeding): aisha@demo.com / demo-pass-123
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  brand: {
    ...typography.display,
    color: colors.gold,
    fontSize: 40,
    marginTop: spacing.xxl * 3,
    textAlign: 'center',
  },
  error: { ...typography.small, color: colors.danger, marginBottom: spacing.sm, textAlign: 'center' },
  footnote: {
    ...typography.small,
    color: colors.textMuted,
    marginTop: spacing.xl,
    textAlign: 'center',
  },
  tagline: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
  wrap: { backgroundColor: colors.ink, flex: 1, padding: spacing.xl },
});
