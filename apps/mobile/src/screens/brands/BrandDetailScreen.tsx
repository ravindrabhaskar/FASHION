import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { brandsApi } from '@/api/endpoints';
import type { BrandProfile, BrandProduct } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function BrandDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'BrandDetail'>>();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { slug } = route.params;
  const [brand, setBrand] = useState<(BrandProfile & { products: BrandProduct[] }) | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setBrand(await brandsApi.detail(slug));
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return (
      <Screen title="Brand">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!brand) {
    return (
      <Screen title="Brand">
        <View style={styles.center}><Text style={styles.emptyText}>Brand not found.</Text></View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false}>
      <FlatList
        data={brand.products ?? []}
        keyExtractor={(item) => item.id}
        numColumns={2}
        columnWrapperStyle={styles.gridRow}
        contentContainerStyle={{ padding: spacing.xl }}
        ListHeaderComponent={
          <>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={styles.back}>← Back</Text>
            </TouchableOpacity>
            <View style={styles.header}>
              <Text style={styles.name}>{brand.name}</Text>
              {brand.verified && (
                <View style={styles.verifiedBadge}>
                  <Text style={styles.verifiedText}>✓ Verified</Text>
                </View>
              )}
            </View>
            {brand.about ? <Text style={styles.about}>{brand.about}</Text> : null}
            <View style={styles.metaRow}>
              {brand.city ? <Text style={styles.metaTag}>📍 {brand.city}</Text> : null}
              {brand.categories?.length ? <Text style={styles.metaTag}>{brand.categories.join(' · ')}</Text> : null}
            </View>
            {brand.website ? <Text style={styles.website}>{brand.website}</Text> : null}
            <Text style={styles.sectionTitle}>PRODUCTS</Text>
          </>
        }
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
            <Text style={styles.productPrice}>₹{item.price_inr.toLocaleString('en-IN')}</Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <Text style={styles.noProducts}>No products in this store yet.</Text>
        }
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  about: { ...typography.body, color: colors.textSecondary, marginTop: spacing.md },
  back: { ...typography.body, color: colors.gold, marginBottom: spacing.lg },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  emptyText: { ...typography.body, color: colors.textSecondary },
  gridRow: { gap: spacing.md },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md },
  metaTag: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    color: colors.textSecondary,
    fontSize: 11,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  name: { ...typography.h1, color: colors.textPrimary },
  noProducts: { ...typography.small, color: colors.textMuted, marginTop: spacing.lg, textAlign: 'center' },
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
  productImage: { height: 140, width: '100%' },
  productPrice: { ...typography.h3, color: colors.gold, paddingHorizontal: spacing.sm, marginTop: spacing.sm },
  productTitle: { ...typography.small, color: colors.textPrimary, paddingHorizontal: spacing.sm, marginTop: spacing.sm },
  sectionTitle: { ...typography.micro, color: colors.gold, letterSpacing: 1.2, marginBottom: spacing.md, marginTop: spacing.xl },
  verifiedBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.goldSoft,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  verifiedText: { ...typography.micro, color: colors.gold },
  website: { ...typography.small, color: colors.gold, marginTop: spacing.md },
});