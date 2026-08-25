/**
 * CAU360 MASTER SUITE V11.0 CONTROLLER
 * Tình báo 24/7, Điểm Nóng 24h Đa Chiều Chuyên Sâu Đối Đầu Việt - Trung, Bảng giá đa vùng, Máy tính Mẻ sấy
 */
let currentView = 'VN';
let cachedData = null;
let currentUser = null;
let allAdminUsers = [];

// ==========================================
// 1. HỆ THỐNG XÁC THỰC & BẢO MẬT ĐĂNG NHẬP
// ==========================================
function checkAuthStatus() {
  const savedUser = localStorage.getItem('cau360_user');
  if (savedUser) {
    try {
      currentUser = JSON.parse(savedUser);
      
      if (currentUser.is_expired && currentUser.role !== 'ADMIN') {
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('main-app').style.display = 'none';
        document.getElementById('expired-screen').style.display = 'flex';
        document.getElementById('expired-text').innerText = 
          `Tài khoản '${currentUser.username}' của bạn đã hết hạn gói cước vào ngày ${currentUser.expires_at_formatted}. Vui lòng liên hệ Admin để gia hạn tiếp tục sử dụng.`;
        return;
      }

      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('expired-screen').style.display = 'none';
      document.getElementById('main-app').style.display = 'block';
      
      const expText = currentUser.role === 'ADMIN' ? 'Vĩnh Viễn' : `Hạn: ${currentUser.expires_at_formatted}`;
      document.getElementById('user-display-badge').innerText = `👤 ${currentUser.display_name} (${expText})`;

      const alertBanner = document.getElementById('expiration-alert-banner');
      if (currentUser.is_expiring_soon && currentUser.role !== 'ADMIN') {
        alertBanner.style.display = 'block';
        document.getElementById('banner-days-left').innerText = currentUser.days_remaining;
        document.getElementById('banner-exp-date').innerText = currentUser.expires_at_formatted;
      } else {
        alertBanner.style.display = 'none';
      }

      if (currentUser.role === 'ADMIN') {
        document.getElementById('btn-tab-admin-users').style.display = 'inline-block';
        loadAdminDashboard();
      } else {
        document.getElementById('btn-tab-admin-users').style.display = 'none';
      }

      loadData();
      runCustomProfitCalc();
      runPassportCalc();
      return;
    } catch (e) {}
  }
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('expired-screen').style.display = 'none';
  document.getElementById('main-app').style.display = 'none';
}

async function performLogin() {
  const uInput = document.getElementById('login-username').value.trim();
  const pInput = document.getElementById('login-password').value.trim();
  const errBox = document.getElementById('login-error-msg');
  const btn = document.getElementById('btn-submit-login');

  if (!uInput || !pInput) {
    errBox.style.display = 'block';
    errBox.innerText = 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!';
    return;
  }

  btn.innerText = '⏳ Đang đăng nhập...';
  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: uInput, password: pInput })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      btn.innerText = '✔ Đăng nhập thành công!';
      localStorage.setItem('cau360_user', JSON.stringify(data.user));
      setTimeout(() => {
        checkAuthStatus();
      }, 200);
    } else {
      btn.innerText = 'ĐĂNG NHẬP VÀO HỆ THỐNG';
      errBox.style.display = 'block';
      errBox.innerText = data.detail || 'Sai tên đăng nhập hoặc mật khẩu!';
    }
  } catch (err) {
    btn.innerText = 'ĐĂNG NHẬP VÀO HỆ THỐNG';
    errBox.style.display = 'block';
    errBox.innerText = 'Lỗi kết nối máy chủ! Vui lòng thử lại sau vài giây.';
  }
}

function performLogout() {
  localStorage.removeItem('cau360_user');
  window.location.reload();
}

// ==========================================
// 2. ADMIN SAAS SUBSCRIPTION MANAGEMENT
// ==========================================
function toggleCustomDaysInput() {
  const plan = document.getElementById('new-user-plan').value;
  document.getElementById('wrap-custom-days').style.display = plan === 'CUSTOM' ? 'block' : 'none';
}

async function loadAdminDashboard() {
  try {
    const res = await fetch('/api/v1/admin/subscription-dashboard');
    const data = await res.json();

    document.getElementById('stat-total-users').innerText = data.total_users;
    document.getElementById('stat-active-users').innerText = data.active_users;
    document.getElementById('stat-expiring-soon').innerText = data.expiring_soon_count;
    document.getElementById('stat-expired').innerText = data.expired_count;
    document.getElementById('stat-total-revenue').innerText = `${data.total_revenue_vnd.toLocaleString()} VND`;

    allAdminUsers = data.users || [];
    renderUsersList(allAdminUsers);
  } catch (err) {
    console.error('Admin dashboard error:', err);
  }
}

function filterUsersList() {
  const q = (document.getElementById('user-search-box').value || '').trim().toLowerCase();
  if (!q) {
    renderUsersList(allAdminUsers);
    return;
  }
  const filtered = allAdminUsers.filter(u => 
    (u.username && u.username.toLowerCase().includes(q)) || 
    (u.display_name && u.display_name.toLowerCase().includes(q)) ||
    (u.phone && u.phone.includes(q))
  );
  renderUsersList(filtered);
}

function renderUsersList(users) {
  const container = document.getElementById('admin-users-list-container');
  container.innerHTML = '';

  if (!users || users.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:12px; padding:10px;">Không tìm thấy hội viên nào phù hợp.</div>';
    return;
  }

  users.forEach(u => {
    const badgeColor = u.status_color === 'green' ? 'var(--green)' : (u.status_color === 'yellow' ? 'var(--yellow)' : (u.status_color === 'red' ? 'var(--red)' : '#64748b'));
    const badgeBg = u.status_color === 'green' ? 'rgba(16,185,129,0.15)' : (u.status_color === 'yellow' ? 'rgba(245,158,11,0.2)' : 'rgba(239,68,68,0.2)');

    container.innerHTML += `
      <div style="background:rgba(0,0,0,0.35); border:1px solid var(--border); border-radius:8px; padding:10px; margin-bottom:8px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
          <div>
            <strong style="font-size:14px; color:var(--blue);">${u.username}</strong>
            <span style="font-size:12px; color:#fff;"> - ${u.display_name}</span><br>
            <span style="font-size:11px; color:var(--text-muted);">Đã nạp: <strong>${(u.plan_price_vnd||0).toLocaleString()} đ</strong> | Hạn: <strong style="color:#fff;">${u.expires_at_formatted}</strong></span>
          </div>
          <span class="logo-badge" style="background:${badgeBg}; color:${badgeColor}; font-size:10px; border:1px solid ${badgeColor};">
            ${u.status_label}
          </span>
        </div>

        <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;">
          <button onclick="openRenewModal('${u.id}', '${u.username}')" style="background:var(--green); color:#fff; border:none; padding:5px 9px; border-radius:5px; font-size:11px; font-weight:700; cursor:pointer;">
            ⚡ Gia Hạn
          </button>
          <button onclick="adminResetPassword('${u.id}', '${u.username}')" style="background:#2563eb; color:#fff; border:none; padding:5px 9px; border-radius:5px; font-size:11px; font-weight:700; cursor:pointer;">
            🔑 Reset Pass
          </button>
          ${u.role !== 'ADMIN' ? `
            <button onclick="adminToggleUserStatus('${u.id}')" style="background:${u.is_active === 1 ? '#eab308' : '#10b981'}; color:#000; border:none; padding:5px 9px; border-radius:5px; font-size:11px; font-weight:700; cursor:pointer;">
              ${u.is_active === 1 ? '🔒 Khóa' : '🔓 Mở'}
            </button>
            <button onclick="adminDeleteUser('${u.id}', '${u.username}')" style="background:#ef4444; color:#fff; border:none; padding:5px 9px; border-radius:5px; font-size:11px; font-weight:700; cursor:pointer;">
              🗑️ Xóa
            </button>
          ` : ''}
        </div>
      </div>
    `;
  });
}

