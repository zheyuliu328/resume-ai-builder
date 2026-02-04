/** @type {import('eslint').Linter.Config} */
module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2021: true,
  },
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'script',
  },
  extends: ['eslint:recommended'],
  globals: {
    // Shared globals across plain <script> files (no bundler)
    API_BASE: 'readonly',
    apiCall: 'readonly',
    currentResumeData: 'writable',
    isConfigHealthy: 'writable',
    activeVariantName: 'writable',
    initVariants: 'readonly',
    setDirty: 'readonly',
    showNotification: 'readonly',
    switchView: 'readonly',
    onVariantChangedForChat: 'readonly',
  },
  rules: {
    // In this repo we expose many functions via global scope / HTML handlers.
    // Disable false positives; keep real correctness checks like no-undef.
    'no-unused-vars': 'off',
  },
  ignorePatterns: ['node_modules/'],
};
