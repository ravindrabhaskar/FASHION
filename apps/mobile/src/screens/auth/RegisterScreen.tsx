import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Input } from '@/components/ui';
import { colors, spacing, typography } from '@/theme/tokens';
import { useAuth } from '@/state/auth';
import { ApiError } from '@/api/client';
import type { RootStackParamList } from '@/navigation/types';

export default function RegisterScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { signUp } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setError('');
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setLoading(true);
    try {
      await signUp(email.trim().toLowerCase(), fullName.trim(), password);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not create your account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Text style={styles.title}>Join FashionXP</Text>
      <Text style={styles.subtitle}>Style, design and earn — all in one place.</Text>

      <View style={{ marginTop: spacing.xxl }}>
        <Input onChangeText={setFullName} placeholder="Full name" value={fullName} />
        <Input
          autoCapitalize="none"
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="Email"
          value={email}
        />
        <Input
          onChangeText={setPassword}
          placeholder="Password (8+ characters)"
          secureTextEntry
          value={password}
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Button label="Create account" loading={loading} onPress={submit} style={{ marginTop: spacing.md }} />
        <Button
          label="I already have an account"
          variant="ghost"
          onPress={() => navigation.goBack()}
          style={{ marginTop: spacing.md }}
        />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  error: { ...typography.small, color: colors.danger, marginBottom: spacing.sm },
  subtitle: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  title: { ...typography.display, color: colors.textPrimary, marginTop: spacing.xxl * 3 },
  wrap: { backgroundColor: colors.ink, flex: 1, padding: spacing.xl },
});
