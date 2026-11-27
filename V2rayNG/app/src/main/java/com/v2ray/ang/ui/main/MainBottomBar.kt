package com.v2ray.ang.ui.main

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

@Composable
fun MainBottomBar(
    displayText: String,
    isRunning: Boolean,
    isDarkTheme: Boolean,
    onAction: (MainAction) -> Unit,
    modifier: Modifier = Modifier
) {
    var livePing by remember { mutableStateOf<Long?>(null) }

    // ЖИВОЙ ПИНГ
    LaunchedEffect(isRunning) {
        if (isRunning) {
            while (true) {
                try {
                    val start = System.currentTimeMillis()
                    // Пингуем 8.8.8.8 через системный API
                    val process = Runtime.getRuntime().exec("ping -c 1 8.8.8.8")
                    process.waitFor()
                    livePing = System.currentTimeMillis() - start
                } catch (e: Exception) {
                    livePing = null
                }
                delay(1000) // Обновляем каждую секунду
            }
        } else {
            livePing = null // Сбрасываем пинг при отключении
        }
    }

    Surface(
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 8.dp,
        modifier = modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            // Левая часть (Кнопка питания)
            Button(
                onClick = { onAction(MainAction.ToggleService) },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isRunning) Color(0xFF4CAF50) else MaterialTheme.colorScheme.primary
                )
            ) {
                Text(if (isRunning) "Стоп" else "Вкл")
            }

            // Центральная часть (Логи и пинг)
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                if (isRunning) {
                    Text(
                        text = if (livePing != null) "Пинг: $livePing ms" else "Пинг: ...",
                        color = if (livePing != null && livePing!! < 150) Color.Green else if (livePing != null && livePing!! < 300) Color.Yellow else Color.Red,
                        fontSize = 14.sp
                    )
                } else {
                    Text(
                        text = "Не подключено",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 14.sp
                    )
                }
            }

            // Правая часть (заглушка)
            Spacer(modifier = Modifier.width(48.dp))
        }
    }
}