let autoScrollEnabled = true;
let methodsData = { layer7: [], layer4: [], amplification: [], socks_types: [] };

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initTabs();
  fetchMethods();
  fetchFilesInfo();
  initStatsPolling();
  initAttacksPolling();
  initLogStream();
  initEventListeners();
});

function initTheme() {
  const savedTheme = localStorage.getItem("mhddos_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeButton(savedTheme);
}

function updateThemeButton(theme) {
  const themeLabel = document.getElementById("themeLabel");
  const themeIcon = document.getElementById("themeIcon");
  if (!themeLabel || !themeIcon) return;

  if (theme === "dark") {
    themeLabel.textContent = "Tema Claro";
    themeIcon.innerHTML = `
      <circle cx="12" cy="12" r="5"></circle>
      <line x1="12" y1="1" x2="12" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="23"></line>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
      <line x1="1" y1="12" x2="3" y2="12"></line>
      <line x1="21" y1="12" x2="23" y2="12"></line>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    `;
  } else {
    themeLabel.textContent = "Tema Escuro";
    themeIcon.innerHTML = `
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    `;
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const target = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", target);
  localStorage.setItem("mhddos_theme", target);
  updateThemeButton(target);
}

function initTabs() {
  const buttons = document.querySelectorAll(".nav-item");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

  const targetBtn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const targetPane = document.getElementById(`tab-${tabId}`);

  if (targetBtn && targetPane) {
    targetBtn.classList.add("active");
    targetPane.classList.add("active");

    const titles = {
      dashboard: ["Painel Geral", "Métricas do sistema e visão integrada do MHDDoS"],
      launcher: ["Execução de Métodos", "Configuração de operações Layer 4 e Layer 7"],
      "active-attacks": ["Tarefas Ativas", "Monitoramento e controle de instâncias em execução"],
      tools: ["Ferramentas de Rede", "Testes de conectividade, resolução e diagnósticos"],
      console: ["Terminal de Logs", "Visualização em tempo real das mensagens e eventos"]
    };

    const info = titles[tabId] || ["MHDDoS", "Painel de Controle"];
    document.getElementById("pageTitle").textContent = info[0];
    document.getElementById("pageSubtitle").textContent = info[1];
  }
}

function fetchMethods() {
  fetch("/api/methods")
    .then((res) => res.json())
    .then((data) => {
      methodsData = data;
      renderMethodsOptions("L7");
      renderSocksOptions(data.socks_types);
    })
    .catch((err) => console.error(err));
}

function renderMethodsOptions(layer) {
  const select = document.getElementById("methodSelect");
  if (!select) return;
  select.innerHTML = "";

  const list = layer === "L7" ? methodsData.layer7 : [...methodsData.layer4, ...methodsData.amplification];
  list.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    select.appendChild(opt);
  });

  updateFormVisibility();
}

function renderSocksOptions(types) {
  const select = document.getElementById("socksTypeSelect");
  if (!select || !types) return;
  select.innerHTML = "";
  types.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = t.id;
    opt.textContent = t.name;
    select.appendChild(opt);
  });
}

function updateFormVisibility() {
  const layer = document.getElementById("layerSelect").value;
  const method = document.getElementById("methodSelect").value;
  const targetLabel = document.getElementById("targetLabel");
  const targetInput = document.getElementById("targetInput");
  const socksGroup = document.getElementById("socksGroup");
  const proxyFileGroup = document.getElementById("proxyFileGroup");
  const rpcGroup = document.getElementById("rpcGroup");
  const reflectorGroup = document.getElementById("reflectorGroup");

  const isAmp = methodsData.amplification && methodsData.amplification.includes(method);

  if (layer === "L7") {
    targetLabel.textContent = "Alvo (URL com http/https)";
    targetInput.placeholder = "https://example.com";
    socksGroup.style.display = "flex";
    proxyFileGroup.style.display = "flex";
    rpcGroup.style.display = "flex";
    reflectorGroup.style.display = "none";
  } else {
    targetLabel.textContent = "Alvo (IP:Porta)";
    targetInput.placeholder = "1.1.1.1:80";
    rpcGroup.style.display = "none";

    if (isAmp) {
      reflectorGroup.style.display = "flex";
      socksGroup.style.display = "none";
      proxyFileGroup.style.display = "none";
    } else {
      reflectorGroup.style.display = "none";
      socksGroup.style.display = "flex";
      proxyFileGroup.style.display = "flex";
    }
  }
}

