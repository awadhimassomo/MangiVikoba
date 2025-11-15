module.exports = {
  content: [
    './templates/**/*.html',
    './landing/templates/landing/**/*.html',
    './registration/templates/registration/**/*.html',
    './dashboard/templates/dashboard/**/*.html',
    // Add paths to any other template files here
  ],
  theme: {
    extend: {
      colors: {
        'mangi-red': '#C72C41',
        'mangi-bright-red': '#EE4540',
        'mangi-burgundy': '#801336',
        'mangi-dark-maroon': '#510A32',
        'mangi-deep-purple': '#20142C',
      },
      backgroundImage: {
        'gradient-mangi': 'linear-gradient(to right, #C72C41, #510A32)',
      },
      boxShadow: {
        'card': '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}