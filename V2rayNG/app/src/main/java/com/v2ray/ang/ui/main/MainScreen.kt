package com.v2ray.ang.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.v2ray.ang.dto.entities.ProfileItem
import com.v2ray.ang.handler.AngConfigManager // <-- ВАЖНО: добавлен импорт
import com.v2ray.ang.ui.compose.LocalDarkTheme
import com.v2ray.ang.ui.compose.QRCodeDialog
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.distinctUntilChanged
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
    val isLoading by mainViewModel.isLoading.collectAsStateWithLifecycle()
    val isRunning = uiState.isRunning
    val selectedGuid = uiState.selectedGuid
    val doubleColumnDisplay = uiState.doubleColumnDisplay
    val confirmRemove = uiState.confirmRemove
    val shareQRCodeBitmap = uiState.shareQRCodeBitmap

    // Состояние для Python-скрипта
    var isUpdating by remember { mutableStateOf(false) }
    var updateLog by remember { mutableStateOf("") }

    val isDarkTheme = LocalDarkTheme.current
    val drawerState = rememberDrawerState(DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val searchQuery = uiState.searchQuery
    var showDelInvalidConfirm by remember { mutableStateOf(false) }
    var showRemoveConfirm by rememberSaveable(stateSaver = ServerDeleteTarget.Saver) {
        mutableStateOf<ServerDeleteTarget?>(null)
    }

    var shareTarget by remember { mutableStateOf<Triple<String, ProfileItem, Boolean>?>(null) }
    val removeServer: (String, String) -> Unit = { guid, profileName ->
        if (confirmRemove) {
            showRemoveConfirm = ServerDeleteTarget(guid, profileName)
        } else {
            onAction(MainAction.RemoveServer(guid))
        }
    }

    val pagerState = rememberPagerState(initialPage = 0, pageCount = { groups.size.coerceAtLeast(1) })

    LaunchedEffect(groups, uiState.selectedGroupId) {
        if (groups.isEmpty()) return@LaunchedEffect
        val selectedIndex = groups.indexOfFirst { it.id == uiState.selectedGroupId }.takeIf { it >= 0 } ?: 0
        if (!pagerState.isScrollInProgress && pagerState.settledPage != selectedIndex) {
            pagerState.scrollToPage(selectedIndex)
        }
    }

    val latestGroups by rememberUpdatedState(groups)
    var bottomBarHeightPx by remember { mutableIntStateOf(0) }

    LaunchedEffect(pagerState) {
        snapshotFlow { pagerState.settledPage }.distinctUntilChanged().collect { page ->
            val currentGroups = latestGroups
            if (page in currentGroups.indices) {
                onAction(MainAction.SelectGroup(currentGroups[page].id))
            }
        }
    }

    MainDialogs(
        showDelAllConfirm = false, onDismissDelAll = { }, onConfirmDelAll = { },
        showDelDuplicateConfirm = false, onDismissDelDuplicate = { }, onConfirmDelDuplicate = { },
        showDelInvalidConfirm = showDelInvalidConfirm,
        onDismissDelInvalid = { showDelInvalidConfirm = false },
        onConfirmDelInvalid = { showDelInvalidConfirm = false; onAction(MainAction.RemoveInvalidServers) },
        showRemoveConfirm = showRemoveConfirm,
        onDismissRemove = { showRemoveConfirm = null },
        onConfirmRemove = { guid -> showRemoveConfirm = null; onAction(MainAction.RemoveServer(guid)) }
    )

    if (shareTarget != null) {
        val (guid, profile, more) = shareTarget!!
        ShareMethodDialog(guid, profile, more, { shareTarget = null }, onAction, removeServer)
    }
    if (shareQRCodeBitmap != null) {
        QRCodeDialog(bitmap = shareQRCodeBitmap, onDismiss = { onAction(MainAction.DismissQRCodeDialog) })
    }

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            MainDrawerContent(drawerState, { route ->
                scope.launch { drawerState.close() }
                onNavigate(route)
            })
        }
    ) {
        Scaffold(
            contentWindowInsets = ScaffoldDefaults.contentWindowInsets,
            topBar = {
                MainTopBar(
                    isLoading = isLoading, showSearch = false, searchQuery = "",
                    onSearchQueryChange = { }, onSearchClose = { }, onSearchToggle = { },
                    onMenuClick = { scope.launch { drawerState.open() } },
                    onAction = onAction,
                    onMoreMenuAction = { action ->
                        when (action) {
                            MainMoreMenuAction.RestartService -> onAction(MainAction.RestartService)
                            MainMoreMenuAction.DeleteInvalid -> showDelInvalidConfirm = true
                            MainMoreMenuAction.TestAll -> onAction(MainAction.TestAllServers)
                            MainMoreMenuAction.TestAllRealPing -> onAction(MainAction.TestRealAllServers)
                            MainMoreMenuAction.SortByTestResults -> onAction(MainAction.SortByTestResults)
                            
                            // --- ЗАПУСК PYTHON И СОХРАНЕНИЕ ---
                            MainMoreMenuAction.UpdateSubscriptions -> {
                                isUpdating = true
                                updateLog = "Инициализация Python..."
                                scope.launch(Dispatchers.IO) {
                                    try {
                                        if (!Python.isStarted()) {
                                            Python.start(AndroidPlatform(mainViewModel.getApplication()))
                                        }
                                        val py = Python.getInstance()
                                        val pyModule = py.getModule("sub")
                                        
                                        withContext(Dispatchers.Main) { updateLog = "Запуск проверки серверов..." }
                                        
                                        // Получаем текст с серверами
                                        val result = pyModule.callAttr("run").toString()
                                        
                                        withContext(Dispatchers.Main) { updateLog = "Сохранение в базу..." }
                                        
                                        // СОХРАНЯЕМ В БАЗУ v2rayNG
                                        if (result.isNotBlank()) {
                                            AngConfigManager.importBatchConfig(
                                                mainViewModel.getApplication(), 
                                                result, 
                                                "", 
                                                true
                                            )
                                        }
                                        
                                        // Обновляем список на экране
                                        mainViewModel.onAction(MainAction.RefreshGroups)
                                        
                                        withContext(Dispatchers.Main) {
                                            updateLog = "Успешно! Серверы добавлены."
                                            isUpdating = false
                                        }
                                    } catch (e: Exception) {
                                        withContext(Dispatchers.Main) {
                                            updateLog = "Ошибка: ${e.message}"
                                            isUpdating = false
                                        }
                                    }
                                }
                            }
                            else -> {}
                        }
                    }
                )
            },
            floatingActionButton = {},
        ) { innerPadding ->
            val layoutDirection = LocalLayoutDirection.current
            val bottomBarHeight = with(LocalDensity.current) { bottomBarHeightPx.toDp() }

            Box(Modifier.fillMaxSize()) {
                if (groups.isNotEmpty()) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(
                                start = innerPadding.calculateStartPadding(layoutDirection),
                                top = innerPadding.calculateTopPadding(),
                                end = innerPadding.calculateEndPadding(layoutDirection)
                            )
                    ) {
                        HorizontalPager(
                            state = pagerState,
                            modifier = Modifier.fillMaxSize(),
                            userScrollEnabled = true,
                            beyondViewportPageCount = 1,
                            key = { page -> groups.getOrNull(page)?.id ?: "group-page-$page" }
                        ) { page ->
                            val group = groups.getOrNull(page) ?: return@HorizontalPager
                            GroupPagerPage(
                                groupId = group.id, mainViewModel = mainViewModel, selectedGuid = selectedGuid,
                                locateTarget = uiState.locateTarget, doubleColumnDisplay = doubleColumnDisplay,
                                searchQuery = searchQuery,
                                onSelectServer = { guid -> onAction(MainAction.SelectServer(guid)) },
                                onEditServer = { guid, profile -> onAction(MainAction.EditServer(guid, profile)) },
                                onShareServer = { guid, profile -> shareTarget = Triple(guid, profile, false) },
                                onMoreServer = { guid, profile -> shareTarget = Triple(guid, profile, true) },
                                onRemoveServer = removeServer, usageInfo = group.usageInfo, groupTitle = group.remarks,
                                onOpenLink = { url -> onAction(MainAction.OpenSubscriptionLink(url)) },
                                contentPadding = PaddingValues(0.dp, 0.dp, 0.dp, bottomBarHeight + 8.dp)
                            )
                        }
                    }
                }
                
                MainBottomBar(
                    displayText = "",
                    isRunning = isRunning,
                    isDarkTheme = isDarkTheme,
                    onAction = onAction,
                    modifier = Modifier.align(Alignment.BottomCenter).onSizeChanged { bottomBarHeightPx = it.height }
                )

                // ОВЕРЛЕЙ ЗАГРУЗКИ
                if (isUpdating) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color.Black.copy(alpha = 0.85f))
                            .padding(32.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator(color = Color(0xFF4CAF50), strokeWidth = 6.dp)
                            Spacer(modifier = Modifier.height(24.dp))
                            Text(
                                text = updateLog,
                                color = Color.White,
                                fontSize = 16.sp,
                                textAlign = TextAlign.Center
                            )
                        }
                    }
                }
            }
        }
    }
}