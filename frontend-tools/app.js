// ============================================================
// Navigation & Theme
// ============================================================
const toolNav = document.getElementById('toolNav');
const toolContainer = document.getElementById('toolContainer');

toolNav.addEventListener('click', (e) => {
  const btn = e.target.closest('.nav-btn');
  if (!btn) return;
  const tool = btn.dataset.tool;
  toolNav.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  toolContainer.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tool-' + tool).classList.add('active');
});

const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');
const savedTheme = localStorage.getItem('theme') || 'light';
if (savedTheme === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
updateThemeIcon();

themeToggle.addEventListener('click', () => {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
  updateThemeIcon();
});

function updateThemeIcon() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  themeIcon.innerHTML = isDark ? '&#9788;' : '&#9790;';
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => showToast('已复制到剪贴板'));
}

function copyResult(id) {
  const el = document.getElementById(id);
  copyText(el.value || el.textContent);
}

// ============================================================
// Color Tool
// ============================================================
const colorPicker = document.getElementById('colorPicker');
const colorPreview = document.getElementById('colorPreview');
const colorValues = document.getElementById('colorValues');

colorPicker.addEventListener('input', () => updateColorDisplay(colorPicker.value));
updateColorDisplay(colorPicker.value);

function updateColorDisplay(hex) {
  colorPreview.style.background = hex;
  const rgb = hexToRgb(hex);
  const hsl = rgbToHsl(rgb.r, rgb.g, rgb.b);
  colorValues.innerHTML = `
    <div onclick="copyText('${hex}')">${hex} <small>点击复制</small></div>
    <div onclick="copyText('rgb(${rgb.r}, ${rgb.g}, ${rgb.b})')">rgb(${rgb.r}, ${rgb.g}, ${rgb.b}) <small>点击复制</small></div>
    <div onclick="copyText('hsl(${hsl.h}, ${hsl.s}%, ${hsl.l}%)')">hsl(${hsl.h}, ${hsl.s}%, ${hsl.l}%) <small>点击复制</small></div>
    <div onclick="copyText('rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)')">rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1) <small>点击复制</small></div>
  `;
}

function hexToRgb(hex) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
  return {
    r: parseInt(hex.substring(0, 2), 16),
    g: parseInt(hex.substring(2, 4), 16),
    b: parseInt(hex.substring(4, 6), 16)
  };
}

function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(c => Math.max(0, Math.min(255, Math.round(c))).toString(16).padStart(2, '0')).join('');
}

function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  if (max === min) { h = s = 0; }
  else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
}

function hslToRgb(h, s, l) {
  h /= 360; s /= 100; l /= 100;
  let r, g, b;
  if (s === 0) { r = g = b = l; }
  else {
    const hue2rgb = (p, q, t) => { if (t < 0) t += 1; if (t > 1) t -= 1; if (t < 1/6) return p + (q-p)*6*t; if (t < 1/2) return q; if (t < 2/3) return p + (q-p)*(2/3-t)*6; return p; };
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1/3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1/3);
  }
  return { r: Math.round(r * 255), g: Math.round(g * 255), b: Math.round(b * 255) };
}

function convertColor() {
  const input = document.getElementById('colorInput').value.trim();
  const result = document.getElementById('colorConvertResult');
  try {
    let r, g, b;
    if (input.startsWith('#')) {
      const rgb = hexToRgb(input);
      r = rgb.r; g = rgb.g; b = rgb.b;
    } else if (input.startsWith('rgb')) {
      const m = input.match(/(\d+)/g);
      r = parseInt(m[0]); g = parseInt(m[1]); b = parseInt(m[2]);
    } else if (input.startsWith('hsl')) {
      const m = input.match(/(\d+)/g);
      const rgb = hslToRgb(parseInt(m[0]), parseInt(m[1]), parseInt(m[2]));
      r = rgb.r; g = rgb.g; b = rgb.b;
    } else {
      result.textContent = '无法识别的颜色格式';
      return;
    }
    const hex = rgbToHex(r, g, b);
    const hsl = rgbToHsl(r, g, b);
    result.innerHTML = `HEX: ${hex}\nRGB: rgb(${r}, ${g}, ${b})\nHSL: hsl(${hsl.h}, ${hsl.s}%, ${hsl.l}%)`;
  } catch (e) {
    result.textContent = '转换失败，请检查格式';
  }
}

