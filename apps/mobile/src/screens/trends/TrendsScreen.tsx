import React, { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Card, Chip, ErrorState, Skeleton } from '@/components/ui';
import { colors, spacing, typography } from '@/theme/tokens';
import { fashionApi } from '@/api/endpoints';
import { useI18n } from '@/i18n';
import type { RootStackParamList } from '@/navigation/types';
import type { TrendingEntry } from '@/api/types';

function Section({
  title,
  entries,
  onEntry,
}: {
  title: string;
  entries: TrendingEntry[];
  onEntry?: (entry: TrendingEntry) => void;
}) {
  if (!entries?.length) return null;
  return (
    <Card style={{ marginBottom: spacing.lg }}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: spacing.sm }}>
        {entries.map((entry) => (
          <View key={title + entry.value} style={{ marginRight: spacing.sm, marginBottom: spacing.sm }}>
            <Chip label={`${entry.label || entry.value} · ${entry.count}`} onPress={() => onEntry?.(entry)} />
          </View>
        ))}
      </View>
    </Card>
  );
}

export default function TrendsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { t } = useI18n();
  const [data, setData] = useState<{
    colors: TrendingEntry[];
    fabrics: TrendingEntry[];
    categories: TrendingEntry[];
    hashtags: TrendingEntry[];
    cities: TrendingEntry[];
  } | null>(null);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await fashionApi.trends();
      setData({
        colors: result.colors,
        fabrics: result.fabrics,
        categories: result.categories,
        hashtags: result.hashtags,
        cities: result.cities,
      });
    } catch (e) {
      setError('Trends are unavailable right now.');
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openShop = () => {
    navigation.navigate('Main', { screen: 'Shop' });
  };

  return (
    <View style={styles.wrap}>
      <Text style={styles.header}>{t('tr.header')}</Text>
      <Text style={styles.subheader}>Colors, fabrics and cities pulling fashion forward right now.</Text>

      <ScrollView
        contentContainerStyle={{ paddingBottom: spacing.xxl }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load().finally(() => setRefreshing(false)); }} tintColor={colors.gold} />}
      >
        {error ? <ErrorState message={error} onRetry={load} /> : null}
        {!data && !error ? (
          <>
            <Skeleton height={96} width="100%" />
            <View style={{ marginTop: spacing.md }}>
              <Skeleton height={96} width="100%" />
            </View>
            <View style={{ marginTop: spacing.md }}>
              <Skeleton height={96} width="100%" />
            </View>
          </>
        ) : null}
        {data ? (
          <>
            <Section title={t('tr.colors')} entries={data.colors} onEntry={openShop} />
            <Section title={t('tr.fabrics')} entries={data.fabrics} onEntry={openShop} />
            <Section title={t('tr.categories')} entries={data.categories} onEntry={openShop} />
            <Section title={t('tr.locations')} entries={data.cities} onEntry={openShop} />
            <Section title="Trending hashtags" entries={data.hashtags} />
          </>
        ) : null}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    ...typography.display,
    color: colors.textPrimary,
    fontSize: 28,
    marginTop: spacing.xl,
    paddingHorizontal: spacing.xl,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  subheader: {
    ...typography.small,
    color: colors.textSecondary,
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.lg,
    marginTop: spacing.sm,
  },
  wrap: { backgroundColor: colors.ink, flex: 1 },
});