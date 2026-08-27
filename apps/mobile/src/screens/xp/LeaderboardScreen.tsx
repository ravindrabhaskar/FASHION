import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { xpApi } from '@/api/endpoints';
import type { LeaderboardEntry } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function LeaderboardScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'Leaderboard'>>();
  const navigation = useNavigation();
  const scope = route.params?.scope ?? 'global';
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await xpApi.leaderboard({ scope, challenge: route.params?.challenge });
      setEntries(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [scope, route.params?.challenge]);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return (
      <Screen title="Leaderboard">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false} title="Leaderboard" subtitle={scope.toUpperCase()}>
      <FlatList
        data={entries}
        keyExtractor={(item) => `${item.user_id}-${item.rank}`}
        contentContainerStyle={{ padding: spacing.xl }}
        renderItem={({ item, index }) => (
          <View style={[styles.row, index < 3 && styles.rowTop]}>
            <Text style={[styles.rank, index < 3 && styles.rankTop]}>
              {item.rank <= 3 ? ['🥇', '🥈', '🥉'][item.rank - 1] : `#${item.rank}`}
            </Text>
            <View style={styles.info}>
              <Text style={styles.name}>{item.user_name}</Text>
              <Text style={styles.level}>{item.level}</Text>
            </View>
            <Text style={styles.xp}>{item.total_xp.toLocaleString()} XP</Text>
          </View>
        )}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.emptyText}>No leaderboard data yet.</Text>
          </View>
        }
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  emptyText: { ...typography.body, color: colors.textSecondary },
  info: { flex: 1 },
  level: { ...typography.small, color: colors.textMuted },
  name: { ...typography.h3, color: colors.textPrimary },
  rank: { ...typography.h2, color: colors.textSecondary, marginRight: spacing.lg, width: 40 },
  rankTop: { color: colors.gold },
  row: {
    alignItems: 'center',
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    flexDirection: 'row',
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  rowTop: { borderColor: colors.gold, borderWidth: 1 },
  xp: { ...typography.h3, color: colors.gold },
});
