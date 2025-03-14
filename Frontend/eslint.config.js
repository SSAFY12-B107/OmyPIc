module.exports = {
  root: true, // 이 설정이 최상위 설정임을 나타냄
  
  env: { browser: true, es2020: true }, // 브라우저 환경, ES2020 문법 사용
  
  extends: [
    'eslint:recommended', // 기본 권장 규칙
    'plugin:@typescript-eslint/recommended', // TS 권장 규칙
    'plugin:react-hooks/recommended' // React Hooks 권장 규칙
  ],
  
  ignorePatterns: ['dist', '.eslintrc.cjs'], // 린트 검사 제외 경로
  
  parser: '@typescript-eslint/parser', // TS 코드 파싱용
  
  plugins: [
    'react', // React 규칙
    'react-refresh', // Fast Refresh 규칙
    'react-hooks', // Hooks 규칙
    'jsx-a11y', // 접근성 규칙
    'prettier', // 코드 포맷팅 연동
    'import' // import 문법 검사
  ],
  
  rules: {
    'react/no-unknown-property': ['error', { ignore: ['css'] }], 
    // CSS-in-JS 사용 시 'css' prop 허용

    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': 'error',
    // JS 대신 TS의 미사용 변수 규칙 사용
    
    'react/react-in-jsx-scope': 'off', 
    // React 17+ 에서는 import React 불필요
    
    'react-refresh/only-export-components': 'off', 
    // Fast Refresh 규칙 비활성화
  },
};