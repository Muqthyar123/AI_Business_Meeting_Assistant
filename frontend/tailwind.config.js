/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#6558E8',
          hover: '#5548D5',
          light: '#EFEDFF',
          navy: '#15172B',
          secondary: '#8B7CF6',
          cyan: '#35C9D8',
          teal: '#DDF7F6',
        },
        surface: {
          bg: '#F7F8FC',
          card: '#FFFFFF',
          secondary: '#F0F2F8',
          darkBg: '#101224',
          darkCard: '#191C32',
          darkSecondary: '#212543',
        },
        content: {
          primary: '#202238',
          secondary: '#73768C',
          darkPrimary: '#F1F3FA',
          darkSecondary: '#9FA4C0',
        },
        edge: {
          light: '#E5E7F0',
          dark: '#2A2E54',
        },
        semantic: {
          success: '#18865B',
          successBg: '#E6F7EE',
          warning: '#B7791F',
          warningBg: '#FFF4D6',
          error: '#D14343',
          errorBg: '#FDEAEA',
          info: '#3275C7',
          infoBg: '#EAF2FF',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        'button': '10px',
        'card': '16px',
      },
      animation: {
        'pulse-subtle': 'pulseSubtle 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'waveform': 'waveform 1.2s ease-in-out infinite',
      },
      keyframes: {
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.65' },
        },
        waveform: {
          '0%, 100%': { transform: 'scaleY(0.4)' },
          '50%': { transform: 'scaleY(1)' },
        }
      }
    },
  },
  plugins: [],
}
