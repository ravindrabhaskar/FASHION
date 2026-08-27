import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { marketplaceApi } from '@/api/endpoints';
import type { Product } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function MyProductsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await marketplaceApi.products({ mine: true });
      setProducts(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const remove = (product: Product) => {
    Alert.alert('Remove product', `Deactivate "${product.title}"?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          try {
            await marketplaceApi.deleteProduct(product.id);
            setProducts((prev) => prev.filter((p) => p.id !== product.id));
          } catch {
            Alert.alert('Error', 'Could not remove product.');
          }
        },
      },
    ]);
  };

  const formatPrice = (price: number) => `₹${price.toLocaleString('en-IN')}`;

  return (
    <Screen scroll={false} title="My Products">
      <View style={{ paddingHorizontal: spacing.xl }}>
        <Button
          label="+ Add product"
          variant="gold"
          onPress={() => navigation.navigate('CreateProduct', {})}
          style={{ marginBottom: spacing.lg }}
        />

        {loading ? (
          <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
        ) : (
          <FlatList
            data={products}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <Card style={{ marginBottom: spacing.md }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                  <Text style={styles.title} numberOfLines={1}>{item.title}</Text>
                  <Text style={styles.price}>{formatPrice(item.price_inr)}</Text>
                </View>
                <Text style={styles.meta}>
                  {item.category} · {item.in_stock ? 'In stock' : 'Out of stock'}
                </Text>
                <View style={styles.actions}>
                  <Button
                    label="Edit"
                    variant="ghost"
                    onPress={() => navigation.navigate('CreateProduct', { productId: item.id })}
                    style={{ flex: 1 }}
                  />
                  <View style={{ width: spacing.sm }} />
                  <Button label="Delete" variant="danger" onPress={() => remove(item)} style={{ flex: 1 }} />
                </View>
              </Card>
            )}
            ListEmptyComponent={
              <View style={styles.center}>
                <Text style={styles.emptyText}>You haven't listed any products yet.</Text>
              </View>
            }
          />
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { flexDirection: 'row', marginTop: spacing.md },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  emptyText: { ...typography.body, color: colors.textSecondary },
  meta: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  price: { ...typography.h3, color: colors.gold },
  title: { ...typography.h3, color: colors.textPrimary, flex: 1 },
});