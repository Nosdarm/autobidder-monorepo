module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    // Add prettier and tailwind plugins here after installation and setup
    // 'plugin:prettier/recommended', 
    // 'plugin:tailwindcss/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    // Add any project-specific rules here
  },
  settings: {
    react: {
      version: 'detect', // Automatically detect the React version
    },
  }
}
