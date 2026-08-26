import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, spacing, typography } from '@/theme/tokens';

export function Screen({
  children,
  title,
  subtitle,
  scroll = true,
}: {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  scroll?: boolean;
}) {
  const insets = useSafeAreaInsets();
  const content = (
    <>
      {title ? (
        <View style={{ paddingHorizontal: spacing.xl, paddingTop: spacing.xl }}>
          <Text accessibilityRole="header" style={styles.title}>
            {title}
          </Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
      ) : null}
      {children}
    </>
  );

  return (
    <View
      style={[
        styles.screen,
        { paddingBottom: insets.bottom, paddingTop: insets.top },
      ]}
    >
      {scroll ? (
        <ScrollView
          contentContainerStyle={{ paddingBottom: spacing.xxl }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {content}
        </ScrollView>
      ) : (
        content
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { backgroundColor: colors.ink, flex: 1 },
  title: { ...typography.display, color: colors.textPrimary },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
});
