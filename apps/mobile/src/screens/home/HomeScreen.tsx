import React from 'react';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { FlatList, StyleSheet, Text, TouchableOpacity, useWindowDimensions, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Screen } from '@/components/ui/Screen';
import { SectionHeader } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { useAuth } from '@/state/auth';
import type { RootStackParamList } from '@/navigation/types';

type Destination = { stack?: keyof RootStackParamList; tab?: string; params?: object };
type Feature = Destination & { title: string; body: string; icon: React.ComponentProps<typeof Ionicons>['name']; accent: string };

export default function HomeScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { user } = useAuth();
  const { width } = useWindowDimensions();
  const columns = width >= 760 ? 3 : width >= 520 ? 2 : 1;
  const firstName = user?.full_name?.split(' ')[0] || 'there';
  const open = (item: Destination) => {
    if (item.stack) (navigation as any).navigate(item.stack, item.params ?? {});
    else if (item.tab) (navigation as any).navigate('Main', { screen: item.tab });
  };

  return (
    <Screen scroll={false}>
      <FlatList
        key={columns}
        numColumns={columns}
        data={FEATURES}
        keyExtractor={(item) => item.title}
        columnWrapperStyle={columns > 1 ? styles.columns : undefined}
        contentContainerStyle={styles.content}
        ListHeaderComponent={(
          <>
            <View style={styles.topline}>
              <View><Text style={styles.eyebrow}>FASHIONXP · YOUR DAILY EDIT</Text><Text style={styles.greeting}>Good day, {firstName}</Text></View>
              <TouchableOpacity accessibilityLabel="Notifications" onPress={() => navigation.navigate('Notifications')} style={styles.roundButton}><Ionicons color={colors.textPrimary} name="notifications-outline" size={21} /></TouchableOpacity>
            </View>
            <TouchableOpacity activeOpacity={0.88} onPress={() => open({ tab: 'Stylist' })} style={styles.hero}>
              <View style={styles.heroGlow} />
              <Text style={styles.heroKicker}>PERSONAL STYLIST</Text>
              <Text style={styles.heroTitle}>A complete look,{`\n`}made for today.</Text>
              <Text style={styles.heroBody}>Tell us the occasion and budget. Your AI stylist handles the silhouette, palette, accessories, and finishing touches.</Text>
              <View style={styles.heroButton}><Text style={styles.heroButtonText}>Style me now</Text><Ionicons color={colors.textPrimary} name="arrow-forward" size={17} /></View>
            </TouchableOpacity>
            <View style={styles.quickRow}>
              {QUICK_ACTIONS.map((item) => <TouchableOpacity key={item.label} onPress={() => open(item)} style={styles.quickAction}><Ionicons color={colors.gold} name={item.icon} size={20} /><Text style={styles.quickLabel}>{item.label}</Text></TouchableOpacity>)}
            </View>
            <SectionHeader eyebrow="Explore" title="Everything in your wardrobe world" />
          </>
        )}
        renderItem={({ item }) => (
          <TouchableOpacity activeOpacity={0.82} onPress={() => open(item)} style={[styles.card, { borderTopColor: item.accent }, columns > 1 && { flex: 1 }]}>
            <View style={[styles.cardIcon, { backgroundColor: `${item.accent}18` }]}><Ionicons color={item.accent} name={item.icon} size={22} /></View>
            <Text style={styles.cardTitle}>{item.title}</Text><Text style={styles.cardBody}>{item.body}</Text>
            <View style={styles.cardLink}><Text style={styles.cardLinkText}>Explore</Text><Ionicons color={colors.gold} name="arrow-forward" size={15} /></View>
          </TouchableOpacity>
        )}
      />
    </Screen>
  );
}

const QUICK_ACTIONS = [
  { label: 'Wardrobe', icon: 'shirt-outline' as const, tab: 'Wardrobe' },
  { label: 'Saved looks', icon: 'bookmark-outline' as const, stack: 'SavedLooks' as const },
  { label: 'AI designer', icon: 'color-wand-outline' as const, stack: 'DesignerChat' as const, params: {} },
  { label: 'Try on', icon: 'body-outline' as const, stack: 'TryOn' as const, params: {} },
];

