import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { socialApi } from '@/api/endpoints';
import type { PublicProfile as PublicProfileType, SocialPost } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function PublicProfileScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'PublicProfile'>>();
  const navigation = useNavigation();
  const { userId } = route.params;
  const [profile, setProfile] = useState<PublicProfileType | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setProfile(await socialApi.publicProfile(userId));
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => { void load(); }, [load]);

  const toggleFollow = async () => {
    if (!profile) return;
    try {
      const result = await socialApi.follow(userId);
      setProfile((prev) => prev ? { ...prev, is_following: result.following } : prev);
    } catch { /* ignore */ }
  };

  if (loading) {
    return (
      <Screen>
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!profile) {
    return (
      <Screen>
        <View style={styles.center}><Text style={styles.emptyText}>User not found.</Text></View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false}>
      <FlatList
        data={profile.recent_posts}
        keyExtractor={(item) => item.id}
        numColumns={3}
        contentContainerStyle={{ padding: spacing.xl }}
        ListHeaderComponent={
          <>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={styles.back}>← Back</Text>
            </TouchableOpacity>
            <View style={styles.profileHeader}>
              {profile.avatar ? (
                <Image source={{ uri: profile.avatar }} style={styles.avatar} />
              ) : (
                <View style={[styles.avatar, styles.avatarPlaceholder]}>
                  <Text style={{ fontSize: 28, color: colors.textMuted }}>◉</Text>
                </View>
              )}
              <Text style={styles.name}>{profile.full_name}</Text>
              {profile.bio ? <Text style={styles.bio}>{profile.bio}</Text> : null}
              <View style={styles.statsRow}>
                <Text style={styles.stat}>{profile.post_count} posts</Text>
                <Text style={styles.stat}>{profile.follower_count} followers</Text>
                <Text style={styles.stat}>{profile.following_count} following</Text>
              </View>
              <Button
                label={profile.is_following ? 'Unfollow' : 'Follow'}
                variant={profile.is_following ? 'ghost' : 'gold'}
                onPress={() => void toggleFollow()}
                style={{ marginTop: spacing.md }}
              />
            </View>
            <Text style={styles.sectionTitle}>POSTS</Text>
          </>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.gridItem}
            onPress={() => (navigation as any).navigate('PostDetail', { postId: item.id })}
          >
            {item.image ? (
              <Image source={{ uri: item.image }} style={styles.gridImage} />
            ) : (
              <View style={[styles.gridImage, styles.gridPlaceholder]}>
                <Text style={{ color: colors.textMuted }}>♡</Text>
              </View>
            )}
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <Text style={styles.noPosts}>No posts yet.</Text>
        }
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  avatar: { borderRadius: 40, height: 80, width: 80 },
  avatarPlaceholder: {
    alignItems: 'center',
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderWidth: 1,
    justifyContent: 'center',
  },
  back: { ...typography.body, color: colors.gold, marginBottom: spacing.lg },
  bio: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm, textAlign: 'center' },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  emptyText: { ...typography.body, color: colors.textSecondary },
  gridImage: { borderRadius: radii.sm, height: 110, width: '100%' },
  gridItem: { flex: 1, margin: 2, maxWidth: '33%' },
  gridPlaceholder: { alignItems: 'center', backgroundColor: colors.inkElevated, justifyContent: 'center' },
  name: { ...typography.h2, color: colors.textPrimary, marginTop: spacing.md },
  noPosts: { ...typography.small, color: colors.textMuted, marginTop: spacing.lg, textAlign: 'center' },
  profileHeader: { alignItems: 'center', marginBottom: spacing.xl },
  sectionTitle: { ...typography.micro, color: colors.textMuted, letterSpacing: 1.2, marginBottom: spacing.md },
  stat: { ...typography.small, color: colors.textSecondary, marginRight: spacing.lg },
  statsRow: { flexDirection: 'row', marginTop: spacing.md },
});
