import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { quotesApi } from '@/api/endpoints';
import type { QuoteRequest } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { ApiError } from '@/api/client';

export default function QuoteDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'QuoteDetail'>>();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { requestId } = route.params;
  const [request, setRequest] = useState<QuoteRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [offersData, listData] = await Promise.all([
        quotesApi.offers(requestId),
        quotesApi.list(),
      ]);
      const req = listData.results.find((r) => r.id === requestId) ?? null;
      if (req) req.offers = offersData.results;
      setRequest(req);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [requestId]);

  useEffect(() => { void load(); }, [load]);

  const acceptOffer = async (offerId: string) => {
    setAccepting(true);
    try {
      await quotesApi.accept(offerId);
      Alert.alert('Offer accepted!', 'Your order has been created.', [
        { text: 'OK', onPress: () => navigation.navigate('Orders') },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not accept offer.');
    } finally {
      setAccepting(false);
    }
  };

  if (loading) {
    return (
      <Screen title="Quote">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!request) {
    return (
      <Screen title="Quote">
        <View style={styles.center}><Text style={styles.emptyText}>Quote not found.</Text></View>
      </Screen>
    );
  }

  return (
    <Screen title="Quote Detail">
      <ScrollView contentContainerStyle={{ padding: spacing.xl }}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>

        <Card>
          <Text style={styles.title}>{request.product_title || 'Custom design'}</Text>
          <Text style={styles.brief}>{request.brief}</Text>
          {request.budget_inr ? (
            <Text style={styles.budget}>Budget: ₹{request.budget_inr.toLocaleString('en-IN')}</Text>
          ) : null}
          {request.designer ? (
            <Text style={styles.designer}>Studio: {request.designer.studio_name}</Text>
          ) : null}
        </Card>

        <Text style={styles.sectionTitle}>OFFERS</Text>
        {request.offers.length === 0 ? (
          <Card>
            <Text style={styles.emptyText}>No offers yet.</Text>
          </Card>
        ) : (
          request.offers.map((offer) => (
            <Card key={offer.id} style={{ marginBottom: spacing.md }}>
              <View style={styles.offerHeader}>
                <Text style={styles.offerPrice}>₹{offer.price_inr.toLocaleString('en-IN')}</Text>
                <Text style={styles.offerTimeline}>{offer.timeline_days} days</Text>
              </View>
              {offer.notes ? <Text style={styles.notes}>{offer.notes}</Text> : null}
              <Text style={styles.offerStatus}>{offer.status.replace('_', ' ')}</Text>
              {offer.status === 'PROPOSED' && (
                <Button
                  label="Accept offer"
                  variant="gold"
                  loading={accepting}
                  onPress={() => void acceptOffer(offer.id)}
                  style={{ marginTop: spacing.md }}
                />
              )}
            </Card>
          ))
        )}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { ...typography.body, color: colors.gold, marginBottom: spacing.lg },
  brief: { ...typography.body, color: colors.textPrimary, marginTop: spacing.sm },
  budget: { ...typography.small, color: colors.gold, marginTop: spacing.md },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  designer: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  emptyText: { ...typography.body, color: colors.textSecondary },
  notes: { ...typography.small, color: colors.textSecondary, marginTop: spacing.sm },
  offerHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  offerPrice: { ...typography.h1, color: colors.gold },
  offerStatus: { ...typography.micro, color: colors.gold, marginTop: spacing.sm },
  offerTimeline: { ...typography.small, color: colors.textMuted },
  sectionTitle: { ...typography.micro, color: colors.gold, letterSpacing: 1.2, marginBottom: spacing.md, marginTop: spacing.xl },
  title: { ...typography.h1, color: colors.textPrimary },
});