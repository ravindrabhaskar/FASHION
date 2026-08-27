import React, { useRef, useState } from 'react';
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
import { Audio } from 'expo-av';
import { Button } from '@/components/ui';
import { Screen } from '@/components/ui/Screen';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { socialApi, aiMetadataApi, aiApi } from '@/api/endpoints';
import { ApiError } from '@/api/client';
import type { RootStackParamList } from '@/navigation/types';

export default function CreatePostScreen() {
  const navigation = useNavigation();
  const route = useRoute<RouteProp<RootStackParamList, 'CreatePost'>>();
  const outfitId = route.params?.outfitId;
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [caption, setCaption] = useState('');
  const [occasion, setOccasion] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [recordingVoice, setRecordingVoice] = useState(false);
  const recordingRef = useRef<Audio.Recording | null>(null);

  const toggleVoice = async () => {
    if (recordingRef.current) {
      try {
        await recordingRef.current.stopAndUnloadAsync();
        const uri =
          (recordingRef.current.getURI?.() as string | null) ??
          (recordingRef.current as unknown as { uri?: string }).uri;
        recordingRef.current = null;
        setRecordingVoice(false);
        if (uri) {
          setSuggesting(true);
          try {
            const result = await aiApi.transcribe(uri);
            if (result.text) {
              setCaption((prev) => (prev ? `${prev}\n${result.text}` : result.text));
            }
          } catch {
            Alert.alert('Transcription failed', 'Voice note could not be transcribed.');
          } finally {
            setSuggesting(false);
          }
        }
      } catch {
        recordingRef.current = null;
        setRecordingVoice(false);
      }
      return;
    }
    const perm = await Audio.requestPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Permission needed', 'Enable microphone access in Settings.');
      return;
    }
    try {
      const rec = new Audio.Recording();
      await rec.prepareToRecordAsync(Audio.RecordingOptionsPresets.LOW_QUALITY);
      await rec.startAsync();
      recordingRef.current = rec;
      setRecordingVoice(true);
    } catch {
      Alert.alert('Recording error', 'Could not start the microphone.');
    }
  };

  const suggestCaption = async () => {
    setSuggesting(true);
    try {
      const result = await aiMetadataApi.suggest({
        seed: photoUri ? undefined : caption.trim() || undefined,
        occasion: occasion.trim() || undefined,
      });
      if (result.suggested_caption) setCaption(result.suggested_caption);
      if (result.suggested_tags.length > 0) {
        Alert.alert('Suggested tags', result.suggested_tags.map((t) => `#${t}`).join('  '));
      }
    } catch {
      Alert.alert('AI busy', 'Could not get a suggestion right now.');
    } finally {
      setSuggesting(false);
    }
  };

  const pickPhoto = async (fromCamera: boolean) => {
    const perm = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Permission needed', 'Enable photo access in Settings.');
      return;
    }
    const result = fromCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.7 })
      : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.7 });
    if (!result.canceled && result.assets.length > 0) {
      setPhotoUri(result.assets[0].uri);
    }
  };

  const submit = async () => {
    if (!photoUri) {
      Alert.alert('Photo required', 'Pick a photo for your post.');
      return;
    }
    setLoading(true);
    try {
      await socialApi.createPost(photoUri, {
        caption: caption.trim(),
        occasion: occasion.trim(),
        outfit_id: outfitId,
      });
      Alert.alert('Posted!', 'Your post is now live.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Error', e instanceof ApiError ? e.message : 'Could not create post.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
      <Screen title="New Post">
        <View style={{ padding: spacing.xl }}>
          <View style={styles.photoRow}>
            <Button label="📷 Camera" variant="ghost" onPress={() => void pickPhoto(true)} style={{ flex: 1 }} />
            <View style={{ width: spacing.md }} />
            <Button label="🖼 Gallery" onPress={() => void pickPhoto(false)} style={{ flex: 1 }} />
          </View>

          {photoUri ? (
            <Text style={styles.photoHint}>✓ Photo selected</Text>
          ) : (
            <Text style={styles.photoHint}>Select a photo to share your look.</Text>
          )}

          <Text style={styles.label}>Caption</Text>
          <View style={styles.captionRow}>
            <Button
              label="✨ Suggest caption"
              variant="ghost"
              loading={suggesting && !recordingVoice}
              onPress={() => void suggestCaption()}
            />
            <View style={{ width: spacing.md }} />
            <TouchableOpacity onPress={() => void toggleVoice()}>
              <Text style={[styles.micButton, recordingVoice && styles.micButtonActive]}>
                {recordingVoice ? '⏺ Recording… tap to stop' : '🎙 Speak caption'}
              </Text>
            </TouchableOpacity>
          </View>
          <TextInput
            style={styles.input}
            placeholder="What's the story behind this look?"
            placeholderTextColor={colors.textMuted}
            value={caption}
            onChangeText={setCaption}
            multiline
            numberOfLines={3}
          />

          <Text style={styles.label}>Occasion (optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. casual, wedding, office"
            placeholderTextColor={colors.textMuted}
            value={occasion}
            onChangeText={setOccasion}
          />

          <Button
            label="Share post"
            variant="gold"
            loading={loading}
            disabled={!photoUri}
            onPress={() => void submit()}
            style={{ marginTop: spacing.xl }}
          />
        </View>
      </Screen>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  captionRow: { alignItems: 'center', flexDirection: 'row', marginBottom: spacing.sm },
  micButton: {
    color: colors.gold,
    fontSize: 14,
    fontWeight: '600',
  },
  micButtonActive: { color: colors.danger },
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
  photoHint: { ...typography.small, color: colors.textMuted, marginTop: spacing.sm },
  photoRow: { flexDirection: 'row', marginTop: spacing.md },
  wrap: { backgroundColor: colors.ink, flex: 1 },
});
