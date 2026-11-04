package com.nzboost.nzhub.theme;

import android.content.Context;
import android.content.res.Resources;
import com.nzboost.nzhub.NZ;

/**
 * NZHub theme selection. Theme ids are persisted in NZHub's own preference file
 * under "nzhub_theme_id": 0 = System (follow OS light/dark), 1..12 = fixed palettes.
 *
 * Style resource ids are pinned in apktool/res/values/public.xml and mirrored
 * in p56 (the app's R-style class). Keep both in sync when adding themes.
 */
public final class ThemeManager {

    public static final String KEY_THEME_ID = "nzhub_theme_id";

    public static final String[] NAMES = {
            "System",
            "Light", "Dark", "AMOLED Black", "Midnight Blue", "Forest", "Sunset",
            "Ocean", "Rose", "Lavender", "Mono", "High Contrast", "Cyberpunk",
    };

    static final int[] STYLE_IDS = {
            0x7f1506b8, // 1 Light
            0x7f1506b9, // 2 Dark
            0x7f1506ba, // 3 AMOLED Black
            0x7f1506bb, // 4 Midnight Blue
            0x7f1506bc, // 5 Forest
            0x7f1506bd, // 6 Sunset
            0x7f1506be, // 7 Ocean
            0x7f1506bf, // 8 Rose
            0x7f1506c0, // 9 Lavender
            0x7f1506c1, // 10 Mono
            0x7f1506c2, // 11 High Contrast
            0x7f1506c3, // 12 Cyberpunk
    };

    private static final boolean[] DARK = {
            false, true, true, true, true, false, true, false, false, true, false, true,
    };

    private static final int SYSTEM = 0;
    private static final int APP_THEME_DARK = 0x7f15000f;
    private static final int APP_THEME_LIGHT = 0x7f150011;

    private ThemeManager() {
    }

    /** Hands an application context to NZHub's preference holder. */
    public static void attach(Context context) {
        NZ.attach(context);
    }

    public static int getThemeId(Resources res) {
        int id = NZ.getInt(KEY_THEME_ID, SYSTEM);
        if (id < SYSTEM || id > STYLE_IDS.length) {
            id = SYSTEM;
        }
        return id;
    }

    public static void setThemeId(int id) {
        NZ.putInt(KEY_THEME_ID, id);
    }

    /** True when the selected theme id resolves to a dark palette. */
    private static boolean isDarkThemeId(int id, Resources res) {
        if (id == SYSTEM) {
            return (res.getConfiguration().uiMode & 0x30) == 0x20;
        }
        return DARK[id - 1];
    }

    /**
     * Called from BaseActivity#tw: -1 lets the original System/Light/Dark
     * preference decide; 0/1 forces light/dark for fixed palettes.
     */
    public static int darkOverride(Resources res) {
        int id = getThemeId(res);
        if (id == SYSTEM) {
            return -1;
        }
        return DARK[id - 1] ? 1 : 0;
    }

    /** Resolves the style resource the current activity should setTheme with. */
    public static int themeResourceId(Resources res) {
        int id = getThemeId(res);
        if (id == SYSTEM) {
            return isDarkThemeId(SYSTEM, res) ? APP_THEME_DARK : APP_THEME_LIGHT;
        }
        return STYLE_IDS[id - 1];
    }

    /** Opens the theme picker dialog with live apply + instant recreate. */
    public static void showPicker(final android.content.Context context) {
        if (!(context instanceof android.app.Activity)) {
            return;
        }
        final android.app.Activity activity = (android.app.Activity) context;
        if (activity.isFinishing()) {
            return;
        }
        final int current = getThemeId(activity.getResources());
        new android.app.AlertDialog.Builder(activity)
                .setTitle("Theme")
                .setSingleChoiceItems(NAMES, current, new android.content.DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(android.content.DialogInterface dialog, int which) {
                        setThemeId(which);
                        dialog.dismiss();
                        activity.recreate();
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }
}
