import React from 'react';
import { useNavigation } from '@react-navigation/native';
import { FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Screen } from '@/components/ui/Screen';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function HomeScreen() {
  const navigation = useNavigation();
  return (
    <Screen scroll={false} subtitle="Your daily fashion companion" title="FashionXP">
      <FlatList
        contentContainerStyle={{ padding: spacing.xl }}
        data={HOME_CARDS}
        keyExtractor={(item) => item.title}
        renderItem={({ item }) => (
          <TouchableOpacity
            activeOpacity={0.85}
            style={styles.card}
            onPress={() => item.destination && navigation.navigate(item.destination as never)}
          >
            <Text style={styles.emoji}>{item.emoji}</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardBody}>{item.body}</Text>
            </View>
            <Text style={styles.chevron}>→</Text>
          </TouchableOpacity>
        )}
      />
    </Screen>
  );
}

const HOME_CARDS = [
  {
    emoji: '✂',
    title: "Today: What should I wear?",
    body: 'Open the Stylist, pick your occasion and get a complete look with colors, accessories and budget.',
    destination: 'Stylist',
  },
  {
    emoji: '◈',
    title: 'Design something new',
    body: 'Chat with the AI designer — change colors, sleeves, embroidery — until it feels like you.',
    destination: 'DesignerChat',
  },
  {
    emoji: '▤',
    title: 'Style from your closet',
    body: 'Your digital wardrobe composes outfits from clothes you already own before suggesting anything new.',
    destination: 'Wardrobe',
  },
];

const styles = StyleSheet.create({
  card: {
    alignItems: 'center',
    backgroundColor: colors.inkCard,
    borderColor: colors.inkBorder,
    borderRadius: radii.lg,
    borderWidth: 1,
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.lg,
    padding: spacing.lg,
  },
  cardBody: { ...typography.small, color: colors.textSecondary, marginTop: 4 },
  cardTitle: { ...typography.h3, color: colors.textPrimary },
  chevron: { color: colors.gold, fontSize: 18 },
  emoji: { fontSize: 26 },
});
