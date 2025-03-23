import { configureStore } from "@reduxjs/toolkit";
import authReducer from './authSlice';
// import testReducer from '.testSlice';

// 2. Redux 스토어 설정
export const store = configureStore({
  reducer: {
    auth: authReducer,
    // test: testReducer,
  },
});

// RootState 타입 export (useSelector에서 사용)
export type RootState = ReturnType<typeof store.getState>;

// AppDispatch 타입 export (useDispatch에서 사용)
export type AppDispatch = typeof store.dispatch;
