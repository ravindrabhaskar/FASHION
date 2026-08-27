import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { quotesApi } from '@/api/endpoints';
import type { QuoteRequest } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { ApiError } from '@/api/client';

export default function QuoteRequestScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'QuoteRequestScreen'>>();
  const navigation = useNavigation();
  const { productId, designerSlug, outfitId } = route.params ?? {};
  const [brief, setBrief] = useState('');
  const [budget, setBudget] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!brief.trim()) {
      Alert.alert('Brief required', 'Describe what you want made.');
      return;
    }
    setSubmitting(true);
    try {
      await quotesApi.create({
        brief: brief.trim(),
        budget_inr: budget ? parseInt(budget, 10) : undefined,
        product_id: productId,
        designer_slug: designerSlug,
        outfit_id: outfitId,
      });
      Alert.alert('Request sent!', 'Designers can now send you quotes.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not send request.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Screen title="Custom Quote">
      <View style={{ padding: spacing.xl }}>
        <Text style={styles.label}>What do you want made?</Text>
        <TextInput
          style={[styles.input, { minHeight: 110 }]}
          placeholder="Describe the garment, fabric, details..."
          placeholderTextColor={colors.textMuted}
          value={brief}
          onChangeText={setBrief}
          multiline
          numberOfLines={4}
        />

        <Text style={styles.label}>Budget (₹, optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. 5000"
          placeholderTextColor={colors.textMuted}
          value={budget}
          onChangeText={setBudget}
          keyboardType="number-pad"
        />

        <Button
          label="Send request"
          variant="gold"
          loading={submitting}
          onPress={() => void submit()}
          style={{ marginTop: spacing.xl }}
        />
      </View>
    </Screen>
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
});