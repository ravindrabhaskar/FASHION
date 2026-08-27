import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { campaignsApi } from '@/api/endpoints';
import type { Campaign } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { useAuth } from '@/state/auth';

export default function CampaignsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { user } = useAuth();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await campaignsApi.list();
      setCampaigns(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <Screen scroll={false} title="Campaigns">
      <View style={{ paddingHorizontal: spacing.xl }}>
        {user?.role === 'BRAND' && (
          <TouchableOpacity
            style={styles.createBtn}
            onPress={() => navigation.navigate('CreateCampaign')}
          >
            <Text style={styles.createText}>+ Create campaign</Text>
          </TouchableOpacity>
        )}

        {loading ? (
          <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
        ) : (
          <FlatList
            data={campaigns}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() => navigation.navigate('CampaignDetail', { campaignId: item.id })}
              >
                <Card style={{ marginBottom: spacing.md }}>
                  <Text style={styles.title}>{item.title}</Text>
                  <Text style={styles.brief} numberOfLines={2}>{item.brief}</Text>
                  <View style={styles.metaRow}>
                    {item.brand_name ? <Text style={styles.metaTag}>{item.brand_name}</Text> : null}
                    <Text style={styles.metaTag}>₹{item.payout_inr?.toLocaleString('en-IN') ?? '—'} payout</Text>
                    <Text style={styles.metaTag}>👥 {item.min_audience}+</Text>
                  </View>
                  <Text style={styles.apps}>{item.application_count} application(s)</Text>
                </Card>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.center}>
                <Text style={styles.emptyText}>No open campaigns.</Text>
              </View>
            }
          />
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  apps: { ...typography.micro, color: colors.gold, marginTop: spacing.sm },
  brief: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  createBtn: {
    backgroundColor: colors.goldSoft,
    borderColor: colors.gold,
    borderRadius: radii.md,
    borderWidth: 1,
    marginBottom: spacing.lg,
    padding: spacing.lg,
  },
  createText: { ...typography.h3, color: colors.gold },
  emptyText: { ...typography.body, color: colors.textSecondary },
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
  title: { ...typography.h3, color: colors.textPrimary },
});