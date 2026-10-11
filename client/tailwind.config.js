/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        finance: {
          950: '#070B14', // Deepest background canvas
          900: '#0B1120', // Main dark canvas
          850: '#0E1726', // Elevated panels / sidebar
          800: '#111827', // Primary card surfaces
          750: '#151F32', // Elevated interactive cards
          700: '#1E293B', // Subtle containers & headers
          600: '#334155', // Borders & dividers
          500: '#64748B', // Secondary icons / muted text
          400: '#94A3B8', // Secondary body text
          300: '#CBD5E1', // Primary body text
          200: '#E2E8F0', // Highlight text
          100: '#F1F5F9', // Near-white headers
          50: '#F8FAFC',
        },
        brand: {
          primary: '#0EA5E9', // Vivid fintech cyan/blue
          accent: '#38BDF8',  // Glowing active cyan
          dark: '#0369A1',
          light: '#38BDF8',
        },
        status: {
          success: '#10B981', // Emerald
          warning: '#F59E0B', // Amber
          danger: '#F43F5E',  // Rose/red
          info: '#0EA5E9',    // Cyan/blue
          neutral: '#64748B', // Slate
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      }
    },
  },
  plugins: [],
}
