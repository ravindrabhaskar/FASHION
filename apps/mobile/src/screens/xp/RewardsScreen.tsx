import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, StyleSheet, Text, View } from 'react-native';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { rewardsApi } from '@/api/endpoints';
import type { Reward } from '@/api/types';
import { ApiError } from '@/api/client';

export default function RewardsScreen() {
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [redeeming, setRedeeming] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await rewardsApi.list();
      setRewards(data.results);
      setBalance(data.balance);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const redeem = async (code: string) => {
    setRedeeming(code);
    try {
      const result = await rewardsApi.redeem(code);
      setBalance(result.balance_after);
      Alert.alert('Redeemed!', `You spent ${result.cost_xp} XP. Check your redemptions.`);
      void load();
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not redeem reward.');
    } finally {
      setRedeeming(null);
    }
  };

  if (loading) {
    return (
      <Screen title="Rewards">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false} title="Rewards" subtitle={`${balance.toLocaleString()} XP available`}>
      <FlatList
        data={rewards}
        keyExtractor={(item) => item.code}
        contentContainerStyle={{ padding: spacing.xl }}
        renderItem={({ item }) => (
          <Card style={{ marginBottom: spacing.lg }}>
            <View style={styles.header}>
              <Text style={styles.name}>{item.name}</Text>
              <Text style={styles.cost}>{item.cost_xp} XP</Text>
            </View>
            <Text style={styles.description}>{item.description}</Text>
            {item.partner ? <Text style={styles.partner}>by {item.partner}</Text> : null}
            <View style={styles.footer}>
              <Text style={styles.stock}>
                {item.stock > 0 ? `${item.stock} left` : 'Out of stock'}
              </Text>
              <Button
                label={item.affordable ? 'Redeem' : 'Not enough XP'}
                variant={item.affordable ? 'gold' : 'ghost'}
                disabled={!item.affordable || item.stock <= 0 || redeeming === item.code}
                loading={redeeming === item.code}
                onPress={() => void redeem(item.code)}
                style={{ minWidth: 120 }}
              />
            </View>
          </Card>
        )}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.emptyText}>No rewards available yet.</Text>
          </View>
        }
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  cost: { ...typography.h3, color: colors.gold },
  description: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  emptyText: { ...typography.body, color: colors.textSecondary },
  footer: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.md },
  header: { flexDirection: 'row', justifyContent: 'space-between' },
  name: { ...typography.h3, color: colors.textPrimary, flex: 1 },
  partner: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  stock: { ...typography.small, color: colors.textMuted },
});
