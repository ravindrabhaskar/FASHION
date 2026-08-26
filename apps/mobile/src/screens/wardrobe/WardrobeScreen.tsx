import React, { useCallback, useEffect, useState } from 'react';
import * as ImagePicker from 'expo-image-picker';
import {
  ActivityIndicator,
  Alert,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Button, Card, Chip, EmptyState, ErrorState, Skeleton } from '@/components/ui';
import { PaletteRow } from '@/components/ui/OutfitCard';
import { Screen } from '@/components/ui/Screen';
import { wardrobeApi, fashionApi } from '@/api/endpoints';
import { ApiError } from '@/api/client';
import type {
  DailySuggestion,
  Outfit,
  WardrobeCategory,
  WardrobeItem,
} from '@/api/types';
import { colors, radii, spacing, typography } from '@/theme/tokens';

const CATEGORY_LABEL: Record<WardrobeCategory, string> = {
  tops: 'Tops',
  bottoms: 'Bottoms',
  dresses: 'Dresses',
  outerwear: 'Outerwear',
  footwear: 'Footwear',
  accessories: 'Accessories',
  ethnic: 'Ethnic',
  other: 'Other',
};

const FILTERS: { key: WardrobeCategory | 'all'; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'tops', label: 'Tops' },
  { key: 'bottoms', label: 'Bottoms' },
  { key: 'ethnic', label: 'Ethnic' },
  { key: 'footwear', label: 'Shoes' },
  { key: 'accessories', label: 'Extras' },
];

