package com.example.webview_3;

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
import android.webkit.JavascriptInterface;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
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
    private WebView geminiWebView;
    private EditText etUrl;
    private TextView tvServiceStatus;
    private Button btnToggleService;
    private Button btnCopyColabCode;
    private Button btnPasteCode;
    private Button btnToggleView;
    private EditText etJsCode;
    private Button btnRunJs;
    private LinearLayout webViewContainer;

    // Tabs layout controls
    private Button btnTabColab;
    private Button btnTabGemini;

    // Monospace Terminal UI Components
    private LinearLayout llTerminalHeader;
    private TextView tvTerminalTitle;
    private TextView tvTerminalToggle;
    private ScrollView svTerminalLogs;
    private TextView tvTerminalLogs;

    private boolean isServiceRunning = false;
    private boolean isDesktopMode = true; // Default is Desktop Mode for Colab fully active execution
    private ValueCallback<Uri[]> uploadMessage;

    private boolean colabDetectedLogged = false;

    // State machine controls for upgraded automated Gemini flow
    private String sActivePrompt = "";
    private String sActiveUId = "";
    private boolean sAutomationInProgress = false;
    private int geminiState = 0; // 0: Idle, 1: Paste/Send, 2: Wait/Copy Response
    private long geminiStateTimestamp = 0;

    // Standard User-Agents
    private final String DESKTOP_USER_AGENT = "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
    private final String MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36";

    // Polling and Automation Handler
    private final android.os.Handler automationHandler = new android.os.Handler();
    private final Runnable automationRunnable = new Runnable() {
        @Override
        public void run() {
            if (webView != null) {
                injectPollingScript();
            }
            if (sAutomationInProgress) {
                pollGeminiAutomation();
            }
            automationHandler.postDelayed(this, 2500); // Poll every 2.5 seconds
        }
    };

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
        geminiWebView = findViewById(R.id.geminiWebView);
        etUrl = findViewById(R.id.etUrl);
        tvServiceStatus = findViewById(R.id.tvServiceStatus);
        btnToggleService = findViewById(R.id.btnToggleService);
        btnCopyColabCode = findViewById(R.id.btnCopyColabCode);
        btnPasteCode = findViewById(R.id.btnPasteCode);
        btnToggleView = findViewById(R.id.btnToggleView);
        etJsCode = findViewById(R.id.etJsCode);
        btnRunJs = findViewById(R.id.btnRunJs);
        webViewContainer = findViewById(R.id.webViewContainer);

        // Tab Buttons
        btnTabColab = findViewById(R.id.btnTabColab);
        btnTabGemini = findViewById(R.id.btnTabGemini);

        btnTabColab.setOnClickListener(v -> switchTab(true));
        btnTabGemini.setOnClickListener(v -> switchTab(false));

        // Initialize Monospace Terminal Views
        llTerminalHeader = findViewById(R.id.llTerminalHeader);
        tvTerminalTitle = findViewById(R.id.tvTerminalTitle);
        tvTerminalToggle = findViewById(R.id.tvTerminalToggle);
        svTerminalLogs = findViewById(R.id.svTerminalLogs);
        tvTerminalLogs = findViewById(R.id.tvTerminalLogs);

        llTerminalHeader.setOnClickListener(v -> {
            if (svTerminalLogs.getVisibility() == View.GONE) {
                svTerminalLogs.setVisibility(View.VISIBLE);
                tvTerminalToggle.setText("▼ COLLAPSE");
            } else {
                svTerminalLogs.setVisibility(View.GONE);
                tvTerminalToggle.setText("▲ EXPAND");
            }
        });

        addLog("SYSTEM: Monospace terminal initialized. Awaiting Colab runs...");

        ImageButton btnBack = findViewById(R.id.btnBack);
        ImageButton btnForward = findViewById(R.id.btnForward);
        ImageButton btnGo = findViewById(R.id.btnGo);

        // Setup toolbar listeners
        btnBack.setOnClickListener(v -> {
            if (isColabActive()) {
                if (webView.canGoBack()) webView.goBack();
            } else {
                if (geminiWebView.canGoBack()) geminiWebView.goBack();
            }
        });

        btnForward.setOnClickListener(v -> {
            if (isColabActive()) {
                if (webView.canGoForward()) webView.goForward();
            } else {
                if (geminiWebView.canGoForward()) geminiWebView.goForward();
            }
        });

        btnGo.setOnClickListener(v -> {
            String url = etUrl.getText().toString().trim();
            if (!url.startsWith("http://") && !url.startsWith("https://")) {
                url = "https://" + url;
            }
            if (isColabActive()) {
                webView.loadUrl(url);
            } else {
                geminiWebView.loadUrl(url);
            }
        });

        // Initialize WebView settings
        setupWebView();
        setupGeminiWebView();

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

        // Toggle layout user agent mode between Desktop & Mobile view
        btnToggleView.setOnClickListener(v -> {
            isDesktopMode = !isDesktopMode;
            WebSettings settings = webView.getSettings();
            WebSettings gemSettings = geminiWebView.getSettings();
            if (isDesktopMode) {
                settings.setUserAgentString(DESKTOP_USER_AGENT);
                gemSettings.setUserAgentString(DESKTOP_USER_AGENT);
                btnToggleView.setText("🖥️ DESKTOP");
                btnToggleView.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#673AB7")));
                Toast.makeText(this, "Switched to Desktop Layout (Chrome Desktop UA)", Toast.LENGTH_SHORT).show();
            } else {
                settings.setUserAgentString(MOBILE_USER_AGENT);
                gemSettings.setUserAgentString(MOBILE_USER_AGENT);
                btnToggleView.setText("📱 MOBILE");
                btnToggleView.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#E91E63")));
                Toast.makeText(this, "Switched to Mobile Layout (Android Chrome Bypass UA)", Toast.LENGTH_SHORT).show();
            }
            webView.reload();
            geminiWebView.reload();
        });

        // Execute Custom JavaScript inside WebView context
        btnRunJs.setOnClickListener(v -> {
            String js = etJsCode.getText().toString().trim();
            if (!js.isEmpty()) {
                WebView active = isColabActive() ? webView : geminiWebView;
                active.evaluateJavascript(js, value -> {
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

        // Start periodic active automation checking
        automationHandler.postDelayed(automationRunnable, 2500);
    }

    private boolean isColabActive() {
        return webView.getVisibility() == View.VISIBLE;
    }

    private void switchTab(boolean isColab) {
        runOnUiThread(() -> {
            if (isColab) {
                webView.setVisibility(View.VISIBLE);
                geminiWebView.setVisibility(View.GONE);
                btnTabColab.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#2196F3")));
                btnTabGemini.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#78909C")));
                etUrl.setText(webView.getUrl());
            } else {
                webView.setVisibility(View.GONE);
                geminiWebView.setVisibility(View.VISIBLE);
                btnTabColab.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#78909C")));
                btnTabGemini.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#673AB7")));
                etUrl.setText(geminiWebView.getUrl());
            }
        });
    }

    public void addLog(final String msg) {
        runOnUiThread(() -> {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault());
            String time = sdf.format(new java.util.Date());
            String formattedMsg = "[" + time + "] " + msg + "\n";
            tvTerminalLogs.append(formattedMsg);

            // Auto scroll to bottom
            svTerminalLogs.post(() -> svTerminalLogs.fullScroll(View.FOCUS_DOWN));

            // Update terminal title header status dynamically
            if (msg.contains("Copy button found") || msg.contains("copied to clipboard") || msg.contains("Switching to Gemini")) {
                tvTerminalTitle.setText("💻 AGENT: ACTIVE AUTOMATION");
            }
        });
    }

    private void injectPollingScript() {
        String url = webView.getUrl();
        if (url == null) return;

        // Detect and log Colab environment status
        if (url.contains("colab.research.google.com")) {
            if (!colabDetectedLogged) {
                addLog("🔬 SYSTEM: Google Colab run/environment detected.");
                colabDetectedLogged = true;
            }
        } else {
            colabDetectedLogged = false;
        }

        // Active Iframe / Shadow root scanning script to detect prompt button and copy automatically
        String js = "javascript:(function() {\n" +
                "    if (window.hasCopyButtonScannerInjected) return;\n" +
                "    window.hasCopyButtonScannerInjected = true;\n" +
                "    console.log('Copy Button Scanner Injected!');\n" +
                "    \n" +
                "    let lastProcessedId = '';\n" +
                "    function findElements(root) {\n" +
                "        if (!root) return null;\n" +
                "        let copyBtn = root.querySelector('button[id^=\"copy-\"]');\n" +
                "        if (copyBtn) return { copyBtn };\n" +
                "        let iframes = root.querySelectorAll('iframe');\n" +
                "        for (let iframe of iframes) {\n" +
                "            try {\n" +
                "                if (iframe.contentDocument) {\n" +
                "                    let res = findElements(iframe.contentDocument);\n" +
                "                    if (res) return res;\n" +
                "                }\n" +
                "            } catch (e) {}\n" +
                "        }\n" +
                "        let all = root.querySelectorAll('*');\n" +
                "        for (let el of all) {\n" +
                "            if (el.shadowRoot) {\n" +
                "                let res = findElements(el.shadowRoot);\n" +
                "                if (res) return res;\n" +
                "            }\n" +
                "        }\n" +
                "        return null;\n" +
                "    }\n" +
                "    \n" +
                "    setInterval(() => {\n" +
                "        let res = findElements(document);\n" +
                "        if (res) {\n" +
                "            let uId = res.copyBtn.id.replace('copy-', '');\n" +
                "            let isCopiedText = res.copyBtn.innerText.includes('COPIED') || res.copyBtn.innerText.includes('COPIED TO CLIPBOARD');\n" +
                "            if (uId !== lastProcessedId && !isCopiedText && !res.copyBtn.disabled) {\n" +
                "                console.log('Detected copy button with ID: copy-' + uId);\n" +
                "                res.copyBtn.click();\n" +
                "                \n" +
                "                let promptText = '';\n" +
                "                let parent = res.copyBtn.parentElement;\n" +
                "                if (parent) {\n" +
                "                    promptText = parent.innerText || '';\n" +
                "                }\n" +
                "                \n" +
                "                setTimeout(() => {\n" +
                "                    navigator.clipboard.readText().then(text => {\n" +
                "                        let finalPrompt = (text && text.trim().length > 0) ? text : promptText;\n" +
                "                        lastProcessedId = uId;\n" +
                "                        AndroidApp.onCopyButtonDetected(uId, finalPrompt);\n" +
                "                    }).catch(err => {\n" +
                "                        lastProcessedId = uId;\n" +
                "                        AndroidApp.onCopyButtonDetected(uId, promptText);\n" +
                "                    });\n" +
                "                }, 500);\n" +
                "            }\n" +
                "        }\n" +
                "    }, 1500);\n" +
                "})()";
        webView.evaluateJavascript(js, null);
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

        settings.setSupportMultipleWindows(true);
        settings.setUserAgentString(DESKTOP_USER_AGENT);

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            cookieManager.setAcceptThirdPartyCookies(webView, true);
        }

        webView.addJavascriptInterface(new AgenticAutomationInterface(), "AndroidApp");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (isColabActive()) etUrl.setText(url);
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                if (isColabActive()) etUrl.setText(url);
                CookieManager.getInstance().flush();
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
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
                        return false;
                    }

                    @Override
                    public void onPageFinished(WebView v, String url) {
                        super.onPageFinished(v, url);
                        etUrl.setText(url);
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
                        webView.setVisibility(View.VISIBLE);
                        etUrl.setText(webView.getUrl());
                    }
                });

                if (webViewContainer != null) {
                    webView.setVisibility(View.GONE);
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

        webView.loadUrl("https://colab.research.google.com");
    }

    private void setupGeminiWebView() {
        WebSettings settings = geminiWebView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setJavaScriptCanOpenWindowsAutomatically(true);

        settings.setUserAgentString(DESKTOP_USER_AGENT);

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            cookieManager.setAcceptThirdPartyCookies(geminiWebView, true);
        }

        geminiWebView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (!isColabActive()) etUrl.setText(url);
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                if (!isColabActive()) etUrl.setText(url);
                CookieManager.getInstance().flush();
            }
        });

        geminiWebView.loadUrl("https://gemini.google.com");
    }

    // Upgraded Gemini Automation State Machine
    private void pollGeminiAutomation() {
        long elapsed = System.currentTimeMillis() - geminiStateTimestamp;

        if (geminiState == 1) { // Paste and send prompt
            Log.d(TAG, "pollGeminiAutomation: Attempting to locate and paste prompt into Gemini...");

            String escapedPrompt = sActivePrompt.replace("\\", "\\\\")
                                                 .replace("'", "\\'")
                                                 .replace("\n", "\\n")
                                                 .replace("\r", "");

            String jsSend = "javascript:(function() {\n" +
                    "    let editor = document.querySelector('.ql-editor') || \n" +
                    "                 document.querySelector('div[contenteditable=\"true\"]') || \n" +
                    "                 document.querySelector('textarea') ||\n" +
                    "                 document.querySelector('rich-textarea div');\n" +
                    "    if (editor) {\n" +
                    "        editor.focus();\n" +
                    "        document.execCommand('selectAll', false, null);\n" +
                    "        document.execCommand('delete', false, null);\n" +
                    "        document.execCommand('insertText', false, '" + escapedPrompt + "');\n" +
                    "        \n" +
                    "        if (editor.innerText.indexOf('" + escapedPrompt.substring(0, Math.min(10, escapedPrompt.length())) + "') === -1) {\n" +
                    "            if (editor.tagName === 'TEXTAREA' || editor.tagName === 'INPUT') {\n" +
                    "                editor.value = '" + escapedPrompt + "';\n" +
                    "            } else {\n" +
                    "                editor.innerHTML = '<p>' + '" + escapedPrompt + "'.replace(/\\\\n/g, '<br>') + '</p>';\n" +
                    "            }\n" +
                    "        }\n" +
                    "        \n" +
                    "        let evt = new Event('input', { bubbles: true });\n" +
                    "        editor.dispatchEvent(evt);\n" +
                    "        let changeEvt = new Event('change', { bubbles: true });\n" +
                    "        editor.dispatchEvent(changeEvt);\n" +
                    "        \n" +
                    "        setTimeout(() => {\n" +
                    "            let sendBtn = document.querySelector('button[aria-label*=\"Send\"]') || \n" +
                    "                          document.querySelector('button[aria-label*=\"send\"]') || \n" +
                    "                          document.querySelector('button[class*=\"send\"]') || \n" +
                    "                          document.querySelector('button:has(svg)') ||\n" +
                    "                          document.querySelector('.send-button-container button');\n" +
                    "            if (sendBtn) {\n" +
                    "                sendBtn.focus();\n" +
                    "                sendBtn.click();\n" +
                    "                console.log('Send button clicked!');\n" +
                    "            } else {\n" +
                    "                let svgs = document.querySelectorAll('svg');\n" +
                    "                for (let svg of svgs) {\n" +
                    "                    let p = svg.parentElement;\n" +
                    "                    if (p && p.tagName === 'BUTTON') {\n" +
                    "                        p.click(); break;\n" +
                    "                    }\n" +
                    "                }\n" +
                    "            }\n" +
                    "        }, 1000);\n" +
                    "        return 'success';\n" +
                    "    }\n" +
                    "    return 'not_found';\n" +
                    "})()";

            geminiWebView.evaluateJavascript(jsSend, value -> {
                Log.d(TAG, "Gemini send script evaluation: " + value);
                if (value != null && value.contains("success")) {
                    addLog("🤖 AGENT: Gemini textbox detected.");
                    addLog("🤖 AGENT: Pasting copied text into Gemini...");
                    addLog("🤖 AGENT: Clicking submit button...");
                    addLog("🤖 AGENT: Waiting for full response creation...");
                    geminiState = 2; // Transition to Wait Response
                    geminiStateTimestamp = System.currentTimeMillis();
                } else {
                    if (elapsed > 20000) {
                        addLog("⚠️ ERROR: Timed out waiting for Gemini editor container.");
                        sAutomationInProgress = false;
                        geminiState = 0;
                        switchTab(true);
                    }
                }
            });

        } else if (geminiState == 2) { // Wait for response & Extract JSON
            Log.d(TAG, "pollGeminiAutomation: Polling for completed response...");

            String jsPoll = "javascript:(function() {\n" +
                    "    let responses = document.querySelectorAll('.model-response') || document.querySelectorAll('message-content') || document.querySelectorAll('.chat-content');\n" +
                    "    if (responses.length > 0) {\n" +
                    "        let lastResponse = responses[responses.length - 1];\n" +
                    "        let isGenerating = document.querySelector('.generating') || document.querySelector('mat-progress-bar') || document.querySelector('.loading-spinner');\n" +
                    "        if (isGenerating) {\n" +
                    "            return JSON.stringify({ status: 'generating' });\n" +
                    "        }\n" +
                    "        let copyBtn = lastResponse.querySelector('button[aria-label*=\"Copy\"]') || \n" +
                    "                      lastResponse.querySelector('button[class*=\"copy\"]') ||\n" +
                    "                      document.querySelector('button[aria-label*=\"Copy\"]');\n" +
                    "        if (copyBtn) {\n" +
                    "            let text = lastResponse.innerText || lastResponse.textContent || '';\n" +
                    "            return JSON.stringify({ status: 'ready', text: text });\n" +
                    "        }\n" +
                    "    }\n" +
                    "    return JSON.stringify({ status: 'waiting' });\n" +
                    "})()";

            geminiWebView.evaluateJavascript(jsPoll, value -> {
                Log.d(TAG, "Gemini response poll result: " + value);
                if (value != null && !value.equals("null")) {
                    try {
                        String cleanJson = value;
                        if (cleanJson.startsWith("\"") && cleanJson.endsWith("\"")) {
                            cleanJson = cleanJson.substring(1, cleanJson.length() - 1)
                                                 .replace("\\\"", "\"")
                                                 .replace("\\\\", "\\");
                        }
                        org.json.JSONObject result = new org.json.JSONObject(cleanJson);
                        String status = result.optString("status");

                        if (status.equals("ready")) {
                            String text = result.optString("text");
                            if (text != null && !text.isEmpty()) {
                                addLog("🤖 AGENT: Full response generated by Gemini.");
                                addLog("🤖 AGENT: Extracting JSON part of response...");

                                String jsonOnly = extractJsonFromResponse(text);

                                // Write to device clipboard
                                ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                                ClipData clip = ClipData.newPlainText("Copied JSON reply", jsonOnly);
                                if (clipboard != null) {
                                    clipboard.setPrimaryClip(clip);
                                    addLog("🤖 AGENT: JSON copied to clipboard!");
                                    Toast.makeText(MainActivity.this, "JSON auto-copied to clipboard!", Toast.LENGTH_SHORT).show();
                                }

                                addLog("🤖 AGENT: Automation task completed. Switching back to Colab view.");
                                geminiState = 0;
                                sAutomationInProgress = false;
                                switchTab(true);
                            }
                        } else if (status.equals("generating")) {
                            Log.d(TAG, "Gemini is currently generating answer...");
                        }
                    } catch (Exception e) {
                        Log.e(TAG, "Error parsing Gemini polling result JSON", e);
                    }
                }

                if (elapsed > 60000) { // 60s timeout
                    addLog("⚠️ ERROR: Timed out waiting for Gemini complete response.");
                    geminiState = 0;
                    sAutomationInProgress = false;
                    switchTab(true);
                }
            });
        }
    }

    private String extractJsonFromResponse(String rawResponse) {
        String cleaned = rawResponse.trim();
        if (cleaned.contains("```")) {
            int firstIdx = cleaned.indexOf("```");
            int lastIdx = cleaned.lastIndexOf("```");
            if (firstIdx != -1 && lastIdx != -1 && lastIdx > firstIdx) {
                String sub = cleaned.substring(firstIdx + 3, lastIdx).trim();
                if (sub.startsWith("json")) {
                    sub = sub.substring(4).trim();
                } else if (sub.startsWith("javascript")) {
                    sub = sub.substring(10).trim();
                }
                cleaned = sub;
            }
        }

        int startBrace = cleaned.indexOf('{');
        int startBracket = cleaned.indexOf('[');
        int startIdx = -1;
        if (startBrace != -1 && startBracket != -1) {
            startIdx = Math.min(startBrace, startBracket);
        } else if (startBrace != -1) {
            startIdx = startBrace;
        } else if (startBracket != -1) {
            startIdx = startBracket;
        }

        int endBrace = cleaned.lastIndexOf('}');
        int endBracket = cleaned.lastIndexOf(']');
        int endIdx = -1;
        if (endBrace != -1 && endBracket != -1) {
            endIdx = Math.max(endBrace, endBracket);
        } else if (endBrace != -1) {
            endIdx = endBrace;
        } else if (endBracket != -1) {
            endIdx = endBracket;
        }

        if (startIdx != -1 && endIdx != -1 && endIdx > startIdx) {
            cleaned = cleaned.substring(startIdx, endIdx + 1).trim();
        }

        return cleaned;
    }

    private void performSmartPaste() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboard != null && clipboard.hasPrimaryClip()) {
            ClipData.Item item = clipboard.getPrimaryClip().getItemAt(0);
            CharSequence textChar = item.getText();
            if (textChar != null) {
                String rawText = textChar.toString();
                String escapedText = rawText.replace("\\", "\\\\")
                                             .replace("'", "\\'")
                                             .replace("\n", "\\n")
                                             .replace("\r", "");

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

                WebView active = isColabActive() ? webView : geminiWebView;
                active.evaluateJavascript(jsPaste, value -> {
                    Toast.makeText(MainActivity.this, "Pasted text successfully!", Toast.LENGTH_SHORT).show();
                    Log.d(TAG, "Smart paste evaluation result: " + value);
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
        Toast.makeText(this, "Foreground service started!", Toast.LENGTH_SHORT).show();
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
        if (webViewContainer != null && webViewContainer.getChildCount() > 1) {
            View activePopup = webViewContainer.getChildAt(1);
            if (activePopup instanceof WebView) {
                webViewContainer.removeView(activePopup);
                ((WebView) activePopup).destroy();
                Log.d(TAG, "Successfully closed authorization tab via onBackPressed");
            }
            WebView active = isColabActive() ? webView : geminiWebView;
            active.setVisibility(View.VISIBLE);
            etUrl.setText(active.getUrl());
            Toast.makeText(this, "Closed authorization tab.", Toast.LENGTH_SHORT).show();
        } else if (isColabActive() && webView.canGoBack()) {
            webView.goBack();
        } else if (!isColabActive() && geminiWebView.canGoBack()) {
            geminiWebView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    // Upgraded Agentic JavaScript Interface Class
    public class AgenticAutomationInterface {
        @JavascriptInterface
        public void onCopyButtonDetected(final String uId, final String promptText) {
            runOnUiThread(() -> {
                addLog("🤖 AGENT: Colab run detected!");
                addLog("🤖 AGENT: Copy button found!");

                // Copy directly to device's native system clipboard
                ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                ClipData clip = ClipData.newPlainText("Copied Prompt from Colab", promptText);
                if (clipboard != null) {
                    clipboard.setPrimaryClip(clip);
                    addLog("🤖 AGENT: Prompt copied to clipboard!");

                    sActivePrompt = promptText;
                    sActiveUId = uId;
                    sAutomationInProgress = true;
                    geminiState = 1; // Transition to Paste/Send state
                    geminiStateTimestamp = System.currentTimeMillis();

                    // Automatically switch to Gemini WebView tab and start processing
                    addLog("🤖 AGENT: Switching to Gemini tab to process the prompt...");
                    switchTab(false);

                    Toast.makeText(MainActivity.this, "Prompt auto-copied & transitioning to Gemini!", Toast.LENGTH_SHORT).show();
                } else {
                    addLog("⚠️ ERROR: ClipboardManager is not available.");
                }
            });
        }
    }
}