function generatePalette(type) {
  const hex = document.getElementById('paletteBase').value;
  const rgb = hexToRgb(hex);
  const hsl = rgbToHsl(rgb.r, rgb.g, rgb.b);
  let colors = [];

  if (type === 'complementary') {
    colors = [hsl.h, (hsl.h + 180) % 360].map(h => {
      const c = hslToRgb(h, hsl.s, hsl.l);
      return rgbToHex(c.r, c.g, c.b);
    });
  } else if (type === 'analogous') {
    colors = [-30, -15, 0, 15, 30].map(offset => {
      const c = hslToRgb((hsl.h + offset + 360) % 360, hsl.s, hsl.l);
      return rgbToHex(c.r, c.g, c.b);
    });
  } else if (type === 'triadic') {
    colors = [0, 120, 240].map(offset => {
      const c = hslToRgb((hsl.h + offset) % 360, hsl.s, hsl.l);
      return rgbToHex(c.r, c.g, c.b);
    });
  } else if (type === 'shades') {
    colors = [90, 75, 60, 45, 30, 20, 10].map(l => {
      const c = hslToRgb(hsl.h, hsl.s, l);
      return rgbToHex(c.r, c.g, c.b);
    });
  }

  const display = document.getElementById('paletteDisplay');
  display.innerHTML = colors.map(c =>
    `<div class="palette-swatch" data-color="${c}" style="background:${c}" onclick="copyText('${c}')" title="点击复制 ${c}"></div>`
  ).join('');
}

// ============================================================
// JSON Tool
// ============================================================
function formatJSON() {
  const input = document.getElementById('jsonInput').value;
  const output = document.getElementById('jsonOutput');
  const validation = document.getElementById('jsonValidation');
  try {
    const obj = JSON.parse(input);
    output.value = JSON.stringify(obj, null, 2);
    validation.textContent = 'JSON 格式正确';
    validation.style.color = 'var(--success)';
  } catch (e) {
    validation.textContent = '错误: ' + e.message;
    validation.style.color = 'var(--danger)';
  }
}

function minifyJSON() {
  const input = document.getElementById('jsonInput').value;
  const output = document.getElementById('jsonOutput');
  const validation = document.getElementById('jsonValidation');
  try {
    output.value = JSON.stringify(JSON.parse(input));
    validation.textContent = 'JSON 已压缩';
    validation.style.color = 'var(--success)';
  } catch (e) {
    validation.textContent = '错误: ' + e.message;
    validation.style.color = 'var(--danger)';
  }
}

function validateJSON() {
  const input = document.getElementById('jsonInput').value;
  const validation = document.getElementById('jsonValidation');
  try {
    JSON.parse(input);
    validation.textContent = 'JSON 格式正确!';
    validation.style.color = 'var(--success)';
  } catch (e) {
    validation.textContent = '格式错误: ' + e.message;
    validation.style.color = 'var(--danger)';
  }
}

// ============================================================
// Base64 Tool
// ============================================================
function base64Encode() {
  const input = document.getElementById('base64Input').value;
  try {
    document.getElementById('base64Output').value = btoa(unescape(encodeURIComponent(input)));
  } catch (e) {
    showToast('编码失败');
  }
}

function base64Decode() {
  const input = document.getElementById('base64Output').value;
  try {
    document.getElementById('base64Input').value = decodeURIComponent(escape(atob(input)));
  } catch (e) {
    showToast('解码失败，请检查输入');
  }
}

function imageToBase64(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    document.getElementById('imageBase64Output').value = reader.result;
  };
  reader.readAsDataURL(file);
}

// ============================================================
// URL Tool
// ============================================================
function urlEncode() {
  document.getElementById('urlOutput').value = encodeURIComponent(document.getElementById('urlInput').value);
}

function urlDecode() {
  try {
    document.getElementById('urlInput').value = decodeURIComponent(document.getElementById('urlOutput').value);
  } catch (e) {
    showToast('解码失败');
  }
}

function parseURL() {
  const input = document.getElementById('urlParseInput').value;
  const result = document.getElementById('urlParseResult');
  try {
    const url = new URL(input);
    let html = `协议: ${url.protocol}\n主机: ${url.hostname}\n端口: ${url.port || '(默认)'}\n路径: ${url.pathname}\n哈希: ${url.hash || '(无)'}\n\n查询参数:\n`;
    url.searchParams.forEach((v, k) => { html += `  ${k} = ${v}\n`; });
    if (!url.search) html += '  (无参数)';
    result.textContent = html;
  } catch (e) {
    result.textContent = '无效的 URL，请输入完整网址 (包含 http/https)';
  }
}