async function adminDeleteUser(userId, username) {
  if (!confirm(`⚠️ CẢNH BÁO: Bạn có chắc chắn muốn XÓA VĨNH VIỄN tài khoản '${username}' không?`)) {
    return;
  }

  try {
    const res = await fetch('/api/v1/admin/users/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      alert(`✔ ${data.message}`);
      loadAdminDashboard();
    } else {
      alert(data.detail || 'Lỗi xóa tài khoản!');
    }
  } catch (err) {
    alert('Lỗi kết nối máy chủ!');
  }
}

async function adminCreateUserWithPlan() {
  const u = document.getElementById('new-user-username').value.trim();
  const p = document.getElementById('new-user-password').value.trim();
  const plan = document.getElementById('new-user-plan').value;
  const customDays = parseInt(document.getElementById('new-user-custom-days').value) || 30;
  const price = parseFloat(document.getElementById('new-user-price').value) || 0;
  const msgBox = document.getElementById('admin-user-msg');

  if (!u || !p) {
    alert('Vui lòng nhập Tên đăng nhập và Mật khẩu ban đầu!');
    return;
  }

  try {
    const res = await fetch('/api/v1/admin/users/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: u, password: p, display_name: `Hội Viên (${u})`, phone: '',
        role: 'SUBSCRIBER', plan_type: plan, custom_days: customDays, price_vnd: price
      })
    });
    const data = await res.json();
    msgBox.style.display = 'block';
    if (res.ok && data.success) {
      msgBox.style.background = 'rgba(16,185,129,0.2)';
      msgBox.style.border = '1px solid var(--green)';
      msgBox.style.color = '#a7f3d0';
      msgBox.innerText = `✔ ${data.message}`;
      document.getElementById('new-user-username').value = '';
      document.getElementById('new-user-password').value = '';
      loadAdminDashboard();
    } else {
      msgBox.style.background = 'rgba(239,68,68,0.2)';
      msgBox.style.border = '1px solid var(--red)';
      msgBox.style.color = '#fca5a5';
      msgBox.innerText = data.detail || 'Lỗi tạo tài khoản!';
    }
  } catch (err) {
    alert('Lỗi kết nối máy chủ!');
  }
}

function openRenewModal(userId, username) {
  document.getElementById('renew-target-user-id').value = userId;
  document.getElementById('renew-modal-title').innerText = `GIA HẠN GÓI CƯỚC — ${username.toUpperCase()}`;
  document.getElementById('renew-modal').style.display = 'flex';
}

function closeRenewModal() {
  document.getElementById('renew-modal').style.display = 'none';
}

async function confirmRenewSubscription() {
  const userId = document.getElementById('renew-target-user-id').value;
  const plan = document.getElementById('renew-plan-type').value;
  const amount = parseFloat(document.getElementById('renew-amount-paid').value) || 0;

  try {
    const res = await fetch('/api/v1/admin/users/renew', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, plan_type: plan, amount_paid: amount })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      alert(data.message);
      closeRenewModal();
      loadAdminDashboard();
    } else {
      alert(data.detail || 'Lỗi gia hạn!');
    }
  } catch (err) {
    alert('Lỗi kết nối máy chủ!');
  }
}

async function adminResetPassword(userId, username) {
  const newPass = prompt(`Nhập mật khẩu mới cho người dùng '${username}':`, '123456');
  if (!newPass || !newPass.trim()) return;

  try {
    const res = await fetch('/api/v1/admin/users/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, new_password: newPass.trim() })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      alert(`✔ Đã đặt lại mật khẩu cho '${username}' thành: ${newPass}`);
    } else {
      alert(data.detail || 'Lỗi reset mật khẩu!');
    }
  } catch (err) {
    alert('Lỗi kết nối!');
  }
}

async function adminToggleUserStatus(userId) {
  if (!confirm('Bạn có chắc chắn muốn thay đổi trạng thái Khóa / Mở Khóa tài khoản này?')) return;
  try {
    const res = await fetch('/api/v1/admin/users/toggle-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      alert(data.message);
      loadAdminDashboard();
    } else {
      alert(data.detail || 'Lỗi!');
    }
  } catch (err) {
    alert('Lỗi kết nối!');
  }
}

// ==========================================
// 3. TỰ ĐỘNG CẬP NHẬT 1-CHẠM (PWA AUTO-UPDATER)
// ==========================================
async function forceAppUpdate() {
  const btn = document.getElementById('btn-update-app');
  btn.innerText = '⏳ Đang xóa cache...';
  try {
    if ('serviceWorker' in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (let reg of registrations) await reg.unregister();
    }
    if ('caches' in window) {
      const keys = await caches.keys();
      for (let key of keys) await caches.delete(key);
    }
    btn.innerText = '✔ Xong! Đang tải lại...';
    setTimeout(() => {
      window.location.href = window.location.pathname + '?v=' + new Date().getTime();
    }, 400);
  } catch (err) {
    window.location.reload();
  }
}

