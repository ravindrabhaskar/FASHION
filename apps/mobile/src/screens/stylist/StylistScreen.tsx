import React, { useState } from 'react';
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput as RNInput,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Button, Card, Chip, ErrorState } from '@/components/ui';
import { Screen } from '@/components/ui/Screen';
import { PaletteRow } from '@/components/ui/OutfitCard';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { fashionApi, plansApi } from '@/api/endpoints';
import type { Entitlements, Occasion, Outfit, RecommendationResult } from '@/api/types';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RootStackParamList } from '@/navigation/types';

type Phase = 'setup' | 'analyzing' | 'result';

const BUDGET_OPTIONS = [2000, 3500, 5000, 8000];

export default function StylistScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [occasions, setOccasions] = useState<Occasion[]>([]);
  const [occasion, setOccasion] = useState<string | null>(null);
  const [budget, setBudget] = useState<number | null>(3500);
  const [notes, setNotes] = useState('');
  const [phase, setPhase] = useState<Phase>('setup');
  const [outfit, setOutfit] = useState<Outfit | null>(null);
  const [error, setError] = useState('');
  const [entitlements, setEntitlements] = useState<Entitlements | null>(null);

  React.useEffect(() => {
    fashionApi
      .occasions()
      .then(setOccasions)
      .catch(() => setOccasions([]));
    plansApi
      .entitlements()
      .then(setEntitlements)
      .catch(() => undefined);
  }, []);

  const pickPhoto = async (fromCamera: boolean) => {
    const permission = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setError('We need photo access to style you. Enable it in Settings.');
      return;
    }
    const result = fromCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.7 })
      : await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          quality: 0.7,
        });
    if (!result.canceled && result.assets.length > 0) {
      setPhotoUri(result.assets[0].uri);
      setError('');
    }
  };

  const styleMe = async () => {
    setError('');
    setPhase('analyzing');
    try {
      // Step 1: photo analysis when a photo is provided.
      let analysis: RecommendationResult | Record<string, unknown> | null = null;
      if (photoUri) {
        const response = await fashionApi.analyzePhoto(photoUri, occasion ?? undefined, notes);
        analysis = response.analysis;
      }
      // Step 2: personalized recommendation (uses style profile server-side).
      const created = await fashionApi.recommend({
        occasion: occasion ?? 'casual',
        budget_inr: budget ?? undefined,
        notes: notes || undefined,
      });
      void analysis; // v1 keeps the flow simple; analysis informs future turns.
      setOutfit(created);
      setPhase('result');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Styling failed.');
      setPhase('setup');
    }
  };

  const saveLook = async () => {
    if (!outfit) return;
    try {
      await fashionApi.saveOutfit(outfit.id);
      const updated = await fashionApi.outfit(outfit.id);
      setOutfit(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save look.');
    }
  };

  const generateConcept = async () => {
    if (!outfit) return;
    try {
      const job = await fashionApi.generateImage(outfit.id);
      setOutfit(job);
      pollImage(outfit.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not start image generation.');
    }
  };

  const pollImage = (id: string) => {
    const started = Date.now();
    const timer = setInterval(async () => {
      try {
        const latest = await fashionApi.outfit(id);
        setOutfit(latest);
        if (
          latest.status === 'COMPLETED' ||
          latest.status === 'FAILED' ||
          Date.now() - started > 60_000
        ) {
          clearInterval(timer);
        }
      } catch {
        clearInterval(timer);
      }
    }, 2000);
  };

  // ---- Result phase -------------------------------------------------------
  if (phase === 'result' && outfit) {
    const rec = outfit.recommendation;
    return (
      <Screen scroll={false} title="Your look ✦">
        <ScrollView contentContainerStyle={styles.resultScroll}>
          <Card>
            <Text style={styles.headline}>{rec.headline}</Text>
            <PaletteRow palette={rec.palette} />
            <Text style={[styles.body, styles.explanation]}>{rec.explanation}</Text>
            {rec.occasion_fit_notes ? (
              <Text style={styles.notes}>◈ {rec.occasion_fit_notes}</Text>
            ) : null}
          </Card>

          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>The outfit</Text>
            {rec.outfit_components.map((component) => (
              <View key={component.slot} style={styles.componentRow}>
                <Text style={styles.slot}>{component.slot.replace('_', ' ')}</Text>
                <Text style={styles.componentDesc}>
                  {component.item.description}
                  {component.item.fabric ? ` · ${component.item.fabric}` : ''}
                </Text>
              </View>
            ))}
          </Card>

          {rec.accessories.length > 0 && (
            <Card style={{ marginTop: spacing.lg }}>
              <Text style={styles.sectionTitle}>Finish with</Text>
              {rec.accessories.map((accessory) => (
                <Text key={accessory} style={styles.listItem}>
                  • {accessory}
                </Text>
              ))}
              {rec.footwear_note ? (
                <Text style={styles.listItem}>• {rec.footwear_note}</Text>
              ) : null}
            </Card>
          )}

          {rec.budget_allocation && rec.budget_allocation.length > 0 && (
            <Card style={{ marginTop: spacing.lg }}>
              <Text style={styles.sectionTitle}>
                Budget · ₹{rec.budget_total_inr?.toLocaleString('en-IN')}
              </Text>
              {rec.budget_allocation.map((line) => (
                <View key={line.component} style={styles.budgetRow}>
                  <Text style={styles.componentDesc}>{line.component}</Text>
                  <Text style={styles.slot}>₹{line.amount_inr.toLocaleString('en-IN')}</Text>
                </View>
              ))}
            </Card>
          )}

          {rec.styling_tips && rec.styling_tips.length > 0 && (
            <Card style={{ marginTop: spacing.lg }}>
              <Text style={styles.sectionTitle}>Stylist tips</Text>
              {rec.styling_tips.map((tip) => (
                <Text key={tip} style={styles.listItem}>
                  ✦ {tip}
                </Text>
              ))}
            </Card>
          )}

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Button label={outfit.saved ? 'Saved ✓' : 'Save this look'} onPress={saveLook} disabled={outfit.saved} />
          <Button
            label="Design variations →"
            variant="ghost"
            onPress={() =>
              navigation.navigate('DesignerChat', {
                conversationId: undefined,
                occasion: outfit.occasion || undefined,
              })
            }
            style={{ marginTop: spacing.md }}
          />

          {(outfit.image || outfit.status === 'FAILED') && (
            <View style={{ marginTop: spacing.md }}>
              {outfit.image ? (
                <Image source={{ uri: outfit.image }} style={styles.concept} />
              ) : (
                <Button label="Retry concept image" variant="ghost" onPress={generateConcept} />
              )}
            </View>
          )}

          <Button
            label="Style another look"
            variant="ghost"
            onPress={() => {
              setPhase('setup');
              setOutfit(null);
              setPhotoUri(null);
              setNotes('');
            }}
            style={{ marginTop: spacing.md, marginBottom: spacing.xl }}
          />
        </ScrollView>
      </Screen>
    );
  }

  // ---- Setup phase --------------------------------------------------------
  if (phase === 'analyzing') {
    return (
      <Screen title="Designing…">
        <View style={styles.analyzingWrap}>
          <ActivityIndicator color={colors.gold} size="large" />
          <Text style={styles.analyzingTitle}>Reading your style profile</Text>
          <Text style={styles.analyzingBody}>
            Considering the occasion, your colours and budget to compose something you'll love…
          </Text>
        </View>
      </Screen>
    );
  }

  return (
    <Screen subtitle="One photo. One occasion. A look made for you." title="AI Stylist">
      <View style={styles.body}>
        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Text style={styles.label}>1 · Your photo</Text>
        <Card>
          {photoUri ? (
            <Image source={{ uri: photoUri }} style={styles.photoPreview} />
          ) : (
            <Text style={styles.photoHint}>
              Add an outfit photo so the stylist can see your base look (optional but recommended).
            </Text>
          )}
          <View style={{ flexDirection: 'row', gap: spacing.md }}>
            <Button label="Take photo" variant="ghost" onPress={() => pickPhoto(true)} style={{ flex: 1 }} />
            <Button label="Choose" variant="ghost" onPress={() => pickPhoto(false)} style={{ flex: 1 }} />
          </View>
        </Card>

        <Text style={[styles.label, styles.gapTop]}>2 · Occasion</Text>
        <View style={styles.chipWrap}>
          {occasions.map((o) => (
            <Chip
              key={o.slug}
              label={o.label}
              selected={occasion === o.slug}
              onPress={() => setOccasion(o.slug)}
            />
          ))}
          {occasions.length === 0 && (
            <Text style={styles.photoHint}>Loading occasions…</Text>
          )}
        </View>

        <Text style={[styles.label, styles.gapTop]}>3 · Budget</Text>
        <View style={styles.chipWrap}>
          {BUDGET_OPTIONS.map((amount) => (
            <Chip
              key={amount}
              label={`₹${amount.toLocaleString('en-IN')}`}
              selected={budget === amount}
              onPress={() => setBudget(amount)}
            />
          ))}
        </View>

        <Text style={[styles.label, styles.gapTop]}>4 · Anything else? (optional)</Text>
        <RNInput
          multiline
          onChangeText={setNotes}
          placeholder='e.g. "Sangeet evening, love emerald green, want something elegant"'
          placeholderTextColor={colors.textMuted}
          style={styles.notesInput}
          value={notes}
        />

        <Text style={styles.quota}>
          {entitlements
            ? `${entitlements.tier ?? 'Free'} plan · ${entitlements.ai_text_daily_limit} AI stylings/day`
            : ''}
        </Text>

        <Button
          disabled={!occasion}
          label={occasion ? `Style me for ${occasions.find((o) => o.slug === occasion)?.label ?? ''} ✦` : 'Pick an occasion'}
          loading={false}
          onPress={styleMe}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  analyzingBody: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
  analyzingTitle: { ...typography.h2, color: colors.textPrimary, marginTop: spacing.lg },
  analyzingWrap: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.xxl },
  body: { padding: spacing.xl },
  budgetRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap' },
  componentDesc: { ...typography.body, color: colors.textPrimary, flex: 1 },
  componentRow: { flexDirection: 'row', marginBottom: spacing.md, paddingRight: spacing.lg },
  concept: {
    borderColor: colors.inkBorder,
    borderRadius: radii.lg,
    borderWidth: 1,
    height: 260,
    width: '100%',
  },
  error: { ...typography.small, color: colors.danger, marginBottom: spacing.md },
  explanation: { color: colors.textSecondary, marginTop: spacing.md },
  gapTop: { marginTop: spacing.xl },
  headline: { ...typography.h1, color: colors.textPrimary },
  label: { ...typography.micro, color: colors.gold, marginBottom: spacing.md },
  listItem: { ...typography.body, color: colors.textSecondary, marginBottom: spacing.sm },
  notes: { ...typography.small, color: colors.gold, marginTop: spacing.md },
  notesInput: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    color: colors.textPrimary,
    minHeight: 90,
    padding: spacing.lg,
    textAlignVertical: 'top',
  },
  photoHint: { ...typography.small, color: colors.textSecondary, marginBottom: spacing.md },
  photoPreview: {
    borderRadius: radii.md,
    height: 180,
    marginBottom: spacing.md,
    width: '100%',
  },
  quota: { ...typography.micro, color: colors.textMuted, marginVertical: spacing.md },
  resultScroll: { padding: spacing.xl },
  sectionTitle: { ...typography.h3, color: colors.gold, marginBottom: spacing.md },
  slot: { ...typography.micro, color: colors.textMuted, textTransform: 'uppercase', width: 90 },
});
