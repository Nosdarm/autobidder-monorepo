import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'
// import path from 'path' // No longer needed

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  // resolve: { // Handled by vite-tsconfig-paths
  //   alias: {
  //     "@": path.resolve(__dirname, "./src"),
  //   }
  // }
})
