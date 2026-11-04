package com.nzboost.nzhub.update;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;

import com.nzboost.nzhub.NZ;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * NZHub update checker backed by GitHub Releases:
 * GET https://api.github.com/repos/sambukuper/nzhub/releases/latest
 *
 * - semantic comparison of tag_name against the installed versionName
 * - changelog (release body) shown in the "Update available" dialog
 * - in-place download of the release .apk asset, then install prompt
 * - graceful handling of offline / rate limit / no releases
 *
 * Manual checks report failures as toasts; automatic (startup) checks are
 * silent and throttled to one request every CHECK_INTERVAL_MS.
 */
public final class UpdateChecker {

    public static final String REPO_URL = "https://github.com/sambukuper/nzhub";
    private static final String API_URL = "https://api.github.com/repos/sambukuper/nzhub/releases/latest";
    private static final String APK_FILE_NAME = "NZHub_update.apk";
    private static final String KEY_LAST_CHECK = "nzhub_last_update_check";
    private static final long CHECK_INTERVAL_MS = 6L * 60L * 60L * 1000L;

    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private UpdateChecker() {
    }

    /** Entry point. manual=true always checks and reports; manual=false is throttled+silent. */
    public static void check(final Context context, final boolean manual) {
        if (!manual) {
            long now = System.currentTimeMillis();
            long last = NZ.getLong(KEY_LAST_CHECK, 0L);
            if (now - last < CHECK_INTERVAL_MS) {
                return;
            }
            NZ.putLong(KEY_LAST_CHECK, now);
        }
        new Thread(new Runnable() {
            @Override
            public void run() {
                performCheck(context, manual);
            }
        }, "nzhub-update-check").start();
    }

    /** Throttled, silent startup check invoked from MainActivity.onCreate. */
    public static void maybeAutoCheck(Context context) {
        check(context, false);
    }

