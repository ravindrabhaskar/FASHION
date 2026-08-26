import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, EmptyState, ErrorState, Skeleton } from '@/components/ui';
import { OutfitCard } from '@/components/ui/OutfitCard';
import { Screen } from '@/components/ui/Screen';
import { colors, spacing, typography } from '@/theme/tokens';
import { fashionApi } from '@/api/endpoints';
import type { Outfit } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function SavedLooksScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [outfits, setOutfits] = useState<Outfit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setError('');
    setLoading(true);
    try {
      const data = await fashionApi.outfits();
      setOutfits(data.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load your looks.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <Screen scroll={false} title="My Looks">
      {loading ? (
        <View style={{ padding: spacing.xl }}>
          {[0, 1].map((i) => (
            <Skeleton key={i} height={280} />
          ))}
        </View>
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : outfits.length === 0 ? (
        <>
          <EmptyState
            emoji="✦"
            title="No looks yet"
            message={'Visit the AI Stylist to create your first personalized outfit.'}
          />
          <Button label="Open Stylist" onPress={() => navigation.navigate('Main')} style={{ marginHorizontal: spacing.xl }} />
        </>
      ) : (
        <FlatList
          contentContainerStyle={{ padding: spacing.xl }}
          data={outfits}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <>
              <OutfitCard outfit={item} />
              {item.saved ? null : (
                <Text style={{ ...typography.micro, color: colors.textMuted, marginBottom: spacing.md }}>
                  Not saved yet
                </Text>
              )}
            </>
          )}
        />
      )}
    </Screen>
  );
}
