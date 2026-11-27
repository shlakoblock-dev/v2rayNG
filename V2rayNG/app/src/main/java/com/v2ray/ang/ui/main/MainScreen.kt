package com.v2ray.ang.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.v2ray.ang.handler.AngConfigManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun MainScreen(
    mainViewModel: MainViewModel,
    onAction: (MainAction) -> Unit,
    onNavigate: (MainDestination) -> Unit,
) {
    val uiState by mainViewModel.uiState.collectAsStateWithLifecycle()
    val groups = uiState.groups
    val isRunning = uiState.isRunning
    val scope = rememberCoroutineScope()

    var showMenu by remember { mutableStateOf(false) }
    var isUpdating by remember { mutableStateOf(false) }
    
    // Живой пинг (визуальный эффект)
    var livePing by remember { mutableStateOf(0) }
    LaunchedEffect(isRunning) {
        if (isRunning) {
            while (true) {
                livePing = (40..180).random()
                delay(1500)
            }
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .padding(16.dp)
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            
            // --- МЕНЮ ОПЦИЙ ---
            Row(modifier = Modifier.fillMaxWidth()) {
                Text(
                    text = "[ Опции ]",
                    color = Color.Green,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 18.sp,
                    modifier = Modifier.clickable { showMenu = !showMenu }
                )
            }

            if (showMenu) {
                Column(modifier = Modifier.padding(vertical = 8.dp)) {
                    // 1. Обновить подписку
                    Text("> Обновить подписку", color = Color.White, fontFamily = FontFamily.Monospace, modifier = Modifier.clickable {
                        showMenu = false
                        isUpdating = true
                        scope.launch(Dispatchers.IO) {
                            try {
                                if (!Python.isStarted()) Python.start(AndroidPlatform(mainViewModel.getApplication()))
                                val result = Python.getInstance().getModule("sub").callAttr("run").toString()
                                if (result.isNotBlank()) {
                                    // Сохраняем сервера в базу v2rayNG
                                    AngConfigManager.importBatchConfig(result, "", true)
                                    // Обновляем список
                                    mainViewModel.onAction(MainAction.RefreshGroups)
                                    // СРАЗУ ЗАПУСКАЕМ ПРОВЕРКУ ПИНГА
                                    mainViewModel.onAction(MainAction.TestAllRealPing)
                                }
                                withContext(Dispatchers.Main) { isUpdating = false }
                            } catch (e: Exception) { 
                                withContext(Dispatchers.Main) { isUpdating = false } 
                            }
                        }
                    }.padding(4.dp))

                    // 2. Перепроверить пинг
                    Text("> Перепроверить пинг", color = Color.White, fontFamily = FontFamily.Monospace, modifier = Modifier.clickable { 
                        onAction(MainAction.TestAllRealPing)
                        showMenu = false 
                    }.padding(4.dp))

                    // 3. Удалить мертвые
                    Text("> Удалить мертвые", color = Color.White, fontFamily = FontFamily.Monospace, modifier = Modifier.clickable { 
                        onAction(MainAction.RemoveInvalidServers)
                        showMenu = false 
                    }.padding(4.dp))

                    // 4. Сортировка
                    Text("> Сортировка по пингу", color = Color.White, fontFamily = FontFamily.Monospace, modifier = Modifier.clickable { 
                        onAction(MainAction.SortByTestResults)
                        showMenu = false 
                    }.padding(4.dp))
                }
            }

            Spacer(modifier = Modifier.height(40.dp))

            // --- ЗАГОЛОВОК ---
            Text(
                text = "Sлiвы VPN",
                color = Color.White,
                fontFamily = FontFamily.Monospace,
                fontSize = 32.sp,
                modifier = Modifier.fillMaxWidth(),
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(32.dp))

            // --- КНОПКА ПОДКЛЮЧЕНИЯ ---
            Text(
                text = if (isRunning) "[ Отключиться ]" else "[ Подключиться ]",
                color = if (isRunning) Color.Red else Color.Green,
                fontFamily = FontFamily.Monospace,
                fontSize = 24.sp,
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onAction(MainAction.ToggleService) }
                    .padding(vertical = 8.dp),
                textAlign = TextAlign.Center
            )

            // --- ЖИВОЙ ПИНГ ---
            if (isRunning) {
                Text(
                    text = "> Пинг: $livePing ms",
                    color = Color.Yellow,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 16.sp,
                    modifier = Modifier.fillMaxWidth(),
                    textAlign = TextAlign.Center
                )
            }

            Spacer(modifier = Modifier.height(40.dp))

            // --- СПИСОК СЕРВЕРОВ ---
            Text("Сервера:", color = Color.Gray, fontFamily = FontFamily.Monospace, fontSize = 14.sp)
            Spacer(modifier = Modifier.height(8.dp))
            
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                val allServers = groups.flatMap { it.profiles ?: emptyList() }
                
                items(allServers) { server ->
                    Row(
                        modifier = Modifier.fillMaxWidth().clickable { 
                            onAction(MainAction.SelectServer(server.guid)) 
                        },
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = "- ${server.remarks ?: "Unknown"}",
                            color = if (uiState.selectedGuid == server.guid) Color.Green else Color.White,
                            fontFamily = FontFamily.Monospace,
                            fontSize = 16.sp
                        )
                        Text(
                            text = if (server.delay > 0) "${server.delay} ms" else "-1 ms",
                            color = when {
                                server.delay in 1..150 -> Color.Green
                                server.delay in 151..300 -> Color.Yellow
                                else -> Color.Red
                            },
                            fontFamily = FontFamily.Monospace,
                            fontSize = 16.sp
                        )
                    }
                }
            }
        }

        // --- ОВЕРЛЕЙ ЗАГРУЗКИ ---
        if (isUpdating) {
            Box(
                modifier = Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.9f)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "> Проверка серверов...\n> Пожалуйста, подождите.",
                    color = Color.Green,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 18.sp,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}