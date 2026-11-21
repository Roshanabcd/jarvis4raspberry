/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        jarvis: { bg: '#050B16', panel: '#101E30', cyan: '#00D9FF', blue: '#218BFF', purple: '#9868FF', green: '#25E6A2', text: '#F0F8FF' },
      },
    },
  },
  plugins: [],
};