// ============================================================
// Timestamp Tool
// ============================================================
function updateCurrentTime() {
  const now = new Date();
  const el = document.getElementById('currentTime');
  if (el) {
    el.innerHTML = `
      ${now.toLocaleString('zh-CN')}
      <br>Unix 时间戳 (秒): ${Math.floor(now.getTime() / 1000)}
      <br>Unix 时间戳 (毫秒): ${now.getTime()}
    `;
  }
}
setInterval(updateCurrentTime, 1000);
updateCurrentTime();

const dateInput = document.getElementById('dateInput');
dateInput.value = new Date().toISOString().slice(0, 16);

function timestampToDate() {
  let ts = document.getElementById('timestampInput').value.trim();
  const result = document.getElementById('timestampResult');
  if (!ts) { result.textContent = '请输入时间戳'; return; }
  ts = parseInt(ts);
  if (ts < 1e12) ts *= 1000;
  const d = new Date(ts);
  result.textContent = `本地时间: ${d.toLocaleString('zh-CN')}\nISO 格式: ${d.toISOString()}\nUTC 时间: ${d.toUTCString()}`;
}

function dateToTimestamp() {
  const input = document.getElementById('dateInput').value;
  const result = document.getElementById('dateResult');
  if (!input) { result.textContent = '请选择日期'; return; }
  const d = new Date(input);
  result.textContent = `秒级时间戳: ${Math.floor(d.getTime() / 1000)}\n毫秒时间戳: ${d.getTime()}`;
}

// ============================================================
// Regex Tool
// ============================================================
function testRegex() {
  const pattern = document.getElementById('regexPattern').value;
  const flags = document.getElementById('regexFlags').value;
  const text = document.getElementById('regexTestText').value;
  const result = document.getElementById('regexResult');
  if (!pattern) { result.textContent = '请输入正则表达式'; return; }
  try {
    const regex = new RegExp(pattern, flags);
    const matches = [];
    let m;
    if (flags.includes('g')) {
      while ((m = regex.exec(text)) !== null) {
        matches.push({ match: m[0], index: m.index, groups: m.slice(1) });
        if (m[0] === '') { regex.lastIndex++; }
      }
    } else {
      m = regex.exec(text);
      if (m) matches.push({ match: m[0], index: m.index, groups: m.slice(1) });
    }
    if (matches.length === 0) {
      result.textContent = '没有找到匹配';
    } else {
      let html = `找到 ${matches.length} 个匹配:\n\n`;
      matches.forEach((m, i) => {
        html += `#${i + 1}  "${m.match}"  (位置: ${m.index})`;
        if (m.groups.length) html += `  分组: [${m.groups.join(', ')}]`;
        html += '\n';
      });
      result.textContent = html;
    }
  } catch (e) {
    result.textContent = '正则表达式错误: ' + e.message;
  }
}

const regexPresets = [
  { name: '邮箱', pattern: '[\\w.-]+@[\\w.-]+\\.\\w+' },
  { name: '手机号', pattern: '1[3-9]\\d{9}' },
  { name: 'URL', pattern: 'https?://[\\w\\-._~:/?#\\[\\]@!$&\'()*+,;=]+' },
  { name: 'IP 地址', pattern: '\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}' },
  { name: '身份证', pattern: '\\d{17}[\\dXx]' },
  { name: '中文', pattern: '[\\u4e00-\\u9fa5]+' },
  { name: 'HTML 标签', pattern: '<[^>]+>' },
  { name: '日期 YYYY-MM-DD', pattern: '\\d{4}-\\d{2}-\\d{2}' },
  { name: '十六进制颜色', pattern: '#[0-9a-fA-F]{3,8}' },
];

const presetsContainer = document.getElementById('regexPresets');
regexPresets.forEach(p => {
  const btn = document.createElement('button');
  btn.className = 'regex-preset-btn';
  btn.textContent = p.name;
  btn.onclick = () => {
    document.getElementById('regexPattern').value = p.pattern;
    showToast(`已加载: ${p.name}`);
  };
  presetsContainer.appendChild(btn);
});

