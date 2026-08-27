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
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Card, Chip } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { marketplaceApi } from '@/api/endpoints';
import type { Product } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

const CATEGORIES = [
  { key: 'all', label: 'All' },
  { key: 'tops', label: 'Tops' },
  { key: 'bottoms', label: 'Bottoms' },
  { key: 'dresses', label: 'Dresses' },
  { key: 'ethnic', label: 'Ethnic' },
  { key: 'accessories', label: 'Accessories' },
  { key: 'footwear', label: 'Footwear' },
];

export default function MarketplaceScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await marketplaceApi.products({
        category: category === 'all' ? undefined : category,
      });
      setProducts(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => { void load(); }, [load]);

  const search = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await marketplaceApi.search(searchQuery.trim());
      // Search returns full product payloads + a relevance score
      setProducts(data.results as unknown as Product[]);
    } catch { /* ignore */ } finally {
      setSearching(false);
    }
  };

  const formatPrice = (price: number) =>
    `₹${price.toLocaleString('en-IN')}`;

  return (
    <Screen scroll={false} title="Marketplace">
      <View style={{ paddingHorizontal: spacing.xl }}>
        <View style={styles.searchRow}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search fashion..."
            placeholderTextColor={colors.textMuted}
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={() => void search()}
            returnKeyType="search"
          />
          {searching ? <ActivityIndicator color={colors.gold} style={{ marginLeft: spacing.md }} /> : null}
        </View>

        <View style={styles.categoryRow}>
          {CATEGORIES.map((c) => (
            <Chip
              key={c.key}
              label={c.label}
              selected={category === c.key}
              onPress={() => { setCategory(c.key); setSearchQuery(''); }}
            />
          ))}
        </View>

        {loading ? (
          <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
        ) : (
          <FlatList
            data={products}
            keyExtractor={(item) => item.id}
            numColumns={2}
            columnWrapperStyle={styles.gridRow}
            contentContainerStyle={{ paddingBottom: spacing.xxl }}
            renderItem={({ item }) => (
              <TouchableOpacity
                activeOpacity={0.85}
                style={styles.productCard}
                onPress={() => navigation.navigate('ProductDetail', { productId: item.id })}
              >
                {item.image ? (
                  <Image source={{ uri: item.image }} style={styles.productImage} />
                ) : (
                  <View style={[styles.productImage, styles.placeholderImage]}>
                    <Text style={{ fontSize: 24, color: colors.textMuted }}>◈</Text>
                  </View>
                )}
                <Text style={styles.productTitle} numberOfLines={2}>{item.title}</Text>
                <Text style={styles.productPrice}>{formatPrice(item.price_inr)}</Text>
                {item.city ? <Text style={styles.productCity}>{item.city}</Text> : null}
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.center}>
                <Text style={styles.emptyText}>No products found.</Text>
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
  categoryRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md },
  emptyText: { ...typography.body, color: colors.textSecondary },
  gridRow: { gap: spacing.md },
  placeholderImage: { alignItems: 'center', backgroundColor: colors.inkElevated, justifyContent: 'center' },
  productCard: {
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    flex: 1,
    marginBottom: spacing.md,
    maxWidth: '48%',
    overflow: 'hidden',
  },
  productCity: { ...typography.micro, color: colors.textMuted, paddingHorizontal: spacing.md, paddingBottom: spacing.md },
  productImage: { height: 160, width: '100%' },
  productPrice: { ...typography.h3, color: colors.gold, paddingHorizontal: spacing.md, marginTop: spacing.sm },
  productTitle: { ...typography.small, color: colors.textPrimary, paddingHorizontal: spacing.md, marginTop: spacing.sm },
  searchInput: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    color: colors.textPrimary,
    flex: 1,
    fontSize: 15,
    paddingHorizontal: spacing.lg,
    paddingVertical: 10,
  },
  searchRow: { alignItems: 'center', flexDirection: 'row', marginBottom: spacing.md },
});
