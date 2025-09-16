// src/api/uploadToFirebase.ts
import { storage } from './firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import * as FileSystem from 'expo-file-system';

export async function uploadVideoAsync(localUri: string, filename: string): Promise<string> {
  const response = await FileSystem.readAsStringAsync(localUri, {
    encoding: FileSystem.EncodingType.Base64,
  });

  const storageRef = ref(storage, `videos/${filename}`);
  const blob = Buffer.from(response, 'base64');

  const metadata = {
    contentType: 'video/mp4',
  };

  await uploadBytes(storageRef, blob, metadata);
  return await getDownloadURL(storageRef);
}