// ============================================================
// Diff Tool
// ============================================================
function computeDiff() {
  const oldText = document.getElementById('diffOld').value;
  const newText = document.getElementById('diffNew').value;
  const output = document.getElementById('diffOutput');
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');

  const lcs = longestCommonSubsequence(oldLines, newLines);
  const result = [];
  let oi = 0, ni = 0, li = 0;

  while (oi < oldLines.length || ni < newLines.length) {
    if (li < lcs.length && oi < oldLines.length && ni < newLines.length && oldLines[oi] === lcs[li] && newLines[ni] === lcs[li]) {
      result.push({ type: 'same', text: oldLines[oi] });
      oi++; ni++; li++;
    } else if (ni < newLines.length && (li >= lcs.length || newLines[ni] !== lcs[li])) {
      result.push({ type: 'add', text: newLines[ni] });
      ni++;
    } else if (oi < oldLines.length && (li >= lcs.length || oldLines[oi] !== lcs[li])) {
      result.push({ type: 'remove', text: oldLines[oi] });
      oi++;
    }
  }

  output.innerHTML = result.map(r => {
    const prefix = r.type === 'add' ? '+' : r.type === 'remove' ? '-' : ' ';
    const cls = r.type === 'add' ? 'diff-add' : r.type === 'remove' ? 'diff-remove' : 'diff-same';
    return `<div class="diff-line ${cls}">${escapeHTML(prefix + ' ' + r.text)}</div>`;
  }).join('');
}

function longestCommonSubsequence(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1] + 1 : Math.max(dp[i-1][j], dp[i][j-1]);
    }
  }
  const result = [];
  let i = m, j = n;
  while (i > 0 && j > 0) {
    if (a[i-1] === b[j-1]) { result.unshift(a[i-1]); i--; j--; }
    else if (dp[i-1][j] > dp[i][j-1]) { i--; }
    else { j--; }
  }
  return result;
}

function escapeHTML(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ============================================================
// Hash Tool
// ============================================================
async function generateHashes() {
  const input = document.getElementById('hashInput').value;
  const container = document.getElementById('hashResults');
  if (!input) { container.innerHTML = '<p>请输入文本</p>'; return; }

  const encoder = new TextEncoder();
  const data = encoder.encode(input);

  const algorithms = ['SHA-1', 'SHA-256', 'SHA-384', 'SHA-512'];
  let html = '';

  for (const algo of algorithms) {
    const hashBuffer = await crypto.subtle.digest(algo, data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    html += `<div class="hash-row" onclick="copyText('${hashHex}')"><span class="hash-label">${algo}</span><span class="hash-value">${hashHex}</span><small>点击复制</small></div>`;
  }

  container.innerHTML = html;
}

function generateUUID() {
  const uuid = crypto.randomUUID ? crypto.randomUUID() :
    'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  document.getElementById('uuidOutput').value = uuid;
}

function generateBatchUUID() {
  const count = parseInt(document.getElementById('uuidCount').value) || 5;
  const uuids = [];
  for (let i = 0; i < Math.min(count, 100); i++) {
    uuids.push(crypto.randomUUID ? crypto.randomUUID() :
      'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
      }));
  }
  document.getElementById('uuidBatchOutput').value = uuids.join('\n');
}

function generatePassword() {
  const upper = document.getElementById('pwdUpper').checked;
  const lower = document.getElementById('pwdLower').checked;
  const digit = document.getElementById('pwdDigit').checked;
  const special = document.getElementById('pwdSpecial').checked;
  const length = parseInt(document.getElementById('pwdLength').value) || 16;

  let chars = '';
  if (upper) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  if (lower) chars += 'abcdefghijklmnopqrstuvwxyz';
  if (digit) chars += '0123456789';
  if (special) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';
  if (!chars) { showToast('请至少选择一种字符类型'); return; }

  const array = new Uint32Array(length);
  crypto.getRandomValues(array);
  let pwd = '';
  for (let i = 0; i < length; i++) {
    pwd += chars[array[i] % chars.length];
  }
  document.getElementById('pwdOutput').value = pwd;
}

generateUUID();

