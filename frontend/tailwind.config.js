/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: { 950: '#050912', 900: '#0a1020', 800: '#0f1830', 700: '#16213f', 600: '#223056' },
        accent: { DEFAULT: '#0891b2', soft: '#06b6d4', green: '#059669' },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'Consolas', 'monospace'],
      },
      boxShadow: { glow: '0 0 60px -15px rgba(8,145,178,0.25)' },
    },
  },
  plugins: [],
}
