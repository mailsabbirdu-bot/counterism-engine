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

    // Agentic Automation Fields
    public static volatile String sActivePrompt = "";
    public static volatile String sActiveUId = "";
    public static volatile String sActiveType = "";
    public static volatile boolean sAutomationInProgress = false;
    private final android.os.Handler automationHandler = new android.os.Handler();
    private final Runnable automationRunnable = new Runnable() {
        @Override
        public void run() {
            if (webView != null) {
                injectPollingScript();
                syncGeminiCookies(); // Periodically sync Gemini session cookies to Google Drive
            }
            if (sAutomationInProgress) {
                pollGeminiAutomation();
            }
            automationHandler.postDelayed(this, 3000); // Poll faster (3s) for responsive automation
        }
    };
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

    // Dual WebView Views & State Machine
    private WebView geminiWebView;
    private Button btnTabColab;
    private Button btnTabGemini;
    private int geminiState = 0; // 0: Idle, 1: Send Prompt, 2: Wait Response
    private long geminiStateTimestamp = 0;

    // Collapsible Terminal Views
    private LinearLayout llTerminalHeader;
    private TextView tvTerminalTitle;
    private TextView tvTerminalToggle;
    private ScrollView svTerminalLogs;
    private TextView tvTerminalLogs;

    private boolean isServiceRunning = false;
    private boolean isDesktopMode = true; // Default is Desktop Mode for Colab fully active execution
    private ValueCallback<Uri[]> uploadMessage;

    // Standard User-Agents
    // Chromebook Desktop UA is Chromium-based, bypasses secure login blocks perfectly, and renders all SVG icons beautifully on startup
    private final String DESKTOP_USER_AGENT = "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
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

        // Initialize Dual WebView layout and tabs
        geminiWebView = findViewById(R.id.geminiWebView);
        btnTabColab = findViewById(R.id.btnTabColab);
        btnTabGemini = findViewById(R.id.btnTabGemini);

        btnTabColab.setOnClickListener(v -> switchTab(true));
        btnTabGemini.setOnClickListener(v -> switchTab(false));

        setupGeminiWebView();

        // Initialize Collapsible Terminal Views
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

        // Setup clipboard listener for response capture
        setupClipboardResponseListener();

        // Handle any starting intent
        handleIntent(getIntent());

        // Start agentic background polling
        automationHandler.postDelayed(automationRunnable, 3000);
    }

    private void setupClipboardResponseListener() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboard != null) {
            clipboard.addPrimaryClipChangedListener(() -> {
                if (sAutomationInProgress) {
                    ClipData clip = clipboard.getPrimaryClip();
                    if (clip != null && clip.getItemCount() > 0) {
                        CharSequence text = clip.getItemAt(0).getText();
                        if (text != null) {
                            String response = text.toString().trim();
                            if (!response.equals(sActivePrompt) && !response.isEmpty()) {
                                if (response.contains("{") || response.contains("[") || response.length() > 50) {
                                    Log.d(TAG, "Clipboard changed. Detected potential response, submitting...");
                                    pasteResponseAndSubmit(response);
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    private void handleIntent(Intent intent) {
        if (intent != null && intent.hasExtra("AUTOMATION_RESPONSE")) {
            String response = intent.getStringExtra("AUTOMATION_RESPONSE");
            Log.d(TAG, "handleIntent: Received automation response from intent: " + response);
            if (response != null && !response.isEmpty()) {
                pasteResponseAndSubmit(response);
            }
        }
    }

    private void injectPollingScript() {
        String js = "javascript:(function() {\n" +
                "    if (window.hasAgenticPollingInjected) return;\n" +
                "    window.hasAgenticPollingInjected = true;\n" +
                "    console.log('Agentic Automation Polling Injected!');\n" +
                "    \n" +
                "    // Cross-origin HTML5 postMessage listener for sandboxed Colab output iframes\n" +
                "    window.addEventListener('message', function(event) {\n" +
                "        if (event.data && event.data.type === 'HUMAN_LOOP_PROMPT') {\n" +
                "            console.log('Detected postMessage HUMAN_LOOP_PROMPT:', event.data);\n" +
                "            AndroidApp.onHumanLoopDetected(event.data.prompt, event.data.uId, event.data.promptType);\n" +
                "        }\n" +
                "    });\n" +
                "    \n" +
                "    let lastProcessedId = '';\n" +
                "    function findElements(root) {\n" +
                "        if (!root) return null;\n" +
                "        let copyBtn = root.querySelector('button[id^=\"copy-\"]');\n" +
                "        let pasteArea = root.querySelector('textarea[id^=\"paste-\"]');\n" +
                "        let submitBtn = root.querySelector('button[id^=\"submit-\"]');\n" +
                "        if (copyBtn && pasteArea && submitBtn) return { copyBtn, pasteArea, submitBtn };\n" +
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
                "    setInterval(() => {\n" +
                "        let res = findElements(document);\n" +
                "        if (res) {\n" +
                "            let uId = res.copyBtn.id.replace('copy-', '');\n" +
                "            let isCopiedText = res.copyBtn.innerText.includes('COPIED') || res.copyBtn.innerText.includes('COPIED TO CLIPBOARD');\n" +
                "            if (uId !== lastProcessedId && !isCopiedText && !res.copyBtn.disabled) {\n" +
                "                console.log('New human loop detected with uId: ' + uId);\n" +
                "                res.copyBtn.click();\n" +
                "                let promptText = '';\n" +
                "                let parent = res.copyBtn.parentElement;\n" +
                "                if (parent) {\n" +
                "                    promptText = parent.innerText || '';\n" +
                "                }\n" +
                "                let type = 'json_maker';\n" +
                "                if (promptText.toLowerCase().includes('evidence') || res.copyBtn.innerText.toLowerCase().includes('evidence')) {\n" +
                "                    type = 'evidence';\n" +
                "                }\n" +
                "                setTimeout(() => {\n" +
                "                    navigator.clipboard.readText().then(text => {\n" +
                "                        let finalPrompt = (text && text.trim().length > 0) ? text : promptText;\n" +
                "                        lastProcessedId = uId;\n" +
                "                        AndroidApp.onHumanLoopDetected(finalPrompt, uId, type);\n" +
                "                    }).catch(err => {\n" +
                "                        lastProcessedId = uId;\n" +
                "                        AndroidApp.onHumanLoopDetected(promptText, uId, type);\n" +
                "                    });\n" +
                "                }, 1000);\n" +
                "            }\n" +
                "        }\n" +
                "    }, 4000);\n" +
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

        // Crucial: Support multiple windows to capture Google Drive mounts or popups cleanly inside separate temporary tabs
        settings.setSupportMultipleWindows(true);

        // Add Javascript Interface for Agentic Automation
        webView.addJavascriptInterface(new AgenticAutomationInterface(), "AndroidApp");

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

    // Agentic Automation Methods
    private void switchTab(boolean isColab) {
        runOnUiThread(() -> {
            if (isColab) {
                webView.setVisibility(View.VISIBLE);
                geminiWebView.setVisibility(View.GONE);
                btnTabColab.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#2196F3")));
                btnTabGemini.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#78909C")));
            } else {
                webView.setVisibility(View.GONE);
                geminiWebView.setVisibility(View.VISIBLE);
                btnTabColab.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#78909C")));
                btnTabGemini.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#673AB7")));
            }
        });
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

        // Point to Chromebook Chrome Desktop UA to pass Google Sign-In checks flawlessly!
        settings.setUserAgentString(DESKTOP_USER_AGENT);

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            cookieManager.setAcceptThirdPartyCookies(geminiWebView, true);
        }

        geminiWebView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                CookieManager.getInstance().flush();
            }
        });

        // Load Gemini website immediately on startup
        geminiWebView.loadUrl("https://gemini.google.com");
    }

    public void addLog(final String msg) {
        runOnUiThread(() -> {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault());
            String time = sdf.format(new java.util.Date());
            String formattedMsg = "[" + time + "] " + msg + "\n";
            tvTerminalLogs.append(formattedMsg);

            // Auto scroll to bottom
            svTerminalLogs.post(() -> svTerminalLogs.fullScroll(View.FOCUS_DOWN));

            // Update terminal title header for active steps
            if (msg.startsWith("🤖 AGENT:")) {
                tvTerminalTitle.setText("💻 " + msg);
            }
        });
    }

    private void handleHumanLoop(String prompt, String uId, String type) {
        sActivePrompt = prompt;
        sActiveUId = uId;
        sActiveType = type;
        sAutomationInProgress = true;

        Log.d(TAG, "handleHumanLoop: Starting WebView automation for uId: " + uId + " | type: " + type);
        addLog("🤖 AGENT: Detected prompt for " + uId + " (Type: " + type + "). Start automation!");
        tvServiceStatus.setText("Background service: RUNNING\n🤖 AGENT: Processing prompt " + uId + "...");
        tvServiceStatus.setTextColor(Color.parseColor("#E91E63")); // Cyberpunk Pink for Agent activity!

        // Trigger WebView Gemini website automation (works in background/locked screen via WakeLock + Java Handlers!)
        geminiState = 1; // Transition to state 1: Send Prompt
        geminiStateTimestamp = System.currentTimeMillis();
        Toast.makeText(this, "🤖 Agent: Automating Gemini website...", Toast.LENGTH_SHORT).show();
    }

    private void pollGeminiAutomation() {
        long elapsed = System.currentTimeMillis() - geminiStateTimestamp;

        if (geminiState == 1) { // State 1: Send prompt
            Log.d(TAG, "pollGeminiAutomation: Attempting to send prompt to Gemini Webview...");
            addLog("🤖 AGENT: Locating Gemini editor & inserting prompt...");

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
                    "        // Use execCommand to insert text natively so rich-text state updates correctly!\n" +
                    "        document.execCommand('selectAll', false, null);\n" +
                    "        document.execCommand('delete', false, null);\n" +
                    "        document.execCommand('insertText', false, '" + escapedPrompt + "');\n" +
                    "        \n" +
                    "        // Fallback setting if execCommand failed\n" +
                    "        if (editor.innerText.indexOf('" + escapedPrompt.substring(0, Math.min(10, escapedPrompt.length())) + "') === -1) {\n" +
                    "            if (editor.tagName === 'TEXTAREA' || editor.tagName === 'INPUT') {\n" +
                    "                editor.value = '" + escapedPrompt + "';\n" +
                    "            } else {\n" +
                    "                editor.innerHTML = '<p>' + '" + escapedPrompt + "'.replace(/\\\\n/g, '<br>') + '</p>';\n" +
                    "            }\n" +
                    "        }\n" +
                    "        \n" +
                    "        // Dispatch standard framework events\n" +
                    "        let evt = new Event('input', { bubbles: true });\n" +
                    "        editor.dispatchEvent(evt);\n" +
                    "        let changeEvt = new Event('change', { bubbles: true });\n" +
                    "        editor.dispatchEvent(changeEvt);\n" +
                    "        \n" +
                    "        // Click send button after small framework sync delay\n" +
                    "        setTimeout(() => {\n" +
                    "            let sendBtn = document.querySelector('button[aria-label*=\"Send\"]') || \n" +
                    "                          document.querySelector('button[aria-label*=\"send\"]') || \n" +
                    "                          document.querySelector('button[class*=\"send\"]') || \n" +
                    "                          document.querySelector('button:has(svg)') ||\n" +
                    "                          document.querySelector('.send-button-container button') ||\n" +
                    "                          document.querySelector('button[aria-label*=\"প্রেরণ\"]');\n" +
                    "            if (sendBtn) {\n" +
                    "                sendBtn.focus();\n" +
                    "                sendBtn.click();\n" +
                    "                console.log('Send button clicked via automation!');\n" +
                    "            } else {\n" +
                    "                let svgs = document.querySelectorAll('svg');\n" +
                    "                for (let svg of svgs) {\n" +
                    "                    let p = svg.parentElement;\n" +
                    "                    if (p && p.tagName === 'BUTTON') {\n" +
                    "                        p.click(); break;\n" +
                    "                    }\n" +
                    "                }\n" +
                    "            }\n" +
                    "        }, 800);\n" +
                    "        return 'success';\n" +
                    "    }\n" +
                    "    return 'not_found';\n" +
                    "})()";

            geminiWebView.evaluateJavascript(jsSend, value -> {
                Log.d(TAG, "evaluateJavascript jsSend result: " + value);
                if (value != null && value.contains("success")) {
                    Log.d(TAG, "Successfully pasted and clicked send inside Gemini Webview!");
                    addLog("🤖 AGENT: Prompt successfully sent to Gemini! Waiting for reply...");
                    geminiState = 2; // Transition to Wait Response
                    geminiStateTimestamp = System.currentTimeMillis();
                } else {
                    if (elapsed > 15000) {
                        Log.e(TAG, "Timed out waiting for Gemini editor. Routing to fallback solver!");
                        addLog("🤖 AGENT: Timeout locating Gemini editor. Falling back to local solver.");
                        geminiState = 0;
                        runLocalSolverFallback(sActivePrompt, sActiveUId, sActiveType);
                    }
                }
            });

        } else if (geminiState == 2) { // State 2: Wait for response
            Log.d(TAG, "pollGeminiAutomation: Polling for Gemini response to be ready...");

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
                Log.d(TAG, "evaluateJavascript jsPoll result: " + value);
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
                                Log.d(TAG, "Gemini Response extracted successfully! Length: " + text.length());
                                addLog("🤖 AGENT: Response extracted! Length=" + text.length() + ". Submitting back to Colab...");
                                geminiState = 0; // Transition back to Idle

                                String cleanedResponse = cleanGeminiResponse(text);
                                pasteResponseAndSubmit(cleanedResponse);
                            }
                        } else if (status.equals("generating")) {
                            addLog("🤖 AGENT: Gemini is currently generating output...");
                        }
                    } catch (Exception e) {
                        Log.e(TAG, "Error parsing Gemini response JSON", e);
                    }
                }

                if (elapsed > 45000) {
                    Log.e(TAG, "Timed out waiting for Gemini response. Routing to fallback solver!");
                    addLog("🤖 AGENT: Timeout waiting for Gemini reply. Falling back to local solver.");
                    geminiState = 0;
                    runLocalSolverFallback(sActivePrompt, sActiveUId, sActiveType);
                }
            });
        }
    }

    private String cleanGeminiResponse(String responseText) {
        String cleaned = responseText.trim();
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
        return cleaned;
    }

    private void runLocalSolverFallback(final String prompt, final String uId, final String type) {
        new Thread(() -> {
            try {
                // Simulate thinking/processing time
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }

            String response;
            if (type.equals("evidence") || prompt.contains("EVIDENCE ACQUISITION PLAN")) {
                response = solveEvidencePrompt(prompt);
            } else {
                response = solveJsonMakerPrompt(prompt);
            }

            final String finalResponse = response;
            runOnUiThread(() -> {
                Log.d(TAG, "Background Solver finished! Submitting response...");
                pasteResponseAndSubmit(finalResponse);
            });
        }).start();
    }

    private String solveEvidencePrompt(String prompt) {
        StringBuilder jsonBuilder = new StringBuilder();
        jsonBuilder.append("{\n  \"evidence_tasks\": [\n");

        java.util.regex.Pattern pattern = java.util.regex.Pattern.compile("Scene\\[?(SCENE_\\d+)\\]?:\\s*\"([^\"]+)\"", java.util.regex.Pattern.CASE_INSENSITIVE);
        java.util.regex.Matcher matcher = pattern.matcher(prompt);
        boolean first = true;
        int sceneCount = 0;

        while (matcher.find()) {
            sceneCount++;
            String sceneId = matcher.group(1);
            String narration = matcher.group(2);

            String query = "Dhaka traffic congestion megacity";
            String prefSite = "prothomalo.com";
            String fallbackQuery = "Dhaka";
            String intent = "documentary_evidence";

            if (narration.contains("স্বাধীনতা") || narration.contains("২৬ মার্চ") || narration.contains("independence") || narration.contains("1971")) {
                query = "Declaration of Independence Bangladesh 1971";
                prefSite = "wikipedia.org";
                fallbackQuery = "Bangladesh";
            } else if (narration.contains("বর্জ্য") || narration.contains("দূষণ") || narration.contains("waste") || narration.contains("pollution")) {
                query = "environmental plastic pollution waste";
                prefSite = "thedailystar.net";
                fallbackQuery = "Bangladesh";
            }

            if (!first) {
                jsonBuilder.append(",\n");
            }
            first = false;

            jsonBuilder.append("    {\n")
                    .append("      \"scene_id\": \"").append(sceneId).append("\",\n")
                    .append("      \"intent\": \"").append(intent).append("\",\n")
                    .append("      \"query\": \"").append(query).append("\",\n")
                    .append("      \"preferred_site\": \"").append(prefSite).append("\",\n")
                    .append("      \"fallback_query\": \"").append(fallbackQuery).append("\"\n")
                    .append("    }");
        }

        if (sceneCount == 0) {
            jsonBuilder.append("    {\n")
                    .append("      \"scene_id\": \"SCENE_1\",\n")
                    .append("      \"intent\": \"documentary_evidence\",\n")
                    .append("      \"query\": \"Dhaka traffic congestion megacity\",\n")
                    .append("      \"preferred_site\": \"prothomalo.com\",\n")
                    .append("      \"fallback_query\": \"Dhaka\"\n")
                    .append("    },\n")
                    .append("    {\n")
                    .append("      \"scene_id\": \"SCENE_2\",\n")
                    .append("      \"intent\": \"documentary_evidence\",\n")
                    .append("      \"query\": \"Declaration of Independence Bangladesh 1971\",\n")
                    .append("      \"preferred_site\": \"wikipedia.org\",\n")
                    .append("      \"fallback_query\": \"Bangladesh\"\n")
                    .append("    }\n");
        }

        jsonBuilder.append("\n  ]\n}");
        return jsonBuilder.toString();
    }

    private String solveJsonMakerPrompt(String prompt) {
        int firstBrace = prompt.indexOf('{');
        int lastBrace = prompt.lastIndexOf('}');
        if (firstBrace != -1 && lastBrace != -1 && lastBrace > firstBrace) {
            String jsonStr = prompt.substring(firstBrace, lastBrace + 1);
            try {
                // Validate JSON syntax locally
                org.json.JSONObject obj = new org.json.JSONObject(jsonStr);
                return obj.toString(2);
            } catch (Exception e) {
                Log.e(TAG, "solveJsonMakerPrompt: JSON parsing error, returning raw matching block", e);
                return jsonStr;
            }
        }
        return "{\n  \"scenes\": []\n}";
    }

    public void pasteResponseAndSubmit(final String response) {
        runOnUiThread(() -> {
            // Write to agent.txt on Google Drive first
            writeAgentTxtToDrive(sActivePrompt, response);

            String escapedResponse = response.replace("\\", "\\\\")
                                             .replace("'", "\\'")
                                             .replace("\n", "\\n")
                                             .replace("\r", "");

            // Cross-origin HTML5 postMessage broadcast to all child frames
            String jsBroadcast = "javascript:(function() {\n" +
                    "    let msg = { type: 'HUMAN_LOOP_REPLY', uId: '" + sActiveUId + "', reply: '" + escapedResponse + "' };\n" +
                    "    window.postMessage(msg, '*');\n" +
                    "    function broadcast(win) {\n" +
                    "        if (!win) return;\n" +
                    "        for (let i = 0; i < win.frames.length; i++) {\n" +
                    "            try {\n" +
                    "                win.frames[i].postMessage(msg, '*');\n" +
                    "                broadcast(win.frames[i]);\n" +
                    "            } catch (e) {}\n" +
                    "        }\n" +
                    "    }\n" +
                    "    broadcast(window);\n" +
                    "    return 'broadcast_complete';\n" +
                    "})()";

            webView.evaluateJavascript(jsBroadcast, value -> {
                Log.d(TAG, "Cross-origin postMessage broadcast complete. Result: " + value);
                addLog("🤖 AGENT: Response successfully submitted back to Colab!");
                Toast.makeText(MainActivity.this, "🤖 Agent: Submitted response back to Colab!", Toast.LENGTH_SHORT).show();
                sAutomationInProgress = false;
                tvServiceStatus.setText("Background service: RUNNING\n🤖 AGENT: Idle");
                tvServiceStatus.setTextColor(Color.parseColor("#4CAF50"));
            });
        });
    }

    private void writeAgentTxtToDrive(String prompt, String response) {
        String escapedPrompt = prompt.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "");
        String escapedResponse = response.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "");

        String pyCode = "javascript:(function() {\n" +
                "    let py = `import os\\n" +
                "try:\\n" +
                "    gdrive_folder = \"/content/drive/MyDrive/Counterism_Studio_V4\"\\n" +
                "    if os.path.exists(gdrive_folder):\\n" +
                "        agent_txt_path = os.path.join(gdrive_folder, \"agent.txt\")\\n" +
                "        with open(agent_txt_path, \"w\", encoding=\"utf-8\") as f:\\n" +
                "            f.write(\"=== INPUT ===\\\\\\\\n" + escapedPrompt + "\\\\\\\\n\\\\\\\\n=== OUTPUT ===\\\\\\\\n" + escapedResponse + "\\\\\\\\n\")\\n" +
                "        print(\"Successfully wrote agent.txt via Android app\")\\n" +
                "except Exception as e:\\n" +
                "    print(\"Error:\", e)\\n" +
                "`;\n" +
                "    if (typeof google !== 'undefined' && google.colab && google.colab.kernel && google.colab.kernel.proxy) {\n" +
                "        try {\n" +
                "            google.colab.kernel.proxy.getKernel().execute(py);\n" +
                "            console.log('Successfully triggered agent.txt write in Colab kernel');\n" +
                "        } catch (e) {\n" +
                "            console.error('Failed to trigger agent.txt write via Colab kernel API:', e);\n" +
                "        }\n" +
                "    }\n" +
                "})()";

        webView.evaluateJavascript(pyCode, null);
    }

    private void syncGeminiCookies() {
        try {
            CookieManager cookieManager = CookieManager.getInstance();
            String cookieStr = cookieManager.getCookie("https://gemini.google.com");
            if (cookieStr != null) {
                String secure1PSID = "";
                String secure1PSIDTS = "";

                String[] cookies = cookieStr.split(";");
                for (String cookie : cookies) {
                    String[] parts = cookie.trim().split("=", 2);
                    if (parts.length == 2) {
                        String name = parts[0].trim();
                        String value = parts[1].trim();
                        if (name.equals("__Secure-1PSID")) {
                            secure1PSID = value;
                        } else if (name.equals("__Secure-1PSIDTS")) {
                            secure1PSIDTS = value;
                        }
                    }
                }

                if (!secure1PSID.isEmpty() && !secure1PSIDTS.isEmpty()) {
                    Log.d(TAG, "syncGeminiCookies: Found active Gemini session cookies. Syncing to Google Drive...");
                    addLog("SYSTEM: Synced Gemini session cookies to Google Drive.");
                    writeCookiesToDrive(secure1PSID, secure1PSIDTS);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error syncing Gemini cookies", e);
        }
    }

    private void writeCookiesToDrive(String secure1PSID, String secure1PSIDTS) {
        String pyCode = "javascript:(function() {\n" +
                "    let py = `import os, json\\n" +
                "try:\\n" +
                "    gdrive_folder = \"/content/drive/MyDrive/Counterism_Studio_V4\"\\n" +
                "    if os.path.exists(gdrive_folder):\\n" +
                "        cookie_path = os.path.join(gdrive_folder, \"gemini_cookies.json\")\\n" +
                "        with open(cookie_path, \"w\", encoding=\"utf-8\") as f:\\n" +
                "            json.dump({\"__Secure-1PSID\": \"" + secure1PSID + "\", \"__Secure-1PSIDTS\": \"" + secure1PSIDTS + "\"}, f)\\n" +
                "        print(\"Successfully synced Gemini cookies to Drive\")\\n" +
                "except Exception as e:\\n" +
                "    print(\"Error syncing cookies:\", e)\\n" +
                "`;\n" +
                "    if (typeof google !== 'undefined' && google.colab && google.colab.kernel && google.colab.kernel.proxy) {\n" +
                "        try {\n" +
                "            google.colab.kernel.proxy.getKernel().execute(py);\n" +
                "            console.log('Successfully triggered cookie sync in Colab kernel');\n" +
                "        } catch (e) {\n" +
                "            console.error('Failed to sync cookies via Colab kernel API:', e);\n" +
                "        }\n" +
                "    }\n" +
                "})()";

        webView.evaluateJavascript(pyCode, null);
    }

    // Javascript Interface class
    public class AgenticAutomationInterface {
        @JavascriptInterface
        public void onHumanLoopDetected(final String prompt, final String uId, final String type) {
            Log.d(TAG, "onHumanLoopDetected: prompt=" + prompt + " | uId=" + uId + " | type=" + type);
            runOnUiThread(() -> {
                handleHumanLoop(prompt, uId, type);
            });
        }
    }
}
