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
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import * as ImagePicker from 'expo-image-picker';
import { Screen } from '@/components/ui/Screen';
import { Button } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { marketplaceApi } from '@/api/endpoints';
import { ApiError } from '@/api/client';
import type { RootStackParamList } from '@/navigation/types';

const CATEGORIES = ['tops', 'bottoms', 'dresses', 'ethnic', 'accessories', 'footwear', 'outerwear'];

export default function CreateProductScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'CreateProduct'>>();
  const navigation = useNavigation();
  const productId = route.params?.productId;
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [stock, setStock] = useState('');
  const [category, setCategory] = useState('ethnic');
  const [fabric, setFabric] = useState('');
  const [city, setCity] = useState('');
  const [customizable, setCustomizable] = useState(false);
  const [readyToShip, setReadyToShip] = useState(true);
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (productId) {
      marketplaceApi.product(productId).then((p) => {
        setTitle(p.title);
        setDescription(p.description);
        setPrice(String(p.price_inr));
        setStock('');
        setCategory(p.category || 'ethnic');
        setFabric(p.fabric);
        setCity(p.city);
        setCustomizable(p.is_customizable);
        setReadyToShip(p.ready_to_ship);
      }).catch(() => undefined);
    }
  }, [productId]);

  const pickPhoto = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) { Alert.alert('Permission needed'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
    });
    if (!result.canceled && result.assets.length > 0) setPhotoUri(result.assets[0].uri);
  };

  const submit = async () => {
    if (!title.trim() || !price) {
      Alert.alert('Required', 'Title and price are required.');
      return;
    }
    setSubmitting(true);
    try {
      const base = {
        title: title.trim(),
        description: description.trim(),
        price_inr: parseInt(price, 10),
        category,
        fabric: fabric.trim(),
        city: city.trim(),
        is_customizable: customizable,
        ready_to_ship: readyToShip,
      };
      if (productId) {
        await marketplaceApi.updateProduct(productId, {
          ...base,
          ...(stock.trim() ? { stock: parseInt(stock, 10) } : {}),
          ...(photoUri
            ? { photo: { uri: photoUri, name: `product-${Date.now()}.jpg`, type: 'image/jpeg' } }
            : {}),
        });
      } else {
        const payload: Parameters<typeof marketplaceApi.createProduct>[0] = {
          ...base,
          stock: stock.trim() ? parseInt(stock, 10) : 1,
        };
        if (photoUri) {
          payload.photo = { uri: photoUri, name: `product-${Date.now()}.jpg`, type: 'image/jpeg' };
        }
        await marketplaceApi.createProduct(payload);
      }
      Alert.alert('Saved!', productId ? 'Product updated.' : 'Your product is live.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not save product.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Screen title={productId ? 'Edit Product' : 'New Product'}>
        <View style={{ padding: spacing.xl }}>
          <Button label={photoUri ? '✓ Photo chosen' : 'Add product photo'} variant="ghost" onPress={() => void pickPhoto()} />

          <Text style={styles.label}>Title *</Text>
          <TextInput style={styles.input} placeholder="e.g. Handloom cotton saree" placeholderTextColor={colors.textMuted} value={title} onChangeText={setTitle} />

          <Text style={styles.label}>Price (₹) *</Text>
          <TextInput style={styles.input} placeholder="e.g. 4999" placeholderTextColor={colors.textMuted} value={price} onChangeText={setPrice} keyboardType="number-pad" />

          <Text style={styles.label}>Stock</Text>
          <TextInput style={styles.input} placeholder="e.g. 10" placeholderTextColor={colors.textMuted} value={stock} onChangeText={setStock} keyboardType="number-pad" />

          <Text style={styles.label}>Category</Text>
          <View style={styles.chipWrap}>
            {CATEGORIES.map((c) => (
              <Chip key={c} label={c} selected={category === c} onPress={() => setCategory(c)} />
            ))}
          </View>

          <Text style={styles.label}>Fabric</Text>
          <TextInput style={styles.input} placeholder="e.g. cotton, silk" placeholderTextColor={colors.textMuted} value={fabric} onChangeText={setFabric} />

          <Text style={styles.label}>City</Text>
          <TextInput style={styles.input} placeholder="e.g. Jaipur" placeholderTextColor={colors.textMuted} value={city} onChangeText={setCity} />

          <Text style={styles.label}>Description</Text>
          <TextInput style={[styles.input, { minHeight: 80 }]} placeholder="Describe the product..." placeholderTextColor={colors.textMuted} value={description} onChangeText={setDescription} multiline />

          <View style={styles.toggleRow}>
            <TouchableOpacity style={styles.toggle} onPress={() => setCustomizable(!customizable)}>
              <Text style={styles.toggleText}>{customizable ? '✓' : '○'} Customizable</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.toggle} onPress={() => setReadyToShip(!readyToShip)}>
              <Text style={styles.toggleText}>{readyToShip ? '✓' : '○'} Ready to ship</Text>
            </TouchableOpacity>
          </View>

          <Button label={productId ? 'Save changes' : 'Publish product'} variant="gold" loading={submitting} onPress={() => void submit()} style={{ marginTop: spacing.xl }} />
        </View>
      </Screen>
    </KeyboardAvoidingView>
  );
}

function Chip({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} style={[styles.chip, selected && styles.chipSelected]} accessibilityRole="button">
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
  toggle: {
    backgroundColor: colors.inkElevated,
    borderColor: colors.inkBorder,
    borderRadius: radii.md,
    borderWidth: 1,
    marginRight: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: 10,
  },
  toggleRow: { flexDirection: 'row', marginTop: spacing.md },
  toggleText: { ...typography.small, color: colors.textSecondary },
  wrap: { backgroundColor: colors.ink, flex: 1 },
});