// ============================================================
// CSS Tools
// ============================================================
function updateShadow() {
  const x = document.getElementById('shadowX').value;
  const y = document.getElementById('shadowY').value;
  const blur = document.getElementById('shadowBlur').value;
  const spread = document.getElementById('shadowSpread').value;
  const color = document.getElementById('shadowColor').value;
  const opacity = document.getElementById('shadowOpacity').value / 100;

  document.getElementById('shadowXVal').textContent = x;
  document.getElementById('shadowYVal').textContent = y;
  document.getElementById('shadowBlurVal').textContent = blur;
  document.getElementById('shadowSpreadVal').textContent = spread;
  document.getElementById('shadowOpacityVal').textContent = opacity.toFixed(2);

  const rgb = hexToRgb(color);
  const shadow = `${x}px ${y}px ${blur}px ${spread}px rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity})`;
  document.getElementById('shadowPreview').style.boxShadow = shadow;
  document.getElementById('shadowCode').textContent = `box-shadow: ${shadow};`;
}

function updateBorderRadius() {
  const tl = document.getElementById('brTL').value;
  const tr = document.getElementById('brTR').value;
  const br = document.getElementById('brBR').value;
  const bl = document.getElementById('brBL').value;

  document.getElementById('brTLVal').textContent = tl;
  document.getElementById('brTRVal').textContent = tr;
  document.getElementById('brBRVal').textContent = br;
  document.getElementById('brBLVal').textContent = bl;

  const radius = `${tl}px ${tr}px ${br}px ${bl}px`;
  document.getElementById('borderRadiusPreview').style.borderRadius = radius;
  document.getElementById('borderRadiusCode').textContent = `border-radius: ${radius};`;
}

function updateGradient() {
  const type = document.getElementById('gradientType').value;
  const angle = document.getElementById('gradientAngle').value;
  const c1 = document.getElementById('gradientColor1').value;
  const c2 = document.getElementById('gradientColor2').value;

  document.getElementById('gradientAngleVal').textContent = angle;

  let gradient;
  if (type === 'linear') {
    gradient = `linear-gradient(${angle}deg, ${c1}, ${c2})`;
  } else {
    gradient = `radial-gradient(circle, ${c1}, ${c2})`;
  }

  document.getElementById('gradientPreview').style.background = gradient;
  document.getElementById('gradientCode').textContent = `background: ${gradient};`;
}

updateShadow();
updateBorderRadius();
updateGradient();

// ============================================================
// Lorem Ipsum
// ============================================================
const loremZh = [
  '天地玄黄，宇宙洪荒。日月盈昃，辰宿列张。寒来暑往，秋收冬藏。闰馀成岁，律吕调阳。',
  '云腾致雨，露结为霜。金生丽水，玉出昆冈。剑号巨阙，珠称夜光。果珍李柰，菜重芥姜。',
  '海咸河淡，鳞潜羽翔。龙师火帝，鸟官人皇。始制文字，乃服衣裳。推位让国，有虞陶唐。',
  '前端开发是一项充满挑战和创造力的工作，它涉及到HTML、CSS和JavaScript等核心技术的运用。',
  '现代前端开发框架如React、Vue和Angular极大地提高了开发效率，使得构建复杂的用户界面变得更加简单。',
  '响应式设计是现代Web开发中不可或缺的一部分，它确保网站在各种设备上都能提供良好的用户体验。',
  '前端性能优化是一个持续的过程，包括代码分割、懒加载、缓存策略和资源压缩等多种技术手段。',
  '用户界面设计需要兼顾美观和可用性，良好的交互设计能够显著提升用户满意度和产品转化率。',
  'Web安全是前端开发中非常重要的一环，XSS防护、CSRF防御和内容安全策略都是必须考虑的因素。',
  '前端工程化包含了自动化构建、持续集成、代码规范检查和自动化测试等多个方面的内容。',
];

const loremEn = [
  'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
  'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.',
  'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.',
  'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
  'Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius dolor et augue.',
  'Praesent dapibus neque id cursus faucibus tortor neque egestas augue eu vulputate magna eros eu erat.',
  'Aliquam erat volutpat. Nam dui mi tincidunt quis accumsan porttitor facilisis luctus metus.',
  'Phasellus ultrices nulla quis nibh. Quisque a lectus. Donec consectetuer ligula vulputate sem tristique cursus.',
  'Nam nulla. Integer pede justo lacinia eget tincidunt eget tempus vel pede.',
  'Morbi luctus facilisis magna. Praesent molestie ipsum eget arcu dictum varius pretium.',
];