function initStatsPolling() {
  const updateStats = () => {
    fetch("/api/system/stats")
      .then((res) => res.json())
      .then((data) => {
        document.getElementById("cpuStat").textContent = `${data.cpu_percent}%`;
        document.getElementById("cpuBar").style.width = `${data.cpu_percent}%`;

        document.getElementById("ramStat").textContent = `${data.ram_percent}%`;
        document.getElementById("ramBar").style.width = `${data.ram_percent}%`;
        document.getElementById("ramDetail").textContent = `${data.ram_used_gb} GB / ${data.ram_total_gb} GB`;

        const sentMB = (data.bytes_sent / (1024 * 1024)).toFixed(1);
        document.getElementById("netSentStat").textContent = `${sentMB} MB`;
        document.getElementById("packetsSentStat").textContent = `${data.packets_sent.toLocaleString()} pacotes`;

        document.getElementById("activeAttacksStat").textContent = data.active_attacks;
      })
      .catch((err) => console.error(err));
  };

  updateStats();
  setInterval(updateStats, 2000);
}

function fetchFilesInfo() {
  fetch("/api/files/info")
    .then((res) => res.json())
    .then((data) => {
      document.getElementById("uaCount").textContent = data.useragents_count.toLocaleString();
      document.getElementById("refCount").textContent = data.referers_count.toLocaleString();
      document.getElementById("proxyFilesCount").textContent = data.proxy_files.length;
    })
    .catch((err) => console.error(err));
}

function initAttacksPolling() {
  const updateAttacks = () => {
    fetch("/api/attacks/active")
      .then((res) => res.json())
      .then((data) => {
        renderAttacksTable(data);
      })
      .catch((err) => console.error(err));
  };

  updateAttacks();
  setInterval(updateAttacks, 3000);
}

