import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { challengesApi } from '@/api/endpoints';
import type { Challenge } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

const STATUS_COLORS: Record<Challenge['status'], string> = {
  UPCOMING: colors.textMuted,
  LIVE: colors.success,
  CLOSED: colors.danger,
};

export default function ChallengesScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await challengesApi.list();
      setChallenges(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return (
      <Screen title="Challenges">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false} title="Challenges">
      <FlatList
        data={challenges}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: spacing.xl }}
        renderItem={({ item }) => (
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => navigation.navigate('ChallengeDetail', { challengeId: item.id })}
          >
            <Card style={{ marginBottom: spacing.lg }}>
              <View style={styles.header}>
                <Text style={styles.title}>{item.title}</Text>
                <Text style={[styles.status, { color: STATUS_COLORS[item.status] }]}>
                  {item.status}
                </Text>
              </View>
              <Text style={styles.description} numberOfLines={2}>{item.description}</Text>
              <View style={styles.meta}>
                <Text style={styles.metaText}>🎫 {item.hashtag}</Text>
                <Text style={styles.metaText}>✦ {item.xp_reward} XP</Text>
                <Text style={styles.metaText}>👥 {item.entry_count}</Text>
              </View>
              {item.enrolled && (
                <View style={styles.enrolledBadge}>
                  <Text style={styles.enrolledText}>Enrolled · Score: {item.my_score}</Text>
                </View>
              )}
            </Card>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.emptyText}>No challenges yet. Check back soon!</Text>
          </View>
        }
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  description: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  emptyText: { ...typography.body, color: colors.textSecondary },
  enrolledBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.goldSoft,
    borderRadius: radii.pill,
    marginTop: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  enrolledText: { ...typography.micro, color: colors.gold },
  header: { flexDirection: 'row', justifyContent: 'space-between' },
  meta: { flexDirection: 'row', gap: spacing.lg, marginTop: spacing.md },
  metaText: { ...typography.small, color: colors.textMuted },
  status: { ...typography.micro, fontWeight: '700' },
  title: { ...typography.h3, color: colors.textPrimary, flex: 1 },
});
