package com.nzboost.nzhub.update;

import android.content.Context;
import android.view.View;

/** Click listener bound to the Settings "Check for updates" row. */
public final class ManualCheckListener implements View.OnClickListener {

    @Override
    public void onClick(View v) {
        Context ctx = v.getContext();
        UpdateChecker.check(ctx, true);
    }
}