function generateLorem() {
  const type = document.getElementById('loremType').value;
  const count = parseInt(document.getElementById('loremCount').value) || 3;
  const lang = document.getElementById('loremLang').value;
  const source = lang === 'zh' ? loremZh : loremEn;

  let result = '';
  if (type === 'paragraph') {
    for (let i = 0; i < count; i++) {
      result += source[i % source.length] + '\n\n';
    }
  } else if (type === 'sentence') {
    for (let i = 0; i < count; i++) {
      const sentences = source[i % source.length].split(/[.。]/);
      result += sentences[0].trim() + (lang === 'zh' ? '。' : '.') + '\n';
    }
  } else {
    const words = source.join(lang === 'zh' ? '' : ' ').split(lang === 'zh' ? '' : /\s+/);
    result = words.slice(0, count).join(lang === 'zh' ? '' : ' ');
  }

  document.getElementById('loremOutput').value = result.trim();
}

// ============================================================
// Markdown Preview
// ============================================================
function renderMarkdown() {
  const input = document.getElementById('markdownInput').value;
  const preview = document.getElementById('markdownPreview');
  preview.innerHTML = simpleMarkdown(input);
}

function simpleMarkdown(md) {
  let html = md;
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />');
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/^---$/gm, '<hr>');
  html = html.replace(/^\- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  const lines = html.split('\n');
  const result = [];
  let inParagraph = false;
  for (const line of lines) {
    if (line.trim() === '') {
      if (inParagraph) { result.push('</p>'); inParagraph = false; }
    } else if (/^<(h[1-6]|pre|ul|ol|li|blockquote|hr|table|div)/.test(line.trim())) {
      if (inParagraph) { result.push('</p>'); inParagraph = false; }
      result.push(line);
    } else {
      if (!inParagraph) { result.push('<p>'); inParagraph = true; }
      result.push(line);
    }
  }
  if (inParagraph) result.push('</p>');
  return result.join('\n');
}

// ============================================================
// QR Code Generator (Canvas-based)
// ============================================================
function generateQRCode() {
  const text = document.getElementById('qrcodeInput').value.trim();
  const size = parseInt(document.getElementById('qrcodeSize').value);
  const fg = document.getElementById('qrcodeFg').value;
  const bg = document.getElementById('qrcodeBg').value;
  const output = document.getElementById('qrcodeOutput');

  if (!text) { showToast('请输入内容'); return; }

  const qr = generateQRMatrix(text);
  const moduleCount = qr.length;
  const cellSize = Math.floor(size / (moduleCount + 8));
  const realSize = cellSize * (moduleCount + 8);

  const canvas = document.createElement('canvas');
  canvas.width = realSize;
  canvas.height = realSize;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, realSize, realSize);

  ctx.fillStyle = fg;
  const offset = cellSize * 4;
  for (let row = 0; row < moduleCount; row++) {
    for (let col = 0; col < moduleCount; col++) {
      if (qr[row][col]) {
        ctx.fillRect(offset + col * cellSize, offset + row * cellSize, cellSize, cellSize);
      }
    }
  }

  output.innerHTML = '';
  output.appendChild(canvas);

  const downloadBtn = document.createElement('button');
  downloadBtn.className = 'btn btn-sm';
  downloadBtn.style.marginTop = '0.5rem';
  downloadBtn.textContent = '下载图片';
  downloadBtn.onclick = () => {
    const a = document.createElement('a');
    a.download = 'qrcode.png';
    a.href = canvas.toDataURL();
    a.click();
  };
  output.appendChild(document.createElement('br'));
  output.appendChild(downloadBtn);
}

function generateQRMatrix(text) {
  const data = new TextEncoder().encode(text);
  let version = 1;
  while (version <= 40) {
    const capacity = getQRCapacity(version);
    if (data.length <= capacity) break;
    version++;
  }
  if (version > 10) version = 10;

  const size = 17 + version * 4;
  const matrix = Array.from({ length: size }, () => new Array(size).fill(false));
  const reserved = Array.from({ length: size }, () => new Array(size).fill(false));

  addFinderPattern(matrix, reserved, 0, 0);
  addFinderPattern(matrix, reserved, size - 7, 0);
  addFinderPattern(matrix, reserved, 0, size - 7);

  for (let i = 0; i < size; i++) {
    if (!reserved[6][i]) { matrix[6][i] = i % 2 === 0; reserved[6][i] = true; }
    if (!reserved[i][6]) { matrix[i][6] = i % 2 === 0; reserved[i][6] = true; }
  }

  if (version >= 2) {
    const positions = getAlignmentPositions(version);
    for (const r of positions) {
      for (const c of positions) {
        if (reserved[r] && reserved[r][c]) continue;
        addAlignmentPattern(matrix, reserved, r, c, size);
      }
    }
  }

  reserveFormatInfo(reserved, size);

  const bits = encodeData(data, version);
  placeData(matrix, reserved, bits, size);

  applyMask(matrix, reserved, size);

  return matrix;
}

