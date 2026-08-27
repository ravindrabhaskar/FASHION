import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { creatorsApi } from '@/api/endpoints';
import type { CreatorProfile } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function CreatorsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [profile, setProfile] = useState<CreatorProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setProfile(await creatorsApi.me());
    } catch { /* profile doesn't exist yet, that's fine */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return (
      <Screen title="Creators">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!profile) {
    return (
      <Screen title="Creators">
        <View style={{ padding: spacing.xl }}>
          <Card>
            <Text style={styles.emptyTitle}>Become a creator</Text>
            <Text style={styles.emptyBody}>
              Earn from brand campaigns, showcase your portfolio, and grow your influence in the fashion community.
            </Text>
            <Button
              label="Get started"
              variant="gold"
              onPress={() => navigation.navigate('BecomeCreator')}
              style={{ marginTop: spacing.lg }}
            />
          </Card>
        </View>
      </Screen>
    );
  }

  return (
    <Screen title="Creator Dashboard">
      <View style={{ padding: spacing.xl }}>
        <Card>
          <Text style={styles.handle}>@{profile.handle}</Text>
          <Text style={styles.niche}>{profile.niche}</Text>
          <Text style={styles.audience}>
            {profile.audience_size.toLocaleString()} followers
          </Text>
          {profile.is_eligible ? (
            <View style={styles.eligibleBadge}>
              <Text style={styles.eligibleText}>✓ Eligible for campaigns</Text>
            </View>
          ) : (
            <View style={styles.notEligibleBadge}>
              <Text style={styles.notEligibleText}>Not yet eligible</Text>
            </View>
          )}
        </Card>

        <Button
          label="Browse campaigns"
          variant="ghost"
          onPress={() => navigation.navigate('Campaigns')}
          style={{ marginTop: spacing.md }}
        />
        <Button
          label="Register another creator profile"
          variant="ghost"
          style={{ marginTop: spacing.md }}
          onPress={() => navigation.navigate('BecomeCreator')}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  audience: { ...typography.h3, color: colors.gold, marginTop: spacing.md },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  eligibleBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.goldSoft,
    borderRadius: radii.pill,
    marginTop: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  eligibleText: { ...typography.micro, color: colors.gold },
  emptyBody: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  emptyTitle: { ...typography.h2, color: colors.textPrimary },
  handle: { ...typography.display, color: colors.textPrimary },
  niche: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  notEligibleBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.inkElevated,
    borderRadius: radii.pill,
    marginTop: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  notEligibleText: { ...typography.micro, color: colors.textMuted },
});