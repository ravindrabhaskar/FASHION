import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { Card, Chip } from '@/components/ui';
import { colors, spacing, typography } from '@/theme/tokens';
import { useI18n } from '@/i18n';

export default function LanguageScreen() {
  const { locale, supported, setLocale } = useI18n();
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setSaving(false);
  }, [locale]);

  const pick = async (code: string) => {
    if (code === locale) return;
    setSaving(true);
    await setLocale(code);
  };

  const entries = Object.entries(supported);

  return (
    <View style={styles.wrap}>
      <ScrollView contentContainerStyle={{ padding: spacing.xl }}>
        <Text style={styles.header}>App language</Text>
        <Text style={styles.subheader}>
          Your stylist replies and app labels follow this language. English is the fallback.
        </Text>
        <Card style={{ marginTop: spacing.lg }}>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {entries.map(([code, label]) => (
              <View key={code} style={{ marginRight: spacing.sm, marginBottom: spacing.sm }}>
                <Chip
                  label={`${label}${saving && code === locale ? ' ✓' : ''}`}
                  selected={locale === code}
                  onPress={() => pick(code)}
                />
              </View>
            ))}
          </View>
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  header: { ...typography.display, color: colors.textPrimary, fontSize: 26 },
  subheader: { ...typography.small, color: colors.textSecondary, marginVertical: spacing.sm },
  wrap: { backgroundColor: colors.ink, flex: 1 },
});