function getQRCapacity(version) {
  const capacities = [0, 17, 32, 53, 78, 106, 134, 154, 192, 230, 271];
  return capacities[version] || 271;
}

function addFinderPattern(matrix, reserved, row, col) {
  for (let r = -1; r <= 7; r++) {
    for (let c = -1; c <= 7; c++) {
      const mr = row + r, mc = col + c;
      if (mr < 0 || mr >= matrix.length || mc < 0 || mc >= matrix.length) continue;
      const isOuter = r === -1 || r === 7 || c === -1 || c === 7;
      const isBorder = r === 0 || r === 6 || c === 0 || c === 6;
      const isInner = r >= 2 && r <= 4 && c >= 2 && c <= 4;
      matrix[mr][mc] = !isOuter && (isBorder || isInner);
      reserved[mr][mc] = true;
    }
  }
}

function addAlignmentPattern(matrix, reserved, row, col, size) {
  if (row < 0 || row >= size || col < 0 || col >= size) return;
  for (let r = -2; r <= 2; r++) {
    for (let c = -2; c <= 2; c++) {
      const mr = row + r, mc = col + c;
      if (mr < 0 || mr >= size || mc < 0 || mc >= size) continue;
      if (reserved[mr][mc]) return;
    }
  }
  for (let r = -2; r <= 2; r++) {
    for (let c = -2; c <= 2; c++) {
      const mr = row + r, mc = col + c;
      if (mr < 0 || mr >= size || mc < 0 || mc >= size) continue;
      matrix[mr][mc] = Math.abs(r) === 2 || Math.abs(c) === 2 || (r === 0 && c === 0);
      reserved[mr][mc] = true;
    }
  }
}

function getAlignmentPositions(version) {
  const table = {
    2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
    7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]
  };
  return table[version] || [6, 18];
}

function reserveFormatInfo(reserved, size) {
  for (let i = 0; i < 8; i++) {
    if (i < size) reserved[8][i] = true;
    if (i < size) reserved[i][8] = true;
  }
  reserved[8][8] = true;
  for (let i = 0; i < 8; i++) {
    if (size - 1 - i >= 0) reserved[8][size - 1 - i] = true;
    if (size - 1 - i >= 0) reserved[size - 1 - i][8] = true;
  }
}

function encodeData(data, version) {
  const bits = [];
  bits.push(0, 1, 0, 0);
  const lenBits = version <= 1 ? 8 : 16;
  for (let i = lenBits - 1; i >= 0; i--) {
    bits.push((data.length >> i) & 1);
  }
  for (const byte of data) {
    for (let i = 7; i >= 0; i--) {
      bits.push((byte >> i) & 1);
    }
  }
  const totalBits = getQRCapacity(version) * 8 + 100;
  while (bits.length < totalBits) {
    bits.push(0);
  }
  return bits;
}

function placeData(matrix, reserved, bits, size) {
  let bitIndex = 0;
  let upward = true;
  for (let col = size - 1; col >= 0; col -= 2) {
    if (col === 6) col = 5;
    const rows = upward ? Array.from({ length: size }, (_, i) => size - 1 - i) : Array.from({ length: size }, (_, i) => i);
    for (const row of rows) {
      for (let c = 0; c < 2; c++) {
        const cc = col - c;
        if (cc < 0 || reserved[row][cc]) continue;
        matrix[row][cc] = bitIndex < bits.length ? bits[bitIndex] === 1 : false;
        bitIndex++;
      }
    }
    upward = !upward;
  }
}

function applyMask(matrix, reserved, size) {
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      if (reserved[row][col]) continue;
      if ((row + col) % 2 === 0) {
        matrix[row][col] = !matrix[row][col];
      }
    }
  }
}

// Initialize
generatePassword();
