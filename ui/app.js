/**
 * LUX - Frontend Uygulamasi
 *
 * Sohbet etkilesimi, dokuman yonetimi, sohbet gecmisi,
 * debug paneli ve API iletisimini yonetir.
 */

const API_BASE = '/api';

// -- Durum --
let currentConversationId = null;
let showSources = true;
let showDebug = false;
let isLoading = false;
let autoScroll = true;

// -- DOM Elemanlari --
const chatArea = document.getElementById('chat-area');
const messagesContainer = document.getElementById('messages-container');
const welcomeScreen = document.getElementById('welcome-screen');
const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const btnNewChat = document.getElementById('btn-new-chat');
const btnMenu = document.getElementById('btn-menu');
const sidebar = document.getElementById('sidebar');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const toggleDebug = document.getElementById('toggle-debug');
const toggleSourcesEl = document.getElementById('toggle-sources');
const btnDocuments = document.getElementById('btn-documents');
const docsPanel = document.getElementById('documents-panel');
const btnCloseDocs = document.getElementById('btn-close-docs');
const btnIngest = document.getElementById('btn-ingest');
const conversationList = document.getElementById('conversation-list');
const convEmpty = document.getElementById('conv-empty');
const btnSettings = document.getElementById('btn-settings');
const settingsPanel = document.getElementById('settings-panel');
const btnCloseSettings = document.getElementById('btn-close-settings');
const themeBtns = document.querySelectorAll('.theme-btn');
const toggleAutoscroll = document.getElementById('setting-autoscroll');

// -- Baslatma --
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setupEventListeners();
    autoResizeInput();
    loadConversations();
});

function setupEventListeners() {
    // Mesaj gonder
    btnSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Giris degisiklikleri
    chatInput.addEventListener('input', () => {
        btnSend.disabled = !chatInput.value.trim();
        autoResizeInput();
    });

    // Yeni sohbet
    btnNewChat.addEventListener('click', startNewChat);

    // Mobil menu
    btnMenu.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // Anahtarlar
    toggleDebug.addEventListener('change', (e) => {
        showDebug = e.target.checked;
    });
    toggleSourcesEl.addEventListener('change', (e) => {
        showSources = e.target.checked;
    });

    // Dokuman paneli
    btnDocuments.addEventListener('click', openDocumentsPanel);
    btnCloseDocs.addEventListener('click', closeDocumentsPanel);
    docsPanel.addEventListener('click', (e) => {
        if (e.target === docsPanel) closeDocumentsPanel();
    });

    // Iceri aktar
    btnIngest.addEventListener('click', ingestDocuments);

    // Oneri butonlari
    document.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.dataset.query;
            btnSend.disabled = false;
            sendMessage();
        });
    });

    // Ayarlar paneli
    btnSettings.addEventListener('click', () => settingsPanel.style.display = 'flex');
    btnCloseSettings.addEventListener('click', () => settingsPanel.style.display = 'none');
    settingsPanel.addEventListener('click', (e) => {
        if (e.target === settingsPanel) settingsPanel.style.display = 'none';
    });

    // Tema butonlari
    themeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            themeBtns.forEach(b => b.classList.remove('active'));
            const target = e.target;
            target.classList.add('active');
            
            const color = target.dataset.color;
            document.documentElement.style.setProperty('--accent', color);
            
            // RGB ayrıştırması ve glow/border için uyarlama
            // Basitlik için sadece accent rengini güncelliyoruz, diğerleri de uyumlu görünür
            if (color === '#60a5fa') {
                document.documentElement.style.setProperty('--accent-glow', 'rgba(96, 165, 250, 0.15)');
                document.documentElement.style.setProperty('--accent-border', 'rgba(96, 165, 250, 0.3)');
            } else if (color === '#34d399') {
                document.documentElement.style.setProperty('--accent-glow', 'rgba(52, 211, 153, 0.15)');
                document.documentElement.style.setProperty('--accent-border', 'rgba(52, 211, 153, 0.3)');
            } else {
                document.documentElement.style.setProperty('--accent-glow', 'rgba(177, 152, 255, 0.15)');
                document.documentElement.style.setProperty('--accent-border', 'rgba(177, 152, 255, 0.3)');
            }
        });
    });

    // Otomatik kaydirma ayari
    toggleAutoscroll.addEventListener('change', (e) => {
        autoScroll = e.target.checked;
    });
}

