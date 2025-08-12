import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import surveySlice from './slices/surveySlice';
import processingSlice from './slices/processingSlice';
import querySlice from './slices/querySlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    survey: surveySlice,
    processing: processingSlice,
    query: querySlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
