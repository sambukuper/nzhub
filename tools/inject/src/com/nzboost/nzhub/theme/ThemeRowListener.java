package com.nzboost.nzhub.theme;

import android.view.View;

/** Click listener bound to the UI Settings "Theme" row. */
public final class ThemeRowListener implements View.OnClickListener {

    @Override
    public void onClick(View v) {
        ThemeManager.showPicker(v.getContext());
    }
}