function switchTab(tabId) {
  document.querySelectorAll('.tabs-nav .tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  
  const targetContent = document.getElementById(tabId);
  if (targetContent) targetContent.classList.add('active');
  
  // Highlight active nav button
  const targetBtn = document.querySelector(`.tabs-nav .tab-btn[onclick*="${tabId}"]`);
  if (targetBtn) targetBtn.classList.add('active');
  
  if (tabId === 'tab-charts') renderCharts();
  if (tabId === 'tab-hotspot') loadHotspot24h();
  if (tabId === 'tab-xinhua') loadXinhua3YearSuite();
}

function toggleRegionView(region) {
  currentView = region;
  document.getElementById('btn-show-vn').classList.toggle('active', region === 'VN');
  document.getElementById('btn-show-cn').classList.toggle('active', region === 'CN');
  renderRegions();
}

// ==========================================
// 4. ĐIỂM NÓNG 24H: BÁO CÁO TÌNH BÁO CHUYÊN SÂU
// ==========================================
async function loadHotspot24h() {
  try {
    const res = await fetch('/api/v1/intelligence/hotspot-24h');
    const data = await res.json();
    
    // 0. Render Mạng lưới 12 nguồn độc lập
    if (data.audit_sources_12_registry) {
      const srcGrid = document.getElementById('hotspot-12-sources-grid');
      if (srcGrid) {
        srcGrid.innerHTML = '';
        data.audit_sources_12_registry.forEach(s => {
          const tierColor = s.tier.includes('CẤP A') ? 'var(--green)' : (s.tier.includes('CẤP B') ? 'var(--blue)' : 'var(--orange)');
          srcGrid.innerHTML += `
            <div style="background:rgba(0,0,0,0.3); border-left:2px solid ${tierColor}; padding:6px 8px; border-radius:4px;">
              <div style="display:flex; justify-content:space-between; font-weight:700;">
                <span style="color:#fff;">${s.name}</span>
                <span style="color:${tierColor}; font-size:9px;">${s.tier.split(' ')[0]}</span>
              </div>
              <div style="color:var(--text-muted); font-size:9px; margin-top:2px;">${s.role} (${s.frequency})</div>
            </div>
          `;
        });
      }
    }

    // 1. Render Báo cáo Chuyên gia Việt Nam
    const vn = data.vietnam_report;
    if (vn) {
      document.getElementById('hotspot-vn-time').innerText = vn.publish_time;
      document.getElementById('hotspot-vn-title').innerText = vn.title;
      document.getElementById('hotspot-vn-summary').innerText = vn.executive_summary;

      const indContainer = document.getElementById('hotspot-vn-indicators');
      indContainer.innerHTML = '';
      vn.deep_analysis_sections.forEach(sec => {
        indContainer.innerHTML += `
          <div style="background:rgba(0,0,0,0.35); padding:10px; border-radius:8px; margin-bottom:8px; line-height:1.6;">
            <strong style="color:var(--green); font-size:12px;">${sec.heading}</strong><br>
            <span style="color:#e2e8f0; font-size:11px;">${sec.content.replace(/\n/g, '<br>')}</span>
          </div>
        `;
      });

      const fc = vn.forecast_3_to_10_days;
      document.getElementById('hotspot-vn-forecast-header').innerText = `🎯 ${fc.horizon.toUpperCase()}`;
      document.getElementById('hotspot-vn-forecast-body').innerHTML = `
        <div style="font-size:13px; font-weight:700; color:#fff; margin-bottom:6px;">
          • Quỹ đạo phân vị: <strong style="color:var(--yellow);">${fc.p10_p50_p90}</strong> (${fc.trend_direction})
        </div>
        <div style="background:rgba(0,0,0,0.25); padding:8px; border-radius:6px; margin-bottom:6px;">
          <strong style="color:var(--blue);">Căn cứ động lực:</strong><br>
          ${fc.core_drivers.replace(/\n/g, '<br>')}
        </div>
        <div style="color:var(--green); font-weight:700; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin-bottom:6px;">
          ${fc.tactical_orders.replace(/\n/g, '<br>')}
        </div>
        <div style="color:#f87171; font-size:10px;">
          ⚠️ <strong>Điều kiện làm sai dự báo:</strong> ${fc.invalidation_criteria}
        </div>
      `;
    }

    // 2. Render Báo cáo Mật Chuyên gia Trung Quốc
    const cn = data.china_report;
    if (cn) {
      document.getElementById('hotspot-cn-time').innerText = cn.publish_time;
      document.getElementById('hotspot-cn-title').innerText = cn.title;
      document.getElementById('hotspot-cn-summary').innerText = cn.executive_summary;

      const insContainer = document.getElementById('hotspot-cn-insights');
      insContainer.innerHTML = '';
      cn.hunan_factory_economics.forEach(ins => {
        insContainer.innerHTML += `
          <div style="margin-bottom:6px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
            • <strong style="color:var(--orange);">${ins.name}:</strong> <span style="color:#fff;">${ins.detail}</span>
          </div>
        `;
      });

      const tacContainer = document.getElementById('hotspot-cn-tactics');
      tacContainer.innerHTML = '';
      cn.trader_manipulation_playbook.forEach(t => {
        tacContainer.innerHTML += `
          <div style="margin-bottom:6px;">
            <strong style="color:#fca5a5;">${t.tactic}:</strong> <span style="color:#cbd5e1;">${t.mechanism}</span>
          </div>
        `;
      });

      const cnFc = cn.china_forecast_3_to_10_days;
      document.getElementById('hotspot-cn-verdict').innerHTML = `
        • <strong>Diễn biến cau tươi Hải Nam:</strong> <span style="color:#fff; font-weight:700;">${cnFc.hainan_fresh_outlook}</span><br>
        • <strong>Chỉ số áp lực nhập khẩu:</strong> <strong style="color:var(--red);">${cnFc.import_pressure_index}</strong><br>
        <div style="background:rgba(0,0,0,0.25); padding:8px; border-radius:6px; margin-top:6px; color:#fff;">
          👉 <em>"${cnFc.strategic_verdict}"</em>
        </div>
      `;
    }
  } catch (err) {
    console.error('Error loading hotspot briefing:', err);
  }
}

// ==========================================
// 5. MÁY TÍNH LỢI NHUẬN MẺ SẤY TÙY CHỈNH (TAB 6)
// ==========================================
function setRatioPreset(ratio) {
  document.getElementById('calc-ratio').value = ratio;
  runCustomProfitCalc();
}

async function runCustomProfitCalc() {
  const freshPrice = parseFloat(document.getElementById('calc-fresh-price').value) || 20000;
  const dryPrice = parseFloat(document.getElementById('calc-dry-price').value) || 192500;
  const ratio = parseFloat(document.getElementById('calc-ratio').value) || 6.0;
  const batchWeight = parseFloat(document.getElementById('calc-batch-weight').value) || 10000;
  const fuelCost = parseFloat(document.getElementById('calc-fuel-cost').value) || 12000;
  const laborCost = parseFloat(document.getElementById('calc-labor-cost').value) || 500;
  const wasteRate = (parseFloat(document.getElementById('calc-waste-rate').value) || 4) / 100.0;

  const isBunch = document.getElementById('raw-type-bunch') ? document.getElementById('raw-type-bunch').checked : true;
  const rawType = isBunch ? 'BUNCH' : 'FRUIT';

  try {
    const chinaWholesale = parseFloat(document.getElementById('calc-china-wholesale') ? document.getElementById('calc-china-wholesale').value : 102) || 102.0;

    const res = await fetch('/api/v1/tactics/custom-batch-profit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fresh_price: freshPrice,
        dry_selling_price: dryPrice,
        fresh_to_dry_ratio: ratio,
        batch_weight_kg: batchWeight,
        raw_type: rawType,
        stem_tare_pct: parseFloat(document.getElementById('calc-stem-tare') ? document.getElementById('calc-stem-tare').value : 20) || 20.0,
        fuel_cost_per_kg_dry: fuelCost,
        labor_fresh_per_kg: laborCost,
        packaging_per_kg_dry: 1200,
        waste_rate: wasteRate,
        china_wholesale_cny_jin: chinaWholesale
      })
    });
    const data = await res.json();
    const out = document.getElementById('calculator-result-box');

    const statusColor = data.status === 'GOOD_PROFIT' ? 'var(--green)' : (data.status === 'LOSS' ? 'var(--red)' : 'var(--yellow)');
    const statusBg = data.status === 'GOOD_PROFIT' ? 'rgba(16,185,129,0.1)' : (data.status === 'LOSS' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.1)');

    out.innerHTML = `
      <div class="result-box" style="border-left:4px solid ${statusColor}; background:${statusBg}; padding:14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <strong style="font-size:13px; color:${statusColor};">${data.verdict}</strong>
          <span class="logo-badge" style="background:${statusColor}; font-size:11px;">${data.financial_summary.profit_margin_pct}% LÃI</span>
        </div>
        ${data.decision_advice ? `
          <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); padding:8px 10px; border-radius:6px; font-size:11px; color:#f1f5f9; margin-bottom:8px;">
            💡 <strong>Quyết sách lò:</strong> ${data.decision_advice}
          </div>
        ` : ''}

        <div style="background:rgba(0,0,0,0.3); padding:10px; border-radius:8px; margin-bottom:8px; font-size:12px; line-height:1.7;">
          • Mẻ tươi <strong>${batchWeight.toLocaleString()} kg</strong> (Tỷ lệ <strong>${ratio}:1</strong>) ──► Thu được: <strong style="color:#fff; font-size:14px;">${data.production_output.commercial_dry_weight_kg.toLocaleString()} kg khô</strong><br>
          • Giá thành sản xuất $1kg$ khô: <strong style="color:var(--orange); font-size:14px;">${data.production_output.true_cost_per_kg_dry.toLocaleString()} đ/kg</strong><br>
          • Tiền Lãi / Lỗ trên $1kg$ khô: <strong style="color:${statusColor}; font-size:15px;">${data.financial_summary.profit_per_kg_dry_vnd > 0 ? '+' : ''}${data.financial_summary.profit_per_kg_dry_vnd.toLocaleString()} đ/kg</strong><br>
          • <span style="font-size:13px; font-weight:700;">TỔNG LÃI RÒNG CẢ MẺ SẤY:</span> <strong style="color:${statusColor}; font-size:18px;">${data.financial_summary.total_net_profit_vnd > 0 ? '+' : ''}${data.financial_summary.total_net_profit_vnd.toLocaleString()} VND</strong>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:11px; color:var(--text-muted); background:rgba(0,0,0,0.2); padding:8px; border-radius:6px; margin-bottom:8px;">
          <div>Tổng chi phí mẻ: <strong>${data.financial_summary.total_production_cost_vnd.toLocaleString()} đ</strong></div>
          <div>Tổng doanh thu bán: <strong>${data.financial_summary.total_revenue_vnd.toLocaleString()} đ</strong></div>
          <div>Điểm hòa vốn giá khô: <strong style="color:var(--yellow);">${data.break_even.break_even_dry_price_vnd.toLocaleString()} đ/kg</strong></div>
          <div>Giá tươi mua tối đa: <strong style="color:var(--blue);">${data.break_even.break_even_fresh_price_vnd.toLocaleString()} đ/kg</strong></div>
        </div>

        ${data.reverse_netback_china ? `
          <div style="background:rgba(37,99,235,0.12); border:1px solid rgba(37,99,235,0.3); padding:10px; border-radius:6px; font-size:11px; line-height:1.6;">
            <strong style="color:var(--blue); font-size:12px;">🇨🇳 BÓC TRẦN ĐỊNH GIÁ NGƯỢC THƯỢNG NGUỒN ĐẠI LỤC:</strong><br>
            • Giá sỉ hạt khô đại lục quy đổi: <strong style="color:#fff;">${data.reverse_netback_china.china_wholesale_cny_jin} CNY/jin</strong> ≈ <strong style="color:var(--green);">${data.reverse_netback_china.china_wholesale_vnd_kg.toLocaleString()} đ/kg</strong> (Tỷ giá VCB: ${data.reverse_netback_china.fx_rate_applied.toLocaleString()} đ)<br>
            • Tổng biên mậu dịch chuỗi (Lò sấy ──► Bán buôn TQ): <strong style="color:var(--yellow); font-size:13px;">+${data.reverse_netback_china.macro_trade_spread_per_kg.toLocaleString()} đ/kg khô</strong><br>
            • <span style="color:var(--text-muted);">Ý nghĩa: Thương lái trung gian còn dư địa chênh lệch khổng lồ, bạn hoàn toàn tự tin giữ vững giá chào bán tại kho!</span>
          </div>
        ` : ''}
      </div>
    `;
  } catch (err) {}
}

