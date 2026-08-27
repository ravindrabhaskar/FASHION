import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button, Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { campaignsApi } from '@/api/endpoints';
import type { Campaign } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';
import { useAuth } from '@/state/auth';
import { ApiError } from '@/api/client';

export default function CampaignDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'CampaignDetail'>>();
  const navigation = useNavigation();
  const { campaignId } = route.params;
  const { user } = useAuth();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [pitch, setPitch] = useState('');

  const load = useCallback(async () => {
    try {
      setCampaign(await campaignsApi.detail(campaignId));
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => { void load(); }, [load]);

  const apply = async () => {
    if (!pitch.trim()) {
      Alert.alert('Pitch required', 'Tell the brand why you want to collaborate.');
      return;
    }
    setApplying(true);
    try {
      await campaignsApi.apply(campaignId, pitch.trim());
      Alert.alert('Applied!', 'The brand will review your pitch.');
      void load();
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not apply.');
    } finally {
      setApplying(false);
    }
  };

  const review = async (applicationId: string, accept: boolean) => {
    try {
      await campaignsApi.review(applicationId, accept);
      Alert.alert(accept ? 'Accepted' : 'Rejected', 'Application updated.');
      void load();
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not update.');
    }
  };

  if (loading) {
    return (
      <Screen title="Campaign">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!campaign) {
    return (
      <Screen title="Campaign">
        <View style={styles.center}><Text style={styles.emptyText}>Campaign not found.</Text></View>
      </Screen>
    );
  }

  const isBrand = user?.role === 'BRAND';

  return (
    <Screen title="Campaign">
      <ScrollView contentContainerStyle={{ padding: spacing.xl }}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>

        <Card>
          <Text style={styles.title}>{campaign.title}</Text>
          <Text style={styles.brand}>{campaign.brand_name}</Text>
          <Text style={styles.brief}>{campaign.brief}</Text>
          <View style={styles.metaRow}>
            <Text style={styles.metaTag}>Payout: ₹{campaign.payout_inr?.toLocaleString('en-IN') ?? '—'}</Text>
            <Text style={styles.metaTag}>Budget: ₹{campaign.budget_inr.toLocaleString('en-IN')}</Text>
            <Text style={styles.metaTag}>Min audience: {campaign.min_audience.toLocaleString()}</Text>
          </View>
          {campaign.deliverables.length > 0 && (
            <Text style={styles.deliverables}>
              Deliverables: {campaign.deliverables.join(' · ')}
            </Text>
          )}
        </Card>

        {isBrand && campaign.applications && campaign.applications.length > 0 ? (
          <>
            <Text style={styles.sectionTitle}>APPLICATIONS</Text>
            {campaign.applications.map((app) => (
              <Card key={app.id} style={{ marginBottom: spacing.md }}>
                <Text style={styles.appHandle}>@{app.handle}</Text>
                <Text style={styles.appAudience}>{app.audience_size.toLocaleString()} followers</Text>
                <Text style={styles.appPitch}>{app.pitch}</Text>
                <Text style={styles.appStatus}>{app.status.replace('_', ' ')}</Text>
                {app.status === 'PENDING' && (
                  <View style={styles.reviewRow}>
                    <Button label="Accept" variant="gold" onPress={() => void review(app.id, true)} style={{ flex: 1 }} />
                    <View style={{ width: spacing.sm }} />
                    <Button label="Reject" variant="danger" onPress={() => void review(app.id, false)} style={{ flex: 1 }} />
                  </View>
                )}
              </Card>
            ))}
          </>
        ) : (
          <>
            {campaign.my_application_status ? (
              <Card style={{ marginTop: spacing.lg }}>
                <Text style={styles.appliedText}>
                  ✓ You applied · Status: {campaign.my_application_status.replace('_', ' ')}
                </Text>
              </Card>
            ) : (
              <Card style={{ marginTop: spacing.lg }}>
                <Text style={styles.sectionTitle}>APPLY</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Tell the brand your pitch..."
                  placeholderTextColor={colors.textMuted}
                  value={pitch}
                  onChangeText={setPitch}
                  multiline
                />
                <Button label="Apply" variant="gold" loading={applying} onPress={() => void apply()} />
              </Card>
            )}
          </>
        )}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  appAudience: { ...typography.small, color: colors.textMuted },
  appHandle: { ...typography.h3, color: colors.textPrimary },
  appPitch: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  appStatus: { ...typography.micro, color: colors.gold, marginTop: spacing.sm },
  appliedText: { ...typography.body, color: colors.success },
  back: { ...typography.body, color: colors.gold, marginBottom: spacing.lg },
  brand: { ...typography.small, color: colors.textMuted, marginTop: 4 },
  brief: { ...typography.body, color: colors.textPrimary, marginTop: spacing.md },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  deliverables: { ...typography.small, color: colors.textSecondary, marginTop: spacing.md },
  emptyText: { ...typography.body, color: colors.textSecondary },
  input: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    color: colors.textPrimary,
    fontSize: 15,
    marginBottom: spacing.md,
    minHeight: 80,
    paddingHorizontal: spacing.lg,
    paddingVertical: 12,
    textAlignVertical: 'top',
  },
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
  reviewRow: { flexDirection: 'row', marginTop: spacing.md },
  sectionTitle: { ...typography.micro, color: colors.gold, letterSpacing: 1.2, marginBottom: spacing.md },
  title: { ...typography.h1, color: colors.textPrimary },
});