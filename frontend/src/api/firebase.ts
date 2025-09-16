// src/api/firebase.ts
import { initializeApp } from 'firebase/app';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: "AIzaSyAxyx10kXqri_8P-QAxsjdgSLs7g9dDU4",
  authDomain: "deepfake-89954.firebaseapp.com",
  projectId: "deepfake-89954",
  storageBucket: "deepfake-89954.appspot.com",
  messagingSenderId: "41308097744",
  appId: "1:41308097744:web:7bfbf1872ccca75692285",
  measurementId: "G-NSWRBNJ8DZ"
};

const app = initializeApp(firebaseConfig);
export const storage = getStorage(app);
