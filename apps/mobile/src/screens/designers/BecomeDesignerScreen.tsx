import React, { useEffect, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Screen } from '@/components/ui/Screen';
import { Button } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { designersApi } from '@/api/endpoints';
import { ApiError } from '@/api/client';

const SPECIALITIES = ['bridal', 'western', 'ethnic', 'menswear', 'accessories', 'couture'];

export default function BecomeDesignerScreen() {
  const navigation = useNavigation();
  const [studioName, setStudioName] = useState('');
  const [bio, setBio] = useState('');
  const [city, setCity] = useState('');
  const [specialities, setSpecialities] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [existing, setExisting] = useState(false);

  useEffect(() => {
    designersApi.me()
      .then(() => setExisting(true))
      .catch(() => undefined);
  }, []);

  const toggle = (s: string) =>
    setSpecialities((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);

  const submit = async () => {
    if (!studioName.trim()) {
      Alert.alert('Studio name required');
      return;
    }
    setSubmitting(true);
    try {
      await designersApi.register({
        studio_name: studioName.trim(),
        bio: bio.trim(),
        city: city.trim(),
        specialities,
      });
      Alert.alert(existing ? 'Designer profile updated!' : 'You are now a designer!', 'Your studio is live.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not register studio.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Screen title={existing ? 'Update studio' : 'Become a designer'}>
        <View style={{ padding: spacing.xl }}>
          <Text style={styles.label}>Studio name *</Text>
          <TextInput style={styles.input} placeholder="Your studio / label" placeholderTextColor={colors.textMuted} value={studioName} onChangeText={setStudioName} />

          <Text style={styles.label}>City</Text>
          <TextInput style={styles.input} placeholder="e.g. Jaipur" placeholderTextColor={colors.textMuted} value={city} onChangeText={setCity} />

          <Text style={styles.label}>Bio</Text>
          <TextInput style={[styles.input, { minHeight: 80 }]} placeholder="Tell buyers about your work" placeholderTextColor={colors.textMuted} value={bio} onChangeText={setBio} multiline />

          <Text style={styles.label}>Specialities</Text>
          <View style={styles.chipWrap}>
            {SPECIALITIES.map((s) => (
              <TouchableChip key={s} label={s} selected={specialities.includes(s)} onPress={() => toggle(s)} />
            ))}
          </View>

          <Button label={existing ? 'Save changes' : 'Launch studio'} variant="gold" loading={submitting} onPress={() => void submit()} style={{ marginTop: spacing.xl }} />
        </View>
      </Screen>
    </KeyboardAvoidingView>
  );
}

function TouchableChip({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[styles.chip, selected && styles.chipSelected]}
      accessibilityRole="button"
    >
      <Text style={[styles.chipLabel, selected && { color: colors.ink }]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  chip: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: 8,
  },
  chipLabel: { ...typography.small, color: colors.textSecondary, fontWeight: '600' },
  chipSelected: { backgroundColor: colors.gold, borderColor: colors.gold },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap' },
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
  wrap: { backgroundColor: colors.ink, flex: 1 },
});