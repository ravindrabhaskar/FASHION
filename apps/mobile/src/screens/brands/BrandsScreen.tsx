import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Card } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { brandsApi } from '@/api/endpoints';
import type { BrandProfile } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

export default function BrandsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [brands, setBrands] = useState<BrandProfile[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await brandsApi.list();
      setBrands(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <Screen scroll={false} title="Brands">
      <View style={{ paddingHorizontal: spacing.xl }}>
        <ButtonRow onPress={() => navigation.navigate('BecomeBrand')} label="Register your brand" />

        {loading ? (
          <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
        ) : (
          <FlatList
            data={brands}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() => navigation.navigate('BrandDetail', { slug: item.slug })}
              >
                <Card style={{ marginBottom: spacing.md }}>
                  <View style={styles.header}>
                    <Text style={styles.name}>{item.name}</Text>
                    {item.verified && (
                      <View style={styles.verifiedBadge}>
                        <Text style={styles.verifiedText}>✓ Verified</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.meta}>
                    {item.city}{item.city ? ' · ' : ''}{item.product_count} products
                  </Text>
                  {item.categories.length > 0 ? (
                    <Text style={styles.cats}>{item.categories.join(' · ')}</Text>
                  ) : null}
                </Card>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.center}>
                <Text style={styles.emptyText}>No brands yet.</Text>
              </View>
            }
          />
        )}
      </View>
    </Screen>
  );
}

function ButtonRow({ onPress, label }: { onPress: () => void; label: string }) {
  return (
    <TouchableOpacity style={styles.registerBtn} onPress={onPress}>
      <Text style={styles.registerText}>+ {label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  cats: { ...typography.micro, color: colors.gold, marginTop: spacing.sm },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  emptyText: { ...typography.body, color: colors.textSecondary },
  header: { flexDirection: 'row', justifyContent: 'space-between' },
  meta: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  name: { ...typography.h3, color: colors.textPrimary },
  registerBtn: {
    backgroundColor: colors.goldSoft,
    borderColor: colors.gold,
    borderRadius: radii.md,
    borderWidth: 1,
    marginBottom: spacing.lg,
    padding: spacing.lg,
  },
  registerText: { ...typography.h3, color: colors.gold },
  verifiedBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.goldSoft,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  verifiedText: { ...typography.micro, color: colors.gold },
});