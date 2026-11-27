// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    
    // Добавлена версия плагина, которую Gradle не мог найти
    id("com.jaredsburrows.license") version "0.9.8" apply false
    
    // Плагин для Python
    id("com.chaquo.python") version "17.0.0" apply false
}

buildscript {
    repositories {
        google()
        mavenCentral()
        // Репозиторий для Chaquopy
        maven { url = uri("https://chaquo.com/maven") }
    }
    dependencies {
        // Если класснейм лицензии тоже ругается, можно закомментировать эту строку,
        // так как мы уже подключили плагин через блок plugins выше.
        classpath(libs.gradle.license.plugin)
    }
}