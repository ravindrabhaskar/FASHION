import React, { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { creatorsApi } from '@/api/endpoints';
import { ApiError } from '@/api/client';

export default function BecomeCreatorScreen() {
  const navigation = useNavigation();
  const [handle, setHandle] = useState('');
  const [niche, setNiche] = useState('');
  const [audience, setAudience] = useState('');
  const [qualifies, setQualifies] = useState<boolean | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    creatorsApi.eligibility().then((res) => setQualifies(res.qualifies)).catch(() => undefined);
  }, []);

  const submit = async () => {
    if (!handle.trim()) {
      Alert.alert('Handle required');
      return;
    }
    setSubmitting(true);
    try {
      await creatorsApi.register({
        handle: handle.trim().replace('@', ''),
        niche: niche.trim(),
        audience_size: audience ? parseInt(audience, 10) : 0,
      });
      Alert.alert('Welcome, creator!', 'Your creator profile is live.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not register.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Screen title="Become a creator">
        <View style={{ padding: spacing.xl }}>
          {qualifies !== null && (
            <View style={qualifies ? styles.qualifyBadge : styles.qualifyBadgeOff}>
              <Text style={qualifies ? styles.qualifyTextOn : styles.qualifyTextOff}>
                {qualifies
                  ? '✓ You meet the eligibility threshold'
                  : 'Publish more posts to become eligible for campaigns'}
              </Text>
            </View>
          )}

          <Text style={styles.label}>Handle *</Text>
          <TextInput style={styles.input} placeholder="e.g. yourstyle" placeholderTextColor={colors.textMuted} value={handle} onChangeText={setHandle} autoCapitalize="none" />

          <Text style={styles.label}>Niche</Text>
          <TextInput style={styles.input} placeholder="e.g. ethnic fashion, streetwear" placeholderTextColor={colors.textMuted} value={niche} onChangeText={setNiche} />

          <Text style={styles.label}>Audience size</Text>
          <TextInput style={styles.input} placeholder="e.g. 10000" placeholderTextColor={colors.textMuted} value={audience} onChangeText={setAudience} keyboardType="number-pad" />

          <Button label="Register creator" variant="gold" loading={submitting} onPress={() => void submit()} style={{ marginTop: spacing.xl }} />
        </View>
      </Screen>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  input: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    color: colors.textPrimary,
    fontSize: 15,
    marginBottom: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: 14,
    textAlignVertical: 'top',
  },
  label: { ...typography.small, color: colors.textSecondary, marginBottom: spacing.sm, marginTop: spacing.md },
  qualifyBadge: {
    backgroundColor: colors.goldSoft,
    borderRadius: radii.md,
    borderColor: colors.gold,
    borderWidth: 1,
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  qualifyBadgeOff: {
    backgroundColor: colors.inkElevated,
    borderRadius: radii.md,
    borderColor: colors.inkBorder,
    borderWidth: 1,
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  qualifyTextOff: { ...typography.small, color: colors.textMuted },
  qualifyTextOn: { ...typography.small, color: colors.gold },
  wrap: { backgroundColor: colors.ink, flex: 1 },
});