// ==========================================
// 6. BIỂU ĐỒ & DÒNG TIN TÌNH BÁO 24H
// ==========================================
async function renderCharts() {
  try {
    const resVn = await fetch('/api/v1/charts/vietnam');
    const dataVn = await resVn.json();
    document.getElementById('vn-chart-time').innerText = `Cập nhật: ${dataVn.last_updated}`;
    drawCanvasChart('canvas-vn-chart', dataVn.history_7d.map(d => ({ label: d.date, val: d.p50 / 1000 })), 'VND/kg (nghìn đ)', '#10b981');

    const resCn = await fetch('/api/v1/charts/china');
    const dataCn = await resCn.json();
    document.getElementById('cn-chart-time').innerText = `Cập nhật: ${dataCn.last_updated}`;
    drawCanvasChart('canvas-cn-chart', dataCn.history_7d.map(d => ({ label: d.date, val: d.cny_per_jin })), 'CNY/jin (500g)', '#f97316');
  } catch (err) {}
}

function drawCanvasChart(canvasId, points, unitLabel, strokeColor) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.lineWidth = 1;
  for (let y = 30; y < h - 30; y += 35) {
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(w - 20, y);
    ctx.stroke();
  }

  if (!points || points.length === 0) return;
  const vals = points.map(p => p.val);
  const minVal = Math.min(...vals) * 0.98;
  const maxVal = Math.max(...vals) * 1.02;
  const valRange = maxVal - minVal || 1;

  const paddingLeft = 45;
  const paddingBottom = 35;
  const paddingTop = 25;
  const plotW = w - paddingLeft - 20;
  const plotH = h - paddingTop - paddingBottom;
  const stepX = plotW / (points.length - 1);

  const grad = ctx.createLinearGradient(0, paddingTop, 0, h - paddingBottom);
  grad.addColorStop(0, strokeColor === '#10b981' ? 'rgba(16, 185, 129, 0.35)' : 'rgba(249, 115, 22, 0.35)');
  grad.addColorStop(1, 'rgba(0, 0, 0, 0.0)');

  ctx.beginPath();
  points.forEach((p, i) => {
    const x = paddingLeft + i * stepX;
    const y = paddingTop + plotH - ((p.val - minVal) / valRange) * plotH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.lineTo(paddingLeft + (points.length - 1) * stepX, h - paddingBottom);
  ctx.lineTo(paddingLeft, h - paddingBottom);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.beginPath();
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 3;
  points.forEach((p, i) => {
    const x = paddingLeft + i * stepX;
    const y = paddingTop + plotH - ((p.val - minVal) / valRange) * plotH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  points.forEach((p, i) => {
    const x = paddingLeft + i * stepX;
    const y = paddingTop + plotH - ((p.val - minVal) / valRange) * plotH;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(p.val.toString(), x, y - 8);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px sans-serif';
    ctx.fillText(p.label.split(' ')[0], x, h - 12);
  });
}

// ==========================================
// 7. HỘ CHIẾU & ĐA VÙNG
// ==========================================
function updateSliders(source) {
  const sLong = document.getElementById('slider-long');
  const sRound = document.getElementById('slider-round');
  const sBroken = document.getElementById('slider-broken');
  let valLong = parseInt(sLong.value);
  let valRound = parseInt(sRound.value);
  
  if (valLong + valRound > 100) {
    if (source === 'long') valRound = 100 - valLong;
    else valLong = 100 - valRound;
  }
  const valBroken = 100 - valLong - valRound;
  sLong.value = valLong;
  sRound.value = valRound;
  sBroken.value = valBroken;
  document.getElementById('label-long').innerText = valLong + '%';
  document.getElementById('label-round').innerText = valRound + '%';
  document.getElementById('label-broken').innerText = valBroken + '%';
  runPassportCalc();
}

async function runPassportCalc() {
  const weight = parseFloat(document.getElementById('lot-weight').value) || 10000;
  const pLong = parseInt(document.getElementById('slider-long').value) / 100.0;
  const pRound = parseInt(document.getElementById('slider-round').value) / 100.0;
  const pBroken = parseInt(document.getElementById('slider-broken').value) / 100.0;
  const lowball = parseFloat(document.getElementById('trader-offer').value) || 165000;

  try {
    const res = await fetch('/api/v1/tactics/passport', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lot_id: 'LOT_VN_001', total_kg: weight, p_long: pLong, p_round: pRound, p_broken: pBroken, price_long: 200000, price_round: 175000, price_broken: 90000, lowball_offer: lowball })
    });
    const data = await res.json();
    const out = document.getElementById('passport-output');

    out.innerHTML = `
      <div class="result-box" style="border-left-color:var(--blue);">
        <strong style="color:var(--blue); font-size:13px;">${data.quality_passport_title}</strong><br>
        • Giá trị thực được thẩm định: <strong style="font-size:15px; color:#fff;">${data.true_weighted_price_vnd_kg.toLocaleString()} đ/kg</strong><br>
        • Tổng giá trị lô hàng: <strong>${(data.true_weighted_price_vnd_kg * weight).toLocaleString()} VND</strong><br>
        • Số tiền bảo vệ không bị ép mất: <strong style="color:var(--green);">+${data.loss_prevented_vnd.toLocaleString()} VND</strong><br>
        <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:6px; margin-top:6px;">
          <em>"${data.official_counter_statement}"</em>
        </div>
      </div>
    `;
  } catch (err) {}
}

