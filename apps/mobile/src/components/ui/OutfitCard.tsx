import React from 'react';
import { ActivityIndicator, Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { colors, radii, shadow, spacing, typography } from '@/theme/tokens';
import type { Outfit } from '@/api/types';

const STATUS_LABEL: Record<Outfit['status'], string> = {
  QUEUED: 'Queued…',
  GENERATING: 'Designing your look…',
  COMPLETED: 'Ready',
  FAILED: 'Generation failed',
};

export function OutfitCard({
  outfit,
  onPress,
  onRetryImage,
}: {
  outfit: Outfit;
  onPress?: () => void;
  onRetryImage?: () => void;
}) {
  const rec = outfit.recommendation;
  return (
    <TouchableOpacity
      accessibilityRole="button"
      activeOpacity={0.9}
      style={styles.card}
      onPress={onPress}
    >
      <View>
        {outfit.status === 'COMPLETED' && outfit.image ? (
          <Image source={{ uri: outfit.image }} style={styles.image} />
        ) : (
          <View style={[styles.image, styles.imagePlaceholder]}>
            {outfit.status === 'FAILED' ? (
              <>
                <Text style={typography.h3}>✦</Text>
                <Text style={styles.placeholderText}>{outfit.failed_reason}</Text>
                {onRetryImage ? (
                  <TouchableOpacity
                    onPress={onRetryImage}
                    style={styles.retryButton}
                    accessibilityRole="button"
                  >
                    <Text style={styles.retryLabel}>Retry</Text>
                  </TouchableOpacity>
                ) : null}
              </>
            ) : (
              <>
                <ActivityIndicator color={colors.gold} />
                <Text style={styles.placeholderText}>
                  {STATUS_LABEL[outfit.status] ?? 'Working…'}
                </Text>
              </>
            )}
          </View>
        )}
      </View>

      <View style={{ padding: spacing.lg }}>
        <Text numberOfLines={2} style={styles.headline}>
          {rec?.headline ?? outfit.title}
        </Text>

        {(rec?.palette?.length ?? 0) > 0 && (
          <View style={styles.paletteRow}>
            {rec.palette.slice(0, 5).map((swatch) => (
              <View key={swatch.hex + swatch.name} style={[styles.swatch, { backgroundColor: swatch.hex }]} />
            ))}
          </View>
        )}

        {outfit.occasion ? (
          <Text style={styles.meta}>{outfit.occasion.replace('-', ' ').toUpperCase()}</Text>
        ) : null}
      </View>
    </TouchableOpacity>
  );
}

export function PaletteRow({ palette }: { palette: Outfit['recommendation']['palette'] }) {
  if (!palette.length) return null;
  return (
    <View style={styles.paletteRow}>
      {palette.map((s) => (
        <View key={s.hex} style={styles.swatchDetail}>
          <View style={[styles.swatchLarge, { backgroundColor: s.hex }]} />
          <Text style={styles.swatchName}>{s.name}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderRadius: radii.lg,
    borderWidth: 1,
    marginBottom: spacing.lg,
    overflow: 'hidden',
    ...shadow.card,
  },
  image: { height: 210, width: '100%' },
  imagePlaceholder: {
    alignItems: 'center',
    backgroundColor: colors.inkElevated,
    justifyContent: 'center',
    padding: spacing.xl,
  },
  headline: { ...typography.h2, color: colors.textPrimary },
  meta: { ...typography.micro, color: colors.gold, marginTop: spacing.sm },
  paletteRow: { flexDirection: 'row', marginTop: spacing.md },
  retryButton: {
    borderColor: colors.goldSoft,
    borderRadius: radii.pill,
    borderWidth: 1,
    marginTop: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: 6,
  },
  retryLabel: { ...typography.small, color: colors.gold },
  swatch: {
    borderColor: colors.inkBorder,
    borderRadius: 12,
    borderWidth: 1,
    height: 24,
    marginRight: spacing.sm,
    width: 24,
  },
  swatchDetail: { alignItems: 'center', marginRight: spacing.md },
  swatchLarge: { borderRadius: radii.sm, height: 40, width: 40 },
  swatchName: { ...typography.micro, color: colors.textMuted, marginTop: 4 },
  placeholderText: {
    ...typography.small,
    color: colors.textSecondary,
    marginTop: spacing.md,
    textAlign: 'center',
  },
});
