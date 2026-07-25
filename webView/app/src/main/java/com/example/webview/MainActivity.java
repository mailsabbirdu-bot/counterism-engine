package com.example.webview;

import android.Manifest;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.ColorStateList;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Message;
import android.os.PowerManager;
import android.provider.Settings;
import android.util.Log;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    private static final int REQUEST_CODE_POST_NOTIFICATIONS = 101;
    private static final int FILE_CHOOSER_REQUEST_CODE = 202;

    private WebView webView;
    private EditText etUrl;
    private TextView tvServiceStatus;
    private Button btnToggleService;
    private Button btnCopyColabCode;
    private Button btnPasteCode;
    private Button btnToggleView;
    private EditText etJsCode;
    private Button btnRunJs;
    private LinearLayout webViewContainer;

    private boolean isServiceRunning = false;
    private boolean isDesktopMode = true; // Default is Desktop Mode for Colab fully active execution
    private ValueCallback<Uri[]> uploadMessage;

    // Standard User-Agents
    // Firefox Desktop UA is Gecko-based, bypasses secure login blocks perfectly, and renders all SVG icons beautifully on startup
    private final String DESKTOP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0";
    private final String MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"; // Bypassed UA without "; wv"

    // The automated pipeline python script from colab.md
    private final String COLAB_PYTHON_SCRIPT =
        "# ==============================================================================\n" +
        "# COUNTERISM STUDIO V4 — AUTOMATED CINEMATIC PIPELINE (DYNAMIC DURATION)\n" +
        "# ==============================================================================\n\n" +
        "import os\n" +
        "import shutil\n" +
        "import subprocess\n" +
        "import json\n" +
        "import math\n\n" +
        "def print_banner(text):\n" +
        "    print(\"\\n\" + \"=\"*80)\n" +
        "    print(f\" {text}\")\n" +
        "    print(\"=\"*80)\n\n" +
        "# 1. Mount Google Drive\n" +
        "print_banner(\"📂 MOUNTING GOOGLE DRIVE\")\n" +
        "from google.colab import drive\n" +
        "drive.mount('/content/drive')\n\n" +
        "# 2. Setup Project Environment\n" +
        "PROJECT_NAME = \"counterism-engine\"\n" +
        "DRIVE_BASE_PATH = \"/content/drive/MyDrive/Counterism_Studio_V4\"\n" +
        "REPO_URL = \"https://github.com/mailsabbirdu-bot/counterism-engine\"\n\n" +
        "%cd /content\n" +
        "if not os.path.exists(PROJECT_NAME):\n" +
        "    print(f\"🚀 Cloning repository: {REPO_URL}\")\n" +
        "    !git clone {REPO_URL}\n" +
        "else:\n" +
        "    print(f\"✅ Project folder '{PROJECT_NAME}' already exists.\")\n\n" +
        "%cd {PROJECT_NAME}\n" +
        "# Fetch and checkout active feature branch containing the threading loop fix\n" +
        "!git fetch origin && git checkout feature/evidence-asyncio-loop-fix || true\n\n" +
        "# 3. Handle External Assets (Renders, Audio, Fonts, SFX)\n" +
        "print_banner(\"🔍 ASSET VERIFICATION & COPYING\")\n\n" +
        "# Crucial: Clean and create directories in the correct order\n" +
        "!rm -rf public/renders\n" +
        "!mkdir -p public/renders/audios\n" +
        "!mkdir -p public/audio\n" +
        "!mkdir -p public/fonts\n\n" +
        "# Sync Background Videos\n" +
        "drive_renders = f\"{DRIVE_BASE_PATH}/renders\"\n" +
        "if os.path.exists(drive_renders):\n" +
        "    print(f\"📡 Syncing renders from: {drive_renders}\")\n" +
        "    import glob\n" +
        "    for f in glob.glob(os.path.join(drive_renders, \"*.mp4\")):\n" +
        "        shutil.copy(f, \"public/renders/\")\n" +
        "else:\n" +
        "    print(f\"❌ FATAL: 'renders' folder NOT FOUND in Drive: {drive_renders}\")\n\n" +
        "# Sync Voiceovers\n" +
        "drive_audio = f\"{DRIVE_BASE_PATH}/audio\"\n" +
        "if os.path.exists(drive_audio):\n" +
        "    !cp -r {drive_audio}/* public/audio/\n\n" +
        "# Sync SFX & Narration (Recursive sync from multiple Drive locations)\n" +
        "print(\"📡 Searching for SFX and narration assets...\")\n" +
        "import glob\n" +
        "for sfx_path in [f\"{DRIVE_BASE_PATH}/renders/audios\", f\"{DRIVE_BASE_PATH}/renders/audio\", f\"{DRIVE_BASE_PATH}/audio\"]:\n" +
        "    if os.path.exists(sfx_path):\n" +
        "        print(f\"📦 Syncing audio from: {sfx_path}\")\n" +
        "        for ext in [\"*.mp3\", \"*.wav\", \"*.m4a\", \"*.aac\", \"*.ogg\"]:\n" +
        "            for f in glob.glob(os.path.join(sfx_path, \"**\", ext), recursive=True):\n" +
        "                shutil.copy(f, \"public/renders/audios/\")\n\n" +
        "# Sync Fonts\n" +
        "drive_fonts = f\"{DRIVE_BASE_PATH}/fonts\"\n" +
        "if os.path.exists(drive_fonts):\n" +
        "    !cp -r {drive_fonts}/* public/fonts/\n\n" +
        "# 4. Manifest Verification\n" +
        "print_banner(\"📜 MANIFEST VERIFICATION\")\n" +
        "DRIVE_JSON = f\"{DRIVE_BASE_PATH}/manifests/remotion_render.json\"\n" +
        "if os.path.exists(DRIVE_JSON):\n" +
        "    print(f\"✅ Found Drive manifest: {DRIVE_JSON}\")\n" +
        "else:\n" +
        "    print(f\"❌ FATAL: Manifest NOT FOUND in Drive: {DRIVE_JSON}\")\n\n" +
        "# 5. Install Dependencies\n" +
        "print_banner(\"🛠️ INSTALLING DEPENDENCIES\")\n" +
        "# Use -qq and --silent to ignore verbose node/apt messages\n" +
        "import shutil\n" +
        "if not shutil.which('ffmpeg'):\n" +
        "    print(\"📡 ffmpeg not found. Installing via apt-get...\")\n" +
        "    !apt-get update -y -qq && apt-get install -y -qq ffmpeg build-essential\n" +
        "else:\n" +
        "    print(\"✅ ffmpeg and build-essential are already installed. Skipping slow apt-get update.\")\n" +
        "!npm install --silent\n\n" +
        "# 6. Render Pipeline\n" +
        "print_banner(\"🎬 STARTING RENDERING PIPELINE\")\n" +
        "!npm run render -- --concurrency=1\n\n" +
        "# 7. Automatic Drive Upload\n" +
        "print_banner(\"💾 SAVING RESULTS TO GOOGLE DRIVE\")\n" +
        "LOCAL_RENDER_DIR = \"renders/overlays/remotion\"\n" +
        "DRIVE_RENDER_DIR = f\"{DRIVE_BASE_PATH}/renders/overlays/remotion\"\n" +
        "if os.path.exists(LOCAL_RENDER_DIR):\n" +
        "    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)\n" +
        "    !cp -rvu {LOCAL_RENDER_DIR}/* {DRIVE_RENDER_DIR}/\n\n" +
        "print_banner(\"🏁 PROCESS COMPLETE\")\n";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize view components
        webView = findViewById(R.id.webView);
        etUrl = findViewById(R.id.etUrl);
        tvServiceStatus = findViewById(R.id.tvServiceStatus);
        btnToggleService = findViewById(R.id.btnToggleService);
        btnCopyColabCode = findViewById(R.id.btnCopyColabCode);
        btnPasteCode = findViewById(R.id.btnPasteCode);
        btnToggleView = findViewById(R.id.btnToggleView);
        etJsCode = findViewById(R.id.etJsCode);
        btnRunJs = findViewById(R.id.btnRunJs);
        webViewContainer = findViewById(R.id.webViewContainer);

        ImageButton btnBack = findViewById(R.id.btnBack);
        ImageButton btnForward = findViewById(R.id.btnForward);
        ImageButton btnGo = findViewById(R.id.btnGo);

        // Setup toolbar listeners
        btnBack.setOnClickListener(v -> {
            if (webView.canGoBack()) {
                webView.goBack();
            }
        });

        btnForward.setOnClickListener(v -> {
            if (webView.canGoForward()) {
                webView.goForward();
            }
        });

        btnGo.setOnClickListener(v -> {
            String url = etUrl.getText().toString().trim();
            if (!url.startsWith("http://") && !url.startsWith("https://")) {
                url = "https://" + url;
            }
            webView.loadUrl(url);
        });

        // Initialize WebView settings
        setupWebView();

        // Copy Python Script to clipboard
        btnCopyColabCode.setOnClickListener(v -> {
            ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData clip = ClipData.newPlainText("Colab Python Script", COLAB_PYTHON_SCRIPT);
            if (clipboard != null) {
                clipboard.setPrimaryClip(clip);
                Toast.makeText(this, "Copied python pipeline code to clipboard!", Toast.LENGTH_SHORT).show();
            }
        });

        // Paste clipboard text programmatically into active document element
        btnPasteCode.setOnClickListener(v -> performSmartPaste());

        // Note: webView.setOnLongClickListener is NOT set here to restore Android's native text selection highlighting and standard actions

        // Toggle layout user agent mode between Desktop & Mobile view
        btnToggleView.setOnClickListener(v -> {
            isDesktopMode = !isDesktopMode;
            WebSettings settings = webView.getSettings();
            if (isDesktopMode) {
                settings.setUserAgentString(DESKTOP_USER_AGENT);
                btnToggleView.setText("🖥️ DESKTOP");
                btnToggleView.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#673AB7")));
                Toast.makeText(this, "Switched to Desktop Layout (Chrome Desktop UA)", Toast.LENGTH_SHORT).show();
            } else {
                settings.setUserAgentString(MOBILE_USER_AGENT);
                btnToggleView.setText("📱 MOBILE");
                btnToggleView.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#E91E63")));
                Toast.makeText(this, "Switched to Mobile Layout (Android Chrome Bypass UA)", Toast.LENGTH_SHORT).show();
            }
            webView.reload();
        });

        // Execute Custom JavaScript inside WebView context
        btnRunJs.setOnClickListener(v -> {
            String js = etJsCode.getText().toString().trim();
            if (!js.isEmpty()) {
                webView.evaluateJavascript(js, value -> {
                    Toast.makeText(MainActivity.this, "JS Result: " + value, Toast.LENGTH_LONG).show();
                    Log.d(TAG, "Custom JavaScript executed. Result: " + value);
                });
            } else {
                Toast.makeText(this, "Please enter JavaScript code to execute.", Toast.LENGTH_SHORT).show();
            }
        });

        // Toggle Foreground Service for persistent run
        btnToggleService.setOnClickListener(v -> {
            if (!isServiceRunning) {
                checkNotificationPermissionAndStartService();
            } else {
                stopBackgroundService();
            }
        });

        // Check and prompt for ignoring battery optimization to safeguard background runs
        requestBatteryOptimizationBypass();
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setJavaScriptCanOpenWindowsAutomatically(true);

        // Crucial: Support multiple windows to capture Google Drive mounts or popups cleanly inside separate temporary tabs
        settings.setSupportMultipleWindows(true);

        // Initial default: Chromebook Chrome Desktop UA (renders play buttons and icons perfectly, and passes sign-in)
        settings.setUserAgentString(DESKTOP_USER_AGENT);

        // Enable cookies and third party cookies
        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            cookieManager.setAcceptThirdPartyCookies(webView, true);
        }

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                etUrl.setText(url);
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                etUrl.setText(url);
                // Flush cookies to ensure credential propagation across domains
                CookieManager.getInstance().flush();
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            // For Android 5.0+ - File Upload Support (vital for adding custom manifests)
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (uploadMessage != null) {
                    uploadMessage.onReceiveValue(null);
                    uploadMessage = null;
                }
                uploadMessage = filePathCallback;

                Intent intent = null;
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    intent = fileChooserParams.createIntent();
                } else {
                    intent = new Intent(Intent.ACTION_GET_CONTENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("*/*");
                }

                try {
                    startActivityForResult(intent, FILE_CHOOSER_REQUEST_CODE);
                } catch (Exception e) {
                    uploadMessage = null;
                    Toast.makeText(MainActivity.this, "Cannot Open File Chooser", Toast.LENGTH_SHORT).show();
                    return false;
                }
                return true;
            }

            // Capture new tab/window creation (like Google Drive Sync popups) and overlay a secondary tab safely
            @Override
            public boolean onCreateWindow(WebView view, boolean isDialog, boolean isUserGesture, Message resultMsg) {
                Log.d(TAG, "onCreateWindow triggered");
                WebView newWebView = new WebView(MainActivity.this);

                WebSettings newSettings = newWebView.getSettings();
                newSettings.setJavaScriptEnabled(true);
                newSettings.setDomStorageEnabled(true);
                newSettings.setDatabaseEnabled(true);
                newSettings.setJavaScriptCanOpenWindowsAutomatically(true);
                newSettings.setSupportMultipleWindows(true);
                newSettings.setUserAgentString(isDesktopMode ? DESKTOP_USER_AGENT : MOBILE_USER_AGENT);

                CookieManager cm = CookieManager.getInstance();
                cm.setAcceptCookie(true);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    cm.setAcceptThirdPartyCookies(newWebView, true);
                }

                newWebView.setLayoutParams(new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.MATCH_PARENT
                ));

                newWebView.setWebViewClient(new WebViewClient() {
                    @Override
                    public boolean shouldOverrideUrlLoading(WebView v, String url) {
                        return false; // Load OAuth redirect flows inside the secondary tab itself
                    }

                    @Override
                    public void onPageFinished(WebView v, String url) {
                        super.onPageFinished(v, url);
                        etUrl.setText(url);
                        // Flush cookies so OAuth credentials propagate immediately to main WebView
                        CookieManager.getInstance().flush();
                    }
                });

                newWebView.setWebChromeClient(new WebChromeClient() {
                    @Override
                    public void onCloseWindow(WebView window) {
                        Log.d(TAG, "onCloseWindow triggered for secondary WebView");
                        if (webViewContainer != null) {
                            webViewContainer.removeView(window);
                        }
                        window.destroy();
                        // Restore visibility of original Colab session WebView
                        webView.setVisibility(View.VISIBLE);
                        etUrl.setText(webView.getUrl());
                    }
                });

                if (webViewContainer != null) {
                    webView.setVisibility(View.GONE); // Hide background Colab session
                    webViewContainer.addView(newWebView);
                }

                WebView.WebViewTransport transport = (WebView.WebViewTransport) resultMsg.obj;
                transport.setWebView(newWebView);
                resultMsg.sendToTarget();
                return true;
            }

            @Override
            public void onCloseWindow(WebView window) {
                Log.d(TAG, "onCloseWindow triggered for main WebChromeClient");
                if (webViewContainer != null) {
                    webViewContainer.removeView(window);
                }
                window.destroy();
                webView.setVisibility(View.VISIBLE);
                etUrl.setText(webView.getUrl());
            }
        });

        // Initial Page load
        webView.loadUrl("https://colab.research.google.com");
    }

    private void performSmartPaste() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboard != null && clipboard.hasPrimaryClip()) {
            ClipData.Item item = clipboard.getPrimaryClip().getItemAt(0);
            CharSequence textChar = item.getText();
            if (textChar != null) {
                String rawText = textChar.toString();
                // Safely escape backslashes, single quotes, and newlines for Javascript evaluation
                String escapedText = rawText.replace("\\", "\\\\")
                                             .replace("'", "\\'")
                                             .replace("\n", "\\n")
                                             .replace("\r", "");

                // Traverse shadow roots and nested iframes to find deep active element, then execute insertText on its iframe document or use input value simulation fallback
                String jsPaste = "(function() {" +
                        "try {" +
                        "  function getDeepActive() {" +
                        "    let el = document.activeElement;" +
                        "    while (el && el.shadowRoot && el.shadowRoot.activeElement) {" +
                        "      el = el.shadowRoot.activeElement;" +
                        "    }" +
                        "    while (el && el.contentDocument && el.contentDocument.activeElement) {" +
                        "      el = el.contentDocument.activeElement;" +
                        "      while (el && el.shadowRoot && el.shadowRoot.activeElement) {" +
                        "        el = el.shadowRoot.activeElement;" +
                        "      }" +
                        "    }" +
                        "    return el;" +
                        "  }" +
                        "  let active = getDeepActive();" +
                        "  if (active) {" +
                        "    active.focus();" +
                        "    let doc = active.ownerDocument || document;" +
                        "    let success = doc.execCommand('insertText', false, '" + escapedText + "');" +
                        "    if (!success && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {" +
                        "      let start = active.selectionStart || 0;" +
                        "      let end = active.selectionEnd || 0;" +
                        "      let val = active.value || '';" +
                        "      active.value = val.substring(0, start) + '" + escapedText + "' + val.substring(end);" +
                        "      active.setSelectionRange(start + '" + escapedText + "'.length, start + '" + escapedText + "'.length);" +
                        "      let evt = new Event('input', { bubbles: true });" +
                        "      active.dispatchEvent(evt);" +
                        "    }" +
                        "    return 'success';" +
                        "  }" +
                        "} catch(e) {" +
                        "  return e.toString();" +
                        "}" +
                        "return 'none';" +
                        "})()";

                webView.evaluateJavascript(jsPaste, value -> {
                    Toast.makeText(MainActivity.this, "Pasted text successfully into focused cell or terminal!", Toast.LENGTH_SHORT).show();
                    Log.d(TAG, "Deep smart paste evaluation result: " + value);
                });
            } else {
                Toast.makeText(this, "Clipboard is empty or does not contain text.", Toast.LENGTH_SHORT).show();
            }
        } else {
            Toast.makeText(this, "No text found on clipboard.", Toast.LENGTH_SHORT).show();
        }
    }

    private void checkNotificationPermissionAndStartService() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQUEST_CODE_POST_NOTIFICATIONS);
            } else {
                startBackgroundService();
            }
        } else {
            startBackgroundService();
        }
    }

    private void startBackgroundService() {
        Intent serviceIntent = new Intent(this, BackgroundService.class);
        ContextCompat.startForegroundService(this, serviceIntent);
        isServiceRunning = true;
        tvServiceStatus.setText("Background service: RUNNING (CPU/WiFi Kept Alive)");
        tvServiceStatus.setTextColor(Color.parseColor("#4CAF50"));
        btnToggleService.setText("STOP BACKGROUND RUN");
        btnToggleService.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#F44336")));
        Toast.makeText(this, "Foreground service started! Execution is active in background.", Toast.LENGTH_SHORT).show();
    }

    private void stopBackgroundService() {
        Intent serviceIntent = new Intent(this, BackgroundService.class);
        stopService(serviceIntent);
        isServiceRunning = false;
        tvServiceStatus.setText("Background service: STOPPED");
        tvServiceStatus.setTextColor(Color.parseColor("#333333"));
        btnToggleService.setText("START BACKGROUND RUN");
        btnToggleService.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#4CAF50")));
        Toast.makeText(this, "Background locks released.", Toast.LENGTH_SHORT).show();
    }

    private void requestBatteryOptimizationBypass() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Intent intent = new Intent();
            String packageName = getPackageName();
            PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
            if (pm != null && !pm.isIgnoringBatteryOptimizations(packageName)) {
                intent.setAction(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
                intent.setData(Uri.parse("package:" + packageName));
                try {
                    startActivity(intent);
                } catch (Exception e) {
                    Log.e(TAG, "Failed to launch battery settings", e);
                }
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILE_CHOOSER_REQUEST_CODE) {
            if (uploadMessage == null) return;
            Uri[] results = null;
            if (resultCode == RESULT_OK && data != null) {
                String dataString = data.getDataString();
                if (dataString != null) {
                    results = new Uri[]{Uri.parse(dataString)};
                } else if (data.getClipData() != null) {
                    int count = data.getClipData().getItemCount();
                    results = new Uri[count];
                    for (int i = 0; i < count; i++) {
                        results[i] = data.getClipData().getItemAt(i).getUri();
                    }
                }
            }
            uploadMessage.onReceiveValue(results);
            uploadMessage = null;
        } else {
            super.onActivityResult(requestCode, resultCode, data);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_CODE_POST_NOTIFICATIONS) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startBackgroundService();
            } else {
                Toast.makeText(this, "Notification permission is required to run in background.", Toast.LENGTH_LONG).show();
            }
        }
    }

    @Override
    public void onBackPressed() {
        // Intercept back click if a dynamic popup tab WebView is overlayed inside webViewContainer
        if (webViewContainer != null && webViewContainer.getChildCount() > 1) {
            View activePopup = webViewContainer.getChildAt(1);
            if (activePopup instanceof WebView) {
                webViewContainer.removeView(activePopup);
                ((WebView) activePopup).destroy();
                Log.d(TAG, "Successfully closed authorization tab via onBackPressed");
            }
            webView.setVisibility(View.VISIBLE);
            etUrl.setText(webView.getUrl());
            Toast.makeText(this, "Closed authorization tab.", Toast.LENGTH_SHORT).show();
        } else if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
