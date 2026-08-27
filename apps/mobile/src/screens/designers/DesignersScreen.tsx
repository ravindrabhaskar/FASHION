import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Screen } from '@/components/ui/Screen';
import { Card, Chip } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { designersApi } from '@/api/endpoints';
import type { DesignerProfile } from '@/api/types';
import type { RootStackParamList } from '@/navigation/types';

const SPECIALITIES = [
  { key: '', label: 'All' },
  { key: 'bridal', label: 'Bridal' },
  { key: 'western', label: 'Western' },
  { key: 'ethnic', label: 'Ethnic' },
  { key: 'menswear', label: 'Menswear' },
  { key: 'accessories', label: 'Accessories' },
];

export default function DesignersScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [designers, setDesigners] = useState<DesignerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [speciality, setSpeciality] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await designersApi.list({
        speciality: speciality || undefined,
        search: searchQuery.trim() || undefined,
      });
      setDesigners(data.results);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, [speciality, searchQuery]);

  useEffect(() => { void load(); }, [load]);

  return (
    <Screen scroll={false} title="Designers">
      <View style={{ paddingHorizontal: spacing.xl }}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search designers..."
          placeholderTextColor={colors.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={() => void load()}
          returnKeyType="search"
        />

        <View style={styles.chipRow}>
          {SPECIALITIES.map((s) => (
            <Chip
              key={s.key}
              label={s.label}
              selected={speciality === s.key}
              onPress={() => setSpeciality(s.key)}
            />
          ))}
        </View>

        {loading ? (
          <View style={styles.center}><ActivityIndicator color={colors.gold} /></View>
        ) : (
          <FlatList
            data={designers}
            keyExtractor={(item) => item.id}
            contentContainerStyle={{ paddingBottom: spacing.xxl }}
            renderItem={({ item }) => (
              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() => navigation.navigate('DesignerDetail', { slug: item.slug })}
              >
                <Card style={{ marginBottom: spacing.lg }}>
                  <View style={styles.header}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.studioName}>{item.studio_name}</Text>
                      <Text style={styles.designerName}>{item.tagline}</Text>
                    </View>
                    {item.verified && (
                      <View style={styles.verifiedBadge}>
                        <Text style={styles.verifiedText}>✓ Verified</Text>
                      </View>
                    )}
                  </View>
                  {item.bio ? <Text style={styles.bio} numberOfLines={2}>{item.bio}</Text> : null}
                  <View style={styles.metaRow}>
                    {item.city ? <Text style={styles.metaTag}>📍 {item.city}</Text> : null}
                    {item.specialities.length > 0 && (
                      <Text style={styles.metaTag}>{item.specialities.slice(0, 2).join(' · ')}</Text>
                    )}
                  </View>
                </Card>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.center}>
                <Text style={styles.emptyText}>No designers found.</Text>
              </View>
            }
          />
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  bio: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md },
  designerName: { ...typography.small, color: colors.textMuted },
  emptyText: { ...typography.body, color: colors.textSecondary },
  header: { flexDirection: 'row', justifyContent: 'space-between' },
  metaRow: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.md },
  metaTag: { ...typography.small, color: colors.textMuted },
  searchInput: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    color: colors.textPrimary,
    fontSize: 15,
    marginBottom: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: 10,
  },
  studioName: { ...typography.h3, color: colors.textPrimary },
  verifiedBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.goldSoft,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  verifiedText: { ...typography.micro, color: colors.gold },
});
