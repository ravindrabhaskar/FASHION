import React, { useCallback, useEffect, useState } from 'react';
import { Image, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { Button, Card, Chip, EmptyState, ErrorState, Skeleton } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { fashionApi } from '@/api/endpoints';
import type { RootStackParamList } from '@/navigation/types';
import type { Outfit } from '@/api/types';

export default function TryOnScreen({
  route,
}: {
  route: RouteProp<RootStackParamList, 'TryOn'>;
}) {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { width } = useWindowDimensions();
  const [outfits, setOutfits] = useState<Outfit[]>([]);
  const [selectedId, setSelectedId] = useState(route.params?.outfitId ?? '');
  const [result, setResult] = useState<Outfit | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fashionApi
      .outfits(true)
      .then((page) => {
        setOutfits(page.results);
        setSelectedId((prev: string) => prev || route.params?.outfitId || page.results[0]?.id || '');
      })
      .catch(() => setError('Could not load your looks.'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const generate = async () => {
    if (!selectedId) return;
    setError('');
    setLoading(true);
    try {
      let look = await fashionApi.tryon(selectedId);
      setResult(look);
      // Eager dev workers usually complete inline; poll briefly otherwise.
      let attempts = 0;
      while (look.status !== 'FAILED' && !look.image && attempts < 10) {
        await new Promise((r) => setTimeout(r, 900));
        look = await fashionApi.outfit(look.id);
        attempts += 1;
      }
      setResult(look);
    } catch (e) {
      setError('Try-on could not be generated. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.wrap}>
      <ScrollView contentContainerStyle={{ padding: spacing.xl, paddingBottom: spacing.xxl * 2 }}>
        <Text style={styles.header}>Virtual Try-on</Text>
        <Text style={styles.subheader}>
          Preview how a look fits on a studio mannequin before you commit.
        </Text>

        {error ? <ErrorState message={error} onRetry={generate} /> : null}

        {!result && outfits.length > 0 ? (
          <Card style={{ marginBottom: spacing.lg }}>
            <Text style={styles.sectionTitle}>Pick a look to try on</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: spacing.sm }}>
              {outfits.map((o) => (
                <View key={o.id} style={{ marginRight: spacing.sm, marginBottom: spacing.sm }}>
                  <Chip
                    label={o.title || 'Saved look'}
                    selected={selectedId === o.id}
                    onPress={() => setSelectedId(o.id)}
                  />
                </View>
              ))}
            </View>
            <Text style={styles.note}>Only saved looks appear here.</Text>
          </Card>
        ) : null}

        {!result && outfits.length === 0 && !error ? (
          <EmptyState
            emoji="🪞"
            title="No saved looks yet"
            message="Save a look from the stylist or designer chat, then come back to try it on."
          />
        ) : null}

        {result ? (
          <Card>
            {result.image ? (
              <Image
                source={{ uri: result.image }}
                style={{ width: '100%', height: Math.min(width - spacing.xl * 2, 640), borderRadius: radii.lg }}
                resizeMode="cover"
              />
            ) : (
              <View style={{ height: 360, justifyContent: 'center', alignItems: 'center' }}>
                {result.status === 'FAILED' ? (
                  <Text style={styles.note}>Rendering failed.</Text>
                ) : (
                  <Skeleton height={300} width="100%" />
                )}
              </View>
            )}
            <Text style={[styles.sectionTitle, { marginTop: spacing.lg }]}>{result.title}</Text>
            <Text style={styles.note}>Status: {result.status}</Text>
            {result.image_prompt ? (
              <Text style={styles.prompt}>{result.image_prompt}</Text>
            ) : null}
            <Button
              label="Try another look"
              variant="ghost"
              onPress={() => setResult(null)}
              style={{ marginTop: spacing.lg }}
            />
          </Card>
        ) : (
          <Button
            label="Generate try-on"
            loading={loading}
            disabled={!selectedId}
            onPress={generate}
            style={{ marginTop: spacing.md }}
          />
        )}
        <Button
          label="View saved looks"
          variant="ghost"
          onPress={() => navigation.navigate('SavedLooks')}
          style={{ marginTop: spacing.md }}
        />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    ...typography.display,
    color: colors.textPrimary,
    fontSize: 26,
  },
  note: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  prompt: { ...typography.small, color: colors.textSecondary, marginTop: spacing.md },
  sectionTitle: { ...typography.h3, color: colors.textPrimary },
  subheader: { ...typography.small, color: colors.textSecondary, marginVertical: spacing.sm },
  wrap: { backgroundColor: colors.ink, flex: 1 },
});