// -- Saglik Kontrolu --
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();

        if (data.status === 'healthy') {
            statusDot.className = 'status-dot online';
            statusText.textContent = `Hazir - ${data.knowledge_base?.documents || 0} dokuman, ${data.knowledge_base?.chunks || 0} parca`;
        } else {
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Sagliksiz';
        }
    } catch (e) {
        statusDot.className = 'status-dot error';
        statusText.textContent = 'LUX sunucusuna baglanamadi';
    }
}

// -- Sohbet Gecmisi --
async function loadConversations() {
    try {
        const res = await fetch(`${API_BASE}/conversations`);
        const data = await res.json();

        if (!data.conversations || data.conversations.length === 0) {
            convEmpty.style.display = 'block';
            return;
        }

        convEmpty.style.display = 'none';
        conversationList.innerHTML = '';

        data.conversations.forEach(conv => {
            const el = document.createElement('div');
            el.className = 'conversation-item';
            if (conv.id === currentConversationId) {
                el.classList.add('active');
            }

            const title = conv.title || `Sohbet #${conv.id}`;
            const date = new Date(conv.updated_at).toLocaleDateString('tr-TR', {
                day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
            });

            el.innerHTML = `
                <div class="conv-info" onclick="loadConversation(${conv.id})">
                    <span class="conv-title">${escapeHtml(title)}</span>
                    <span class="conv-date">${date}</span>
                </div>
                <button class="conv-delete" onclick="event.stopPropagation(); deleteConversation(${conv.id})" title="Sohbeti sil">X</button>
            `;
            conversationList.appendChild(el);
        });
    } catch (e) {
        // Sessizce gec
    }
}

async function loadConversation(convId) {
    currentConversationId = convId;

    // Karsilama ekranini gizle
    welcomeScreen.style.display = 'none';
    messagesContainer.style.display = 'flex';
    messagesContainer.innerHTML = '';

    try {
        const res = await fetch(`${API_BASE}/conversations/${convId}/messages`);
        const data = await res.json();

        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                addMessage(msg.role, msg.content, msg.sources, null);
            });
        }
    } catch (e) {
        addMessage('assistant', `Sohbet yuklenirken hata olustu: ${e.message}`);
    }

    // Aktif sohbeti isaretle
    loadConversations();
    sidebar.classList.remove('open');
}

async function deleteConversation(convId) {
    if (!confirm('Bu sohbeti silmek istediginize emin misiniz?')) return;

    try {
        await fetch(`${API_BASE}/conversations/${convId}`, { method: 'DELETE' });

        if (convId === currentConversationId) {
            startNewChat();
        }
        loadConversations();
    } catch (e) {
        alert(`Sohbet silinirken hata: ${e.message}`);
    }
}

// -- Sohbet --
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isLoading) return;

    // Karsilama ekranini gizle, mesajlari goster
    welcomeScreen.style.display = 'none';
    messagesContainer.style.display = 'flex';

    // Kullanici mesajini ekle
    addMessage('user', message);
    chatInput.value = '';
    btnSend.disabled = true;
    autoResizeInput();

    // Yukleniyor goster
    const loadingEl = addLoadingMessage();
    isLoading = true;

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId,
                debug: showDebug,
            }),
        });

        const data = await res.json();

        // Yukleniyor'u kaldir
        loadingEl.remove();

        // Sohbet ID'sini guncelle
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
        }

        // Asistan mesajini ekle
        addMessage('assistant', data.answer, data.sources, data.debug);

        // Saglik durumunu guncelle
        checkHealth();

        // Sohbet gecmisini guncelle
        loadConversations();

    } catch (e) {
        loadingEl.remove();
        addMessage('assistant', `LUX ile iletisim hatasi: ${e.message}`);
    }

    isLoading = false;
}

