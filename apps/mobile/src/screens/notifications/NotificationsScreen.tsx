import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Screen } from '@/components/ui/Screen';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { notificationsApi } from '@/api/endpoints';
import type { Notification } from '@/api/types';

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await notificationsApi.list();
      setNotifications(data.results);
      setUnread(data.unread);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const markRead = async (id: string) => {
    try {
      await notificationsApi.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n)),
      );
      setUnread((prev) => Math.max(0, prev - 1));
    } catch { /* ignore */ }
  };

  const markAllRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read_at: n.read_at ?? new Date().toISOString() })));
      setUnread(0);
    } catch { /* ignore */ }
  };

  if (loading) {
    return (
      <Screen title="Notifications">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false} title={`Notifications${unread > 0 ? ` (${unread})` : ''}`}>
      <View style={{ paddingHorizontal: spacing.xl }}>
        {unread > 0 && (
          <TouchableOpacity style={styles.markAllBtn} onPress={() => void markAllRead()}>
            <Text style={styles.markAllText}>Mark all read</Text>
          </TouchableOpacity>
        )}

        <FlatList
          data={notifications}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ paddingBottom: spacing.xxl }}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.notifCard, !item.read_at && styles.notifUnread]}
              onPress={() => void markRead(item.id)}
            >
              <View style={styles.notifHeader}>
                <Text style={styles.notifTitle}>{item.title}</Text>
                {!item.read_at && <View style={styles.unreadDot} />}
              </View>
              <Text style={styles.notifBody}>{item.body}</Text>
              <Text style={styles.notifTime}>{new Date(item.created_at).toLocaleString()}</Text>
            </TouchableOpacity>
          )}
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyText}>No notifications yet.</Text>
            </View>
          }
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  emptyText: { ...typography.body, color: colors.textSecondary },
  markAllBtn: { alignSelf: 'flex-end', marginBottom: spacing.md },
  markAllText: { ...typography.small, color: colors.gold },
  notifBody: { ...typography.body, color: colors.textSecondary, marginTop: spacing.xs },
  notifCard: {
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  notifHeader: { flexDirection: 'row', justifyContent: 'space-between' },
  notifTime: { ...typography.micro, color: colors.textMuted, marginTop: spacing.sm },
  notifTitle: { ...typography.h3, color: colors.textPrimary, flex: 1 },
  notifUnread: { borderColor: colors.gold, borderWidth: 1 },
  unreadDot: { backgroundColor: colors.gold, borderRadius: 4, height: 8, marginLeft: spacing.sm, width: 8 },
});
