package com.example.webview;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.List;

public class GeminiAccessibilityService extends AccessibilityService {
    private static final String TAG = "GeminiAccessibility";
    private String lastProcessedUId = "";
    private boolean promptSent = false;
    private long lastActionTime = 0;

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (!MainActivity.sAutomationInProgress || MainActivity.sActivePrompt.isEmpty()) {
            return;
        }

        // Rate limit action loops to prevent UI thrashing
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastActionTime < 1500) {
            return;
        }

        String currentUId = MainActivity.sActiveUId;
        if (!currentUId.equals(lastProcessedUId)) {
            // New automation task started
            lastProcessedUId = currentUId;
            promptSent = false;
        }

        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) return;

        if (!promptSent) {
            // Step 1: Find editable text input field and paste prompt
            AccessibilityNodeInfo inputField = findInputField(rootNode);
            if (inputField != null) {
                Log.d(TAG, "Found input field, setting text to prompt...");
                Bundle arguments = new Bundle();
                arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, MainActivity.sActivePrompt);
                boolean success = inputField.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments);

                if (success) {
                    // Step 2: Click the send button
                    lastActionTime = currentTime;
                    automationDelay(500);
                    AccessibilityNodeInfo sendButton = findSendButton(rootNode);
                    if (sendButton != null) {
                        Log.d(TAG, "Found send button, clicking it...");
                        sendButton.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                        promptSent = true;
                        lastActionTime = System.currentTimeMillis();
                    } else {
                        Log.e(TAG, "Send button not found!");
                    }
                }
            }
        } else {
            // Step 3: Monitor and wait for response to finish generating
            // Check for copy button of the latest response
            AccessibilityNodeInfo copyButton = findCopyButton(rootNode);
            if (copyButton != null) {
                Log.d(TAG, "Response is ready! Found copy button, extracting text/clicking...");

                // Try to extract text of the response from the sibling node of copy button if possible,
                // or click the copy button and let MainActivity retrieve it from clipboard.
                // To be doubly secure, we will click copy button AND we can try to extract text directly from text view.
                String responseText = extractTextNearCopyButton(rootNode);

                copyButton.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                lastActionTime = System.currentTimeMillis();

                // If direct extraction succeeded, we set it immediately
                if (responseText != null && !responseText.isEmpty()) {
                    Log.d(TAG, "Extracted response text directly: " + responseText);
                    returnToMainActivity(responseText);
                } else {
                    // Let MainActivity read from clipboard
                    Log.d(TAG, "Clicking copy button and returning to main to paste clipboard...");
                    automationDelay(500);
                    returnToMainActivity(null);
                }
            }
        }
        rootNode.recycle();
    }

    private AccessibilityNodeInfo findInputField(AccessibilityNodeInfo node) {
        if (node == null) return null;
        if (node.isEditable() && (node.getClassName().toString().contains("EditText") || node.isFocused())) {
            return node;
        }
        String desc = node.getContentDescription() != null ? node.getContentDescription().toString().toLowerCase() : "";
        String hint = node.getHintText() != null ? node.getHintText().toString().toLowerCase() : "";
        if (node.isEditable() || desc.contains("type a message") || desc.contains("ask gemini") || hint.contains("type") || hint.contains("ask")) {
            return node;
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = findInputField(child);
            if (res != null) return res;
        }
        return null;
    }

    private AccessibilityNodeInfo findSendButton(AccessibilityNodeInfo node) {
        if (node == null) return null;
        String desc = node.getContentDescription() != null ? node.getContentDescription().toString().toLowerCase() : "";
        String id = node.getViewIdResourceName() != null ? node.getViewIdResourceName().toLowerCase() : "";
        if (node.isClickable() && (desc.contains("send") || desc.contains("submit") || id.contains("send_button") || id.contains("sendbutton") || desc.contains("প্রেরণ"))) {
            return node;
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = findSendButton(child);
            if (res != null) return res;
        }
        return null;
    }

    private AccessibilityNodeInfo findCopyButton(AccessibilityNodeInfo node) {
        if (node == null) return null;
        String desc = node.getContentDescription() != null ? node.getContentDescription().toString().toLowerCase() : "";
        String id = node.getViewIdResourceName() != null ? node.getViewIdResourceName().toLowerCase() : "";
        if (node.isClickable() && (desc.contains("copy") || id.contains("copy_button") || id.contains("copybutton") || desc.contains("অনুলিপি"))) {
            return node;
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = findCopyButton(child);
            if (res != null) return res;
        }
        return null;
    }

    private String extractTextNearCopyButton(AccessibilityNodeInfo rootNode) {
        // Find text nodes containing response content.
        // We can search for the last large text element or a text element with specific content type.
        return findLargestTextNode(rootNode, "");
    }

    private String findLargestTextNode(AccessibilityNodeInfo node, String currentLargest) {
        if (node == null) return currentLargest;
        if (node.getText() != null) {
            String text = node.getText().toString().trim();
            if (text.length() > currentLargest.length() && !text.equals(MainActivity.sActivePrompt)) {
                // Avoid capturing menu items or labels
                if (text.contains("{") || text.contains("[") || text.length() > 50) {
                    currentLargest = text;
                }
            }
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            currentLargest = findLargestTextNode(node.getChild(i), currentLargest);
        }
        return currentLargest;
    }

    private void returnToMainActivity(String responseText) {
        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        if (responseText != null) {
            intent.putExtra("AUTOMATION_RESPONSE", responseText);
        }
        startActivity(intent);
    }

    private void automationDelay(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onInterrupt() {
        Log.d(TAG, "onInterrupt");
    }
}
