import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { paymentsApi, ordersApi } from '@/api/endpoints';
import type { Order } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { ApiError } from '@/api/client';
import { Alert } from 'react-native';

export default function PaymentScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'Payment'>>();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { orderId } = route.params;
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [paid, setPaid] = useState(false);

  const load = useCallback(async () => {
    try {
      setOrder(await ordersApi.detail(orderId));
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => { void load(); }, [load]);

  const pay = async () => {
    setPaying(true);
    try {
      const payment = await paymentsApi.initiate(orderId, {
        provider: 'mock',
        idempotency_key: `${orderId}-${Date.now()}`,
      });
      await paymentsApi.confirm(payment.payment_id);
      setPaid(true);
      Alert.alert('Payment successful!', 'Your order is confirmed.', [
        { text: 'OK', onPress: () => navigation.navigate('Orders') },
      ]);
    } catch (e) {
      Alert.alert('Payment failed', e instanceof ApiError ? e.message : 'Could not process payment.');
    } finally {
      setPaying(false);
    }
  };

  const formatPrice = (price: number) => `₹${price.toLocaleString('en-IN')}`;

  if (loading) {
    return (
      <Screen title="Checkout">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!order) {
    return (
      <Screen title="Checkout">
        <View style={styles.center}><Text style={styles.emptyText}>Order not found.</Text></View>
      </Screen>
    );
  }

  return (
    <Screen title="Checkout">
      <View style={{ padding: spacing.xl }}>
        <Text style={styles.sectionTitle}>ORDER SUMMARY</Text>
        <Card>
          <Text style={styles.productTitle}>{order.title}</Text>
          <Text style={styles.meta}>Seller: {order.seller_name}</Text>
          <Text style={styles.meta}>Status: {order.status.replace('_', ' ')}</Text>
          <View style={styles.divider} />
          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Total</Text>
            <Text style={styles.totalValue}>{formatPrice(order.amount_inr)}</Text>
          </View>
        </Card>

        <Card style={{ marginTop: spacing.lg }}>
          <Text style={styles.sectionTitle}>PAYMENT</Text>
          {paid ? (
            <Text style={styles.successText}>✓ Payment confirmed. Order placed!</Text>
          ) : (
            <>
              <Text style={styles.meta}>
                Gateway: <Text style={{ color: colors.gold }}>Demo mock gateway</Text>
              </Text>
              <Text style={styles.meta}>No real money is charged in the demo.</Text>
              <Button
                label={`Pay ${formatPrice(order.amount_inr)}`}
                variant="gold"
                loading={paying}
                onPress={() => void pay()}
                style={{ marginTop: spacing.lg }}
              />
            </>
          )}
        </Card>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  divider: { backgroundColor: colors.inkBorder, height: 1, marginVertical: spacing.md },
  emptyText: { ...typography.body, color: colors.textSecondary },
  meta: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  productTitle: { ...typography.h2, color: colors.textPrimary },
  sectionTitle: { ...typography.micro, color: colors.gold, letterSpacing: 1.2, marginBottom: spacing.md },
  successText: { ...typography.body, color: colors.success },
  totalLabel: { ...typography.h3, color: colors.textPrimary },
  totalRow: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  totalValue: { ...typography.h1, color: colors.gold },
});