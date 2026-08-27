import React, { useEffect, useState } from 'react';
import { Alert, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Card, Skeleton } from '@/components/ui';
import { Screen } from '@/components/ui/Screen';
import { colors, spacing, typography } from '@/theme/tokens';
import { plansApi, profileApi, xpApi } from '@/api/endpoints';
import type { Entitlements, StyleProfile, XPDashboard } from '@/api/types';
import { useAuth } from '@/state/auth';
import type { RootStackParamList } from '@/navigation/types';

export default function ProfileScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { user, signOutAll, refreshUser } = useAuth();
  const [styleProfile, setStyleProfile] = useState<StyleProfile | null>(null);
  const [entitlements, setEntitlements] = useState<Entitlements | null>(null);
  const [xp, setXp] = useState<XPDashboard | null>(null);

  useEffect(() => {
    profileApi.getStyleProfile().then(setStyleProfile).catch(() => undefined);
    plansApi.entitlements().then(setEntitlements).catch(() => undefined);
    xpApi.me().then(setXp).catch(() => undefined);
  }, []);

  const confirmSignOut = () =>
    Alert.alert('Sign out', 'Sign out from all devices?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign out', style: 'destructive', onPress: () => void signOutAll() },
    ]);

  return (
    <Screen title="Profile">
      <View style={{ padding: spacing.xl }}>
        <Card>
          <Text style={styles.name}>{user?.full_name}</Text>
          <Text style={styles.email}>{user?.email}</Text>
          <View style={styles.rolePill}>
            <Text style={styles.roleText}>{user?.role ?? 'USER'}</Text>
          </View>
        </Card>

        {xp && (
          <Card style={{ marginTop: spacing.lg }}>
            <Text style={styles.sectionTitle}>XP & Level</Text>
            <Text style={styles.body}>
              Level: <Text style={{ color: colors.gold }}>{xp.level}</Text> · {xp.total_xp.toLocaleString()} XP
            </Text>
            <Button
              label="View XP dashboard"
              variant="ghost"
              onPress={() => navigation.navigate('XPDashboard')}
              style={{ marginTop: spacing.md }}
            />
          </Card>
        )}

        <Card style={{ marginTop: spacing.lg }}>
          <Text style={styles.sectionTitle}>Style profile</Text>
          {!styleProfile ? (
            <>
              <Skeleton />
              <View style={{ height: 8 }} />
              <Skeleton width="60%" />
            </>
          ) : (
            <>
              <Text style={styles.body}>
                Completion: <Text style={{ color: colors.gold }}>{styleProfile.completion}%</Text>
              </Text>
              <Text style={styles.body}>
                Styles:{' '}
                {(styleProfile.preferred_styles ?? []).join(', ') || 'not set'}
              </Text>
              <Text style={styles.body}>
                Occasions:{' '}
                {(styleProfile.common_occasions ?? []).map((o) => o.replace('-', ' ')).join(', ') ||
                  'not set'}
              </Text>
            </>
          )}
        </Card>

        <Card style={{ marginTop: spacing.lg }}>
          <Text style={styles.sectionTitle}>Plan</Text>
          <Text style={styles.body}>
            {entitlements ? (entitlements.tier ? `${entitlements.tier} member` : 'Free plan') : '…'}
          </Text>
          {entitlements && (
            <Text style={[typography.small, { color: colors.textMuted }]}>
              {entitlements.ai_text_daily_limit} AI stylings/day ·{' '}
              {entitlements.ai_image_monthly_limit} images/month · {entitlements.max_saved_looks} saved
              looks
            </Text>
          )}
        </Card>

        <Button label="My saved looks" variant="ghost" style={{ marginTop: spacing.lg }} onPress={() => navigation.navigate('SavedLooks')} />
        <Button label="AI Designer chat" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('DesignerChat', {})} />
        <Button label="My orders" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('Orders')} />
        <Button label="Messages" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('ChatList')} />
        <Button label="Browse designers" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('Designers')} />
        <Button label="Custom quotes" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('Quotes')} />
        <Button label="My products & listings" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('MyProducts')} />
        <Button label="Brands" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('Brands')} />
        <Button label="Creators & campaigns" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('Creators')} />
        <Button label="Trending now" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('Trends')} />
        <Button label="Virtual try-on" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('TryOn', {})} />
        <Button label="App language" variant="ghost" style={{ marginTop: spacing.md }} onPress={() => navigation.navigate('Language')} />
        <Button
          label="Refresh profile"
          variant="ghost"
          style={{ marginTop: spacing.md }}
          onPress={() => void refreshUser()}
        />
        <Button label="Sign out" variant="danger" style={{ marginTop: spacing.xl }} onPress={confirmSignOut} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: { ...typography.body, color: colors.textSecondary, marginBottom: 4 },
  email: { ...typography.small, color: colors.textMuted },
  name: { ...typography.h2, color: colors.textPrimary },
  rolePill: {
    alignSelf: 'flex-start',
    backgroundColor: colors.goldSoft,
    borderRadius: 999,
    marginTop: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  roleText: { ...typography.micro, color: colors.gold },
  sectionTitle: { ...typography.h3, color: colors.gold, marginBottom: spacing.sm },
});
