import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    lib: {
      entry: "./src/main.ts",
      name: "ProjectTimelineProjections",
      fileName: "project-timeline-projections",
    }
  },
  plugins: [
    svelte(
      {
        compilerOptions: {
          customElement: true,
          css: true
        },
      },
    ),
  ],
})
