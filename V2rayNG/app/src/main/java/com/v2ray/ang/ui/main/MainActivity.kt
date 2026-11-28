package com.v2ray.ang

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.v2ray.ang.core.LauncherManager

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.setBackgroundColor(android.graphics.Color.BLACK)
        webView.loadUrl("file:///android_asset/index.html")
        
        // Связываем HTML с движком VPN
        webView.addJavascriptInterface(WebAppInterface(), "Android")
        
        setContentView(webView)
    }

    inner class WebAppInterface {
        @JavascriptInterface
        fun connect() {
            runOnUiThread {
                LauncherManager.startService(this@MainActivity)
            }
        }

        @JavascriptInterface
        fun disconnect() {
            runOnUiThread {
                LauncherManager.stopService(this@MainActivity)
            }
        }
    }
}