    private static void performCheck(Context context, boolean manual) {
        HttpURLConnection conn = null;
        try {
            conn = (HttpURLConnection) new URL(API_URL).openConnection();
            conn.setConnectTimeout(10000);
            conn.setReadTimeout(15000);
            conn.setRequestProperty("Accept", "application/vnd.github+json");
            conn.setRequestProperty("User-Agent", "NZHub-Android");
            int code = conn.getResponseCode();
            if (code == 404) {
                if (manual) {
                    toast(context, "No releases published yet.");
                }
                return;
            }
            if (code == 403 || code == 429) {
                if (manual) {
                    toast(context, "GitHub rate limit reached. Try again later.");
                }
                return;
            }
            if (code != 200) {
                if (manual) {
                    toast(context, "Update check failed (HTTP " + code + ").");
                }
                return;
            }
            String body = readAll(conn.getInputStream());
            JSONObject release = new JSONObject(body);
            String tag = release.optString("tag_name", "");
            String notes = release.optString("body", "");
            String releaseName = release.optString("name", "");
            String apkUrl = findApkAsset(release);
            String cleanTag = tag.startsWith("v") ? tag.substring(1) : tag;
            String current = currentVersion(context);
            if (cleanTag.length() == 0) {
                if (manual) {
                    toast(context, "No release version found.");
                }
                return;
            }
            if (compareVersions(cleanTag, current) <= 0) {
                if (manual) {
                    toast(context, "You are on the latest version (" + current + ").");
                }
                return;
            }
            showUpdateDialog(context, cleanTag, releaseName, notes, apkUrl);
        } catch (Exception e) {
            if (manual) {
                toast(context, "Update check failed: offline or unreachable.");
            }
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }

    private static String findApkAsset(JSONObject release) {
        try {
            JSONArray assets = release.getJSONArray("assets");
            for (int i = 0; i < assets.length(); i++) {
                JSONObject a = assets.getJSONObject(i);
                String name = a.optString("name", "");
                if (name.toLowerCase().endsWith(".apk")) {
                    return a.optString("browser_download_url", "");
                }
            }
        } catch (Exception ignored) {
        }
        return null;
    }

    private static String currentVersion(Context context) {
        try {
            return context.getPackageManager()
                    .getPackageInfo(context.getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "0.0.0";
        }
    }

    /** Returns positive when remote > local, 0 equal, negative when remote < local. */
    static int compareVersions(String remote, String local) {
        int[] r = parse(remote);
        int[] l = parse(local);
        for (int i = 0; i < 3; i++) {
            if (r[i] != l[i]) {
                return r[i] < l[i] ? -1 : 1;
            }
        }
        return 0;
    }

    private static int[] parse(String v) {
        int[] out = new int[3];
        if (v == null) {
            return out;
        }
        int dash = v.indexOf('-');
        if (dash >= 0) {
            v = v.substring(0, dash);
        }
        String[] parts = v.split("\\.");
        for (int i = 0; i < 3 && i < parts.length; i++) {
            try {
                out[i] = Integer.parseInt(parts[i].trim());
            } catch (NumberFormatException e) {
                out[i] = 0;
            }
        }
        return out;
    }

    // ------------------------------------------------------------------ UI

    private static void showUpdateDialog(final Context context, final String tag,
                                         final String releaseName, final String notes,
                                         final String apkUrl) {
        MAIN.post(new Runnable() {
            @Override
            public void run() {
                if (!(context instanceof Activity) || ((Activity) context).isFinishing()) {
                    return;
                }
                StringBuilder msg = new StringBuilder();
                if (releaseName.length() > 0 && !releaseName.equals(tag)) {
                    msg.append(releaseName).append('\n');
                }
                msg.append("Version ").append(tag);
                if (notes != null && notes.trim().length() > 0) {
                    String trimmed = notes.trim();
                    if (trimmed.length() > 1200) {
                        trimmed = trimmed.substring(0, 1200) + "…";
                    }
                    msg.append("\n\n").append(trimmed);
                }
                new AlertDialog.Builder(context)
                        .setTitle("Update available")
                        .setMessage(msg.toString())
                        .setPositiveButton("Download & install", new android.content.DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(android.content.DialogInterface d, int w) {
                                if (apkUrl != null && apkUrl.length() > 0) {
                                    downloadAndPrompt(context, apkUrl);
                                } else {
                                    openReleasesPage(context);
                                }
                            }
                        })
                        .setNegativeButton("Later", null)
                        .show();
            }
        });
    }

    private static void downloadAndPrompt(final Context context, final String url) {
        final AlertDialog[] progress = new AlertDialog[1];
        MAIN.post(new Runnable() {
            @Override
            public void run() {
                if (context instanceof Activity) {
                    progress[0] = new AlertDialog.Builder(context)
                            .setTitle("Downloading update")
                            .setMessage("Starting download…")
                            .setNegativeButton("Cancel", null)
                            .show();
                }
            }
        });
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    File out = new File(context.getExternalFilesDir(null), APK_FILE_NAME);
                    HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
                    conn.setConnectTimeout(15000);
                    conn.setReadTimeout(30000);
                    conn.setRequestProperty("User-Agent", "NZHub-Android");
                    int code = conn.getResponseCode();
                    if (code != 200) {
                        throw new IllegalStateException("HTTP " + code);
                    }
                    long total = conn.getContentLength();
                    InputStream in = conn.getInputStream();
                    FileOutputStream fos = new FileOutputStream(out);
                    byte[] buf = new byte[16384];
                    long read = 0;
                    int n;
                    while ((n = in.read(buf)) != -1) {
                        fos.write(buf, 0, n);
                        read += n;
                        if (total > 0) {
                            final int pct = (int) (read * 100 / total);
                            MAIN.post(new Runnable() {
                                @Override
                                public void run() {
                                    if (progress[0] != null && progress[0].isShowing()) {
                                        progress[0].setMessage("Downloading… " + pct + "%");
                                    }
                                }
                            });
                        }
                    }
                    fos.flush();
                    fos.close();
                    in.close();
                    conn.disconnect();
                    MAIN.post(new Runnable() {
                        @Override
                        public void run() {
                            if (progress[0] != null) {
                                progress[0].dismiss();
                            }
                            promptInstall(context, out);
                        }
                    });
                } catch (final Exception e) {
                    MAIN.post(new Runnable() {
                        @Override
                        public void run() {
                            if (progress[0] != null) {
                                progress[0].dismiss();
                            }
                            toast(context, "Download failed. Check your connection.");
                        }
                    });
                }
            }
        }, "nzhub-update-download").start();
    }

    private static void promptInstall(final Context context, final File apk) {
        MAIN.post(new Runnable() {
            @Override
            public void run() {
                if (!(context instanceof Activity) || ((Activity) context).isFinishing()) {
                    return;
                }
                new AlertDialog.Builder(context)
                        .setTitle("Install update")
                        .setMessage("The update has been downloaded. Install it now?")
                        .setPositiveButton("Install", new android.content.DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(android.content.DialogInterface d, int w) {
                                install(context, apk);
                            }
                        })
                        .setNegativeButton("Cancel", null)
                        .show();
            }
        });
    }

    /**
     * The bundled androidx FileProvider has getUriForFile renamed by R8, so the
     * lookup goes by signature instead of by name.
     */
    private static Uri uriForFile(Context context, File apk) throws Exception {
        Class<?> provider = Class.forName("androidx.core.content.FileProvider");
        String authority = context.getPackageName() + ".provider";
        try {
            Method named = provider.getMethod("getUriForFile", Context.class, String.class, File.class);
            return (Uri) named.invoke(null, context, authority, apk);
        } catch (NoSuchMethodException e) {
            for (Method m : provider.getMethods()) {
                if (!Modifier.isStatic(m.getModifiers())) {
                    continue;
                }
                Class<?>[] params = m.getParameterTypes();
                if (params.length == 3 && params[0] == Context.class
                        && params[1] == String.class && params[2] == File.class
                        && Uri.class.equals(m.getReturnType())) {
                    return (Uri) m.invoke(null, context, authority, apk);
                }
            }
            throw e;
        }
    }

    private static void install(Context context, File apk) {
        try {
            Intent intent = new Intent(Intent.ACTION_INSTALL_PACKAGE);
            intent.setData(uriForFile(context, apk));
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
        } catch (Exception e) {
            openReleasesPage(context);
        }
    }

    private static void openReleasesPage(Context context) {
        try {
            context.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(REPO_URL + "/releases")));
        } catch (Exception ignored) {
        }
    }

    private static void toast(final Context context, final String text) {
        MAIN.post(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(context, text, Toast.LENGTH_LONG).show();
            }
        });
    }

    private static String readAll(InputStream in) throws Exception {
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) != -1) {
            bos.write(buf, 0, n);
        }
        in.close();
        return new String(bos.toByteArray(), "UTF-8");
    }
}
