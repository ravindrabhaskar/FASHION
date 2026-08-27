import React, { useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { campaignsApi } from '@/api/endpoints';
import { ApiError } from '@/api/client';

export default function CreateCampaignScreen() {
  const navigation = useNavigation();
  const [title, setTitle] = useState('');
  const [brief, setBrief] = useState('');
  const [budget, setBudget] = useState('');
  const [payout, setPayout] = useState('');
  const [minAudience, setMinAudience] = useState('');
  const [deliverables, setDeliverables] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!title.trim() || !brief.trim()) {
      Alert.alert('Required', 'Title and brief are required.');
      return;
    }
    setSubmitting(true);
    try {
      await campaignsApi.create({
        title: title.trim(),
        brief: brief.trim(),
        budget_inr: budget ? parseInt(budget, 10) : 0,
        payout_inr: payout ? parseInt(payout, 10) : undefined,
        min_audience: minAudience ? parseInt(minAudience, 10) : 0,
        deliverables: deliverables.split(',').map((d) => d.trim()).filter(Boolean),
      });
      Alert.alert('Campaign created!', 'Creators can now apply.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not create campaign.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Screen title="New Campaign">
        <View style={{ padding: spacing.xl }}>
          <Text style={styles.label}>Title *</Text>
          <TextInput style={styles.input} placeholder="e.g. Summer ethnic collection collab" placeholderTextColor={colors.textMuted} value={title} onChangeText={setTitle} />

          <Text style={styles.label}>Brief *</Text>
          <TextInput style={[styles.input, { minHeight: 90 }]} placeholder="Describe the campaign..." placeholderTextColor={colors.textMuted} value={brief} onChangeText={setBrief} multiline />

          <Text style={styles.label}>Budget (₹)</Text>
          <TextInput style={styles.input} placeholder="e.g. 50000" placeholderTextColor={colors.textMuted} value={budget} onChangeText={setBudget} keyboardType="number-pad" />

          <Text style={styles.label}>Payout per creator (₹)</Text>
          <TextInput style={styles.input} placeholder="e.g. 5000" placeholderTextColor={colors.textMuted} value={payout} onChangeText={setPayout} keyboardType="number-pad" />

          <Text style={styles.label}>Min audience</Text>
          <TextInput style={styles.input} placeholder="e.g. 10000" placeholderTextColor={colors.textMuted} value={minAudience} onChangeText={setMinAudience} keyboardType="number-pad" />

          <Text style={styles.label}>Deliverables (comma separated)</Text>
          <TextInput style={styles.input} placeholder="e.g. 2 reels, 4 posts" placeholderTextColor={colors.textMuted} value={deliverables} onChangeText={setDeliverables} />

          <Button label="Create campaign" variant="gold" loading={submitting} onPress={() => void submit()} style={{ marginTop: spacing.xl }} />
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
  wrap: { backgroundColor: colors.ink, flex: 1 },
});