async function loadData() {
  try {
    const res = await fetch('/api/v1/market/multi-region');
    const data = await res.json();
    cachedData = data;

    if (data.fx_snapshot) {
      document.getElementById('fx-sell').innerText = data.fx_snapshot.sell.toLocaleString('vi-VN');
      document.getElementById('fx-buy').innerText = data.fx_snapshot.transfer_buy.toLocaleString('vi-VN');
      document.getElementById('fx-time').innerText = `Cập nhật: ${data.fx_snapshot.source_time}`;
    }

    renderRegions();
    renderCharts();
    loadIntelligence24h();
    loadHotspot24h();
  } catch (err) {}
}

async function loadIntelligence24h() {
  try {
    const res = await fetch('/api/v1/intelligence/live-24h');
    const data = await res.json();

    if (data.timeline_events) {
      const timeContainer = document.getElementById('timeline-container');
      timeContainer.innerHTML = '';
      data.timeline_events.forEach(e => {
        const impactColor = e.impact === 'POSITIVE' || e.impact === 'VERY_POSITIVE' ? 'var(--green)' : (e.impact === 'DANGER' ? 'var(--red)' : 'var(--blue)');
        timeContainer.innerHTML += `
          <div class="card" style="padding:12px; margin-bottom:8px; border-left:3px solid ${impactColor};">
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; margin-bottom:4px;">
              <span style="color:var(--text-muted); font-weight:700;">⏱️ ${e.time}</span>
              <span class="logo-badge" style="background:rgba(255,255,255,0.1); color:#fff; font-size:9px;">${e.tag}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div style="font-size:13px; font-weight:700; color:#fff; margin-bottom:4px;">${e.is_user_posted ? '🔥 ' : ''}${e.title}</div>
              ${e.is_user_posted && currentUser && currentUser.role === 'ADMIN' ? `<button onclick="adminDeleteNewsItem('${e.id}')" style="background:#ef4444; color:#fff; border:none; padding:2px 6px; border-radius:4px; font-size:10px; cursor:pointer;">🗑️ Xóa</button>` : ''}
            </div>
            <div style="font-size:11px; color:var(--text-muted); line-height:1.5; margin-bottom:6px;">${e.content}</div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px; color:var(--blue); margin-bottom:6px;">
              <span>🔗 Nguồn: <a href="${e.source_url}" target="_blank" style="color:var(--blue); text-decoration:underline;">${e.source_name}</a></span>
              <span style="color:var(--green);">✔ Đã xác thực</span>
            </div>
            <div style="font-size:11px; color:${impactColor}; font-weight:600; background:rgba(0,0,0,0.25); padding:6px; border-radius:6px;">
              👉 Hành động: ${e.action}
            </div>
          </div>
        `;
      });
    }
  } catch (err) {}
}

function renderRegions() {
  if (!cachedData) return;
  const container = document.getElementById('regions-container');
  container.innerHTML = '';

  if (currentView === 'VN') {
    cachedData.vietnam_provinces.forEach(r => {
      container.innerHTML += `
        <div class="card">
          <div class="region-header">
            <span class="region-name">${r.name}</span>
            <span class="region-role">${r.role}</span>
          </div>
          <div class="price-display">${r.dry_p50.toLocaleString()} <span style="font-size:13px; color:var(--text-muted);">VND/kg khô (P50)</span></div>
          <div class="sub-grid">
            <div><span style="color:var(--text-muted);">Thấp (P20):</span> <strong>${r.dry_p20.toLocaleString()}</strong></div>
            <div><span style="color:var(--text-muted);">Đồng thuận:</span> <strong style="color:var(--green);">${r.dry_p50.toLocaleString()}</strong></div>
            <div><span style="color:var(--text-muted);">Cao (P80):</span> <strong>${r.dry_p80.toLocaleString()}</strong></div>
          </div>
          
          <div style="background:rgba(0,0,0,0.3); padding:10px; border-radius:8px; margin:6px 0; font-size:11px; line-height:1.6;">
            ${r.fresh_bunch_high > 0 ? `
              • 🌿 <strong>Cau Cành (Nguyên buồng):</strong> <strong style="color:var(--orange);">${r.fresh_bunch_low.toLocaleString()} - ${r.fresh_bunch_high.toLocaleString()} đ/kg</strong> (Hao cành: ${r.stem_tare_pct}% | Công vặt: ${r.destem_labor_cost} đ)<br>
              • 🍈 <strong>Cau Trái (Lặt rời):</strong> <strong style="color:var(--yellow);">${r.fresh_fruit_low.toLocaleString()} - ${r.fresh_fruit_high.toLocaleString()} đ/kg</strong><br>
              • 🎯 <strong>Trần an toàn lò sấy:</strong> Cau cành <strong style="color:var(--green);">≤ ${r.safe_ceiling_bunch.toLocaleString()} đ</strong> | Cau trái <strong style="color:var(--blue);">≤ ${r.safe_ceiling_fruit.toLocaleString()} đ</strong><br>
            ` : `
              • 🏛️ <strong>Cửa khẩu xuất khẩu chính ngạch:</strong> Thông quan 28 container/ngày<br>
            `}
            • Đặc tính: <span style="color:var(--text-muted);">${r.characteristics}</span>
          </div>

          <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted); margin-top:4px;">
            <span style="color:var(--blue); font-weight:700;">${r.status}</span>
            <span>📅 Cập nhật: ${cachedData.fx_snapshot ? cachedData.fx_snapshot.source_time.split(' ')[0] : 'Live'}</span>
          </div>
        </div>
      `;
    });
  } else {
    cachedData.china_regions.forEach(r => {
      container.innerHTML += `
        <div class="card">
          <div class="region-header">
            <span class="region-name">${r.name} (${r.province})</span>
            <span class="region-role">${r.role}</span>
          </div>
          ${r.fresh_cny_p50 ? `
            <div class="price-display" style="color:var(--orange);">
              ${r.fresh_cny_p50.toFixed(1)} <span style="font-size:13px; color:var(--text-muted);">CNY/jin (500g) ≈ <strong style="color:#fff;">${r.vnd_equivalent_kg.toLocaleString()}</strong> VND/kg</span>
            </div>
            <div class="sub-grid">
              <div><span style="color:var(--text-muted);">Biên độ tệ:</span> <strong>${r.fresh_cny_p20} - ${r.fresh_cny_p80}</strong></div>
              <div><span style="color:var(--text-muted);">Thời tiết WSSI:</span> <strong style="color:var(--orange);">${r.wssi}/100</strong></div>
              <div><span style="color:var(--text-muted);">Thu hoạch:</span> <strong>${r.harvestability}%</strong></div>
            </div>
            <div style="font-size:11px; color:var(--text-muted); margin:4px 0;">
              • Đặc tính: ${r.characteristics}
            </div>
          ` : `
            <div style="font-size:13px; color:var(--blue); font-weight:700; margin:6px 0;">
              🏭 Công suất đại xưởng: ${r.factory_utilization} (${r.active_buyers} đầu nậu đang gom)
            </div>
            <div style="font-size:11px; color:var(--text-muted); margin:4px 0;">
              • Quy mô: ${r.characteristics}
            </div>
          `}
          <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted); margin-top:4px;">
            <span>Trạng thái: <strong style="color:${r.fresh_cny_p50 ? 'var(--orange)' : 'var(--green)'};">${r.status}</strong></span>
            <span>📅 ${cachedData.fx_snapshot ? cachedData.fx_snapshot.source_time.split(' ')[0] : 'Live'}</span>
          </div>
        </div>
      `;
    });
  }
}

