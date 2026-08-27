import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { challengesApi } from '@/api/endpoints';
import type { Challenge, LeaderboardEntry } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { ApiError } from '@/api/client';

export default function ChallengeDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'ChallengeDetail'>>();
  const navigation = useNavigation();
  const { challengeId } = route.params;
  const [challenge, setChallenge] = useState<(Challenge & { leaderboard: LeaderboardEntry[] }) | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  const load = useCallback(async () => {
    try {
      setChallenge(await challengesApi.detail(challengeId));
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [challengeId]);

  useEffect(() => { void load(); }, [load]);

  const enroll = async () => {
    setEnrolling(true);
    try {
      await challengesApi.enroll(challengeId);
      Alert.alert('Enrolled!', 'You are now part of this challenge.');
      void load();
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not enroll.');
    } finally {
      setEnrolling(false);
    }
  };

  if (loading) {
    return (
      <Screen title="Challenge">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!challenge) {
    return (
      <Screen title="Challenge">
        <View style={styles.center}><Text style={styles.emptyText}>Challenge not found.</Text></View>
      </Screen>
    );
  }

  return (
    <Screen title={challenge.title}>
      <View style={{ padding: spacing.xl }}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>

        <Card>
          <Text style={styles.description}>{challenge.description}</Text>
          <Text style={styles.meta}>
            ✦ {challenge.xp_reward} XP · 👥 {challenge.entry_count} entries
          </Text>
          {challenge.hashtag ? <Text style={styles.hashtag}>{challenge.hashtag}</Text> : null}
          {!challenge.enrolled && challenge.status === 'LIVE' && (
            <Button
              label="Enroll now"
              variant="gold"
              loading={enrolling}
              onPress={() => void enroll()}
              style={{ marginTop: spacing.lg }}
            />
          )}
          {challenge.enrolled && (
            <View style={styles.enrolledBadge}>
              <Text style={styles.enrolledText}>
                Enrolled · Your score: {challenge.my_score ?? 'N/A'}
              </Text>
            </View>
          )}
        </Card>

        {challenge.leaderboard.length > 0 && (
          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>LEADERBOARD</Text>
            {challenge.leaderboard.slice(0, 10).map((entry) => (
              <View key={entry.user_id} style={styles.lbRow}>
                <Text style={styles.lbRank}>
                  {entry.rank <= 3 ? ['🥇', '🥈', '🥉'][entry.rank - 1] : `#${entry.rank}`}
                </Text>
                <Text style={styles.lbName}>{entry.user_name}</Text>
                <Text style={styles.lbXp}>{entry.total_xp.toLocaleString()}</Text>
              </View>
            ))}
          </Card>
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { ...typography.body, color: colors.gold, marginBottom: spacing.lg },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  description: { ...typography.body, color: colors.textPrimary },
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
  hashtag: { ...typography.small, color: colors.gold, marginTop: spacing.md },
  lbName: { ...typography.body, color: colors.textPrimary, flex: 1 },
  lbRank: { ...typography.h3, color: colors.textSecondary, marginRight: spacing.md, width: 40 },
  lbRow: { alignItems: 'center', flexDirection: 'row', marginBottom: spacing.sm },
  lbXp: { ...typography.h3, color: colors.gold },
  meta: { ...typography.small, color: colors.textMuted, marginTop: spacing.md },
  sectionTitle: { ...typography.micro, color: colors.gold, letterSpacing: 1.2, marginBottom: spacing.md },
});
