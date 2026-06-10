// ── State ──
const state = {
    currentPage: 'skills',
    currentSkillId: null,
    skillEditMode: 'form',   // 'form' | 'markdown'
    skills: [],
};

// ── API helpers ──
async function api(path, options = {}) {
    const res = await fetch('/api' + path, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// ── Navigation ──
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateTo(page);
        });
    });
}

function navigateTo(page) {
    state.currentPage = page;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');
    renderPage(page);
}

// ── Page Router ──
async function renderPage(page) {
    const content = document.getElementById('content');
    switch (page) {
        case 'skills': content.innerHTML = await renderSkillsPage(); setupSkillsPage(); break;
        case 'llm': content.innerHTML = renderLLMPage(); setupLLMPage(); break;
        case 'bot': content.innerHTML = renderBotPage(); setupBotPage(); break;
        case 'platform': content.innerHTML = renderPlatformPage(); setupPlatformPage(); break;
        case 'test': content.innerHTML = renderTestPage(); setupTestPage(); break;
    }
}

// ── Toasts ──
function showToast(msg, type = 'success') {
    const el = document.createElement('div');
    el.style.cssText = `
        position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;
        color:#fff;font-size:14px;z-index:9999;animation:fadeIn 0.3s;
        background:${type === 'success' ? '#22c55e' : '#ef4444'};
    `;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => { el.remove(); }, 3000);
}

// ═══════════════════════════════════════════════════════════════
// SKILLS PAGE
// ═══════════════════════════════════════════════════════════════
async function renderSkillsPage() {
    state.skills = (await api('/admin/skills')).skills;
    return `
    <div class="skill-layout">
        <div class="skill-sidebar card">
            <div class="card-title">Skill 列表</div>
            <ul class="skill-list" id="skillList">
                ${state.skills.map(s => `
                    <li data-id="${s.id}" class="${s.id === state.currentSkillId ? 'active' : ''}">
                        <span>${escapeHtml(s.name)}</span>
                        ${s.is_active ? '<span class="active-dot"></span>' : ''}
                    </li>
                `).join('')}
            </ul>
            <div style="margin-top:12px;">
                <button class="btn btn-primary btn-sm" onclick="createSkill()">+ 新建</button>
            </div>
        </div>
        <div class="skill-main card" id="skillEditor">
            ${state.currentSkillId ? renderSkillEditor() : '<p style="color:var(--text-secondary)">← 选择或创建一个 Skill 开始编辑</p>'}
        </div>
    </div>`;
}

