import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { xpApi } from '@/api/endpoints';
import type { XPDashboard as XPDashboardType } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function XPDashboardScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [data, setData] = useState<XPDashboardType | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setData(await xpApi.me());
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return (
      <Screen title="My XP">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!data) {
    return (
      <Screen title="My XP">
        <View style={styles.center}><Text style={styles.emptyText}>Could not load XP data.</Text></View>
      </Screen>
    );
  }

  const progressWidth = `${data.progress_percent}%` as `${number}%`;

  return (
    <Screen title="My XP">
      <View style={{ padding: spacing.xl }}>
        <Card>
          <Text style={styles.microGold}>LEVEL {data.level_number}</Text>
          <Text style={styles.levelName}>{data.level}</Text>
          <Text style={styles.xpValue}>{data.total_xp.toLocaleString()} XP</Text>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: progressWidth }]} />
          </View>
          <Text style={styles.progressLabel}>
            {data.progress_percent.toFixed(0)}% to next level · {data.next_threshold.toLocaleString()} XP
          </Text>
          <Text style={styles.dailyCap}>
            Earned today: {data.earned_today}/{data.daily_cap} XP
          </Text>
        </Card>

        <TouchableOpacity onPress={() => navigation.navigate('Leaderboard', { scope: 'global' })}>
          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>LEADERBOARD</Text>
            <Text style={styles.cardLink}>View global rankings →</Text>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate('Challenges')}>
          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>CHALLENGES</Text>
            <Text style={styles.cardLink}>Browse active challenges →</Text>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate('Rewards')}>
          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>REWARDS</Text>
            <Text style={styles.cardLink}>Redeem your XP →</Text>
          </Card>
        </TouchableOpacity>

        {data.badges.length > 0 && (
          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>BADGES</Text>
            <View style={styles.badgeGrid}>
              {data.badges.map((b) => (
                <View key={b.code} style={styles.badgeItem}>
                  <Text style={{ fontSize: 24 }}>{b.icon}</Text>
                  <Text style={styles.badgeName}>{b.name}</Text>
                </View>
              ))}
            </View>
          </Card>
        )}

        {data.recent_transactions.length > 0 && (
          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>RECENT ACTIVITY</Text>
            {data.recent_transactions.map((t, i) => (
              <View key={i} style={styles.txnRow}>
                <Text style={styles.txnReason} numberOfLines={1}>{t.reason}</Text>
                <Text style={[styles.txnAmount, t.amount > 0 && { color: colors.success }]}>
                  {t.amount > 0 ? '+' : ''}{t.amount}
                </Text>
              </View>
            ))}
          </Card>
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  badgeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  badgeItem: { alignItems: 'center', width: 72 },
  badgeName: { ...typography.micro, color: colors.textSecondary, marginTop: 4, textAlign: 'center' },
  cardLink: { ...typography.body, color: colors.gold },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  dailyCap: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  emptyText: { ...typography.body, color: colors.textSecondary },
  levelName: { ...typography.h1, color: colors.textPrimary, marginTop: spacing.xs },
  microGold: { ...typography.micro, color: colors.gold, letterSpacing: 1.2 },
  progressBar: {
    backgroundColor: colors.inkElevated,
    borderRadius: radii.pill,
    height: 8,
    marginTop: spacing.md,
    overflow: 'hidden',
  },
  progressFill: { backgroundColor: colors.gold, borderRadius: radii.pill, height: 8 },
  progressLabel: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  sectionTitle: { ...typography.micro, color: colors.gold, letterSpacing: 1.2, marginBottom: spacing.sm },
  txnAmount: { ...typography.small, color: colors.danger },
  txnReason: { ...typography.small, color: colors.textSecondary, flex: 1 },
  txnRow: { alignItems: 'center', flexDirection: 'row', marginBottom: spacing.sm },
  xpValue: { ...typography.display, color: colors.gold, marginTop: spacing.sm },
});