// ==========================================
// 8. ADMIN CỔNG ĐĂNG TIN NÓNG THỰC ĐỊA 24H
// ==========================================
async function adminPostBreakingNews() {
  const title = document.getElementById('news-title').value.trim();
  const content = document.getElementById('news-content').value.trim();
  const tag = document.getElementById('news-tag').value.trim() || 'TRINH SÁT CỬA KHẨU';
  const impact = document.getElementById('news-impact').value;
  const action = document.getElementById('news-action').value.trim();
  const msgBox = document.getElementById('admin-news-msg');

  if (!title || !content) {
    alert('Vui lòng nhập Tiêu đề và Nội dung bản tin nóng!');
    return;
  }

  try {
    const res = await fetch('/api/v1/intelligence/post-news', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title, content: content, tag: tag, category: 'FIELD',
        impact: impact, source_name: 'Chủ Lò / Trinh Sát Cửa Khẩu', source_url: '', action: action
      })
    });
    const data = await res.json();
    msgBox.style.display = 'block';
    if (res.ok && data.success) {
      msgBox.style.background = 'rgba(16,185,129,0.2)';
      msgBox.style.border = '1px solid var(--green)';
      msgBox.style.color = '#a7f3d0';
      msgBox.innerText = '✔ Đã phát bản tin nóng lên Tình Báo 24h thành công!';
      document.getElementById('news-title').value = '';
      document.getElementById('news-content').value = '';
      loadIntelligence24h();
    } else {
      msgBox.style.background = 'rgba(239,68,68,0.2)';
      msgBox.style.border = '1px solid var(--red)';
      msgBox.style.color = '#fca5a5';
      msgBox.innerText = data.detail || 'Lỗi đăng tin!';
    }
  } catch (err) {
    alert('Lỗi kết nối máy chủ!');
  }
}

