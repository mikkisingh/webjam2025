// Import the functions you need from the SDKs you need
import { getAuth } from "firebase/auth"; 
import { initializeApp } from "firebase/app";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "",
  authDomain: "medicheck-71418.firebaseapp.com",
  projectId: "medicheck-71418",
  storageBucket: "medicheck-71418.firebasestorage.app",
  messagingSenderId: "1016966698695",
  appId: "1:1016966698695:web:533fe58e680ce19e9c50e2"
};
// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
