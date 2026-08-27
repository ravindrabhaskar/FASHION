import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
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
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { designersApi } from '@/api/endpoints';
import type { DesignerProfile } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function DesignerDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'DesignerDetail'>>();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { slug } = route.params;
  const [designer, setDesigner] = useState<DesignerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setDesigner(await designersApi.detail(slug));
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return (
      <Screen title="Designer">
        <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
      </Screen>
    );
  }

  if (!designer) {
    return (
      <Screen title="Designer">
        <View style={styles.center}><Text style={styles.emptyText}>Designer not found.</Text></View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false}>
      <ScrollView contentContainerStyle={{ padding: spacing.xl }}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>

        <View style={styles.header}>
          <View>
            <Text style={styles.studioName}>{designer.studio_name}</Text>
            {designer.tagline ? <Text style={styles.designerName}>{designer.tagline}</Text> : null}
          </View>
          {designer.verified && (
            <View style={styles.verifiedBadge}>
              <Text style={styles.verifiedText}>✓ Verified</Text>
            </View>
          )}
        </View>

        {designer.bio ? <Text style={styles.bio}>{designer.bio}</Text> : null}

        <View style={styles.metaRow}>
          {designer.city ? <Text style={styles.metaTag}>📍 {designer.city}</Text> : null}
          {designer.is_accepting_custom_requests ? <Text style={styles.metaTag}>✂ taking custom work</Text> : null}
          {designer.specialities.length > 0 && (
            <Text style={styles.metaTag}>{designer.specialities.join(' · ')}</Text>
          )}
        </View>

        {designer.products && designer.products.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>COLLECTION</Text>
            <View style={styles.portfolioGrid}>
              {designer.products.map((p) => (
                <TouchableOpacity
                  key={p.id}
                  style={styles.portfolioItem}
                  onPress={() => navigation.navigate('ProductDetail', { productId: p.id })}
                >
                  {p.image ? (
                    <Image source={{ uri: p.image }} style={styles.portfolioImage} />
                  ) : (
                    <View style={[styles.portfolioImage, styles.placeholderImage]}>
                      <Text style={{ color: colors.textMuted }}>◈</Text>
                    </View>
                  )}
                  <Text style={styles.productTitle} numberOfLines={1}>{p.title}</Text>
                  <Text style={styles.productPrice}>₹{p.price_inr.toLocaleString('en-IN')}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </>
        )}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { ...typography.body, color: colors.gold, marginBottom: spacing.lg },
  bio: { ...typography.body, color: colors.textPrimary, marginTop: spacing.md },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  designerName: { ...typography.small, color: colors.textMuted },
  emptyText: { ...typography.body, color: colors.textSecondary },
  header: { flexDirection: 'row', justifyContent: 'space-between' },
  metaRow: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.md },
  metaTag: { ...typography.small, color: colors.textMuted },
  portfolioGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md },
  placeholderImage: { alignItems: 'center', backgroundColor: colors.inkElevated, justifyContent: 'center' },
  portfolioImage: { borderRadius: radii.sm, height: 130, width: '100%' },
  portfolioItem: { backgroundColor: colors.inkCard, borderRadius: radii.md, overflow: 'hidden', paddingBottom: spacing.sm, width: '48%' },
  productPrice: { ...typography.small, color: colors.gold, paddingHorizontal: spacing.sm, marginTop: 4 },
  productTitle: { ...typography.small, color: colors.textPrimary, paddingHorizontal: spacing.sm, marginTop: spacing.sm },
  sectionTitle: { ...typography.micro, color: colors.gold, letterSpacing: 1.2, marginTop: spacing.xl },
  studioName: { ...typography.h1, color: colors.textPrimary },
  verifiedBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.goldSoft,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  verifiedText: { ...typography.micro, color: colors.gold },
});
