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

    // Tabs & Terminal UI Components
    private Button btnTabColab;
    private Button btnTabGemini;
    private LinearLayout llTerminalHeader;
    private TextView tvTerminalTitle;
    private TextView tvTerminalToggle;
    private ScrollView svTerminalLogs;
    private TextView tvTerminalLogs;

    private boolean isServiceRunning = false;
    private boolean isDesktopMode = true; // Default is Desktop Mode for Colab fully active execution
    private ValueCallback<Uri[]> uploadMessage;

    // Headless Socket Bridge Fields
    private String mSecure1PSID = "";
    private String mSecure1PSIDTS = "";
    private Thread mBridgeWorkerThread = null;
    private volatile boolean mRunBridgeWorker = true;
    private long mLastWarnTime = 0;

    // Standard User-Agents
    private final String DESKTOP_USER_AGENT = "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
    private final String MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36";

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

        // Initialize Tab & Terminal Buttons
        btnTabColab = findViewById(R.id.btnTabColab);
        btnTabGemini = findViewById(R.id.btnTabGemini);
        llTerminalHeader = findViewById(R.id.llTerminalHeader);
        tvTerminalTitle = findViewById(R.id.tvTerminalTitle);
        tvTerminalToggle = findViewById(R.id.tvTerminalToggle);
        svTerminalLogs = findViewById(R.id.svTerminalLogs);
        tvTerminalLogs = findViewById(R.id.tvTerminalLogs);

        // Setup toolbar buttons
        ImageButton btnBack = findViewById(R.id.btnBack);
        ImageButton btnForward = findViewById(R.id.btnForward);
        ImageButton btnGo = findViewById(R.id.btnGo);

        btnBack.setOnClickListener(v -> {
            if (webView.getVisibility() == View.VISIBLE && webView.canGoBack()) {
                webView.goBack();
            } else if (geminiWebView.getVisibility() == View.VISIBLE && geminiWebView.canGoBack()) {
                geminiWebView.goBack();
            }
        });

        btnForward.setOnClickListener(v -> {
            if (webView.getVisibility() == View.VISIBLE && webView.canGoForward()) {
                webView.goForward();
            } else if (geminiWebView.getVisibility() == View.VISIBLE && geminiWebView.canGoForward()) {
                geminiWebView.goForward();
            }
        });

        btnGo.setOnClickListener(v -> {
            String url = etUrl.getText().toString().trim();
            if (!url.startsWith("http://") && !url.startsWith("https://")) {
                url = "https://" + url;
            }
            if (webView.getVisibility() == View.VISIBLE) {
                webView.loadUrl(url);
            } else {
                geminiWebView.loadUrl(url);
            }
        });

        // Tab switches
        btnTabColab.setOnClickListener(v -> switchTab(true));
        btnTabGemini.setOnClickListener(v -> switchTab(false));

        // Terminal Toggle collapse
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

        // Setup WebViews
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

        // Paste clipboard text programmatically
        btnPasteCode.setOnClickListener(v -> performSmartPaste());

        // Toggle layout Desktop vs Mobile modes
        btnToggleView.setOnClickListener(v -> {
            isDesktopMode = !isDesktopMode;
            WebSettings settings = webView.getSettings();
            WebSettings gSettings = geminiWebView.getSettings();
            if (isDesktopMode) {
                settings.setUserAgentString(DESKTOP_USER_AGENT);
                gSettings.setUserAgentString(DESKTOP_USER_AGENT);
                btnToggleView.setText("🖥️ DESKTOP");
                btnToggleView.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#673AB7")));
                Toast.makeText(this, "Switched to Desktop Layout", Toast.LENGTH_SHORT).show();
            } else {
                settings.setUserAgentString(MOBILE_USER_AGENT);
                gSettings.setUserAgentString(MOBILE_USER_AGENT);
                btnToggleView.setText("📱 MOBILE");
                btnToggleView.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#E91E63")));
                Toast.makeText(this, "Switched to Mobile Layout", Toast.LENGTH_SHORT).show();
            }
            webView.reload();
            geminiWebView.reload();
        });

        // Custom Javascript evaluation execution
        btnRunJs.setOnClickListener(v -> {
            String js = etJsCode.getText().toString().trim();
            if (!js.isEmpty()) {
                WebView active = (webView.getVisibility() == View.VISIBLE) ? webView : geminiWebView;
                active.evaluateJavascript(js, value -> {
                    Toast.makeText(MainActivity.this, "JS Result: " + value, Toast.LENGTH_LONG).show();
                    Log.d(TAG, "Custom JavaScript executed. Result: " + value);
                });
            } else {
                Toast.makeText(this, "Please enter JavaScript code to execute.", Toast.LENGTH_SHORT).show();
            }
        });

        // Toggle background persistence Foreground Service
        btnToggleService.setOnClickListener(v -> {
            if (!isServiceRunning) {
                checkNotificationPermissionAndStartService();
            } else {
                stopBackgroundService();
            }
        });

        requestBatteryOptimizationBypass();

        // Start headless socket bridge background worker thread
        startBridgeWorker();
    }

    private void switchTab(boolean isColab) {
        runOnUiThread(() -> {
            if (isColab) {
                webView.setVisibility(View.VISIBLE);
                geminiWebView.setVisibility(View.GONE);
                etUrl.setText(webView.getUrl());
                btnTabColab.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#2196F3")));
                btnTabGemini.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#78909C")));
            } else {
                webView.setVisibility(View.GONE);
                geminiWebView.setVisibility(View.VISIBLE);
                etUrl.setText(geminiWebView.getUrl());
                btnTabColab.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#78909C")));
                btnTabGemini.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#673AB7")));
            }
        });
    }

    private void addLog(final String msg) {
        runOnUiThread(() -> {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault());
            String time = sdf.format(new java.util.Date());
            String formattedMsg = "[" + time + "] " + msg + "\n";
            tvTerminalLogs.append(formattedMsg);

            // Auto scroll to bottom
            svTerminalLogs.post(() -> svTerminalLogs.fullScroll(View.FOCUS_DOWN));

            // Update terminal status header text
            if (msg.contains("Extracted") || msg.contains("Socket Bridge") || msg.contains("Success")) {
                tvTerminalTitle.setText("💻 AGENT: ACTIVE AUTOMATION");
            }
        });
    }

    private void startBridgeWorker() {
        mRunBridgeWorker = true;
        mBridgeWorkerThread = new Thread(new Runnable() {
            @Override
            public void run() {
                while (mRunBridgeWorker) {
                    try {
                        Thread.sleep(3000);
                    } catch (InterruptedException e) {
                        break;
                    }

                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            harvestGeminiCookies();
                            if (webView != null) {
                                triggerColabBridge();
                            }
                        }
                    });
                }
            }
        });
        mBridgeWorkerThread.start();
    }

    private void harvestGeminiCookies() {
        try {
            CookieManager cookieManager = CookieManager.getInstance();
            String[] targetUrls = {
                "https://gemini.google.com",
                "https://google.com",
                "https://chat.google.com",
                "https://accounts.google.com"
            };

            String secure1PSID = "";
            String secure1PSIDTS = "";

            for (String url : targetUrls) {
                String cookieStr = cookieManager.getCookie(url);
                if (cookieStr != null) {
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
                }
            }

            if (!secure1PSID.isEmpty() && !secure1PSIDTS.isEmpty()) {
                if (!secure1PSID.equals(mSecure1PSID) || !secure1PSIDTS.equals(mSecure1PSIDTS)) {
                    mSecure1PSID = secure1PSID;
                    mSecure1PSIDTS = secure1PSIDTS;
                    Log.d(TAG, "🤖 Harvester: Extracted active Gemini cookies!");
                    addLog("Harvester: Successfully extracted active Gemini session cookies (PSID length=" + secure1PSID.length() + ")");
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error harvesting Gemini cookies", e);
        }
    }

    private void triggerColabBridge() {
        if (mSecure1PSID.isEmpty() || mSecure1PSIDTS.isEmpty()) {
            long now = System.currentTimeMillis();
            if (now - mLastWarnTime > 15000) {
                addLog("🔑 Harvester: Awaiting Gemini session cookies... Please select 'GEMINI VIEW' tab and log in.");
                mLastWarnTime = now;
            }
            return;
        }

        String escapedPSID = mSecure1PSID.replace("\\", "\\\\").replace("'", "\\'");
        String escapedPSIDTS = mSecure1PSIDTS.replace("\\", "\\\\").replace("'", "\\'");

        String js = "javascript:(function() {\n" +
                "    if (typeof google !== 'undefined' && google.colab && google.colab.kernel && google.colab.kernel.proxy) {\n" +
                "        if (window.hasActiveBridgeRunning) return;\n" +
                "        window.hasActiveBridgeRunning = true;\n" +
                "        \n" +
                "        // Set up postMessage communication bridge to log back to app terminal\n" +
                "        if (!window.hasPostMessageBridgeSetup) {\n" +
                "            window.hasPostMessageBridgeSetup = true;\n" +
                "            window.addEventListener('message', function(event) {\n" +
                "                if (event.data && event.data.type === 'BRIDGE_LOG') {\n" +
                "                    AndroidApp.onBridgeLog(event.data.msg);\n" +
                "                }\n" +
                "            });\n" +
                "        }\n" +
                "        \n" +
                "        let py = `import os, json, threading, asyncio, sys\\n" +
                "def log_to_app(msg):\\n" +
                "    try:\\n" +
                "        from google.colab import output\\n" +
                "        escaped = json.dumps(msg)\\n" +
                "        output.eval_js(f\\\"window.top.postMessage({{'type': 'BRIDGE_LOG', 'msg': {escaped}}}, '*')\\\")\\n" +
                "    except: pass\\n" +
                "\\n" +
                "def process_bridge():\\n" +
                "    bridge_dir = '/content/drive/MyDrive/gemini_bridge'\\n" +
                "    prompt_path = os.path.join(bridge_dir, 'prompt.txt')\\n" +
                "    reply_path = os.path.join(bridge_dir, 'reply.txt')\\n" +
                "    if not os.path.exists(prompt_path): return\\n" +
                "    try:\\n" +
                "        log_to_app('🤖 Python Bridge: prompt.txt detected! Reading content...')\\n" +
                "        with open(prompt_path, 'r', encoding='utf-8') as f:\\n" +
                "            prompt = f.read()\\n" +
                "        if not prompt.strip():\\n" +
                "            log_to_app('⚠️ Python Bridge: prompt.txt is empty!')\\n" +
                "            return\\n" +
                "        \\n" +
                "        log_to_app('🤖 Python Bridge: Initializing gemini-webapi...')\\n" +
                "        try:\\n" +
                "            import gemini_webapi\\n" +
                "        except ImportError:\\n" +
                "            log_to_app('📡 Python Bridge: Installing gemini-webapi package...')\\n" +
                "            import subprocess\\n" +
                "            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', 'gemini-webapi'])\\n" +
                "            import gemini_webapi\\n" +
                "            \\n" +
                "        from gemini_webapi import GeminiClient\\n" +
                "        log_to_app('🤖 Python Bridge: Authenticating with Gemini using cookies...')\\n" +
                "        \\n" +
                "        result_container = []\\n" +
                "        error_container = []\\n" +
                "        \\n" +
                "        async def run_query():\\n" +
                "            try:\\n" +
                "                client = GeminiClient(\\\"" + escapedPSID + "\\\", \\\"" + escapedPSIDTS + "\\\")\\n" +
                "                await client.init()\\n" +
                "                chat = client.start_chat()\\n" +
                "                log_to_app('🤖 Python Bridge: Sending query to Gemini...')\\n" +
                "                response = await chat.send_message(prompt)\\n" +
                "                result_container.append(response.text)\\n" +
                "            except Exception as inner_ex:\\n" +
                "                error_container.append(inner_ex)\\n" +
                "                \\n" +
                "        def thread_runner():\\n" +
                "            loop = asyncio.new_event_loop()\\n" +
                "            asyncio.set_event_loop(loop)\\n" +
                "            try:\\n" +
                "                loop.run_until_complete(run_query())\\n" +
                "            finally:\\n" +
                "                loop.close()\\n" +
                "                \\n" +
                "        t = threading.Thread(target=thread_runner)\\n" +
                "        t.start()\\n" +
                "        t.join()\\n" +
                "        \\n" +
                "        if error_container:\\n" +
                "            raise error_container[0]\\n" +
                "            \\n" +
                "        cleaned = result_container[0].strip()\\n" +
                "        if '```' in cleaned:\\n" +
                "            import re\\n" +
                "            m = re.search(r'```(?:json|javascript)?(.*?)```', cleaned, re.DOTALL)\\n" +
                "            if m: cleaned = m.group(1).strip()\\n" +
                "            \\n" +
                "        log_to_app('🤖 Python Bridge: Writing response to reply.txt...')\\n" +
                "        with open(reply_path, 'w', encoding='utf-8') as f:\\n" +
                "            f.write(cleaned)\\n" +
                "            \\n" +
                "        if os.path.exists(prompt_path): os.remove(prompt_path)\\n" +
                "        log_to_app('🤖 Python Bridge: Completed successfully! Deleted prompt.txt')\\n" +
                "    except Exception as ex:\\n" +
                "        log_to_app('❌ Python Bridge Error: ' + str(ex))\\n" +
                "        try:\\n" +
                "            with open(reply_path, 'w', encoding='utf-8') as f:\\n" +
                "                f.write('ERROR: ' + str(ex))\\n" +
                "            if os.path.exists(prompt_path): os.remove(prompt_path)\\n" +
                "        except: pass\\n" +
                "threading.Thread(target=process_bridge, daemon=True).start()`;\n" +
                "        try {\n" +
                "            google.colab.kernel.proxy.getKernel().execute(py);\n" +
                "        } catch(e) {}\n" +
                "        \n" +
                "        setTimeout(() => { window.hasActiveBridgeRunning = false; }, 2000);\n" +
                "    }\n" +
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

        // Add Javascript Interface to support direct python logging to app console!
        webView.addJavascriptInterface(new BridgeLoggerInterface(), "AndroidApp");

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
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                CookieManager.getInstance().flush();
            }
        });

        geminiWebView.loadUrl("https://gemini.google.com");
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

                WebView active = (webView.getVisibility() == View.VISIBLE) ? webView : geminiWebView;
                active.evaluateJavascript(jsPaste, value -> {
                    Toast.makeText(MainActivity.this, "Pasted successfully!", Toast.LENGTH_SHORT).show();
                });
            }
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
                Toast.makeText(this, "Notification permission required.", Toast.LENGTH_LONG).show();
            }
        }
    }

    @Override
    public void onBackPressed() {
        if (webViewContainer != null && webViewContainer.getChildCount() > 2) {
            View activePopup = webViewContainer.getChildAt(2);
            if (activePopup instanceof WebView) {
                webViewContainer.removeView(activePopup);
                ((WebView) activePopup).destroy();
                Log.d(TAG, "Closed popup tab");
            }
            if (webView.getVisibility() == View.VISIBLE) {
                etUrl.setText(webView.getUrl());
            } else {
                etUrl.setText(geminiWebView.getUrl());
            }
        } else {
            WebView active = (webView.getVisibility() == View.VISIBLE) ? webView : geminiWebView;
            if (active.canGoBack()) {
                active.goBack();
            } else {
                super.onBackPressed();
            }
        }
    }

    @Override
    protected void onDestroy() {
        mRunBridgeWorker = false;
        if (mBridgeWorkerThread != null) {
            mBridgeWorkerThread.interrupt();
        }
        super.onDestroy();
    }

    // Direct Python-to-Java bridge logger interface class
    public class BridgeLoggerInterface {
        @JavascriptInterface
        public void onBridgeLog(final String msg) {
            runOnUiThread(() -> {
                addLog(msg);
            });
        }
    }
}
