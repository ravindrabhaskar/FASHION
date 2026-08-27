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
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { chatApi } from '@/api/endpoints';
import type { ChatThread } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function ChatListScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [scope, setScope] = useState<'buying' | 'selling'>('buying');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await chatApi.threads(scope);
      setThreads(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [scope]);

  useEffect(() => { void load(); }, [load]);

  return (
    <Screen scroll={false} title="Messages">
      <View style={{ paddingHorizontal: spacing.xl }}>
        <View style={styles.scopeRow}>
          <TouchableOpacity
            style={[styles.scopeBtn, scope === 'buying' && styles.scopeActive]}
            onPress={() => setScope('buying')}
          >
            <Text style={[styles.scopeText, scope === 'buying' && styles.scopeTextActive]}>Buying</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.scopeBtn, scope === 'selling' && styles.scopeActive]}
            onPress={() => setScope('selling')}
          >
            <Text style={[styles.scopeText, scope === 'selling' && styles.scopeTextActive]}>Selling</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
        ) : (
          <FlatList
            data={threads}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                activeOpacity={0.85}
                style={styles.threadCard}
                onPress={() => navigation.navigate('ChatThread', { threadId: item.id, subject: item.subject })}
              >
                <View style={styles.threadHeader}>
                  <Text style={styles.threadName}>{item.other_user_name}</Text>
                  {item.unread_count > 0 && (
                    <View style={styles.unreadBadge}>
                      <Text style={styles.unreadText}>{item.unread_count}</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.threadSubject} numberOfLines={1}>{item.subject}</Text>
                <Text style={styles.threadPreview} numberOfLines={1}>{item.last_message}</Text>
                <Text style={styles.threadTime}>{new Date(item.last_message_at).toLocaleDateString()}</Text>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.center}>
                <Text style={styles.emptyText}>No conversations yet.</Text>
              </View>
            }
          />
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  emptyText: { ...typography.body, color: colors.textSecondary },
  scopeActive: { borderBottomColor: colors.gold, borderBottomWidth: 2 },
  scopeBtn: { borderBottomColor: 'transparent', borderBottomWidth: 2, marginRight: spacing.xl, paddingBottom: spacing.sm },
  scopeRow: { flexDirection: 'row', marginBottom: spacing.lg },
  scopeText: { ...typography.small, color: colors.textMuted },
  scopeTextActive: { color: colors.gold },
  threadCard: {
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  threadHeader: { flexDirection: 'row', justifyContent: 'space-between' },
  threadName: { ...typography.h3, color: colors.textPrimary },
  threadPreview: { ...typography.small, color: colors.textMuted, marginTop: 4 },
  threadSubject: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  threadTime: { ...typography.micro, color: colors.textMuted, marginTop: spacing.sm },
  unreadBadge: {
    backgroundColor: colors.gold,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
  },
  unreadText: { color: colors.ink, fontSize: 11, fontWeight: '700' },
});
