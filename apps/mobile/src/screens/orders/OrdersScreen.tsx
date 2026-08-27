import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { ordersApi } from '@/api/endpoints';
import type { Order } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

const STATUS_COLORS: Record<string, string> = {
  CREATED: colors.warning,
  AWAITING_PAYMENT: colors.warning,
  PAID: colors.gold,
  IN_PRODUCTION: colors.gold,
  SHIPPED: colors.sage,
  DELIVERED: colors.success,
  COMPLETED: colors.success,
  CANCELLED: colors.danger,
  REFUNDED: colors.danger,
};

export default function OrdersScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [scope, setScope] = useState<'mine' | 'selling'>('mine');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ordersApi.list(scope);
      setOrders(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [scope]);

  useEffect(() => { void load(); }, [load]);

  const formatPrice = (price: number) => `₹${price.toLocaleString('en-IN')}`;

  return (
    <Screen scroll={false} title="Orders">
      <View style={{ paddingHorizontal: spacing.xl }}>
        <View style={styles.scopeRow}>
          <TouchableOpacity
            style={[styles.scopeBtn, scope === 'mine' && styles.scopeActive]}
            onPress={() => setScope('mine')}
          >
            <Text style={[styles.scopeText, scope === 'mine' && styles.scopeTextActive]}>My orders</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.scopeBtn, scope === 'selling' && styles.scopeActive]}
            onPress={() => setScope('selling')}
          >
            <Text style={[styles.scopeText, scope === 'selling' && styles.scopeTextActive]}>Selling</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
        ) : (
          <FlatList
            data={orders}
            keyExtractor={(item) => item.id}
            contentContainerStyle={{ paddingBottom: spacing.xxl }}
            renderItem={({ item }) => (
              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() => navigation.navigate('OrderDetail', { orderId: item.id })}
              >
                <Card style={{ marginBottom: spacing.lg }}>
                  <View style={styles.orderHeader}>
                    <Text style={styles.orderTitle} numberOfLines={1}>{item.title}</Text>
                    <Text style={[styles.orderStatus, { color: STATUS_COLORS[item.status] ?? colors.textMuted }]}>
                      {item.status.replace('_', ' ')}
                    </Text>
                  </View>
                  <Text style={styles.orderPrice}>{formatPrice(item.amount_inr)}</Text>
                  <View style={styles.orderMeta}>
                    <Text style={styles.orderMetaText}>
                      {scope === 'mine' ? `Seller: ${item.seller_name}` : `Customer: ${item.customer_name}`}
                    </Text>
                    <Text style={styles.orderMetaText}>
                      {new Date(item.created_at).toLocaleDateString()}
                    </Text>
                  </View>
                </Card>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.center}>
                <Text style={styles.emptyText}>No orders yet.</Text>
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
  emptyText: { ...typography.body, color: colors.textSecondary },
  orderHeader: { flexDirection: 'row', justifyContent: 'space-between' },
  orderMeta: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.sm },
  orderMetaText: { ...typography.small, color: colors.textMuted },
  orderPrice: { ...typography.h3, color: colors.gold, marginTop: spacing.sm },
  orderStatus: { ...typography.micro, fontWeight: '700' },
  orderTitle: { ...typography.h3, color: colors.textPrimary, flex: 1 },
  scopeActive: { borderBottomColor: colors.gold, borderBottomWidth: 2 },
  scopeBtn: { borderBottomColor: 'transparent', borderBottomWidth: 2, marginRight: spacing.xl, paddingBottom: spacing.sm },
  scopeRow: { flexDirection: 'row', marginBottom: spacing.lg },
  scopeText: { ...typography.small, color: colors.textMuted },
  scopeTextActive: { color: colors.gold },
});