function renderSkillEditor() {
    const skill = state.skills.find(s => s.id === state.currentSkillId);
    if (!skill) return '<p>Skill not found</p>';

    const parsed = parseMarkdownBasic(skill.content);
    const isForm = state.skillEditMode === 'form';

    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <div class="card-title" style="margin-bottom:0;">编辑: ${escapeHtml(skill.name)}</div>
        <div style="display:flex;gap:8px;">
            ${!skill.is_active ? `<button class="btn btn-secondary btn-sm" onclick="activateSkill(${skill.id})">设为活跃</button>` : '<span style="font-size:12px;color:var(--success)">● 当前活跃</span>'}
            <button class="btn btn-danger btn-sm" onclick="deleteSkill(${skill.id})">🗑 删除</button>
        </div>
    </div>

    <div class="mode-toggle">
        <span class="mode-label ${isForm ? 'active' : ''}">📝 表单</span>
        <div class="toggle-switch ${!isForm ? 'active' : ''}" onclick="toggleEditMode()"></div>
        <span class="mode-label ${!isForm ? 'active' : ''}">📄 Markdown</span>
    </div>

    ${isForm ? renderFormEditor(skill, parsed) : renderMarkdownEditor(skill)}
    `;
}

function renderFormEditor(skill, parsed) {
    return `
    <div id="formEditor">
        <div class="form-group">
            <label>角色名称</label>
            <input id="skillName" value="${escapeHtml(skill.name)}">
        </div>
        <div class="form-group">
            <label>角色描述</label>
            <textarea id="skillRole">${escapeHtml(parsed.role || '')}</textarea>
        </div>
        <div class="form-group">
            <label>口吻风格</label>
            <input id="skillTone" value="${escapeHtml(parsed.tone || '')}" placeholder="如：亲切耐心、专业严谨、幽默风趣...">
        </div>
        <div class="form-group">
            <label>回复规则</label>
            <div id="rulesContainer">
                ${(parsed.rules || []).map((r, i) => `
                    <div class="rule-item">
                        <span class="drag-handle">⠿</span>
                        <input value="${escapeHtml(r)}" data-rule-idx="${i}">
                        <button class="btn btn-secondary btn-sm" onclick="removeRule(this)">✕</button>
                    </div>
                `).join('')}
            </div>
            <button class="btn btn-secondary btn-sm" style="margin-top:8px;" onclick="addRule()">+ 添加规则</button>
        </div>
        <div class="form-group">
            <label>知识库 FAQ</label>
            <div id="faqContainer">
                ${(parsed.faq || []).map((f, i) => `
                    <div class="faq-item">
                        <div class="faq-row">
                            <span>Q:</span>
                            <input value="${escapeHtml(f.q || '')}" placeholder="问题" data-faq-idx="${i}" data-faq-field="q">
                        </div>
                        <div class="faq-row">
                            <span>A:</span>
                            <input value="${escapeHtml(f.a || '')}" placeholder="回答" data-faq-idx="${i}" data-faq-field="a">
                        </div>
                        <button class="btn btn-secondary btn-sm" onclick="removeFaq(this)">✕ 删除</button>
                    </div>
                `).join('')}
            </div>
            <button class="btn btn-secondary btn-sm" style="margin-top:8px;" onclick="addFaq()">+ 添加 FAQ</button>
        </div>
        <div class="btn-group">
            <button class="btn btn-primary" onclick="saveSkillForm()">💾 保存</button>
            <button class="btn btn-secondary" onclick="loadSkill(state.currentSkillId)">🔄 重置</button>
        </div>
    </div>`;
}

function renderMarkdownEditor(skill) {
    return `
    <div id="markdownEditor">
        <div class="form-group">
            <textarea id="skillMarkdown" style="min-height:400px;">${escapeHtml(skill.content || '')}</textarea>
        </div>
        <div class="btn-group">
            <button class="btn btn-primary" onclick="saveSkillMarkdown()">💾 保存</button>
            <button class="btn btn-secondary" onclick="loadSkill(state.currentSkillId)">🔄 重置</button>
        </div>
    </div>`;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function parseMarkdownBasic(content) {
    // Simple client-side markdown parsing matching server-side logic
    const result = { name: '', role: '', tone: '', rules: [], faq: [] };
    if (!content) return result;

    const h1Match = content.match(/^#\s+Skill:\s*(.+)$/m);
    if (h1Match) result.name = h1Match[1].trim();

    const sections = content.split(/\n##\s+/);
    for (const section of sections) {
        const lines = section.trim().split('\n');
        const heading = lines[0].trim();
        const body = lines.slice(1).join('\n').trim();

        if (heading.startsWith('角色')) result.role = body;
        else if (heading.startsWith('口吻')) result.tone = body;
        else if (heading.startsWith('回复规则')) {
            result.rules = body.split('\n')
                .filter(l => l.trim())
                .map(l => l.replace(/^\d+\.\s*/, '').trim());
        } else if (heading.startsWith('知识库')) {
            const faq = [];
            let cur = null;
            for (const line of body.split('\n')) {
                const trimmed = line.trim();
                const qMatch = trimmed.match(/^-\s*Q:\s*(.+)/);
                const aMatch = trimmed.match(/^-\s*A:\s*(.+)/);
                if (qMatch) {
                    if (cur) faq.push(cur);
                    cur = { q: qMatch[1], a: '' };
                } else if (aMatch && cur) {
                    cur.a = aMatch[1];
                }
            }
            if (cur) faq.push(cur);
            result.faq = faq;
        }
    }
    return result;
}

function setupSkillsPage() {
    document.querySelectorAll('#skillList li').forEach(li => {
        li.addEventListener('click', () => loadSkill(parseInt(li.dataset.id)));
    });
}

async function loadSkill(id) {
    state.currentSkillId = id;
    const resp = await api('/admin/skills/' + id);
    // Refresh skills list with updated data
    state.skills = (await api('/admin/skills')).skills;
    const content = document.getElementById('content');
    content.innerHTML = await renderSkillsPage();
    setupSkillsPage();
}

async function createSkill() {
    const name = prompt('Skill 名称:');
    if (!name) return;
    await api('/admin/skills', {
        method: 'POST',
        body: JSON.stringify({ name, content: '', is_active: state.skills.length === 0 }),
    });
    state.skills = (await api('/admin/skills')).skills;
    if (state.skills.length > 0) {
        state.currentSkillId = state.skills[state.skills.length - 1].id;
    }
    const content = document.getElementById('content');
    content.innerHTML = await renderSkillsPage();
    setupSkillsPage();
    showToast('Skill 已创建');
}

async function activateSkill(id) {
    await api('/admin/skills/' + id, {
        method: 'PUT',
        body: JSON.stringify({ is_active: true }),
    });
    loadSkill(id);
    showToast('已设为活跃 Skill');
}

async function deleteSkill(id) {
    if (!confirm('确定删除此 Skill?')) return;
    try {
        await api('/admin/skills/' + id, { method: 'DELETE' });
        state.skills = (await api('/admin/skills')).skills;
        state.currentSkillId = state.skills.length > 0 ? state.skills[0].id : null;
        const content = document.getElementById('content');
        content.innerHTML = await renderSkillsPage();
        setupSkillsPage();
        showToast('Skill 已删除');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function toggleEditMode() {
    state.skillEditMode = state.skillEditMode === 'form' ? 'markdown' : 'form';
    loadSkill(state.currentSkillId);
}

function addRule() {
    const container = document.getElementById('rulesContainer');
    const idx = container.children.length;
    const div = document.createElement('div');
    div.className = 'rule-item';
    div.innerHTML = `
        <span class="drag-handle">⠿</span>
        <input data-rule-idx="${idx}" placeholder="规则 ${idx + 1}">
        <button class="btn btn-secondary btn-sm" onclick="removeRule(this)">✕</button>`;
    container.appendChild(div);
}

function removeRule(btn) {
    btn.closest('.rule-item').remove();
}

function addFaq() {
    const container = document.getElementById('faqContainer');
    const idx = container.children.length;
    const div = document.createElement('div');
    div.className = 'faq-item';
    div.innerHTML = `
        <div class="faq-row"><span>Q:</span><input data-faq-idx="${idx}" data-faq-field="q" placeholder="问题"></div>
        <div class="faq-row"><span>A:</span><input data-faq-idx="${idx}" data-faq-field="a" placeholder="回答"></div>
        <button class="btn btn-secondary btn-sm" onclick="removeFaq(this)">✕ 删除</button>`;
    container.appendChild(div);
}

function removeFaq(btn) {
    btn.closest('.faq-item').remove();
}

async function saveSkillForm() {
    const name = document.getElementById('skillName').value.trim();
    const role = document.getElementById('skillRole').value.trim();
    const tone = document.getElementById('skillTone').value.trim();

    const rules = [];
    document.querySelectorAll('#rulesContainer input').forEach(inp => {
        const v = inp.value.trim();
        if (v) rules.push(v);
    });

    const faq = [];
    document.querySelectorAll('#faqContainer .faq-item').forEach(item => {
        const qInp = item.querySelector('[data-faq-field="q"]');
        const aInp = item.querySelector('[data-faq-field="a"]');
        const q = qInp?.value?.trim() || '';
        const a = aInp?.value?.trim() || '';
        if (q || a) faq.push({ q, a });
    });

    // Serialize on server side for consistency
    const resp = await api('/admin/skills/serialize', {
        method: 'POST',
        body: JSON.stringify({ name, role, tone, rules, faq }),
    });

    await api('/admin/skills/' + state.currentSkillId, {
        method: 'PUT',
        body: JSON.stringify({ name, content: resp.content }),
    });

    loadSkill(state.currentSkillId);
    showToast('Skill 已保存');
}

async function saveSkillMarkdown() {
    const content = document.getElementById('skillMarkdown').value;
    // Extract name from markdown heading
    const h1Match = content.match(/^#\s+Skill:\s*(.+)$/m);
    const name = h1Match ? h1Match[1].trim() : 'Untitled';

    await api('/admin/skills/' + state.currentSkillId, {
        method: 'PUT',
        body: JSON.stringify({ name, content }),
    });

    loadSkill(state.currentSkillId);
    showToast('Skill 已保存');
}

// ═══════════════════════════════════════════════════════════════
// LLM CONFIG PAGE
// ═══════════════════════════════════════════════════════════════
function renderLLMPage() {
    return `
    <div class="card">
        <div class="card-title">LLM 提供商配置</div>
        <div class="form-group">
            <label>提供商</label>
            <select id="llmProvider">
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="deepseek">DeepSeek</option>
            </select>
        </div>
        <div class="form-group">
            <label>模型</label>
            <input id="llmModel" value="gpt-4o" placeholder="如: gpt-4o, gpt-4-turbo">
        </div>
        <div class="form-group">
            <label>API Key</label>
            <div class="password-field">
                <input id="llmApiKey" type="password" placeholder="sk-...">
                <button class="toggle-vis" onclick="togglePassword('llmApiKey')">👁</button>
            </div>
        </div>
        <div class="form-group">
            <label>Base URL (可选，用于代理或自部署端点)</label>
            <input id="llmBaseUrl" placeholder="https://api.openai.com/v1">
        </div>
        <div class="btn-group">
            <button class="btn btn-primary" onclick="saveLLMConfig()">💾 保存</button>
            <button class="btn btn-secondary" onclick="testLLM()">🔄 测试连接</button>
        </div>
        <div class="result" id="llmResult"></div>
    </div>`;
}

async function setupLLMPage() {
    try {
        const resp = await api('/admin/config/llm');
        const config = resp.config || resp;
        document.getElementById('llmProvider').value = config.provider || 'openai';
        document.getElementById('llmModel').value = config.model || 'gpt-4o';
        document.getElementById('llmApiKey').value = config.api_key || '';
        document.getElementById('llmBaseUrl').value = config.base_url || '';
    } catch (e) { /* use defaults */ }
}

async function saveLLMConfig() {
    const data = {
        provider: document.getElementById('llmProvider').value,
        model: document.getElementById('llmModel').value,
        api_key: document.getElementById('llmApiKey').value,
        base_url: document.getElementById('llmBaseUrl').value,
    };
    await api('/admin/config/llm', { method: 'PUT', body: JSON.stringify(data) });
    showToast('LLM 配置已保存');
}

async function testLLM() {
    const result = document.getElementById('llmResult');
    result.className = 'result';
    result.style.display = 'block';
    result.textContent = '正在测试连接...';
    try {
        const resp = await api('/admin/config/llm/test', {
            method: 'POST',
            body: JSON.stringify({ message: 'Hi, this is a test.' })
        });
        if (resp.ok) {
            result.className = 'result success';
            result.textContent = '✅ 连接成功！回复: ' + resp.reply;
        } else {
            result.className = 'result error';
            result.textContent = '❌ 连接失败: ' + resp.error;
        }
    } catch (e) {
        result.className = 'result error';
        result.textContent = '❌ 请求失败: ' + e.message;
    }
}

function togglePassword(id) {
    const inp = document.getElementById(id);
    inp.type = inp.type === 'password' ? 'text' : 'password';
}

// ═══════════════════════════════════════════════════════════════
// BOT CONFIG PAGE
// ═══════════════════════════════════════════════════════════════
function renderBotPage() {
    return `
    <div class="card">
        <div class="card-title">回复行为</div>
        <div class="form-group">
            <label>回复触发方式</label>
            <select id="botTriggerMode">
                <option value="all">所有消息</option>
                <option value="mention">仅 @机器人</option>
            </select>
        </div>
        <div class="form-group">
            <label>最大回复长度: <span id="maxLenVal">500</span> 字</label>
            <input type="range" id="botMaxLen" min="50" max="2000" step="50" value="500"
                   oninput="document.getElementById('maxLenVal').textContent = this.value">
        </div>
        <div class="form-group">
            <label>滑动窗口大小</label>
            <input type="number" id="botWindowSize" value="20" min="1" max="100">
        </div>
        <div class="form-group">
            <label>响应延迟 (秒)</label>
            <input type="number" id="botDelay" value="0" min="0" max="10" step="0.5">
        </div>
        <div class="form-group">
            <label>欢迎语 (新用户进群/首次消息时发送，留空则不发送)</label>
            <input id="botWelcome" placeholder="欢迎来到我们的群~">
        </div>
        <div class="form-group">
            <label>黑名单词 (逗号分隔，包含这些词的消息将被忽略)</label>
            <input id="botBlacklist" placeholder="脏话1, 脏话2">
        </div>
        <div class="btn-group">
            <button class="btn btn-primary" onclick="saveBotConfig()">💾 保存</button>
        </div>
    </div>`;
}

async function setupBotPage() {
    try {
        const resp = await api('/admin/config/bot');
        const config = resp.config || resp;
        document.getElementById('botTriggerMode').value = config.trigger_mode || 'all';
        document.getElementById('botMaxLen').value = config.max_reply_length || 500;
        document.getElementById('maxLenVal').textContent = config.max_reply_length || 500;
        document.getElementById('botWindowSize').value = config.window_size || 20;
        document.getElementById('botDelay').value = config.response_delay || 0;
        document.getElementById('botWelcome').value = config.welcome_message || '';
        document.getElementById('botBlacklist').value = config.blacklist || '';
    } catch (e) { /* use defaults */ }
}

async function saveBotConfig() {
    const data = {
        trigger_mode: document.getElementById('botTriggerMode').value,
        max_reply_length: parseInt(document.getElementById('botMaxLen').value),
        window_size: parseInt(document.getElementById('botWindowSize').value),
        response_delay: parseFloat(document.getElementById('botDelay').value),
        welcome_message: document.getElementById('botWelcome').value,
        blacklist: document.getElementById('botBlacklist').value,
    };
    await api('/admin/config/bot', { method: 'PUT', body: JSON.stringify(data) });
    showToast('行为配置已保存');
}

// ═══════════════════════════════════════════════════════════════
// PLATFORM CONFIG PAGE
// ═══════════════════════════════════════════════════════════════
function renderPlatformPage() {
    const webhookUrl = window.location.origin + '/api/feishu/event';
    return `
    <div class="card">
        <div class="card-title">飞书 (Lark) <span class="conn-status disconnected" id="feishuStatus">未配置</span></div>
        <div class="form-group">
            <label>App ID</label>
            <input id="feishuAppId" placeholder="cli_xxxxxxxxxxxx">
        </div>
        <div class="form-group">
            <label>App Secret</label>
            <div class="password-field">
                <input id="feishuAppSecret" type="password" placeholder="输入 App Secret">
                <button class="toggle-vis" onclick="togglePassword('feishuAppSecret')">👁</button>
            </div>
        </div>
        <div class="form-group">
            <label>验证 Token</label>
            <input id="feishuToken" placeholder="输入 Verification Token">
        </div>
        <div class="form-group">
            <label>加密 Key (可选)</label>
            <input id="feishuEncryptKey" placeholder="输入 Encrypt Key (可选)">
        </div>
        <div class="form-group">
            <label>Webhook URL</label>
            <div class="copy-field">
                <input id="webhookUrl" value="${webhookUrl}" readonly>
                <button class="btn btn-secondary btn-sm" onclick="copyWebhookUrl()">📋 复制</button>
            </div>
            <span style="font-size:12px;color:var(--text-secondary);margin-top:4px;display:block;">
                将此 URL 填入飞书开放平台的「事件订阅」配置中
            </span>
        </div>
        <div class="btn-group">
            <button class="btn btn-primary" onclick="savePlatformConfig()">💾 保存</button>
        </div>
    </div>

    <div class="card">
        <div class="card-title">其他平台 (预留)</div>
        <p style="color:var(--text-secondary);font-size:14px;">
            Discord、企业微信、Slack 等平台适配即将支持。
        </p>
    </div>`;
}

async function setupPlatformPage() {
    try {
        const resp = await api('/admin/config/platform');
        const configs = resp.configs || [];
        const feishu = configs.find(c => c.platform_type === 'feishu');
        if (feishu) {
            document.getElementById('feishuAppId').value = feishu.app_id || '';
            document.getElementById('feishuAppSecret').value = feishu.app_secret || '';
            document.getElementById('feishuToken').value = feishu.verification_token || '';
            document.getElementById('feishuEncryptKey').value = feishu.encrypt_key || '';
            const status = document.getElementById('feishuStatus');
            if (feishu.app_id && feishu.app_secret) {
                status.textContent = '✅ 已配置';
                status.className = 'conn-status connected';
            }
        }
    } catch (e) { /* use defaults */ }
}

function copyWebhookUrl() {
    const inp = document.getElementById('webhookUrl');
    inp.select();
    document.execCommand('copy');
    showToast('Webhook URL 已复制到剪贴板');
}

async function savePlatformConfig() {
    const data = {
        app_id: document.getElementById('feishuAppId').value,
        app_secret: document.getElementById('feishuAppSecret').value,
        verification_token: document.getElementById('feishuToken').value,
        encrypt_key: document.getElementById('feishuEncryptKey').value,
    };
    await api('/admin/config/platform/feishu', { method: 'PUT', body: JSON.stringify(data) });
    document.getElementById('feishuStatus').textContent = '✅ 已配置';
    document.getElementById('feishuStatus').className = 'conn-status connected';
    showToast('飞书配置已保存');
}

// ═══════════════════════════════════════════════════════════════
// CHAT TEST PAGE
// ═══════════════════════════════════════════════════════════════
function renderTestPage() {
    return `
    <div class="card">
        <div class="card-title">对话测试</div>
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div style="text-align:center;color:var(--text-secondary);padding:40px;">
                    输入消息测试当前 Skill 和 LLM 配置的效果
                </div>
            </div>
            <div class="chat-input-area">
                <input id="chatInput" placeholder="输入测试消息..." onkeydown="if(event.key==='Enter')sendTestMessage()">
                <button class="btn btn-primary" onclick="sendTestMessage()">⏎ 发送</button>
                <button class="btn btn-secondary" onclick="clearTestChat()">🗑 清空</button>
            </div>
        </div>
    </div>`;
}

function setupTestPage() {
    document.getElementById('chatInput')?.focus();
}

async function sendTestMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    input.value = '';

    const container = document.getElementById('chatMessages');
    // Remove placeholder
    if (container.querySelector('div[style]')) container.innerHTML = '';

    // Add user bubble
    container.innerHTML += `<div class="chat-bubble user">${escapeHtml(message)}</div>`;

    // Add loading bubble
    const loadingId = 'loading-' + Date.now();
    container.innerHTML += `<div class="chat-bubble bot" id="${loadingId}">🤔 思考中...</div>`;
    container.scrollTop = container.scrollHeight;

    const startTime = Date.now();
    try {
        const resp = await api('/admin/chat/test', {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
        const latency = Date.now() - startTime;
        const loading = document.getElementById(loadingId);
        if (loading) {
            if (resp.ok) {
                loading.innerHTML = `${escapeHtml(resp.reply)}<div class="chat-meta">字数: ${resp.length} | 延迟: ${(latency / 1000).toFixed(1)}s</div>`;
            } else {
                loading.innerHTML = `❌ 回复失败: ${escapeHtml(resp.error)}<div class="chat-meta">延迟: ${(latency / 1000).toFixed(1)}s</div>`;
            }
        }
    } catch (e) {
        const loading = document.getElementById(loadingId);
        if (loading) loading.innerHTML = `❌ 请求失败: ${escapeHtml(e.message)}`;
    }
    container.scrollTop = container.scrollHeight;
}

async function clearTestChat() {
    document.getElementById('chatMessages').innerHTML = `
        <div style="text-align:center;color:var(--text-secondary);padding:40px;">
            输入消息测试当前 Skill 和 LLM 配置的效果
        </div>`;
    try { await api('/admin/conversation/test-channel', { method: 'DELETE' }); } catch (e) { /* ignore */ }
}

// ── Init ──
setupNavigation();
navigateTo('skills');
