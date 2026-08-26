import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Button, Chip } from '@/components/ui';
import { Screen } from '@/components/ui/Screen';
import { colors, spacing, typography } from '@/theme/tokens';
import { profileApi } from '@/api/endpoints';
import { useAuth } from '@/state/auth';

const STYLE_TAGS = [
  ['minimal', 'Minimal'],
  ['classic', 'Classic'],
  ['streetwear', 'Streetwear'],
  ['ethnic-traditional', 'Traditional'],
  ['fusion', 'Fusion'],
  ['smart-casual', 'Smart Casual'],
  ['sporty-athleisure', 'Athleisure'],
  ['romantic', 'Romantic'],
];

const OCCASIONS = [
  ['office', 'Office'],
  ['college', 'College'],
  ['wedding', 'Weddings'],
  ['festival', 'Festivals'],
  ['party', 'Parties'],
  ['casual', 'Everyday'],
];

const COLORS = [
  ['navy', 'Navy'],
  ['black', 'Black'],
  ['white', 'White'],
  ['emerald-green', 'Emerald'],
  ['blush-pink', 'Blush'],
  ['marigold', 'Marigold'],
  ['olive', 'Olive'],
  ['wine', 'Wine'],
];

const BUDGETS: [string, number][] = [
  ['Under ₹2,000', 2000],
  ['₹2,000–5,000', 5000],
  ['₹5,000–10,000', 10000],
  ['₹10,000+', 25000],
];

export default function OnboardingScreen() {
  const { user, refreshUser } = useAuth();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [styles_, setStyles] = useState<string[]>([]);
  const [occasions, setOccasions] = useState<string[]>([]);
  const [colors_, setColors] = useState<string[]>([]);
  const [budgetIdx, setBudgetIdx] = useState<number | null>(null);

  const steps = useMemo(
    () => [
      {
        key: 'welcome',
        title: `Hi ${user?.full_name?.split(' ')[0] ?? 'there'} 👋`,
        subtitle: "Let's understand your style so AI can design for you. Takes under a minute.",
      },
      { key: 'styles', title: 'What feels like you?', subtitle: 'Pick up to 4 styles.' },
      { key: 'colors', title: 'Your go-to colours', subtitle: 'Pick the shades you love wearing.' },
      { key: 'occasions', title: 'Where do you dress for?', subtitle: 'Pick your usual occasions.' },
      { key: 'budget', title: 'Comfortable budget?', subtitle: 'Per outfit — you can change this anytime.' },
    ],
    [user],
  );

  const toggle = (list: string[], setList: (v: string[]) => void, value: string) =>
    setList(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);

  const finish = async () => {
    setError('');
    setSaving(true);
    try {
      await profileApi.patchStyleProfile({
        preferred_styles: styles_,
        favorite_colors: colors_,
        common_occasions: occasions,
        budget_max: budgetIdx != null ? BUDGETS[budgetIdx][1] : null,
        budget_min: budgetIdx === 1 ? 2000 : budgetIdx === 2 ? 5000 : budgetIdx === 3 ? 10000 : null,
      });
      await refreshUser();
    } catch {
      setError('Could not save your style profile. Check your connection and retry.');
      setSaving(false);
    }
  };

  const canContinue =
    step === 0 ||
    (step === 1 && styles_.length > 0) ||
    (step === 2 && colors_.length > 0) ||
    (step === 3 && occasions.length > 0) ||
    step === 4;

  return (
    <Screen subtitle={steps[step].subtitle} title={steps[step].title}>
      <View style={styles.body}>
        <Text style={styles.progress}>
          Step {step + 1} of {steps.length}
        </Text>

        {step === 0 && (
          <View style={styles.heroCard}>
            <Text style={{ fontSize: 52 }}>✂</Text>
            <Text style={styles.heroText}>
              Upload a photo. Pick an occasion. Get a look designed just for you — then tweak it
              conversationally.
            </Text>
          </View>
        )}

        {step === 1 && (
          <View style={styles.chipWrap}>
            {STYLE_TAGS.map(([slug, label]) => (
              <Chip
                key={slug}
                label={label}
                selected={styles_.includes(slug)}
                onPress={() => styles_.length < 4 && toggle(styles_, setStyles, slug)}
              />
            ))}
          </View>
        )}

        {step === 2 && (
          <View style={styles.chipWrap}>
            {COLORS.map(([slug, label]) => (
              <Chip
                key={slug}
                label={label}
                selected={colors_.includes(slug)}
                onPress={() => toggle(colors_, setColors, slug)}
              />
            ))}
          </View>
        )}

        {step === 3 && (
          <View style={styles.chipWrap}>
            {OCCASIONS.map(([slug, label]) => (
              <Chip
                key={slug}
                label={label}
                selected={occasions.includes(slug)}
                onPress={() => toggle(occasions, setOccasions, slug)}
              />
            ))}
          </View>
        )}

        {step === 4 && (
          <View style={styles.chipWrap}>
            {BUDGETS.map(([label], index) => (
              <Chip
                key={label}
                label={label}
                selected={budgetIdx === index}
                onPress={() => setBudgetIdx(index)}
              />
            ))}
          </View>
        )}

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <View style={{ marginTop: spacing.xl }}>
          {step < steps.length - 1 ? (
            <>
              <Button disabled={!canContinue} label="Continue" onPress={() => setStep(step + 1)} />
              {step > 0 && (
                <Button label="Back" variant="ghost" onPress={() => setStep(step - 1)} style={styles.gap} />
              )}
            </>
          ) : (
            <>
              <Button label="Start styling ✦" loading={saving} onPress={finish} />
              <Button
                label="Skip for now"
                variant="ghost"
                onPress={finish}
                style={styles.gap}
              />
            </>
          )}
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: { padding: spacing.xl },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', marginTop: spacing.lg },
  error: { ...typography.small, color: colors.danger, marginTop: spacing.md },
  gap: { marginTop: spacing.md },
  heroCard: {
    alignItems: 'center',
    backgroundColor: colors.inkElevated,
    borderColor: colors.goldSoft,
    borderRadius: 24,
    borderWidth: 1,
    padding: spacing.xxl,
  },
  heroText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.lg,
    textAlign: 'center',
  },
  progress: { ...typography.micro, color: colors.gold, marginBottom: spacing.lg },
});
