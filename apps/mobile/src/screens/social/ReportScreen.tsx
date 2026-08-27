import React, { useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button, Chip } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { reportApi } from '@/api/endpoints';
import { ApiError } from '@/api/client';
import type { RootStackParamList } from '@/navigation/types';

const REASONS = ['Spam', 'Harassment', 'Inappropriate content', 'Copyright violation', 'Misinformation', 'Other'];

export default function ReportScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'Report'>>();
  const navigation = useNavigation();
  const { targetType, targetId } = route.params;
  const [reason, setReason] = useState('Spam');
  const [details, setDetails] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    try {
      await reportApi.create({
        target_type: targetType,
        target_id: targetId,
        reason,
        details: details.trim() || undefined,
      });
      Alert.alert('Report submitted', 'Our moderation team will review this.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not submit report.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Screen title="Report">
        <View style={{ padding: spacing.xl }}>
          <Text style={styles.label}>Reason</Text>
          {REASONS.map((r) => (
            <Chip key={r} label={r} selected={reason === r} onPress={() => setReason(r)} />
          ))}

          <Text style={styles.label}>Details (optional)</Text>
          <TextInput
            style={[styles.input, { minHeight: 90 }]}
            placeholder="Anything we should know..."
            placeholderTextColor={colors.textMuted}
            value={details}
            onChangeText={setDetails}
            multiline
          />

          <Button label="Submit report" variant="danger" loading={submitting} onPress={() => void submit()} style={{ marginTop: spacing.xl }} />
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