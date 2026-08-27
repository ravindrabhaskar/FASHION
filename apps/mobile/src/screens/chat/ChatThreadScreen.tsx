import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { chatApi } from '@/api/endpoints';
import type { ChatThreadMessage } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { useAuth } from '@/state/auth';

export default function ChatThreadScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'ChatThread'>>();
  const navigation = useNavigation();
  const { threadId, subject } = route.params;
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatThreadMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const load = useCallback(async () => {
    try {
      const data = await chatApi.thread(threadId);
      setMessages(data.messages);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [threadId]);

  useEffect(() => { void load(); }, [load]);

  const send = async () => {
    if (!input.trim() || sending) return;
    setSending(true);
    const body = input.trim();
    setInput('');
    try {
      const msg = await chatApi.sendMessage(threadId, body);
      setMessages((prev) => [...prev, msg]);
    } catch {
      setInput(body);
    } finally {
      setSending(false);
    }
  };

  const isMe = (msg: ChatThreadMessage) => msg.sender_id === user?.id;

  return (
    <Screen scroll={false}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← </Text>
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.headerTitle} numberOfLines={1}>{subject}</Text>
        </View>
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      ) : (
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ padding: spacing.lg }}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          renderItem={({ item }) => (
            <View style={[styles.bubble, isMe(item) ? styles.bubbleMe : styles.bubbleThem]}>
              {!isMe(item) ? <Text style={styles.senderName}>{item.sender_name}</Text> : null}
              <Text style={[styles.bubbleText, isMe(item) && { color: colors.ink }]}>{item.body}</Text>
              <Text style={[styles.bubbleTime, isMe(item) && { color: colors.textMuted }]}>
                {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Text>
            </View>
          )}
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyText}>No messages yet. Say hello!</Text>
            </View>
          }
        />
      )}

      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Type a message..."
          placeholderTextColor={colors.textMuted}
          value={input}
          onChangeText={setInput}
          multiline
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || sending) && { opacity: 0.4 }]}
          onPress={() => void send()}
          disabled={!input.trim() || sending}
        >
          <Text style={styles.sendText}>{sending ? '...' : '→'}</Text>
        </TouchableOpacity>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { ...typography.body, color: colors.gold, marginRight: spacing.sm },
  bubble: {
    borderRadius: radii.lg,
    marginBottom: spacing.md,
    maxWidth: '78%',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  bubbleMe: { alignSelf: 'flex-end', backgroundColor: colors.gold },
  bubbleThem: { alignSelf: 'flex-start', backgroundColor: colors.inkCard, borderColor: colors.inkBorder, borderWidth: 1 },
  bubbleText: { ...typography.body, color: colors.textPrimary },
  bubbleTime: { ...typography.micro, color: colors.textMuted, marginTop: 4 },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  emptyText: { ...typography.body, color: colors.textSecondary },
  header: { alignItems: 'center', backgroundColor: colors.inkElevated, borderBottomColor: colors.inkBorder, borderBottomWidth: 1, flexDirection: 'row', paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
  headerTitle: { ...typography.h3, color: colors.textPrimary },
  input: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    color: colors.textPrimary,
    flex: 1,
    fontSize: 15,
    maxHeight: 100,
    paddingHorizontal: spacing.lg,
    paddingVertical: 10,
  },
  inputBar: {
    alignItems: 'flex-end',
    backgroundColor: colors.ink,
    borderTopColor: colors.inkBorder,
    borderTopWidth: 1,
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  sendBtn: {
    backgroundColor: colors.gold,
    borderRadius: 18,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    width: 36,
  },
  sendText: { color: colors.ink, fontSize: 16, fontWeight: '700' },
  senderName: { ...typography.micro, color: colors.gold, marginBottom: 2 },
});
