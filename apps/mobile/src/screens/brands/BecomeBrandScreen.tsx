import React, { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { brandsApi } from '@/api/endpoints';
import { ApiError } from '@/api/client';

export default function BecomeBrandScreen() {
  const navigation = useNavigation();
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [about, setAbout] = useState('');
  const [city, setCity] = useState('');
  const [website, setWebsite] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!name.trim() || !slug.trim()) {
      Alert.alert('Required', 'Brand name and a storefront link are required.');
      return;
    }
    setSubmitting(true);
    try {
      await brandsApi.register({ name: name.trim(), slug: slug.trim(), about, city: city.trim(), website: website.trim() });
      Alert.alert('Brand registered!', 'Your storefront is live.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not register brand.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Screen title="Register your brand">
        <View style={{ padding: spacing.xl }}>
          <Text style={styles.note}>
            Note: registering a brand requires your account role to be BRAND. Contact support to switch roles.
          </Text>

          <Text style={styles.label}>Brand name *</Text>
          <TextInput style={styles.input} placeholder="e.g. Studio Vivencia" placeholderTextColor={colors.textMuted} value={name} onChangeText={setName} />

          <Text style={styles.label}>Storefront link *</Text>
          <TextInput style={styles.input} placeholder="e.g. studio-vivencia" placeholderTextColor={colors.textMuted} value={slug} onChangeText={setSlug} autoCapitalize="none" />

          <Text style={styles.label}>City</Text>
          <TextInput style={styles.input} placeholder="e.g. Mumbai" placeholderTextColor={colors.textMuted} value={city} onChangeText={setCity} />

          <Text style={styles.label}>Website</Text>
          <TextInput style={styles.input} placeholder="https://..." placeholderTextColor={colors.textMuted} value={website} onChangeText={setWebsite} autoCapitalize="none" keyboardType="url" />

          <Text style={styles.label}>About</Text>
          <TextInput style={[styles.input, { minHeight: 80 }]} placeholder="Tell shoppers about your brand..." placeholderTextColor={colors.textMuted} value={about} onChangeText={setAbout} multiline />

          <Button label="Register brand" variant="gold" loading={submitting} onPress={() => void submit()} style={{ marginTop: spacing.xl }} />
        </View>
      </Screen>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  input: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    color: colors.textPrimary,
    fontSize: 15,
    marginBottom: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: 14,
    textAlignVertical: 'top',
  },
  label: { ...typography.small, color: colors.textSecondary, marginBottom: spacing.sm, marginTop: spacing.md },
  note: { ...typography.small, color: colors.textMuted, backgroundColor: colors.inkCard, borderColor: colors.inkBorder, borderRadius: radii.md, borderWidth: 1, padding: spacing.md },
  wrap: { backgroundColor: colors.ink, flex: 1 },
});