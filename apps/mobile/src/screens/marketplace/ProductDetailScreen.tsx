import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { marketplaceApi, chatApi } from '@/api/endpoints';
import type { Product } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { useAuth } from '@/state/auth';
import { ApiError } from '@/api/client';

export default function ProductDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'ProductDetail'>>();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { productId } = route.params;
  const { user } = useAuth();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [chatLoading, setChatLoading] = useState(false);
  const [buying, setBuying] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState<Product['variants'][number] | null>(null);

  const load = useCallback(async () => {
    try {
      setProduct(await marketplaceApi.product(productId));
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => { void load(); }, [load]);

  const startChat = async () => {
    if (!product) return;
    setChatLoading(true);
    try {
      const thread = await chatApi.createThread({
        seller_user_id: product.seller_user_id,
        product_id: product.id,
        subject: `About: ${product.title}`,
      });
      navigation.navigate('ChatThread', { threadId: thread.id, subject: thread.subject });
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not start chat.');
    } finally {
      setChatLoading(false);
    }
  };

  const buyNow = async () => {
    if (!product) return;
    if (!product.in_stock) {
      Alert.alert('Out of stock', 'This product is currently unavailable.');
      return;
    }
    setBuying(true);
    try {
      const order = await marketplaceApi.buy(product.id);
      navigation.navigate('Payment', { orderId: order.id });
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not place the order.');
    } finally {
      setBuying(false);
    }
  };

  const formatPrice = (price: number) => `₹${price.toLocaleString('en-IN')}`;

  if (loading) {
    return (
      <Screen title="Product">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!product) {
    return (
      <Screen title="Product">
        <View style={styles.center}><Text style={styles.emptyText}>Product not found.</Text></View>
      </Screen>
    );
  }

  const isSeller = product.seller_user_id === user?.id;

  return (
    <Screen scroll={false}>
      <ScrollView contentContainerStyle={{ padding: spacing.xl }}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>

        {product.image ? (
          <Image source={{ uri: product.image }} style={styles.heroImage} />
        ) : (
          <View style={[styles.heroImage, styles.heroPlaceholder]}>
            <Text style={{ fontSize: 48, color: colors.textMuted }}>◈</Text>
          </View>
        )}

        <Text style={styles.title}>{product.title}</Text>
        <Text style={styles.price}>{formatPrice(product.price_inr)}</Text>

        <View style={styles.metaRow}>
          {product.category ? <Text style={styles.metaTag}>{product.category.toUpperCase()}</Text> : null}
          {product.city ? <Text style={styles.metaTag}>{product.city}</Text> : null}
          {product.ready_to_ship ? <Text style={styles.metaTag}>Ready to ship</Text> : null}
          {product.is_customizable ? <Text style={styles.metaTag}>Customizable</Text> : null}
        </View>

        {product.description ? <Text style={styles.description}>{product.description}</Text> : null}
        {product.fabric ? <Text style={styles.fabric}>Fabric: {product.fabric}</Text> : null}
        <Text style={styles.stock}>
          {product.in_stock ? 'In stock' : 'Out of stock'}
        </Text>

        {product.variants.length > 0 && (
          <View style={{ marginTop: spacing.md }}>
            <Text style={styles.fabric}>Select variant</Text>
            {product.variants.map((v) => {
              const active = selectedVariant?.id === v.id;
              return (
                <TouchableOpacity
                  key={v.id}
                  style={[styles.variantChip, active && styles.variantChipActive]}
                  onPress={() => setSelectedVariant(v)}
                >
                  <Text style={styles.variantText}>
                    {v.name}: {v.value}
                    {v.price_delta_inr ? ` (+₹${v.price_delta_inr})` : ''}
                    {v.stock ? '' : ' · sold out'}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        <Text style={styles.seller}>Sold by: {product.seller_name}</Text>

        {!isSeller && (
          <>
            <Button
              label={product.is_customizable ? '✂ Request custom quote' : '✂ Ask for quote'}
              variant="ghost"
              onPress={() => navigation.navigate('QuoteRequestScreen', { productId: product.id })}
              style={{ marginTop: spacing.lg }}
            />
            <Button
              label={product.in_stock ? '🛒 Buy now' : 'Out of stock'}
              variant="gold"
              disabled={!product.in_stock}
              loading={buying}
              onPress={() => void buyNow()}
              style={{ marginTop: spacing.md }}
            />
            <Button
              label="💬 Chat with seller"
              loading={chatLoading}
              onPress={() => void startChat()}
              style={{ marginTop: spacing.md }}
            />
          </>
        )}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { ...typography.body, color: colors.gold, marginBottom: spacing.lg },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  description: { ...typography.body, color: colors.textPrimary, marginTop: spacing.md },
  emptyText: { ...typography.body, color: colors.textSecondary },
  fabric: { ...typography.small, color: colors.textSecondary, marginTop: spacing.sm },
  heroImage: { borderRadius: radii.lg, height: 320, marginBottom: spacing.lg, width: '100%' },
  heroPlaceholder: { alignItems: 'center', backgroundColor: colors.inkElevated, justifyContent: 'center' },
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
  price: { ...typography.display, color: colors.gold },
  seller: { ...typography.small, color: colors.textMuted, marginTop: spacing.md },
  stock: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  title: { ...typography.h1, color: colors.textPrimary },
  variantChip: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    marginRight: spacing.sm,
    marginTop: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  variantChipActive: { backgroundColor: colors.goldSoft, borderColor: colors.gold },
  variantText: { ...typography.small, color: colors.textPrimary },
});
