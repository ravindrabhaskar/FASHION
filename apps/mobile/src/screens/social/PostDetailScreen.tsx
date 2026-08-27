import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Image,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { socialApi, marketplaceApi } from '@/api/endpoints';
import type { ShopThisLookComponent, SocialComment, SocialPost } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function PostDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'PostDetail'>>();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { postId } = route.params;
  const [post, setPost] = useState<SocialPost | null>(null);
  const [comments, setComments] = useState<SocialComment[]>([]);
  const [look, setLook] = useState<ShopThisLookComponent[]>([]);
  const [commentText, setCommentText] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  const load = useCallback(async () => {
    try {
      const [postData, commentsData, lookData] = await Promise.all([
        socialApi.post(postId),
        socialApi.comments(postId),
        marketplaceApi.shopThisLook(postId).catch(() => null),
      ]);
      setPost(postData);
      setComments(commentsData.results);
      setLook(lookData?.components ?? []);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [postId]);

  useEffect(() => { void load(); }, [load]);

  const toggleLike = async () => {
    if (!post) return;
    try {
      const result = await socialApi.toggleLike(post.id);
      setPost((prev) => prev ? { ...prev, liked: result.liked, like_count: result.like_count } : prev);
    } catch { /* ignore */ }
  };

  const toggleSave = async () => {
    if (!post) return;
    try {
      const result = await socialApi.toggleSave(post.id);
      setPost((prev) => prev ? { ...prev, saved: result.saved } : prev);
    } catch { /* ignore */ }
  };

  const addComment = async () => {
    if (!commentText.trim() || sending) return;
    setSending(true);
    try {
      const comment = await socialApi.addComment(postId, commentText.trim());
      setComments((prev) => [...prev, comment]);
      setCommentText('');
      setPost((prev) => prev ? { ...prev, comment_count: prev.comment_count + 1 } : prev);
    } catch { /* ignore */ } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <Screen>
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} />
        </View>
      </Screen>
    );
  }

  if (!post) {
    return (
      <Screen>
        <View style={styles.center}>
          <Text style={styles.emptyText}>Post not found.</Text>
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false}>
      <FlatList
        data={comments}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: spacing.xl }}
        ListHeaderComponent={
          <>
            <View style={styles.header}>
              <TouchableOpacity onPress={() => navigation.goBack()}>
                <Text style={styles.back}>← Back</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.userRow}>
              {post.user_avatar ? (
                <Image source={{ uri: post.user_avatar }} style={styles.avatar} />
              ) : (
                <View style={[styles.avatar, styles.avatarPlaceholder]}>
                  <Text style={{ fontSize: 14, color: colors.textMuted }}>◉</Text>
                </View>
              )}
              <Text style={styles.userName}>{post.user_name}</Text>
            </View>
            {post.image ? <Image source={{ uri: post.image }} style={styles.postImage} /> : null}
            {post.caption ? <Text style={styles.caption}>{post.caption}</Text> : null}
            <View style={styles.actions}>
              <TouchableOpacity style={styles.actionBtn} onPress={() => void toggleLike()}>
                <Text style={[styles.actionText, post.liked && { color: colors.danger }]}>
                  {post.liked ? '♥' : '♡'} {post.like_count}
                </Text>
              </TouchableOpacity>
              <Text style={styles.actionText}>💬 {comments.length}</Text>
              <TouchableOpacity style={styles.actionBtn} onPress={() => void toggleSave()}>
                <Text style={[styles.actionText, post.saved && { color: colors.gold }]}>
                  {post.saved ? '★' : '☆'} Save
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => navigation.navigate('Report', { targetType: 'POST', targetId: post.id })}
              >
                <Text style={styles.actionText}>⚑ Report</Text>
              </TouchableOpacity>
            </View>

            {look.length > 0 && (
              <>
                <View style={styles.divider} />
                <Text style={styles.sectionTitle}>SHOP THIS LOOK</Text>
                {look.map((component) => {
                  const item = component.product ?? component.similar_products?.[0];
                  if (!item) return null;
                  return (
                    <TouchableOpacity
                      key={component.id}
                      style={styles.lookRow}
                      onPress={() => navigation.navigate('ProductDetail', { productId: item.id })}
                    >
                      {item.image ? (
                        <Image source={{ uri: item.image }} style={styles.lookThumb} />
                      ) : (
                        <View style={[styles.lookThumb, styles.lookThumbPlaceholder]} />
                      )}
                      <View style={{ flex: 1 }}>
                        <Text style={styles.lookLabel}>{component.label}</Text>
                        <Text style={styles.lookProduct} numberOfLines={1}>{item.title}</Text>
                        <Text style={styles.lookPrice}>₹{item.price_inr.toLocaleString('en-IN')}</Text>
                      </View>
                    </TouchableOpacity>
                  );
                })}
              </>
            )}

            <View style={styles.divider} />
            <Text style={styles.sectionTitle}>COMMENTS</Text>
          </>
        }
        renderItem={({ item }) => (
          <View style={styles.commentRow}>
            <Text style={styles.commentUser}>{item.user_name}</Text>
            <Text style={styles.commentText}>{item.text}</Text>
          </View>
        )}
        ListEmptyComponent={
          <Text style={styles.noComments}>No comments yet. Be the first.</Text>
        }
      />
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Add a comment..."
          placeholderTextColor={colors.textMuted}
          value={commentText}
          onChangeText={setCommentText}
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!commentText.trim() || sending) && { opacity: 0.4 }]}
          onPress={() => void addComment()}
          disabled={!commentText.trim() || sending}
        >
          <Text style={styles.sendText}>{sending ? '...' : '→'}</Text>
        </TouchableOpacity>
      </View>
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
  actions: { flexDirection: 'row', paddingVertical: spacing.md },
  back: { ...typography.body, color: colors.gold },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  commentRow: { marginBottom: spacing.md },
  commentText: { ...typography.body, color: colors.textPrimary, marginTop: 2 },
  commentUser: { ...typography.small, color: colors.gold },
  caption: { ...typography.body, color: colors.textPrimary, marginVertical: spacing.sm },
  divider: { backgroundColor: colors.inkBorder, height: 1, marginVertical: spacing.md },
  emptyText: { ...typography.body, color: colors.textSecondary },
  header: { marginBottom: spacing.lg },
  input: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    color: colors.textPrimary,
    flex: 1,
    fontSize: 14,
    paddingHorizontal: spacing.lg,
    paddingVertical: 10,
  },
  inputBar: {
    alignItems: 'center',
    backgroundColor: colors.inkElevated,
    borderTopColor: colors.inkBorder,
    borderTopWidth: 1,
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  noComments: { ...typography.small, color: colors.textMuted, marginVertical: spacing.lg },
  lookLabel: { ...typography.micro, color: colors.gold },
  lookPrice: { ...typography.small, color: colors.gold, marginTop: 2 },
  lookProduct: { ...typography.small, color: colors.textPrimary, marginTop: 2 },
  lookRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.md },
  lookThumb: { borderRadius: radii.sm, height: 56, width: 56 },
  lookThumbPlaceholder: { backgroundColor: colors.inkElevated },
  postImage: { borderRadius: radii.md, height: 300, marginVertical: spacing.md, width: '100%' },
  sectionTitle: { ...typography.micro, color: colors.textMuted, letterSpacing: 1.2, marginBottom: spacing.md },
  sendBtn: {
    backgroundColor: colors.gold,
    borderRadius: 18,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    width: 36,
  },
  sendText: { color: colors.ink, fontSize: 16, fontWeight: '700' },
  userName: { ...typography.h3, color: colors.textPrimary, marginLeft: spacing.md },
  userRow: { alignItems: 'center', flexDirection: 'row', marginBottom: spacing.md },
});
