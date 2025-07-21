import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ThemeState {
  theme: boolean; // true = світла, false = темна
}

const initialState: ThemeState = {
  theme: true,
};

const themeSlice = createSlice({
  name: 'themeSlice',
  initialState,
  reducers: {
    themeChange: (state) => {
      state.theme = !state.theme;
    },
    setTheme: (state, action: PayloadAction<boolean>) => {
      state.theme = action.payload;
    },
  },
});

export const themeActions = themeSlice.actions;
export const themeReducer = themeSlice.reducer; // ✅ ЕКСПОРТ!

export default themeSlice;