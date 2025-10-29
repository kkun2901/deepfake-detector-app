// src/api/firebase.ts
import { initializeApp } from 'firebase/app';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: "AIzaSyBDEZ5rNyCgXs3h5OxtIdRzmpQ8CxKxu48",
  authDomain: "deepfake-fc59d.firebaseapp.com",
  projectId: "deepfake-fc59d",
  storageBucket: "deepfake-fc59d.firebasestorage.app",
  messagingSenderId: "36844317685",
  appId: "1:36844317685:web:cc0fbb9b86642bc45b4ebc"
};

const app = initializeApp(firebaseConfig);
export const storage = getStorage(app);