async function adminDeleteNewsItem(newsId) {
  if (!confirm('Bạn có chắc muốn xóa bản tin này khỏi Tình Báo 24h?')) return;
  try {
    const res = await fetch(`/api/v1/intelligence/news/${newsId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok && data.success) {
      alert('✔ Đã xóa bản tin!');
      loadIntelligence24h();
    }
  } catch (err) {
    alert('Lỗi xóa tin!');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  checkAuthStatus();
});

// ==========================================
// 9. DYNAMIC CROP-CYCLE PRESETS & STEM TARE
// ==========================================
function toggleRawTypeUI() {
  const isBunch = document.getElementById('raw-type-bunch').checked;
  document.getElementById('wrap-season-stage').style.display = isBunch ? 'block' : 'none';
  runCustomProfitCalc();
}

function setSeasonPreset(tare, ratio) {
  document.getElementById('calc-stem-tare').value = tare;
  document.getElementById('calc-ratio').value = ratio;
  runCustomProfitCalc();
}

// ==========================================
// 10. QUICK FX CONVERTER & MOISTURE GUARD
// ==========================================
function quickConvertCNY() {
  const val = parseFloat(document.getElementById('quick-cny-input').value) || 0;
  const rate = (cachedData && cachedData.fx_snapshot) ? cachedData.fx_snapshot.sell : 3948.53;
  const vnd = val * rate;
  document.getElementById('quick-cny-output').innerText = `${vnd.toLocaleString()} đ`;
}

async function runMoistureCheck() {
  const moisture = parseFloat(document.getElementById('moisture-input').value) || 10.5;
  const hours = parseInt(document.getElementById('drying-hours-input').value) || 48;
  const out = document.getElementById('moisture-guard-result');

  try {
    const res = await fetch('/api/v1/tactics/moisture-guard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ core_moisture_pct: moisture, kiln_drying_hours: hours, transport_days: 4, packaging_type: 'PE_DOUBLE_LINED' })
    });
    const data = await res.json();
    const statusColor = data.risk_color === 'green' ? 'var(--green)' : (data.risk_color === 'yellow' ? 'var(--yellow)' : 'var(--red)');
    const statusBg = data.risk_color === 'green' ? 'rgba(16,185,129,0.1)' : (data.risk_color === 'yellow' ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.2)');

    out.innerHTML = `
      <div style="background:${statusBg}; border-left:3px solid ${statusColor}; padding:10px; border-radius:6px; font-size:11px; line-height:1.6;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <strong style="color:${statusColor}; font-size:12px;">${data.risk_level}</strong>
          <span style="color:#fff;">Độ ẩm: <strong>${data.core_moisture_pct}%</strong></span>
        </div>
        <div style="color:#e2e8f0; margin-bottom:6px;">${data.recommendation}</div>
        <div style="border-top:1px solid rgba(255,255,255,0.08); padding-top:6px; font-size:10px; color:var(--text-muted);">
          <strong>Quy chuẩn đóng cont 40ft:</strong> Lót giấy Kraft 5 mặt + Treo 8-10 túi hút ẩm Dry Pole 1kg.
        </div>
      </div>
    `;
  } catch (err) {}
}

// Gọi runMoistureCheck khi load app
const prevCheckAuth = checkAuthStatus;
checkAuthStatus = function() {
  prevCheckAuth();
  runMoistureCheck();
};


// ==========================================
// 13. INDEPENDENT 3-YEAR XINHUA CHARTS & DAILY BRIEFING SUITE
// ==========================================
let currentXinhuaYear = 2026;
let currentXinhua2026Mode = 'daily';
let xinhuaCachedData = null;

async function loadXinhua3YearSuite() {
  try {
    if (!xinhuaCachedData) {
      const res = await fetch('/api/v1/charts/xinhua-index-3years');
      xinhuaCachedData = await res.json();
    }
    renderCurrentXinhuaView();
  } catch (err) {
    console.error("Error loading Xinhua 3Y Suite:", err);
  }
}

function switchXinhuaYear(year) {
  currentXinhuaYear = year;
  ['2026', '2025', '2024'].forEach(y => {
    const wrap = document.getElementById(`wrap-xh-${y}`);
    if (wrap) wrap.style.display = (y === String(year)) ? 'block' : 'none';
    const btn = document.getElementById(`btn-xh-${y}`);
    if (btn) {
      if (y === String(year)) btn.classList.add('active'); else btn.classList.remove('active');
    }
  });
  renderCurrentXinhuaView();
}

function switchXinhua2026Mode(mode) {
  currentXinhua2026Mode = mode;
  const btnD = document.getElementById('btn-xh-mode-daily');
  const btnM = document.getElementById('btn-xh-mode-monthly');
  if (btnD) btnD.classList.toggle('active', mode === 'daily');
  if (btnM) btnM.classList.toggle('active', mode === 'monthly');
  renderCurrentXinhuaView();
}

function renderCurrentXinhuaView() {
  if (!xinhuaCachedData) return;
  
  if (currentXinhuaYear === 2026) renderXinhua2026();
  else if (currentXinhuaYear === 2025) renderXinhua2025();
  else if (currentXinhuaYear === 2024) renderXinhua2024();

  // Render Daily Deep Institutional Dossier
  const r = xinhuaCachedData.daily_xinhua_report;
  const reportDiv = document.getElementById('wrap-xh-daily-report');
  if (r && reportDiv) {
    let sectionsHtml = '';
    if (r.sections) {
      r.sections.forEach(s => {
        sectionsHtml += `
          <div style="background:rgba(0,0,0,0.25); border-left:3px solid var(--blue); padding:10px; border-radius:6px; margin-bottom:8px; font-size:11px; line-height:1.6;">
            <strong style="color:var(--yellow); font-size:12px;">${s.heading}</strong>
            <div style="color:#e2e8f0; margin-top:4px; white-space:pre-line;">${s.content}</div>
          </div>
        `;
      });
    }

    reportDiv.innerHTML = `
      <div style="background:rgba(0,0,0,0.35); border:1px solid var(--blue); padding:14px; border-radius:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <strong style="color:var(--blue); font-size:13px;">📰 ${r.title}</strong>
          <span style="font-size:10px; color:var(--text-muted);">${r.publish_time}</span>
        </div>

        <div style="display:flex; gap:8px; margin-bottom:10px; flex-wrap:wrap;">
          <span style="background:rgba(16,185,129,0.2); color:var(--green); border:1px solid var(--green); padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;">
            Điểm số hôm nay: ${r.current_score.toFixed(2)}
          </span>
          <span style="background:rgba(245,158,11,0.2); color:var(--yellow); border:1px solid var(--yellow); padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;">
            Biến động phiên: ${r.today_change}
          </span>
          <span style="background:rgba(59,130,246,0.2); color:#93c5fd; border:1px solid #3b82f6; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;">
            So với 2025: ${r.yoy_change}
          </span>
        </div>

        ${sectionsHtml}

        <div style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.4); padding:12px; border-radius:6px; margin-top:10px; font-size:11px; line-height:1.6;">
          <strong style="color:var(--green); font-size:12px;">🔮 ${r.forecast_7_days_ahead.horizon}:</strong><br>
          • <strong>Quỹ đạo điểm số 7 ngày tới:</strong> <span style="color:#fff; font-weight:800;">${r.forecast_7_days_ahead.projected_range}</span><br>
          • <strong>Kỳ vọng giá tươi Hải Nam:</strong> <span style="color:var(--orange); font-weight:700;">${r.forecast_7_days_ahead.hainan_fresh_expected}</span><br>
          • <strong>Tác động giá cau khô xuất khẩu VN:</strong> <span style="color:var(--yellow); font-weight:700;">${r.forecast_7_days_ahead.vietnam_dry_price_impact}</span><br>
          • <strong>Chỉ thị tác chiến chủ lò sấy:</strong> <span style="color:#10b981; font-weight:800;">${r.forecast_7_days_ahead.tactical_directive}</span>
        </div>
      </div>
    `;
  }
}

function renderXinhua2026() {
  const d = xinhuaCachedData.data_2026;
  const canvas = document.getElementById('canvas-xinhua-2026');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.parentElement.clientWidth || 600;
  canvas.width = w;
  canvas.height = 250;
  const h = 250;
  ctx.clearRect(0, 0, w, h);

  const padLeft = 45, padRight = 35, padTop = 35, padBottom = 35;
  const chartW = w - padLeft - padRight, chartH = h - padTop - padBottom;

  if (currentXinhua2026Mode === 'daily') {
    const points = d.daily_august;
    const vals = points.map(p => p.index);
    const minVal = Math.min(...vals) - 3;
    const maxVal = Math.max(...vals) + 4;
    const totalPoints = points.length;

    // Grid & Y-Axis
    ctx.strokeStyle = 'rgba(255,255,255,0.08)';
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    const stepY = (maxVal - minVal) / 4;
    for (let i = 0; i <= 4; i++) {
      const v = minVal + i * stepY;
      const y = padTop + chartH - (i / 4) * chartH;
      ctx.beginPath(); ctx.moveTo(padLeft, y); ctx.lineTo(w - padRight, y); ctx.stroke();
      ctx.fillText(v.toFixed(0), padLeft - 6, y + 3);
    }

    // X Axis - Smart Spacing to Prevent Collisions
    ctx.textAlign = 'center';
    const stepX = chartW / (totalPoints - 1);
    points.forEach((p, i) => {
      const x = padLeft + i * stepX;
      const distFromEnd = totalPoints - 1 - i;
      // Draw label if last point OR if far enough from last point and on step
      if (distFromEnd === 0 || (distFromEnd >= 2 && i % 2 === 0)) {
        ctx.fillStyle = distFromEnd === 0 ? '#facc15' : '#94a3b8';
        ctx.font = distFromEnd === 0 ? 'bold 10px sans-serif' : '9px sans-serif';
        ctx.fillText(p.date, x, h - 12);
      }
    });

    // Gradient fill
    const grad = ctx.createLinearGradient(0, padTop, 0, h - padBottom);
    grad.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0.0)');

    ctx.beginPath();
    points.forEach((p, i) => {
      const x = padLeft + i * stepX;
      const y = padTop + chartH - ((p.index - minVal) / (maxVal - minVal)) * chartH;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.lineTo(padLeft + (totalPoints - 1) * stepX, h - padBottom);
    ctx.lineTo(padLeft, h - padBottom);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 3;
    ctx.beginPath();
    points.forEach((p, i) => {
      const x = padLeft + i * stepX;
      const y = padTop + chartH - ((p.index - minVal) / (maxVal - minVal)) * chartH;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Points & Value Labels - Anti-Collision
    points.forEach((p, i) => {
      const x = padLeft + i * stepX;
      const y = padTop + chartH - ((p.index - minVal) / (maxVal - minVal)) * chartH;
      const isLast = (i === totalPoints - 1);
      const distFromEnd = totalPoints - 1 - i;

      // Draw point dot
      ctx.fillStyle = isLast ? '#facc15' : '#10b981';
      ctx.beginPath(); ctx.arc(x, y, isLast ? 5.5 : 4, 0, Math.PI * 2); ctx.fill();
      if (isLast) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Draw value text without overlapping:
      // Last point always shows; intermediate points show only if distance >= 2
      if (isLast) {
        ctx.fillStyle = '#facc15';
        ctx.font = 'bold 11px sans-serif';
        ctx.fillText(p.index.toFixed(1), x, y - 10);
      } else if (distFromEnd >= 2 && (i % 3 === 0 || i === 0)) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '9px sans-serif';
        ctx.fillText(p.index.toFixed(1), x, y - 8);
      }
    });

    const latestPoint = points[points.length - 1];
    const todayVnd = (latestPoint.cny_per_jin * 2 * 3948.53).toLocaleString('vi-VN', {maximumFractionDigits:0});
    document.getElementById('wrap-xh-2026-detail').innerHTML = `
      <strong style="color:#10b981;">⏱️ BẢNG BIẾN ĐỘNG THEO NGÀY THÁNG 8/2026 (LIVE TỪNG PHIÊN):</strong><br>
      • Điểm số hôm nay (${latestPoint.date}): <strong style="color:#facc15; font-size:14px;">${latestPoint.index.toFixed(2)} điểm</strong> (Giá tươi Vạn Ninh: ${latestPoint.cny_per_jin} CNY/jin ≈ ${todayVnd} đ/kg).<br>
      • Đà tăng liên tục trong tháng 8: Từ 278.0đ ngày 01/08 ──► ${latestPoint.index.toFixed(1)}đ hôm nay (+${(latestPoint.index - 278.0).toFixed(1)} điểm do mưa bão & dịch vàng lá).<br>
      • Ý nghĩa lò sấy: Bảo chứng mức giá sàn cau khô VN vững ở 192.500 đ/kg không bị lung lay!
    `;
  } else {
    const months = d.months;
    const actual = d.monthly_actual;
    const minVal = 120, maxVal = 320;

    // Grid
    ctx.strokeStyle = 'rgba(255,255,255,0.08)';
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    for (let v = 150; v <= 300; v += 50) {
      const y = padTop + chartH - ((v - minVal) / (maxVal - minVal)) * chartH;
      ctx.beginPath(); ctx.moveTo(padLeft, y); ctx.lineTo(w - padRight, y); ctx.stroke();
      ctx.fillText(v, padLeft - 6, y + 3);
    }

    ctx.textAlign = 'center';
    const stepX = chartW / (months.length - 1);
    months.forEach((m, i) => {
      const x = padLeft + i * stepX;
      ctx.fillText(m, x, h - 12);
    });

    // Draw Line
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 3;
    ctx.beginPath();
    actual.forEach((val, i) => {
      const x = padLeft + i * stepX;
      const y = padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();

    actual.forEach((val, i) => {
      const x = padLeft + i * stepX;
      const y = padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
      ctx.fillStyle = i === actual.length - 1 ? '#facc15' : '#10b981';
      ctx.beginPath(); ctx.arc(x, y, 4.5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 9px sans-serif';
      ctx.fillText(val.toFixed(1), x, y - 8);
    });

    document.getElementById('wrap-xh-2026-detail').innerHTML = `
      <strong style="color:#10b981;">📅 DIỄN BIẾN 12 THÁNG NĂM 2026:</strong><br>
      • T1 (145.0đ) ──► T4 (210.4đ) ──► T8 Hiện tại (295.4đ).<br>
      • Dự báo 4 tháng kẹo Tết cuối năm (T9-T12): Dự kiến tiếp tục neo đỉnh 310 - 325 điểm do kho lạnh Hồ Nam cạn kiệt!
    `;
  }
}

function renderXinhua2025() {
  const d = xinhuaCachedData.data_2025;
  const canvas = document.getElementById('canvas-xinhua-2025');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.parentElement.clientWidth || 600;
  canvas.width = w;
  canvas.height = 240;
  const h = 240;
  ctx.clearRect(0, 0, w, h);

  const padLeft = 45, padRight = 25, padTop = 30, padBottom = 35;
  const chartW = w - padLeft - padRight, chartH = h - padTop - padBottom;
  const minVal = 80, maxVal = 250;

  ctx.strokeStyle = 'rgba(255,255,255,0.08)';
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'right';
  for (let v = 100; v <= 220; v += 40) {
    const y = padTop + chartH - ((v - minVal) / (maxVal - minVal)) * chartH;
    ctx.beginPath(); ctx.moveTo(padLeft, y); ctx.lineTo(w - padRight, y); ctx.stroke();
    ctx.fillText(v, padLeft - 6, y + 3);
  }

  ctx.textAlign = 'center';
  const stepX = chartW / (d.months.length - 1);
  d.months.forEach((m, i) => {
    const x = padLeft + i * stepX;
    ctx.fillText(m, x, h - 12);
  });

  // Red line
  ctx.strokeStyle = '#ef4444';
  ctx.lineWidth = 3;
  ctx.beginPath();
  d.values.forEach((val, i) => {
    const x = padLeft + i * stepX;
    const y = padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();

  d.values.forEach((val, i) => {
    const x = padLeft + i * stepX;
    const y = padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    ctx.fillStyle = '#ef4444';
    ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
    if (i % 2 === 0 || i === d.values.length - 1) {
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 9px sans-serif';
      ctx.fillText(val.toFixed(1), x, y - 8);
    }
  });

  document.getElementById('wrap-xh-2025-detail').innerHTML = `
    <strong style="color:#ef4444;">📉 BÓC TÁCH NĂM 2025 (NĂM SẬP GIÁ ĐỔ ĐÈO):</strong><br>
    • Đầu năm T1 (225đ) ──► T7 (138.5đ) ──► Đáy T11 (110.5đ) giảm gần 50%.<br>
    • Nguyên nhân: Hải Nam được mùa, thương lái kén chọn quả tròn, dừng gom ồ ạt khiến cau khô VN rớt từ 200k về 80k-100k (các lò sấy mua tươi 80k bị vỡ nợ nặng nề).
  `;
}

function renderXinhua2024() {
  const d = xinhuaCachedData.data_2024;
  const canvas = document.getElementById('canvas-xinhua-2024');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.parentElement.clientWidth || 600;
  canvas.width = w;
  canvas.height = 240;
  const h = 240;
  ctx.clearRect(0, 0, w, h);

  const padLeft = 45, padRight = 25, padTop = 30, padBottom = 35;
  const chartW = w - padLeft - padRight, chartH = h - padTop - padBottom;
  const minVal = 280, maxVal = 560;

  ctx.strokeStyle = 'rgba(255,255,255,0.08)';
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'right';
  for (let v = 300; v <= 500; v += 100) {
    const y = padTop + chartH - ((v - minVal) / (maxVal - minVal)) * chartH;
    ctx.beginPath(); ctx.moveTo(padLeft, y); ctx.lineTo(w - padRight, y); ctx.stroke();
    ctx.fillText(v, padLeft - 6, y + 3);
  }

  ctx.textAlign = 'center';
  const stepX = chartW / (d.months.length - 1);
  d.months.forEach((m, i) => {
    const x = padLeft + i * stepX;
    ctx.fillText(m, x, h - 12);
  });

  // Yellow Line
  ctx.strokeStyle = '#facc15';
  ctx.lineWidth = 3;
  ctx.beginPath();
  d.values.forEach((val, i) => {
    const x = padLeft + i * stepX;
    const y = padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();

  d.values.forEach((val, i) => {
    const x = padLeft + i * stepX;
    const y = padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    ctx.fillStyle = '#facc15';
    ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
    if (i % 2 === 0 || i === d.values.length - 1) {
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 9px sans-serif';
      ctx.fillText(val.toFixed(1), x, y - 8);
    }
  });

  document.getElementById('wrap-xh-2024-detail').innerHTML = `
    <strong style="color:#facc15;">🔥 BÓC TÁCH NĂM 2024 (NĂM SỐT GIÁ KỶ LỤC LỊCH SỬ):</strong><br>
    • T1 (320đ) ──► Lên đỉnh T8 (525.0đ) ──► T12 (350đ).<br>
    • Nguyên nhân: Kho lạnh Hồ Nam cạn kiệt, các đại xưởng tranh mua điên cuồng đẩy giá cau khô VN đạt đỉnh kỷ lục 450.000 - 500.000 đ/kg.
  `;
}
