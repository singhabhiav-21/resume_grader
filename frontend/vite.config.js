import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";