function addMessage(role, content, sources = null, debug = null) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message';

    const avatarClass = role === 'user' ? 'user' : 'assistant';
    const avatarText = role === 'user' ? 'K' : 'L';
    const roleLabel = role === 'user' ? 'Siz' : 'LUX';

    let html = `
        <div class="message-avatar ${avatarClass}">${avatarText}</div>
        <div class="message-body">
            <div class="message-role">${roleLabel}</div>
            <div class="message-content">${formatContent(content)}</div>
    `;

    // Kaynaklar
    if (sources && sources.length > 0 && showSources) {
        html += `<div class="message-sources">
            <div class="sources-title">Kaynaklar</div>`;
        sources.forEach(s => {
            let sourceText = `<span class="source-file">${s.filename}</span>`;
            if (s.page) sourceText += ` - sayfa ${s.page}`;
            if (s.section) sourceText += ` (${s.section})`;
            sourceText += ` <span class="source-score">${(s.score * 100).toFixed(0)}%</span>`;
            html += `<div class="source-item">[D] ${sourceText}</div>`;
        });
        html += `</div>`;
    }

    // Debug
    if (debug && showDebug) {
        html += `<div class="message-debug">
            <div class="debug-title">Hata Ayiklama Bilgisi</div>`;
        html += formatDebug(debug);
        html += `</div>`;
    }

    html += `</div>`;
    messageEl.innerHTML = html;
    messagesContainer.appendChild(messageEl);
    scrollToBottom();
}

function addLoadingMessage() {
    const el = document.createElement('div');
    el.className = 'message';
    el.innerHTML = `
        <div class="message-avatar assistant">L</div>
        <div class="message-body">
            <div class="message-role">LUX</div>
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
            <div class="loading-text">Yanit olusturuluyor... Bu islem biraz zaman alabilir.</div>
        </div>
    `;
    messagesContainer.appendChild(el);
    scrollToBottom();
    return el;
}

function formatContent(text) {
    if (!text) return '';

    // Temel markdown formatlama
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Kod bloklari
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    // Satir ici kod
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Kalin
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italik
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Satir sonlari -> paragraflar
    html = html.split('\n\n').map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');

    return html;
}

function formatDebug(debug) {
    const lines = [];
    if (debug.query) lines.push(`Sorgu: ${debug.query}`);
    if (debug.query_type) lines.push(`Tur: ${debug.query_type}`);
    if (debug.embedding_time) lines.push(`Gomme suresi: ${debug.embedding_time}s`);
    if (debug.search_time) lines.push(`Arama suresi: ${debug.search_time}s`);
    if (debug.raw_results !== undefined) lines.push(`Bulunan sonuc: ${debug.raw_results}`);
    if (debug.filtered_results !== undefined) lines.push(`Filtreleme sonrasi: ${debug.filtered_results}`);
    if (debug.context_chars) lines.push(`Baglam: ${debug.context_chars} karakter`);
    if (debug.model) lines.push(`Model: ${debug.model}`);
    if (debug.generation_time) lines.push(`Uretim suresi: ${debug.generation_time}s`);
    if (debug.total_time) lines.push(`Toplam sure: ${debug.total_time}s`);

    if (debug.top_results && debug.top_results.length > 0) {
        lines.push('\nEn Iyi Sonuclar:');
        debug.top_results.forEach((r, i) => {
            lines.push(`  ${i+1}. ${r.filename} -> ${(r.score * 100).toFixed(1)}%`);
        });
    }

    if (debug.tokens) {
        lines.push(`\nTokenlar: ${debug.tokens.prompt} girdi + ${debug.tokens.completion} cikti = ${debug.tokens.total} toplam`);
    }

    return lines.join('\n');
}

