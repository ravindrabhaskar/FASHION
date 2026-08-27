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
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { socialApi } from '@/api/endpoints';
import type { SocialPost } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function SocialFeedScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async (reset = false) => {
    if (reset) { setLoading(true); setPage(1); }
    setError('');
    try {
      const data = await socialApi.feed(reset ? 1 : page);
      setPosts(reset ? data.results : (prev) => [...prev, ...data.results]);
      setHasMore(data.has_more);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load feed.');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [page]);

  useEffect(() => { void load(true); }, []);

  const loadMore = () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    setPage((p) => p + 1);
  };

  useEffect(() => {
    if (page > 1) void load();
  }, [page]);

  const toggleLike = async (post: SocialPost) => {
    try {
      const result = await socialApi.toggleLike(post.id);
      setPosts((prev) =>
        prev.map((p) =>
          p.id === post.id ? { ...p, liked: result.liked, like_count: result.like_count } : p,
        ),
      );
    } catch { /* ignore */ }
  };

  const toggleSave = async (post: SocialPost) => {
    try {
      const result = await socialApi.toggleSave(post.id);
      setPosts((prev) =>
        prev.map((p) => (p.id === post.id ? { ...p, saved: result.saved } : p)),
      );
    } catch { /* ignore */ }
  };

  const renderItem = ({ item }: { item: SocialPost }) => (
    <TouchableOpacity
      activeOpacity={0.9}
      style={styles.card}
      onPress={() => navigation.navigate('PostDetail', { postId: item.id })}
    >
      <TouchableOpacity
        activeOpacity={0.8}
        style={styles.userRow}
        onPress={() => navigation.navigate('PublicProfile', { userId: item.user_id })}
      >
        {item.user_avatar ? (
          <Image source={{ uri: item.user_avatar }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatar, styles.avatarPlaceholder]}>
            <Text style={{ fontSize: 14, color: colors.textMuted }}>◉</Text>
          </View>
        )}
        <Text style={styles.userName}>{item.user_name}</Text>
        {item.occasion ? (
          <Text style={styles.occasionBadge}>{item.occasion.replace('-', ' ').toUpperCase()}</Text>
        ) : null}
      </TouchableOpacity>

      {item.image ? <Image source={{ uri: item.image }} style={styles.postImage} /> : null}

      {item.caption ? <Text style={styles.caption}>{item.caption}</Text> : null}

      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionBtn} onPress={() => void toggleLike(item)}>
          <Text style={[styles.actionText, item.liked && { color: colors.danger }]}>
            {item.liked ? '♥' : '♡'} {item.like_count}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionBtn}
          onPress={() => navigation.navigate('PostDetail', { postId: item.id })}
        >
          <Text style={styles.actionText}>💬 {item.comment_count}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionBtn} onPress={() => void toggleSave(item)}>
          <Text style={[styles.actionText, item.saved && { color: colors.gold }]}>
            {item.saved ? '★' : '☆'} Save
          </Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  return (
    <Screen scroll={false} title="Social">
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} />
        </View>
      ) : error && posts.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.error}>{error}</Text>
          <TouchableOpacity onPress={() => void load(true)}>
            <Text style={styles.retry}>Tap to retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={posts}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={{ padding: spacing.xl }}
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListFooterComponent={
            loadingMore ? <ActivityIndicator color={colors.gold} style={{ marginVertical: spacing.lg }} /> : null
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={{ fontSize: 44 }}>♡</Text>
              <Text style={styles.emptyTitle}>Your feed is empty</Text>
              <Text style={styles.emptyMsg}>Follow people and create posts to see them here.</Text>
            </View>
          }
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  avatar: { borderRadius: 18, height: 36, width: 36 },
  avatarPlaceholder: {
    alignItems: 'center',
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderWidth: 1,
    justifyContent: 'center',
  },
  actionBtn: { marginRight: spacing.xl },
  actionText: { ...typography.small, color: colors.textSecondary },
  actions: { flexDirection: 'row', paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
  caption: { ...typography.body, color: colors.textPrimary, paddingHorizontal: spacing.lg, paddingVertical: spacing.sm },
  card: {
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderRadius: radii.lg,
    borderWidth: 1,
    marginBottom: spacing.lg,
    overflow: 'hidden',
  },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  emptyMsg: { ...typography.small, color: colors.textSecondary, marginTop: spacing.sm, textAlign: 'center' },
  emptyTitle: { ...typography.h2, color: colors.textPrimary, marginTop: spacing.lg },
  error: { ...typography.body, color: colors.danger, textAlign: 'center' },
  occasionBadge: { ...typography.micro, color: colors.gold, marginLeft: 'auto' },
  postImage: { height: 280, width: '100%' },
  retry: { ...typography.small, color: colors.gold, marginTop: spacing.md },
  userName: { ...typography.h3, color: colors.textPrimary, marginLeft: spacing.md },
  userRow: { alignItems: 'center', flexDirection: 'row', padding: spacing.lg },
});
