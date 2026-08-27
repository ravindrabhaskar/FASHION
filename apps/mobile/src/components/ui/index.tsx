import React from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TextInput as RNInput,
  TextInputProps,
  TouchableOpacity,
  View,
  ViewStyle,
} from 'react-native';
import { colors, radii, spacing, typography } from '@/theme/tokens';

// ---- Button ----------------------------------------------------------------

interface ButtonProps {
  label: string;
  onPress?: () => void;
  variant?: 'primary' | 'ghost' | 'danger' | 'gold';
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
}

export function Button({ label, onPress, variant = 'primary', loading, disabled, style }: ButtonProps) {
  const bg =
    variant === 'primary' ? colors.textPrimary
    : variant === 'gold' ? colors.gold
    : variant === 'danger' ? colors.danger
    : 'transparent';

  return (
    <TouchableOpacity
      accessibilityRole="button"
      activeOpacity={0.8}
      disabled={disabled || loading}
      style={[
        styles.button,
        { backgroundColor: bg },
        variant === 'ghost' && styles.buttonGhost,
        (disabled || loading) && styles.buttonDisabled,
        style,
      ]}
      onPress={onPress}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? colors.ink : colors.gold} />
      ) : (
        <Text
          style={[
            styles.buttonLabel,
            { color: variant === 'ghost' ? colors.gold : variant === 'primary' ? colors.ink : colors.white },
          ]}
        >
          {label}
        </Text>
      )}
    </TouchableOpacity>
  );
}

// ---- Card ------------------------------------------------------------------

export function Card({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function SectionHeader({
  eyebrow,
  title,
  action,
  onAction,
}: {
  eyebrow?: string;
  title: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <View style={styles.sectionHeader}>
      <View style={{ flex: 1 }}>
        {eyebrow ? <Text style={styles.eyebrow}>{eyebrow}</Text> : null}
        <Text style={styles.sectionTitle}>{title}</Text>
      </View>
      {action ? (
        <TouchableOpacity accessibilityRole="button" onPress={onAction} style={styles.textAction}>
          <Text style={styles.textActionLabel}>{action}</Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

export function Metric({ value, label }: { value: string | number; label: string }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

export function ActionRow({
  icon,
  title,
  subtitle,
  onPress,
  destructive,
}: {
  icon: string;
  title: string;
  subtitle?: string;
  onPress?: () => void;
  destructive?: boolean;
}) {
  return (
    <TouchableOpacity accessibilityRole="button" activeOpacity={0.72} onPress={onPress} style={styles.actionRow}>
      <View style={styles.actionIcon}><Text style={styles.actionIconText}>{icon}</Text></View>
      <View style={{ flex: 1 }}>
        <Text style={[styles.actionTitle, destructive && { color: colors.danger }]}>{title}</Text>
        {subtitle ? <Text numberOfLines={1} style={styles.actionSubtitle}>{subtitle}</Text> : null}
      </View>
      <Text style={styles.actionChevron}>›</Text>
    </TouchableOpacity>
  );
}

// ---- Chip ------------------------------------------------------------------

export function Chip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected?: boolean;
  onPress?: () => void;
}) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      style={[styles.chip, selected && styles.chipSelected]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Text style={[styles.chipLabel, selected && { color: colors.ink }]}>{label}</Text>
    </TouchableOpacity>
  );
}

// ---- Input -----------------------------------------------------------------

export function Input(props: TextInputProps) {
  return (
    <RNInput
      placeholderTextColor={colors.textMuted}
      style={styles.input}
      {...props}
    />
  );
}

// ---- States ----------------------------------------------------------------

export function Skeleton({ height = 16, width }: { height?: number; width?: number | `${number}%` }) {
  return <View style={[styles.skeleton, { height, width }]} />;
}

export function EmptyState({ emoji, title, message }: { emoji: string; title: string; message: string }) {
  return (
    <View style={styles.stateWrap}>
      <Text style={{ fontSize: 44 }}>{emoji}</Text>
      <Text style={[typography.h2, styles.stateTitle]}>{title}</Text>
      <Text style={[typography.small, styles.stateMessage]}>{message}</Text>
    </View>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <View style={styles.stateWrap}>
      <Text style={{ fontSize: 40 }}>🧵</Text>
      <Text style={[typography.h3, { color: colors.textPrimary, marginTop: spacing.md }]}>
        Something unraveled
      </Text>
      <Text style={[typography.small, styles.stateMessage]}>{message}</Text>
      {onRetry ? (
        <Button label="Try again" variant="ghost" onPress={onRetry} style={{ marginTop: spacing.lg }} />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    borderRadius: radii.pill,
    justifyContent: 'center',
    minHeight: 52,
    paddingHorizontal: spacing.xl,
    paddingVertical: 14,
  },
  buttonGhost: {
    borderWidth: 1,
    borderColor: colors.goldSoft,
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonLabel: {
    ...typography.h3,
    letterSpacing: 0.2,
  },
  card: {
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderRadius: radii.lg,
    borderWidth: 1,
    padding: spacing.lg,
  },
  sectionHeader: { alignItems: 'flex-end', flexDirection: 'row', marginBottom: spacing.md },
  eyebrow: { ...typography.eyebrow, color: colors.gold, marginBottom: spacing.xs },
  sectionTitle: { ...typography.h2, color: colors.textPrimary },
  textAction: { paddingHorizontal: spacing.sm, paddingVertical: spacing.sm },
  textActionLabel: { ...typography.small, color: colors.gold, fontWeight: '700' },
  metric: { flex: 1, minWidth: 86 },
  metricValue: { ...typography.h2, color: colors.textPrimary },
  metricLabel: { ...typography.micro, color: colors.textMuted, marginTop: 2, textTransform: 'uppercase' },
  actionRow: { alignItems: 'center', borderBottomColor: colors.inkBorder, borderBottomWidth: StyleSheet.hairlineWidth, flexDirection: 'row', minHeight: 70, paddingVertical: spacing.md },
  actionIcon: { alignItems: 'center', backgroundColor: colors.goldFaint, borderColor: colors.goldSoft, borderRadius: radii.md, borderWidth: 1, height: 42, justifyContent: 'center', marginRight: spacing.md, width: 42 },
  actionIconText: { color: colors.gold, fontSize: 18, fontWeight: '700' },
  actionTitle: { ...typography.h3, color: colors.textPrimary },
  actionSubtitle: { ...typography.small, color: colors.textMuted, marginTop: 2 },
  actionChevron: { color: colors.textMuted, fontSize: 28, marginLeft: spacing.sm },
  chip: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.lg,
    paddingVertical: 10,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  chipSelected: {
    backgroundColor: colors.gold,
    borderColor: colors.gold,
  },
  chipLabel: {
    ...typography.small,
    color: colors.textSecondary,
    fontWeight: '600',
  },
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
  },
  skeleton: {
    backgroundColor: colors.inkElevated,
    borderRadius: radii.sm,
    flexGrow: 0,
  },
  stateWrap: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    padding: spacing.xxl,
  },
  stateTitle: {
    color: colors.textPrimary,
    marginTop: spacing.lg,
  },
  stateMessage: {
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
});
