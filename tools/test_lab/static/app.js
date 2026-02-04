document.addEventListener('DOMContentLoaded', () => {
    const testSuites = document.getElementById('test-suites');
    const roadmap = document.getElementById('validation-roadmap');
    const consoleOutput = document.getElementById('console-output');
    const runAllBtn = document.getElementById('run-all-btn');
    const clearConsoleBtn = document.getElementById('clear-console');
    const refreshBtn = document.getElementById('refresh-btn');

    const ui = {
        name: document.getElementById('current-test-name'),
        path: document.getElementById('current-test-path'),
        status: document.getElementById('status-badge'),
        passed: document.getElementById('stat-passed'),
        failed: document.getElementById('stat-failed'),
        rate: document.getElementById('stat-rate'),
        progress: document.getElementById('global-progress'),
        progressPercent: document.getElementById('progress-percent'),
        progressCount: document.getElementById('progress-count')
    };

    let tests = [];
    let stats = { passed: 0, failed: 0 };
    let categoryHealth = {};

    // Load tests on startup
    async function loadTests() {
        try {
            const response = await fetch('/api/tests?t=' + Date.now());
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            tests = await response.json();
            renderTests();
            renderRoadmap();
        } catch (err) {
            console.error("Load error:", err);
            testSuites.innerHTML = `<div class="console-line error">FAILED TO LOAD CORE MODULES: ${err.message}</div>`;
        }
    }

    function renderRoadmap() {
        roadmap.innerHTML = '';
        const categories = [...new Set(tests.map(t => t.category))].sort();

        categoryHealth = {};
        categories.forEach(cat => {
            categoryHealth[cat] = {
                total: tests.filter(t => t.category === cat).length,
                passed: 0,
                failed: 0,
                status: 'STANDBY'
            };

            const cp = document.createElement('div');
            cp.className = 'roadmap-checkpoint';
            cp.id = `cp-${cat.replace(/\s+/g, '-')}`;
            cp.innerHTML = `
                <span class="cp-label">${cat}</span>
                <span class="cp-status" id="cp-status-${cat.replace(/\s+/g, '-')}">STANDBY</span>
            `;
            roadmap.appendChild(cp);
        });
    }

    function updateRoadmapStatus(category, status) {
        const cp = document.getElementById(`cp-${category.replace(/\s+/g, '-')}`);
        const statusEl = document.getElementById(`cp-status-${category.replace(/\s+/g, '-')}`);
        if (!cp || !statusEl) return;

        cp.className = 'roadmap-checkpoint ' + status.toLowerCase();
        statusEl.textContent = status.toUpperCase();

        if (status === 'VERIFYING') cp.classList.add('verifying');
        else cp.classList.remove('verifying');
    }

    function renderTests() {
        testSuites.innerHTML = '';
        const groups = {};

        tests.forEach((test, index) => {
            if (!groups[test.category]) groups[test.category] = [];
            groups[test.category].push({ ...test, index });
        });

        Object.keys(groups).sort().forEach(category => {
            const suiteDiv = document.createElement('div');
            suiteDiv.className = 'suite-group';
            suiteDiv.innerHTML = `
                <div class="suite-header">
                    <h3>${category}</h3>
                    <div class="line"></div>
                </div>
                <div class="test-items" id="suite-${category.replace(/\s+/g, '-')}"></div>
            `;
            testSuites.appendChild(suiteDiv);

            const itemsContainer = suiteDiv.querySelector('.test-items');
            groups[category].forEach(test => {
                const div = document.createElement('div');
                div.className = `test-item ${test.is_critical ? 'critical' : ''}`;
                div.id = `test-${test.index}`;
                div.innerHTML = `
                    <span class="test-name">${test.name}</span>
                    <span class="status-icon" id="icon-${test.index}"></span>
                `;
                div.onclick = () => runSingleTest(test.index);
                itemsContainer.appendChild(div);
            });
        });
    }

    function updateStats() {
        const total = stats.passed + stats.failed;
        ui.passed.textContent = stats.passed;
        ui.failed.textContent = stats.failed;
        ui.rate.textContent = total === 0 ? '0%' : Math.round((stats.passed / total) * 100) + '%';
    }

    function updateProgressBar(completed) {
        const percent = Math.round((completed / tests.length) * 100);
        ui.progress.style.width = `${percent}%`;
        ui.progressPercent.textContent = `${percent}%`;
        ui.progressCount.textContent = `${completed} / ${tests.length}`;
    }

    function log(msg, type = '') {
        const line = document.createElement('div');
        line.className = `console-line ${type}`;
        line.textContent = msg;
        consoleOutput.appendChild(line);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }

    async function runSingleTest(index) {
        const test = tests[index];
        const testEl = document.getElementById(`test-${index}`);
        const iconEl = document.getElementById(`icon-${index}`);

        // UI Reset
        ui.name.textContent = test.name;
        ui.path.textContent = test.path;
        ui.status.textContent = 'RUNNING';
        ui.status.className = 'badge running';
        testEl.className = `test-item active running ${test.is_critical ? 'critical' : ''}`;
        iconEl.className = 'status-icon';
        iconEl.textContent = '⋯';

        updateRoadmapStatus(test.category, 'VERIFYING');

        log(`[LAB] INITIALIZING: ${test.name}`, 'system');

        return new Promise((resolve) => {
            const eventSource = new EventSource(`/api/run/${test.path}`);

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'log') {
                    let logType = '';
                    if (data.msg.includes('PASSED')) logType = 'success';
                    if (data.msg.includes('FAILED')) logType = 'error';
                    log(data.msg, logType);
                } else if (data.type === 'status') {
                    if (data.msg === 'PASSED') {
                        ui.status.textContent = 'PASSED';
                        ui.status.className = 'badge success';
                        testEl.className = `test-item passed ${test.is_critical ? 'critical' : ''}`;
                        iconEl.className = 'status-icon passed';
                        iconEl.textContent = '✓';
                        stats.passed++;
                        categoryHealth[test.category].passed++;
                        resolve(true);
                    } else if (data.msg === 'FAILED') {
                        ui.status.textContent = 'FAILED';
                        ui.status.className = 'badge error';
                        testEl.className = `test-item failed ${test.is_critical ? 'critical' : ''}`;
                        iconEl.className = 'status-icon failed';
                        iconEl.textContent = '✕';
                        stats.failed++;
                        categoryHealth[test.category].failed++;
                        resolve(false);
                    }

                    if (data.msg === 'PASSED' || data.msg === 'FAILED') {
                        const health = categoryHealth[test.category];
                        if (health.passed + health.failed === health.total) {
                            const catStatus = health.failed > 0 ? 'FAILED' : 'VERIFIED';
                            updateRoadmapStatus(test.category, catStatus);
                        }
                        updateStats();
                        eventSource.close();
                    }
                }
            };

            eventSource.onerror = () => {
                log('[LAB] CONNECTION INTERRUPTED', 'error');
                ui.status.textContent = 'ERROR';
                ui.status.className = 'badge error';
                testEl.className = `test-item failed ${test.is_critical ? 'critical' : ''}`;
                iconEl.textContent = '⚠';
                eventSource.close();
                updateRoadmapStatus(test.category, 'FAILED');
                resolve(false);
            };
        });
    }

    async function runSequential() {
        runAllBtn.disabled = true;
        runAllBtn.textContent = 'SQUAD EXECUTING...';

        stats = { passed: 0, failed: 0 };
        updateStats();
        updateProgressBar(0);
        renderRoadmap(); // Reset roadmap

        // Reset all icons
        tests.forEach((_, i) => {
            const icon = document.getElementById(`icon-${i}`);
            if (icon) icon.textContent = '';
            const testEl = document.getElementById(`test-${i}`);
            if (testEl) testEl.className = `test-item ${tests[i].is_critical ? 'critical' : ''}`;
        });

        for (let i = 0; i < tests.length; i++) {
            await runSingleTest(i);
            updateProgressBar(i + 1);
        }

        runAllBtn.disabled = false;
        runAllBtn.textContent = 'SEQUENTIAL EXECUTION';
        log('[LAB] FULL SYSTEM VALIDATION COMPLETED', 'system');
    }

    runAllBtn.onclick = runSequential;
    clearConsoleBtn.onclick = () => { consoleOutput.innerHTML = ''; };
    refreshBtn.onclick = loadTests;

    loadTests();
});