// -- Yeni Sohbet --
function startNewChat() {
    currentConversationId = null;
    messagesContainer.innerHTML = '';
    messagesContainer.style.display = 'none';
    welcomeScreen.style.display = 'flex';
    chatInput.focus();
    sidebar.classList.remove('open');
    loadConversations();
}

// -- Dokuman Paneli --
async function openDocumentsPanel() {
    docsPanel.style.display = 'flex';
    await loadDocuments();
    await loadKBStats();
}

function closeDocumentsPanel() {
    docsPanel.style.display = 'none';
}

async function loadDocuments() {
    const listEl = document.getElementById('document-list');
    try {
        const res = await fetch(`${API_BASE}/documents`);
        const data = await res.json();

        if (data.documents.length === 0) {
            listEl.innerHTML = '<p class="empty-state">Henuz dokuman indekslenmedi. Dosyalarinizi eklemek icin "Dokumanlari Iceri Aktar" butonuna tiklayin.</p>';
            return;
        }

        listEl.innerHTML = data.documents.map(doc => `
            <div class="doc-item">
                <div class="doc-info">
                    <span class="doc-name">${doc.filename}</span>
                    <span class="doc-meta">${doc.file_type} - ${doc.num_chunks} parca - ${doc.title || ''}</span>
                </div>
                <div class="doc-actions">
                    <button class="btn btn-danger" onclick="deleteDocument(${doc.id}, '${doc.filename}')">Sil</button>
                </div>
            </div>
        `).join('');

    } catch (e) {
        listEl.innerHTML = `<p class="empty-state">Dokumanlar yuklenirken hata: ${e.message}</p>`;
    }
}

async function loadKBStats() {
    try {
        const res = await fetch(`${API_BASE}/knowledge-base/status`);
        const data = await res.json();
        document.getElementById('stat-docs').textContent = data.documents || 0;
        document.getElementById('stat-chunks').textContent = data.chunks || 0;
        document.getElementById('stat-db-size').textContent = (data.database_size_mb || 0) + ' MB';
    } catch (e) {
        // Sessizce gec
    }
}

async function ingestDocuments() {
    const statusEl = document.getElementById('ingest-status');
    statusEl.style.display = 'block';
    statusEl.className = 'ingest-status';
    statusEl.textContent = 'Dokumanlar iceri aktariliyor... Bu islem biraz zaman alabilir.';
    btnIngest.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/documents/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recursive: true }),
        });
        const data = await res.json();

        statusEl.className = 'ingest-status success';
        statusEl.textContent = `Tamamlandi! ${data.ingested} aktarildi, ${data.skipped} atlandi, ${data.failed} basarisiz. Toplam parca: ${data.total_chunks}. (${data.duration}s)`;

        if (data.errors.length > 0) {
            statusEl.textContent += '\nHatalar: ' + data.errors.join(', ');
            statusEl.className = 'ingest-status error';
        }

        await loadDocuments();
        await loadKBStats();
        checkHealth();

    } catch (e) {
        statusEl.className = 'ingest-status error';
        statusEl.textContent = `Hata: ${e.message}`;
    }

    btnIngest.disabled = false;
}

async function deleteDocument(docId, filename) {
    if (!confirm(`"${filename}" ve tum parcalarini silmek istediginize emin misiniz?`)) return;

    try {
        await fetch(`${API_BASE}/documents/${docId}`, { method: 'DELETE' });
        await loadDocuments();
        await loadKBStats();
        checkHealth();
    } catch (e) {
        alert(`Dokuman silinirken hata: ${e.message}`);
    }
}

// -- Yardimci Fonksiyonlar --
function scrollToBottom() {
    if (autoScroll) {
        chatArea.scrollTop = chatArea.scrollHeight;
    }
}

function autoResizeInput() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