export default function WardrobeScreen() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [filter, setFilter] = useState<WardrobeCategory | 'all'>('all');
  const [daily, setDaily] = useState<DailySuggestion | null>(null);
  const [adding, setAdding] = useState(false);
  const [styling, setStyling] = useState(false);
  const [closetOutfit, setClosetOutfit] = useState<Outfit | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const list = await wardrobeApi.items();
      setItems(list.results);
      try {
        setDaily(await wardrobeApi.daily());
      } catch {
        // daily pick is a bonus — never block the wardrobe on it
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load your wardrobe.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const pickPhoto = async (fromCamera: boolean) => {
    const permission = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setError('We need photo access to add pieces. Enable it in Settings.');
      return;
    }
    const result = fromCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.7 })
      : await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          quality: 0.7,
        });
    if (result.canceled || result.assets.length === 0) return;

    setAdding(true);
    setError('');
    try {
      await wardrobeApi.addItem(result.assets[0].uri);
      await load();
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : 'Could not analyze that photo. Try another one.',
      );
    } finally {
      setAdding(false);
    }
  };

  const toggleFavorite = async (item: WardrobeItem) => {
    try {
      const updated = await wardrobeApi.updateItem(item.id, { favorite: !item.favorite });
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
    } catch {
      setError('Could not update that piece.');
    }
  };

  const markWorn = async (item: WardrobeItem) => {
    try {
      const updated = await wardrobeApi.markWorn(item.id);
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
    } catch {
      setError('Could not log that wear.');
    }
  };

  const confirmDelete = (item: WardrobeItem) => {
    Alert.alert('Remove piece', `Remove "${item.name}" from your wardrobe?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          try {
            await wardrobeApi.deleteItem(item.id);
            setItems((prev) => prev.filter((i) => i.id !== item.id));
          } catch {
            setError('Could not remove that piece.');
          }
        },
      },
    ]);
  };

  const styleFromCloset = async () => {
    setStyling(true);
    setError('');
    try {
      const result = await wardrobeApi.styleFromCloset({
        occasion: daily?.occasion ?? 'casual',
      });
      setClosetOutfit(result.outfit);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Closet styling failed. Try again.');
    } finally {
      setStyling(false);
    }
  };

  const saveClosetLook = async () => {
    if (!closetOutfit) return;
    try {
      await fashionApi.saveOutfit(closetOutfit.id);
      Alert.alert('Saved ✦', 'This closet look is in your Saved Looks.');
    } catch (e) {
      Alert.alert('Hmm', e instanceof Error ? e.message : 'Could not save the look.');
    }
  };

  const filtered = filter === 'all' ? items : items.filter((i) => i.category === filter);
  const visibleFilters = FILTERS.filter(
    ({ key }) => key === 'all' || items.some((i) => i.category === key),
  );

  return (
    <Screen subtitle="Style what you already own" title="Wardrobe">
      <View style={{ paddingHorizontal: spacing.xl }}>
        {loading ? (
          <>
            <Skeleton height={110} />
            <View style={{ height: spacing.lg }} />
            <Skeleton height={160} />
            <View style={{ height: spacing.lg }} />
            <Skeleton height={160} />
          </>
        ) : error && items.length === 0 ? (
          <ErrorState message={error} onRetry={load} />
        ) : (
          <>
            {!error ? null : (
              <Text style={styles.errorLine}>{error}</Text>
            )}

            {daily ? <DailyCard daily={daily} /> : null}

            <View style={styles.addRow}>
              <Button
                label="📷 Camera"
                variant="ghost"
                loading={adding}
                onPress={() => void pickPhoto(true)}
                style={{ flex: 1 }}
              />
              <View style={{ width: spacing.md }} />
              <Button
                label="🖼 Add from gallery"
                loading={adding}
                onPress={() => void pickPhoto(false)}
                style={{ flex: 1 }}
              />
            </View>

            {adding ? (
              <Text style={styles.analyzing}>✦ Analyzing your piece…</Text>
            ) : null}

            {items.length === 0 && !adding ? (
              <EmptyState
                emoji="▤"
                title="Your digital wardrobe"
                message={
                  'Add a few pieces — AI learns colors, fabrics and occasions, then composes outfits from clothes you already own.'
                }
              />
            ) : null}

            {items.length > 0 ? (
              <>
                <Text style={styles.sectionLabel}>
                  YOUR PIECES · {items.length}
                </Text>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
                  {visibleFilters.map(({ key, label }) => (
                    <Chip
                      key={key}
                      label={label}
                      selected={filter === key}
                      onPress={() => setFilter(key)}
                    />
                  ))}
                </View>

                <View style={styles.grid}>
                  {chunk(filtered, 2).map((row, idx) => (
                    <View key={`row-${idx}`} style={styles.gridRow}>
                      {row.map((item) => (
                        <ItemCard
                          key={item.id}
                          item={item}
                          onFavorite={() => void toggleFavorite(item)}
                          onWorn={() => void markWorn(item)}
                          onDelete={() => confirmDelete(item)}
                        />
                      ))}
                      {row.length === 1 ? <View style={{ flex: 1 }} /> : null}
                    </View>
                  ))}
                </View>
              </>
            ) : null}

            {styling ? (
              <Card>
                <ActivityIndicator color={colors.gold} />
                <Text style={styles.stylingNote}>Composing a look from your pieces…</Text>
              </Card>
            ) : items.length >= 2 && !closetOutfit ? (
              <Button
                label="Style from my closet ✦"
                variant="gold"
                onPress={() => void styleFromCloset()}
                disabled={styling}
              />
            ) : null}

            {closetOutfit ? <ClosetResult outfit={closetOutfit} onSave={() => void saveClosetLook()} /> : null}
          </>
        )}
      </View>
    </Screen>
  );
}

// ---- Daily pick card ----------------------------------------------------------

function DailyCard({ daily }: { daily: DailySuggestion }) {
  const weatherEmoji = daily.weather?.is_mock === false && daily.weather.condition.includes('Rain')
    ? '🌧'
    : (daily.weather?.temp_c ?? 28) >= 32
      ? '☀️'
      : (daily.weather?.temp_c ?? 28) < 18
        ? '🌤'
        : '⛅';
  const rec = daily.closet_outfit?.recommendation;
  return (
    <Card>
      <Text style={styles.microGold}>TODAY'S PICK</Text>
      <Text style={styles.dailyHeadline}>{daily.headline}</Text>
      {daily.tips.slice(0, 2).map((tip) => (
        <Text key={tip} style={styles.tipLine}>· {tip}</Text>
      ))}
      {rec ? (
        <>
          <Text style={styles.pickFrom}>From your closet: {rec.headline}</Text>
          {rec.outfit_components.slice(0, 3).map((c) => (
            <Text key={c.slot + c.item.description} style={styles.componentLine}>
              ◈ {c.item.description}
            </Text>
          ))}
        </>
      ) : (
        <Text style={styles.pickFrom}>Add 2+ pieces to unlock closet styling.</Text>
      )}
      <Text style={styles.weatherMeta}>
        {daily.city ? `${weatherEmoji} ${daily.city}` : `${weatherEmoji} Weather off`}
        {daily.weather ? ` · ${Math.round(daily.weather.temp_c)}°C` : ''}
      </Text>
    </Card>
  );
}

// ---- Item card -----------------------------------------------------------------

function ItemCard({
  item,
  onFavorite,
  onWorn,
  onDelete,
}: {
  item: WardrobeItem;
  onFavorite: () => void;
  onWorn: () => void;
  onDelete: () => void;
}) {
  return (
    <Card style={styles.itemCard}>
      {item.image ? (
        <Image source={{ uri: item.image }} style={styles.itemImage} />
      ) : (
        <View style={[styles.itemImage, styles.itemImagePlaceholder]}>
          <Text style={{ fontSize: 26 }}>▤</Text>
        </View>
      )}
      <TouchableOpacity
        accessibilityRole="button"
        onPress={onFavorite}
        style={styles.favButton}
      >
        <Text style={{ fontSize: 16 }}>{item.favorite ? '♥' : '♡'}</Text>
      </TouchableOpacity>

      <Text numberOfLines={1} style={styles.itemName}>{item.name}</Text>
      <View style={styles.itemMetaRow}>
        <View
          style={[
            styles.colorDot,
            { backgroundColor: item.color_hex || colors.inkBorder },
          ]}
        />
        <Text numberOfLines={1} style={styles.itemMeta}>
          {CATEGORY_LABEL[item.category] ?? item.category}
          {item.times_worn > 0 ? ` · worn ${item.times_worn}×` : ''}
        </Text>
      </View>

      <View style={styles.itemActions}>
        <TouchableOpacity accessibilityRole="button" onPress={onWorn} style={styles.actionButton}>
          <Text style={styles.actionLabel}>✓ Worn</Text>
        </TouchableOpacity>
        <TouchableOpacity
          accessibilityRole="button"
          onPress={onDelete}
          style={[styles.actionButton, { marginLeft: spacing.sm, flexGrow: 0 }]}
        >
          <Text style={[styles.actionLabel, { color: colors.danger }]}>🗑</Text>
        </TouchableOpacity>
      </View>
    </Card>
  );
}

// ---- Closet result ---------------------------------------------------------------

function ClosetResult({ outfit, onSave }: { outfit: Outfit; onSave: () => void }) {
  const rec = outfit.recommendation;
  return (
    <Card style={{ marginTop: spacing.lg }}>
      <Text style={styles.microGold}>FROM YOUR CLOSET</Text>
      <Text style={styles.resultHeadline}>{rec.headline}</Text>
      <PaletteRow palette={rec.palette} />
      <Text style={styles.explanation}>{rec.explanation}</Text>
      {rec.outfit_components.map((c) => (
        <View key={c.slot + c.item.description} style={styles.componentRow}>
          <Text style={styles.slotLabel}>{c.slot.replace('_', ' ').toUpperCase()}</Text>
          <Text style={styles.componentDesc}>{c.item.description}</Text>
        </View>
      ))}
      {(rec.styling_tips ?? []).length > 0 ? (
        <Text style={styles.tipLine}>✦ {rec.styling_tips![0]}</Text>
      ) : null}
      <Button label="Save this look" variant="gold" onPress={onSave} style={{ marginTop: spacing.lg }} />
    </Card>
  );
}

// ---- helpers ----------------------------------------------------------------------

function chunk<T>(list: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < list.length; i += size) out.push(list.slice(i, i + size));
  return out;
}

const styles = StyleSheet.create({
  analyzing: { ...typography.small, color: colors.gold, marginBottom: spacing.lg, textAlign: 'center' },
  colorDot: {
    borderColor: colors.inkBorder,
    borderRadius: 8,
    borderWidth: 1,
    height: 12,
    width: 12,
  },
  componentDesc: { ...typography.small, color: colors.textPrimary, flex: 1, marginLeft: spacing.sm },
  componentLine: { ...typography.small, color: colors.textSecondary, marginTop: 4 },
  componentRow: { alignItems: 'baseline', flexDirection: 'row', marginTop: spacing.sm },
  dailyHeadline: { ...typography.h3, color: colors.textPrimary, marginTop: spacing.xs },
  errorLine: { ...typography.small, color: colors.danger, marginBottom: spacing.lg, textAlign: 'center' },
  explanation: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  favButton: {
    alignItems: 'center',
    backgroundColor: colors.ink,
    borderColor: colors.inkBorder,
    borderRadius: 18,
    borderWidth: 1,
    height: 36,
    justifyContent: 'center',
    position: 'absolute',
    right: spacing.md,
    top: spacing.md,
    width: 36,
  },
  grid: { marginTop: spacing.md },
  gridRow: { flexDirection: 'row', gap: spacing.md },
  itemActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  actionButton: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    flexGrow: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  actionLabel: { ...typography.micro, color: colors.textSecondary, textAlign: 'center' },
  itemCard: { flex: 1, marginBottom: spacing.md, padding: spacing.md },
  itemImage: {
    backgroundColor: colors.inkElevated,
    borderRadius: radii.sm,
    height: 120,
    width: '100%',
  },
  itemImagePlaceholder: { alignItems: 'center', justifyContent: 'center' },
  itemMeta: { ...typography.micro, color: colors.textMuted, flex: 1, marginLeft: 6 },
  itemMetaRow: { alignItems: 'center', flexDirection: 'row', marginTop: 6 },
  itemName: { ...typography.h3, color: colors.textPrimary, marginTop: spacing.sm },
  microGold: { ...typography.micro, color: colors.gold, letterSpacing: 1.2 },
  pickFrom: { ...typography.small, color: colors.textPrimary, fontWeight: '600', marginTop: spacing.md },
  resultHeadline: { ...typography.h2, color: colors.textPrimary, marginTop: spacing.xs },
  sectionLabel: { ...typography.micro, color: colors.textMuted, letterSpacing: 1.2, marginBottom: spacing.sm, marginTop: spacing.xl },
  slotLabel: { ...typography.micro, color: colors.gold, width: 92 },
  stylingNote: { ...typography.body, color: colors.textSecondary, marginTop: spacing.md, textAlign: 'center' },
  tipLine: { ...typography.small, color: colors.textSecondary, marginTop: spacing.md },
  weatherMeta: { ...typography.micro, color: colors.textMuted, marginTop: spacing.md },
  addRow: { flexDirection: 'row', marginVertical: spacing.lg },
});
