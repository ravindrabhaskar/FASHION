import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { ordersApi } from '@/api/endpoints';
import type { Order } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { ApiError } from '@/api/client';
import { Alert } from 'react-native';

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

export default function OrderDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'OrderDetail'>>();
  const navigation = useNavigation();
  const { orderId } = route.params;
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setOrder(await ordersApi.detail(orderId));
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => { void load(); }, [load]);

  const transition = async (toStatus: string) => {
    Alert.alert('Confirm', `Move order to ${toStatus.replace('_', ' ')}?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Confirm',
        onPress: async () => {
          try {
            const updated = await ordersApi.transition(orderId, toStatus);
            setOrder(updated);
          } catch (e) {
            Alert.alert('Error', e instanceof ApiError ? e.message : 'Transition failed.');
          }
        },
      },
    ]);
  };

  const formatPrice = (price: number) => `₹${price.toLocaleString('en-IN')}`;

  if (loading) {
    return (
      <Screen title="Order">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!order) {
    return (
      <Screen title="Order">
        <View style={styles.center}><Text style={styles.emptyText}>Order not found.</Text></View>
      </Screen>
    );
  }

  return (
    <Screen title="Order Detail">
      <ScrollView contentContainerStyle={{ padding: spacing.xl }}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>

        <Card>
          <Text style={styles.productTitle}>{order.title}</Text>
          <View style={styles.statusRow}>
            <Text style={[styles.status, { color: STATUS_COLORS[order.status] ?? colors.textMuted }]}>
              {order.status.replace('_', ' ')}
            </Text>
          </View>
          <Text style={styles.price}>{formatPrice(order.amount_inr)}</Text>
          <Text style={styles.meta}>Quantity: {order.quantity}</Text>
          <Text style={styles.meta}>Seller: {order.seller_name}</Text>
          <Text style={styles.meta}>Customer: {order.customer_name}</Text>
          <Text style={styles.meta}>Created: {new Date(order.created_at).toLocaleDateString()}</Text>
        </Card>

        {order.events && order.events.length > 0 && (
          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>HISTORY</Text>
            {order.events.map((e, i) => (
              <View key={i} style={styles.eventRow}>
                <Text style={styles.eventStatus}>
                  {e.from_status.replace('_', ' ')} → {e.to_status.replace('_', ' ')}
                </Text>
                {e.note ? <Text style={styles.eventNote}>{e.note}</Text> : null}
                <Text style={styles.eventDate}>{new Date(e.created_at).toLocaleString()}</Text>
              </View>
            ))}
          </Card>
        )}

        <View style={styles.actions}>
          {order.status === 'PAID' && (
            <>
              <Button label="Start production" variant="gold" onPress={() => transition('IN_PRODUCTION')} />
              <Button label="Ship now" variant="gold" onPress={() => transition('SHIPPED')} style={{ marginTop: spacing.md }} />
            </>
          )}
          {order.status === 'IN_PRODUCTION' && (
            <Button label="Mark shipped" variant="gold" onPress={() => transition('SHIPPED')} />
          )}
          {order.status === 'SHIPPED' && (
            <Button label="Mark delivered" variant="gold" onPress={() => transition('DELIVERED')} />
          )}
          {order.status === 'DELIVERED' && (
            <>
              <Button label="Confirm delivery" variant="gold" onPress={() => transition('COMPLETED')} />
              <Button label="Refund" variant="danger" onPress={() => transition('REFUNDED')} style={{ marginTop: spacing.md }} />
            </>
          )}
          {['CREATED', 'AWAITING_PAYMENT', 'PAID', 'IN_PRODUCTION'].includes(order.status) && (
            <Button label="Cancel order" variant="danger" onPress={() => transition('CANCELLED')} style={{ marginTop: spacing.md }} />
          )}
        </View>
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { ...typography.body, color: colors.gold, marginBottom: spacing.lg },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  emptyText: { ...typography.body, color: colors.textSecondary },
  eventDate: { ...typography.micro, color: colors.textMuted, marginTop: 2 },
  eventNote: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  eventRow: { marginBottom: spacing.md },
  eventStatus: { ...typography.small, color: colors.textPrimary, fontWeight: '600' },
  actions: { marginTop: spacing.xl },
  meta: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  price: { ...typography.display, color: colors.gold, marginTop: spacing.sm },
  productTitle: { ...typography.h1, color: colors.textPrimary },
  sectionTitle: { ...typography.micro, color: colors.gold, letterSpacing: 1.2, marginBottom: spacing.md },
  status: { ...typography.h3, fontWeight: '700' },
  statusRow: { flexDirection: 'row', marginTop: spacing.sm },
});
