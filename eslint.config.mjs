export default [
  {
    ignores: [
      '**/node_modules/**',
      'frontend/dist/**',
      'frontend/**/*.bundle.js',
      'frontend/**/*.bundle.css',
      'frontend/**/*.bundle.css.map',
      'frontend/whiteboard/**',
      'services/**',
    ],
  },
  {
    files: ['frontend/src/**/*.{js,jsx}', 'frontend/build-dist.mjs'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    rules: {
      'no-unused-vars': ['warn', { varsIgnorePattern: '^_', argsIgnorePattern: '^_' }],
      'no-undef': 'off',
    },
  },
];
