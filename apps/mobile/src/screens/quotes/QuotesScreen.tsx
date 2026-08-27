import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { quotesApi } from '@/api/endpoints';
import type { QuoteRequest } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function QuotesScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [requests, setRequests] = useState<QuoteRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await quotesApi.list();
      setRequests(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return (
      <Screen title="Custom Quotes">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false} title="Custom Quotes">
      <FlatList
        data={requests}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: spacing.xl }}
        renderItem={({ item }) => (
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => navigation.navigate('QuoteDetail', { requestId: item.id })}
          >
            <Card style={{ marginBottom: spacing.lg }}>
              <View style={styles.header}>
                <Text style={styles.title} numberOfLines={1}>{item.product_title || 'Custom design'}</Text>
                <Text style={styles.status}>{item.status.replace('_', ' ')}</Text>
              </View>
              <Text style={styles.brief} numberOfLines={2}>{item.brief}</Text>
              <Text style={styles.meta}>
                {item.budget_inr ? `Budget: ₹${item.budget_inr.toLocaleString('en-IN')}` : ''}
                {item.designer ? ` · Studio: ${item.designer.studio_name}` : ''}
              </Text>
              <Text style={styles.offers}>{item.offers.length} offer(s)</Text>
            </Card>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.emptyText}>No quote requests yet.</Text>
            <Text style={styles.emptySub}>Request custom pieces from designers in the marketplace.</Text>
          </View>
        }
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  brief: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  emptySub: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm, textAlign: 'center' },
  emptyText: { ...typography.body, color: colors.textSecondary },
  header: { flexDirection: 'row', justifyContent: 'space-between' },
  meta: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  offers: { ...typography.micro, color: colors.gold, marginTop: spacing.sm },
  status: { ...typography.micro, color: colors.gold, fontWeight: '700' },
  title: { ...typography.h3, color: colors.textPrimary, flex: 1 },
});