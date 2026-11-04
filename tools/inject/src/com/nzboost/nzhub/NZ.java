package com.nzboost.nzhub;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * NZHub-owned preferences, kept in a separate file so nothing here depends on
 * the host app's obfuscated storage classes.
 */
public final class NZ {

    private static volatile Context sApp;

    private NZ() {
    }

    /** Called from BaseActivity.onCreate before the theme is resolved. */
    public static void attach(Context context) {
        if (context == null) {
            return;
        }
        Context app = context.getApplicationContext();
        sApp = app != null ? app : context;
    }

    public static Context context() {
        return sApp;
    }

    private static SharedPreferences prefs() {
        Context c = sApp;
        return c == null ? null : c.getSharedPreferences("nzhub", Context.MODE_PRIVATE);
    }

    public static int getInt(String key, int def) {
        SharedPreferences p = prefs();
        return p == null ? def : p.getInt(key, def);
    }

    public static void putInt(String key, int value) {
        SharedPreferences p = prefs();
        if (p != null) {
            p.edit().putInt(key, value).apply();
        }
    }

    public static long getLong(String key, long def) {
        SharedPreferences p = prefs();
        return p == null ? def : p.getLong(key, def);
    }

    public static void putLong(String key, long value) {
        SharedPreferences p = prefs();
        if (p != null) {
            p.edit().putLong(key, value).apply();
        }
    }
}