const FEATURES: Feature[] = [
  { icon: 'people-outline', title: 'Style community', body: 'Discover looks, share outfits, and follow people whose taste inspires you.', tab: 'Social', accent: colors.blush },
  { icon: 'bag-handle-outline', title: 'Curated marketplace', body: 'Shop independent designers, local labels, and pieces matched to your style.', tab: 'Shop', accent: colors.gold },
  { icon: 'trending-up-outline', title: 'Trending now', body: 'See the colors, fabrics, silhouettes, and cities defining this week.', stack: 'Trends', accent: colors.danger },
  { icon: 'ribbon-outline', title: 'XP & rewards', body: 'Complete style challenges, grow your level, and unlock member rewards.', stack: 'XPDashboard', accent: colors.sage },
  { icon: 'cut-outline', title: 'Custom-made', body: 'Request a made-to-measure look and compare offers from verified designers.', stack: 'Quotes', accent: colors.goldBright },
  { icon: 'chatbubbles-outline', title: 'Messages', body: 'Keep product, order, and custom-design conversations in one place.', stack: 'ChatList', accent: colors.textSecondary },
];

const styles = StyleSheet.create({
  content: { padding: spacing.xl, paddingBottom: spacing.xxxl }, columns: { gap: spacing.md },
  topline: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.xl },
  eyebrow: { ...typography.eyebrow, color: colors.gold }, greeting: { ...typography.h1, color: colors.textPrimary, marginTop: spacing.xs },
  roundButton: { alignItems: 'center', backgroundColor: colors.inkCard, borderColor: colors.inkBorder, borderRadius: 24, borderWidth: 1, height: 48, justifyContent: 'center', width: 48 },
  hero: { backgroundColor: '#E5D1A8', borderRadius: radii.xl, marginBottom: spacing.lg, overflow: 'hidden', padding: spacing.xl },
  heroGlow: { backgroundColor: 'rgba(255,255,255,0.35)', borderRadius: 160, height: 220, position: 'absolute', right: -60, top: -90, width: 220 },
  heroKicker: { ...typography.eyebrow, color: '#68512D' }, heroTitle: { ...typography.display, color: colors.ink, fontSize: 36, marginTop: spacing.sm, maxWidth: 480 },
  heroBody: { ...typography.body, color: '#5A4C3A', marginTop: spacing.md, maxWidth: 580 },
  heroButton: { alignItems: 'center', alignSelf: 'flex-start', backgroundColor: colors.ink, borderRadius: radii.pill, flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xl, paddingHorizontal: spacing.lg, paddingVertical: 13 },
  heroButtonText: { ...typography.h3, color: colors.textPrimary }, quickRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.xxl },
  quickAction: { alignItems: 'center', backgroundColor: colors.inkCard, borderColor: colors.inkBorder, borderRadius: radii.md, borderWidth: 1, flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.md },
  quickLabel: { ...typography.small, color: colors.textPrimary, fontWeight: '600' },
  card: { backgroundColor: colors.inkCard, borderColor: colors.inkBorder, borderRadius: radii.lg, borderTopWidth: 2, borderWidth: 1, marginBottom: spacing.md, minHeight: 190, padding: spacing.lg },
  cardIcon: { alignItems: 'center', borderRadius: radii.md, height: 42, justifyContent: 'center', width: 42 }, cardTitle: { ...typography.h3, color: colors.textPrimary, marginTop: spacing.md },
  cardBody: { ...typography.small, color: colors.textSecondary, flex: 1, marginTop: spacing.sm }, cardLink: { alignItems: 'center', flexDirection: 'row', gap: spacing.xs, marginTop: spacing.md }, cardLinkText: { ...typography.small, color: colors.gold, fontWeight: '700' },
});
