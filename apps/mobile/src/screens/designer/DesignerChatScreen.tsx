import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput as RNInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { designerApi } from '@/api/endpoints';
import type { ChatMessage, ConversationDetail, DesignState } from '@/api/types';

const SUGGESTIONS = [
  'Design something for my friend\'s wedding',
  'Make it more traditional',
  'Use lighter fabric for summer',
  'Add heavy embroidery',
];

export default function DesignerChatScreen({
  route,
}: {
  route?: { params?: { conversationId?: string; occasion?: string } };
}) {
  const insets = useSafeAreaInsets();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const listRef = useRef<FlatList<ChatMessage>>(null);

  const ensureConversation = useCallback(async () => {
    try {
      if (route?.params?.conversationId) {
        return await designerApi.conversation(route.params.conversationId);
      }
      return await designerApi.createConversation({
        occasion: route?.params?.occasion,
        opening_request: "Design an outfit for me — I'll tell you what to change as we go.",
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not start a design session.');
      return null;
    }
  }, [route]);

  useEffect(() => {
    (async () => {
      const conversation = await ensureConversation();
      setConversation(conversation);
      setLoading(false);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = async (text: string) => {
    if (!conversation || !text.trim() || sending) return;
    setSending(true);
    setError('');
    const optimistic: ChatMessage = {
      id: `local-${Date.now()}`,
      role: 'user',
      content: text.trim(),
      changes: [],
      design_version: null,
      created_at: new Date().toISOString(),
    };
    setConversation({ ...conversation, messages: [...conversation.messages, optimistic] });
    setInput('');
    try {
      const updated = await designerApi.sendMessage(conversation.id, text.trim());
      setConversation(updated);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Message failed.');
      // Roll back the optimistic bubble.
      setConversation((current) =>
        current
          ? { ...current, messages: current.messages.filter((m) => m.id !== optimistic.id) }
          : current,
      );
    } finally {
      setSending(false);
    }
  };

  const materialize = async () => {
    if (!conversation) return;
    setError('');
    try {
      const look = await designerApi.materialize(conversation.id);
      setError(''); 
      alert(`Concept queued! Look #${look.id.slice(0, 8)} is rendering — find it in Saved Looks.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not create the look.');
    }
  };

  const design = conversation?.design_state as DesignState | undefined;

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={{ backgroundColor: colors.ink, flex: 1, paddingTop: insets.top }}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI Fashion Designer</Text>
        {design && (
          <Text numberOfLines={1} style={styles.headerState}>
            {design.garment_type.replace('-', ' ')} · {design.base_color} · {design.fabric}
          </Text>
        )}
      </View>

      {loading ? (
        <View style={{ alignItems: 'center', flex: 1, justifyContent: 'center' }}>
          <ActivityIndicator color={colors.gold} />
          <Text style={styles.loading}>Warming up the atelier…</Text>
        </View>
      ) : !conversation ? (
        <View style={{ padding: spacing.xl }}>
          <Button label="Try again" onPress={() => void ensureConversation()} variant="ghost" />
          {error ? <Text style={styles.error}>{error}</Text> : null}
        </View>
      ) : (
        <>
          <FlatList
            ref={listRef}
            contentContainerStyle={{ padding: spacing.lg }}
            data={conversation.messages}
            keyExtractor={(m) => m.id}
            onLayout={() => listRef.current?.scrollToEnd({ animated: false })}
            renderItem={({ item }) => (
              <View
                style={[styles.bubble, item.role === 'user' ? styles.bubbleUser : styles.bubbleAI]}
              >
                <Text style={item.role === 'user' ? styles.textUser : styles.textAI}>
                  {item.content}
                </Text>
                {item.changes.length > 0 && (
                  <View style={{ marginTop: spacing.sm }}>
                    {item.changes.map((change) => (
                      <Text key={change} style={styles.change}>
                        ◈ {change}
                      </Text>
                    ))}
                  </View>
                )}
              </View>
            )}
          />

          {conversation.messages.length <= 1 && !sending && (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ flexGrow: 0 }}>
              <View style={{ flexDirection: 'row', paddingHorizontal: spacing.lg }}>
                {SUGGESTIONS.map((suggestion) => (
                  <TouchableOpacity key={suggestion} onPress={() => void send(suggestion)} style={styles.suggestion}>
                    <Text style={styles.suggestionText}>{suggestion}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          )}

          {error ? <Text style={[styles.error, { paddingHorizontal: spacing.xl }]}>{error}</Text> : null}

          <View style={styles.composer}>
            <RNInput
              multiline
              onChangeText={setInput}
              placeholder="Describe your design or a change…"
              placeholderTextColor={colors.textMuted}
              style={styles.input}
              value={input}
            />
            <TouchableOpacity
              accessibilityRole="button"
              disabled={sending || !input.trim()}
              onPress={() => void send(input)}
              style={[styles.send, (!input.trim() || sending) && styles.sendDisabled]}
            >
              {sending ? (
                <ActivityIndicator color={colors.ink} size="small" />
              ) : (
                <Text style={styles.sendLabel}>↑</Text>
              )}
            </TouchableOpacity>
          </View>

          <View style={{ paddingBottom: insets.bottom + spacing.sm, paddingHorizontal: spacing.xl }}>
            <Button label="Make this look ✦" variant="gold" loading={false} onPress={materialize} />
          </View>
        </>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  bubble: {
    borderRadius: radii.lg,
    marginBottom: spacing.md,
    maxWidth: '85%',
    padding: spacing.md,
  },
  bubbleAI: {
    alignSelf: 'flex-start',
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderWidth: 1,
  },
  bubbleUser: { alignSelf: 'flex-end', backgroundColor: colors.gold },
  change: { ...typography.micro, color: colors.gold },
  composer: {
    alignItems: 'flex-end',
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
  },
  error: { ...typography.small, color: colors.danger, marginTop: spacing.sm },
  header: { borderBottomColor: colors.inkBorder, borderBottomWidth: 1, padding: spacing.lg },
  headerState: { ...typography.small, color: colors.textMuted, marginTop: 2 },
  headerTitle: { ...typography.h2, color: colors.textPrimary },
  input: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    color: colors.textPrimary,
    flex: 1,
    maxHeight: 110,
    paddingHorizontal: spacing.lg,
    paddingVertical: 12,
  },
  loading: { ...typography.small, color: colors.textSecondary, marginTop: spacing.md },
  send: {
    alignItems: 'center',
    backgroundColor: colors.textPrimary,
    borderRadius: radii.pill,
    height: 46,
    justifyContent: 'center',
    width: 46,
  },
  sendDisabled: { opacity: 0.4 },
  sendLabel: { color: colors.ink, fontSize: 20, fontWeight: '700' },
  suggestion: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.goldSoft,
    borderRadius: radii.pill,
    borderWidth: 1,
    marginRight: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: 8,
  },
  suggestionText: { ...typography.small, color: colors.textSecondary },
  textAI: { ...typography.body, color: colors.textPrimary },
  textUser: { ...typography.body, color: colors.ink },
});
