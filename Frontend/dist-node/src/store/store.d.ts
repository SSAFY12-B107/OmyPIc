export declare const store: import("@reduxjs/toolkit").EnhancedStore<{
    auth: import("./authSlice").AuthState;
    tests: import("./testSlice").TestState;
    script: import("./scriptSlice").ScriptState;
}, import("redux").UnknownAction, import("@reduxjs/toolkit").Tuple<[import("redux").StoreEnhancer<{
    dispatch: import("redux-thunk").ThunkDispatch<{
        auth: import("./authSlice").AuthState;
        tests: import("./testSlice").TestState;
        script: import("./scriptSlice").ScriptState;
    }, undefined, import("redux").UnknownAction>;
}>, import("redux").StoreEnhancer]>>;
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
