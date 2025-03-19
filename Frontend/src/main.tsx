
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import App from './App';
import "./App.css"

// Redux 관련 타입 및 리듀서 import
import  store  from './store'

// import authReducer from './store/slices/authSlice';
// import cartReducer from './store/slices/cartSlice';

// // 2. Redux 스토어 설정
// export const store = configureStore({
//   reducer: {
//     // auth: authReducer,
//     // cart: cartReducer,
//     // 다른 리듀서 추가
//   },
//   middleware: (getDefaultMiddleware) =>
//     getDefaultMiddleware({
//       serializableCheck: {
//         // 필요시 직렬화할 수 없는 값 무시 설정
//         ignoredActions: [],
//         ignoredPaths: [],
//       },
//     }),
//   devTools: process.env.NODE_ENV !== 'production',
// });

// Redux 타입 정의
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// 3. TanStack Query 클라이언트 설정
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      // staleTime: 5 * 60 * 1000, // 5분
      // cacheTime: 10 * 60 * 1000, // 10분
    },
  },
});

// 4. React 앱 렌더링
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <App />
        {process.env.NODE_ENV !== 'production' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </Provider>
  </React.StrictMode>
);