function renderAttacksTable(attacks) {
  const tbody = document.getElementById("activeAttacksTableBody");
  if (!tbody) return;

  if (!attacks || attacks.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 24px;">Nenhuma tarefa ativa no momento.</td></tr>`;
    return;
  }

  tbody.innerHTML = "";
  attacks.forEach((a) => {
    const tr = document.createElement("tr");

    let badgeClass = "badge-running";
    if (a.status === "STOPPED") badgeClass = "badge-stopped";
    if (a.status === "FINISHED") badgeClass = "badge-finished";

    tr.innerHTML = `
      <td><strong>${a.id}</strong></td>
      <td>${a.pid}</td>
      <td>${a.layer}</td>
      <td>${a.method}</td>
      <td>${a.target}</td>
      <td>${a.threads}</td>
      <td>${a.start_time}</td>
      <td>${a.elapsed}s / ${a.duration}s</td>
      <td><span class="badge ${badgeClass}">${a.status}</span></td>
      <td>
        ${
          a.status === "RUNNING"
            ? `<button class="btn btn-danger-sm" onclick="stopAttack('${a.id}')">Parar</button>`
            : `<span style="color: var(--text-muted);">-</span>`
        }
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function stopAttack(id) {
  fetch("/api/attacks/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: id })
  })
    .then((res) => res.json())
    .then(() => {
      initAttacksPolling();
    })
    .catch((err) => console.error(err));
}

function initLogStream() {
  const evtSource = new EventSource("/api/logs/stream");
  const fullTerminal = document.getElementById("fullTerminalBody");
  const quickLog = document.getElementById("dashboardQuickLog");

  evtSource.onmessage = (e) => {
    try {
      const entry = JSON.parse(e.data);
      appendLogLine(fullTerminal, entry);
      appendLogLine(quickLog, entry);

      if (autoScrollEnabled && fullTerminal) {
        fullTerminal.scrollTop = fullTerminal.scrollHeight;
      }
      if (quickLog) {
        quickLog.scrollTop = quickLog.scrollHeight;
      }
    } catch (err) {
      console.error(err);
    }
  };
}

function appendLogLine(container, entry) {
  if (!container) return;
  const div = document.createElement("div");
  div.className = "terminal-line";
  div.innerHTML = `
    <span class="terminal-time">[${entry.time}]</span>
    <span class="terminal-text">${escapeHtml(entry.text)}</span>
  `;
  container.appendChild(div);

  while (container.childNodes.length > 500) {
    container.removeChild(container.firstChild);
  }
}

function escapeHtml(text) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
  return String(text).replace(/[&<>"']/g, (m) => map[m]);
}

function initEventListeners() {
  document.getElementById("themeToggleBtn")?.addEventListener("click", toggleTheme);

  document.getElementById("layerSelect")?.addEventListener("change", (e) => {
    renderMethodsOptions(e.target.value);
  });

  document.getElementById("methodSelect")?.addEventListener("change", updateFormVisibility);

  document.getElementById("stopAllBtn")?.addEventListener("click", () => {
    if (confirm("Tem certeza que deseja parar todos os processos em execução?")) {
      stopAttack("all");
    }
  });

  document.getElementById("refreshAttacksBtn")?.addEventListener("click", () => {
    initAttacksPolling();
  });

  document.getElementById("clearConsoleBtn")?.addEventListener("click", () => {
    const full = document.getElementById("fullTerminalBody");
    const quick = document.getElementById("dashboardQuickLog");
    if (full) full.innerHTML = "";
    if (quick) quick.innerHTML = "";
  });

  document.getElementById("toggleAutoScrollBtn")?.addEventListener("click", (e) => {
    autoScrollEnabled = !autoScrollEnabled;
    e.target.textContent = `Autoscroll: ${autoScrollEnabled ? "Ativado" : "Desativado"}`;
  });

  document.getElementById("attackForm")?.addEventListener("submit", handleAttackSubmit);
  document.getElementById("runToolBtn")?.addEventListener("click", handleRunTool);
}

function handleAttackSubmit(e) {
  e.preventDefault();

  const layer = document.getElementById("layerSelect").value;
  const method = document.getElementById("methodSelect").value;
  const target = document.getElementById("targetInput").value;
  const threads = parseInt(document.getElementById("threadsInput").value, 10);
  const duration = parseInt(document.getElementById("durationInput").value, 10);
  const socksType = parseInt(document.getElementById("socksTypeSelect").value, 10);
  const proxylist = document.getElementById("proxyFileInput").value;
  const rpc = parseInt(document.getElementById("rpcInput").value, 10);
  const reflector = document.getElementById("reflectorInput").value;

  const payload = {
    layer: layer,
    method: method,
    target: target,
    threads: threads,
    duration: duration,
    socks_type: socksType,
    proxylist: proxylist,
    rpc: rpc,
    reflector: reflector
  };

  const startBtn = document.getElementById("startAttackBtn");
  startBtn.disabled = true;
  startBtn.textContent = "Iniciando...";

  fetch("/api/attacks/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then((res) => res.json())
    .then((data) => {
      startBtn.disabled = false;
      startBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        Iniciar Operação
      `;

      if (data.success) {
        switchTab("active-attacks");
        initAttacksPolling();
      } else {
        alert(`Erro: ${data.error || "Não foi possível iniciar"}`);
      }
    })
    .catch((err) => {
      startBtn.disabled = false;
      startBtn.textContent = "Iniciar Operação";
      alert(`Erro na requisição: ${err}`);
    });
}

function handleRunTool() {
  const tool = document.getElementById("toolSelect").value;
  const target = document.getElementById("toolTargetInput").value.trim();
  const resultCard = document.getElementById("toolResultCard");
  const runBtn = document.getElementById("runToolBtn");

  if (!target) {
    alert("Informe o alvo para executar o diagnóstico.");
    return;
  }

  resultCard.classList.add("active");
  resultCard.textContent = "Executando requisição, aguarde...";
  runBtn.disabled = true;

  fetch(`/api/tools/${tool}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target: target })
  })
    .then((res) => res.json())
    .then((data) => {
      runBtn.disabled = false;
      resultCard.textContent = JSON.stringify(data, null, 2);
    })
    .catch((err) => {
      runBtn.disabled = false;
      resultCard.textContent = `Erro ao executar ferramenta: ${err}`;
    });
}
