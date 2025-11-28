// Global analysis status tracking
let analysisJobId = null;
let analysisStatusInterval = null;
let currentRunContext = null;

// Dashboard JavaScript for D3.js visualizations and data updates

let trendChart, pieChart;
let updateInterval;
let runOptions = [];
const DEFAULT_TREND_DAYS = 7;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    initializeRunDropdown();
    startAutoRefresh();
});

function initializeDashboard() {
    setupCharts();
    loadInitialData();
}

function initializeRunDropdown() {
    const selector = document.getElementById('run-selector');
    const refreshButton = document.getElementById('refresh-run-options');

    if (selector) {
        selector.addEventListener('change', event => {
            handleRunSelection(event.target.value);
        });
    }

    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            refreshRunOptions({ preserveSelection: true });
        });
    }

    refreshRunOptions({ preserveSelection: false });
}

async function refreshRunOptions({ preserveSelection = true } = {}) {
    const selector = document.getElementById('run-selector');
    if (!selector) {
        return;
    }

    const previousValue = preserveSelection ? selector.value : '';

    selector.disabled = true;
    selector.innerHTML = '<option value="">Loading runs...</option>';

    try {
        const response = await fetch('/api/pipeline/runs?limit=20');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Failed to load runs');
        }

        runOptions = Array.isArray(result.data) ? result.data : [];
        populateRunDropdown(selector, runOptions, previousValue);
    } catch (error) {
        console.error('Error loading run list:', error);
        selector.innerHTML = '<option value="">Failed to load runs</option>';
    } finally {
        selector.disabled = false;
    }
}

function populateRunDropdown(selector, runs, previousValue) {
    selector.innerHTML = '';

    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = runs.length ? 'All data (no filter)' : 'No runs available';
    selector.appendChild(placeholder);

    runs.forEach(run => {
        const option = document.createElement('option');
        option.value = run.run_id;
        option.textContent = formatRunOptionLabel(run);
        selector.appendChild(option);
    });

    if (previousValue && runs.some(run => run.run_id === previousValue)) {
        selector.value = previousValue;
        handleRunSelection(previousValue, { useCached: true });
    } else if (runs.length) {
        // Auto-select the most recent completed run
        const completedRun = runs.find(run => run.status === 'completed');
        if (completedRun) {
            selector.value = completedRun.run_id;
            handleRunSelection(completedRun.run_id, { useCached: true });
        } else {
            selector.value = '';
            handleRunSelection('');
        }
    } else {
        handleRunSelection('');
    }
}

function formatRunOptionLabel(run) {
    const statusLabel = (run.status || 'unknown').charAt(0).toUpperCase() + (run.status || 'unknown').slice(1);
    const createdLabel = run.created_at ? formatTimestamp(run.created_at) : 'Unknown time';

    let keywordPreview = 'No keywords';
    if (Array.isArray(run.keywords) && run.keywords.length) {
        const sample = run.keywords.slice(0, 2).join(', ');
        keywordPreview = run.keywords.length > 2 ? `${sample}, ...` : sample;
    }

    return `${statusLabel} · ${createdLabel} · ${keywordPreview}`;
}

async function handleRunSelection(runId, { useCached = false } = {}) {
    if (!runId) {
        currentRunContext = null;
        displaySelectedRun(null);
        updateTrendPeriodLabel();
        loadInitialData();
        startAutoRefresh();
        return;
    }

    let runData = null;

    if (useCached) {
        runData = runOptions.find(run => run.run_id === runId) || null;
    }

    if (!runData) {
        try {
            const response = await fetch(`/api/pipeline/runs/${runId}`);
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Failed to load run details');
            }

            runData = result.data;
        } catch (error) {
            console.error(`Error loading run ${runId}:`, error);
            showError('Failed to load run details. Please try again.');
            return;
        }
    }

    mergeRunContext(runData);
    displaySelectedRun(runData);
    loadInitialData();
}

function displaySelectedRun(runData) {
    const statusDiv = document.getElementById('analysis-status');
    if (!statusDiv) {
        return;
    }

    if (!runData) {
        statusDiv.innerHTML = '';
        updateTrendPeriodLabel();
        return;
    }

    const badge = buildStatusBadge(runData.status);
    const details = buildRunDetails(true);
    const created = runData.created_at ? formatTimestamp(runData.created_at) : 'Unknown time';
    const message = runData.message ? escapeHtml(runData.message) : '';

    statusDiv.innerHTML = `
        <div class="alert alert-secondary d-flex align-items-start mb-0" role="alert">
            <div class="me-2">${badge}</div>
            <div>
                <div class="fw-semibold">Selected run from ${escapeHtml(created)}</div>
                ${details}
                ${message ? `<div class="text-muted small mt-1">${message}</div>` : ''}
            </div>
        </div>
    `;

    updateTrendPeriodLabel();
}

function setupCharts() {
    setupTrendChart();
    setupPieChart();
}

function setupTrendChart() {
    const container = d3.select("#trend-chart");
    const margin = {top: 20, right: 80, bottom: 40, left: 50};
    const width = container.node().getBoundingClientRect().width - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    const svg = container.append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    trendChart = {
        svg: svg,
        g: svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`),
        width: width,
        height: height,
        margin: margin
    };

    // Add axis groups
    trendChart.g.append("g").attr("class", "x-axis").attr("transform", `translate(0,${height})`);
    trendChart.g.append("g").attr("class", "y-axis");

    // Add axis labels
    trendChart.g.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x", 0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text("Number of Posts");

    trendChart.g.append("text")
        .attr("transform", `translate(${width / 2}, ${height + margin.bottom})`)
        .style("text-anchor", "middle")
        .text("Time");
}

function setupPieChart() {
    const container = d3.select("#pie-chart");
    const width = container.node().getBoundingClientRect().width;
    const height = 300;
    const radius = Math.min(width, height) / 2 - 10;

    const svg = container.append("svg")
        .attr("width", width)
        .attr("height", height);

    const g = svg.append("g")
        .attr("transform", `translate(${width/2},${height/2})`);

    pieChart = {
        svg: svg,
        g: g,
        radius: radius,
        width: width,
        height: height
    };
}

function loadInitialData() {
    Promise.all([
        fetchSentimentSummary(),
        fetchSentimentTrends(),
        fetchTopPosts('positive'),
        fetchTopPosts('neutral'),
        fetchTopPosts('negative'),
        fetchOverviewStats()
    ]).then(() => {
        updateTrendPeriodLabel();
        updateLastRefreshTime();
    }).catch(error => {
        console.error('Error loading initial data:', error);
        showError('Failed to load dashboard data');
    });
}

async function fetchSentimentSummary() {
    try {
        let url = '/api/sentiment/summary';
        const params = buildRunWindowParams();
        if (params) {
            url += '?' + params;
        }
        
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            updateOverviewStats(result.data);
            updatePieChart(result.data);
        } else if (result.error) {
            showError(result.error);
        }
    } catch (error) {
        console.error('Error fetching sentiment summary:', error);
    }
}

async function fetchSentimentTrends() {
    try {
        const days = getTrendQueryDays();
        updateTrendPeriodLabel();

        let url = `/api/sentiment/trends?days=${days}`;
        const windowParams = buildRunWindowParams();
        if (windowParams) {
            url += '&' + windowParams;
        }
        
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            updateTrendChart(result.data);
        } else if (result.error) {
            showError(result.error);
        }
    } catch (error) {
        console.error('Error fetching sentiment trends:', error);
    }
}

async function fetchTopPosts(sentiment) {
    try {
        let url = `/api/posts/top?sentiment=${sentiment}&limit=5`;
        const windowParams = buildRunWindowParams();
        if (windowParams) {
            url += '&' + windowParams;
        }
        
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            updateTopPosts(sentiment, result.data);
        } else if (result.error) {
            showError(result.error);
        }
    } catch (error) {
        console.error(`Error fetching ${sentiment} posts:`, error);
    }
}

async function fetchOverviewStats() {
    try {
        let url = '/api/stats/overview';
        const windowParams = buildRunWindowParams();
        if (windowParams) {
            url += '?' + windowParams;
        }
        
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            updatePlatformStats(result.data.platforms);
        }
    } catch (error) {
        console.error('Error fetching overview stats:', error);
    }
}

function updateOverviewStats(data) {
    document.getElementById('positive-percent').textContent = `${data.positive.toFixed(1)}%`;
    document.getElementById('neutral-percent').textContent = `${data.neutral.toFixed(1)}%`;
    document.getElementById('negative-percent').textContent = `${data.negative.toFixed(1)}%`;
    document.getElementById('total-posts').textContent = data.total;

    // Calculate counts
    const total = data.total;
    const positiveCount = Math.round(total * data.positive / 100);
    const neutralCount = Math.round(total * data.neutral / 100);
    const negativeCount = Math.round(total * data.negative / 100);

    document.getElementById('positive-count').textContent = `${positiveCount} posts`;
    document.getElementById('neutral-count').textContent = `${neutralCount} posts`;
    document.getElementById('negative-count').textContent = `${negativeCount} posts`;
}

function updatePieChart(data) {
    const pieData = [
        {label: 'Positive', value: data.positive, color: '#28a745'},
        {label: 'Neutral', value: data.neutral, color: '#ffc107'},
        {label: 'Negative', value: data.negative, color: '#dc3545'}
    ];

    const pie = d3.pie().value(d => d.value);
    const arc = d3.arc().innerRadius(0).outerRadius(pieChart.radius);

    pieChart.g.selectAll("*").remove();

    const arcs = pieChart.g.selectAll(".arc")
        .data(pie(pieData))
        .enter().append("g")
        .attr("class", "arc");

    arcs.append("path")
        .attr("d", arc)
        .attr("fill", d => d.data.color)
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
            showTooltip(event, `${d.data.label}: ${d.data.value.toFixed(1)}%`);
        })
        .on("mouseout", hideTooltip);

    arcs.append("text")
        .attr("transform", d => `translate(${arc.centroid(d)})`)
        .attr("dy", ".35em")
        .style("text-anchor", "middle")
        .style("fill", "white")
        .style("font-weight", "bold")
        .text(d => d.data.value > 5 ? `${d.data.value.toFixed(1)}%` : '');
}

function updateTrendChart(data) {
    if (!data || data.length === 0) {
        trendChart.g.selectAll("*").remove();
        trendChart.g.append("text")
            .attr("x", trendChart.width / 2)
            .attr("y", trendChart.height / 2)
            .attr("text-anchor", "middle")
            .style("fill", "#999")
            .text("No trend data available");
        return;
    }

    // Process data
    const processedData = processTrendData(data);

    // Set up scales
    const xScale = d3.scaleTime()
        .domain(d3.extent(processedData, d => d.datetime))
        .range([0, trendChart.width]);

    const yScale = d3.scaleLinear()
        .domain([0, d3.max(processedData, d => Math.max(d.positive, d.negative, d.neutral))])
        .range([trendChart.height, 0]);

    // Create line generator
    const line = d3.line()
        .x(d => xScale(d.datetime))
        .y(d => yScale(d.value))
        .curve(d3.curveMonotoneX);

    // Clear previous chart
    trendChart.g.selectAll(".line, .dot, .legend").remove();

    // Draw lines for each sentiment
    const sentiments = ['positive', 'negative', 'neutral'];
    const colors = {'positive': '#28a745', 'negative': '#dc3545', 'neutral': '#ffc107'};

    sentiments.forEach(sentiment => {
        const sentimentData = processedData.map(d => ({
            datetime: d.datetime,
            value: d[sentiment]
        }));

        trendChart.g.append("path")
            .datum(sentimentData)
            .attr("class", `line ${sentiment}`)
            .attr("d", line)
            .style("stroke", colors[sentiment]);

        // Add dots
        trendChart.g.selectAll(`.dot-${sentiment}`)
            .data(sentimentData)
            .enter().append("circle")
            .attr("class", `dot ${sentiment}`)
            .attr("cx", d => xScale(d.datetime))
            .attr("cy", d => yScale(d.value))
            .attr("r", 3)
            .style("fill", colors[sentiment])
            .on("mouseover", function(event, d) {
                showTooltip(event, `${sentiment}: ${d.value} posts at ${d.datetime.toLocaleString()}`);
            })
            .on("mouseout", hideTooltip);
    });

    // Update axes
    trendChart.g.select(".x-axis")
        .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat("%m/%d %H:%M")));

    trendChart.g.select(".y-axis")
        .call(d3.axisLeft(yScale));

    // Add legend
    const legend = trendChart.g.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${trendChart.width - 70}, 20)`);

    sentiments.forEach((sentiment, i) => {
        const legendRow = legend.append("g")
            .attr("transform", `translate(0, ${i * 20})`);

        legendRow.append("rect")
            .attr("width", 12)
            .attr("height", 12)
            .attr("fill", colors[sentiment]);

        legendRow.append("text")
            .attr("x", 16)
            .attr("y", 10)
            .style("font-size", "12px")
            .text(sentiment.charAt(0).toUpperCase() + sentiment.slice(1));
    });
}

function processTrendData(data) {
    // Group data by datetime and aggregate sentiment counts
    const grouped = {};

    data.forEach(item => {
        const datetime = new Date(`${item.date}T${item.hour.toString().padStart(2, '0')}:00:00`);
        const key = datetime.getTime();

        if (!grouped[key]) {
            grouped[key] = {
                datetime: datetime,
                positive: 0,
                negative: 0,
                neutral: 0
            };
        }

        grouped[key][item.sentiment] += item.count;
    });

    return Object.values(grouped).sort((a, b) => a.datetime - b.datetime);
}

function updateTopPosts(sentiment, posts) {
    const container = document.getElementById(`${sentiment}-posts`);

    if (!posts || posts.length === 0) {
        container.innerHTML = '<div class="text-muted text-center">No posts available</div>';
        return;
    }

    const html = posts.map(post => `
        <div class="post-item">
            <div class="post-text">${post.text}</div>
            <div class="post-meta">
                <span class="platform-badge badge bg-secondary">${post.platform}</span>
                <span class="confidence-badge badge bg-info ms-1">
                    ${(post.sentiment.confidence * 100).toFixed(1)}% confidence
                </span>
                <small class="text-muted ms-2">
                    ${post.created_at ? new Date(post.created_at).toLocaleDateString() : 'Unknown date'}
                </small>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

function updatePlatformStats(platforms) {
    Object.keys(platforms).forEach(platform => {
        const container = document.getElementById(`${platform}-stats`);
        const data = platforms[platform];

        if (data.total === 0) {
            container.innerHTML = '<div class="text-muted text-center">No data available</div>';
            return;
        }

        const html = `
            <div class="platform-stat">
                <span class="stat-label text-success">Positive:</span>
                <span class="stat-value">${data.positive.toFixed(1)}%</span>
            </div>
            <div class="platform-stat">
                <span class="stat-label text-warning">Neutral:</span>
                <span class="stat-value">${data.neutral.toFixed(1)}%</span>
            </div>
            <div class="platform-stat">
                <span class="stat-label text-danger">Negative:</span>
                <span class="stat-value">${data.negative.toFixed(1)}%</span>
            </div>
            <div class="platform-stat">
                <span class="stat-label">Total Posts:</span>
                <span class="stat-value">${data.total}</span>
            </div>
        `;

        container.innerHTML = html;
    });
}

function refreshData() {
    loadInitialData();
    showUpdateNotification();
}

function startAutoRefresh() {
    if (updateInterval) {
        return;
    }

    // Auto-refresh every 30 seconds
    updateInterval = setInterval(() => {
        loadInitialData();
    }, 30000);
}

function stopAutoRefresh() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

function updateLastRefreshTime() {
    document.getElementById('last-update').textContent =
        `Last updated: ${new Date().toLocaleTimeString()}`;
}

function showTooltip(event, text) {
    const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    tooltip.transition()
        .duration(200)
        .style("opacity", .9);

    tooltip.html(text)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 28) + "px");
}

function hideTooltip() {
    d3.selectAll(".tooltip").remove();
}

function showError(message) {
    // Create error notification
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show update-indicator';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

function showUpdateNotification() {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show update-indicator';
    alert.innerHTML = `
        Dashboard updated successfully!
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);

    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 3000);
}

// Handle window resize
window.addEventListener('resize', function() {
    setupCharts();
    setTimeout(() => {
        fetchSentimentSummary();
        fetchSentimentTrends();
    }, 100);
});

function buildRunWindowParams() {
    const params = new URLSearchParams();

    // Prioritize run_id if available
    if (currentRunContext && currentRunContext.runId) {
        params.append('run_id', currentRunContext.runId);
        return params.toString();
    }

    // Fallback to time window filtering
    if (currentRunContext && currentRunContext.windowStart) {
        params.append('start_date', currentRunContext.windowStart);
    }
    if (currentRunContext && currentRunContext.windowEnd) {
        params.append('end_date', currentRunContext.windowEnd);
    }

    return params.toString();
}

function escapeHtml(str) {
    if (typeof str !== 'string') {
        return str;
    }
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return str.replace(/[&<>"']/g, char => map[char]);
}

function formatDurationLabel(durationDays) {
    if (durationDays === null || durationDays === undefined || Number.isNaN(durationDays)) {
        return 'Default';
    }

    const value = Number(durationDays);

    if (value <= 0.001) {
        return 'Last 60 seconds';
    }
    if (Math.abs(value - 1) < 1e-6) {
        return 'Last 24 hours';
    }
    if (Math.abs(value - 3) < 1e-6) {
        return 'Last 3 days';
    }
    if (Math.abs(value - 7) < 1e-6) {
        return 'Last 7 days';
    }
    if (Math.abs(value - 30) < 1e-6) {
        return 'Last 30 days';
    }

    const rounded = value >= 1 ? Math.round(value) : value.toFixed(2);
    return `Last ${rounded} days`;
}

function getTrendQueryDays() {
    if (currentRunContext) {
        const { windowStart, windowEnd, durationDays } = currentRunContext;

        if (windowStart && windowEnd) {
            const startDate = new Date(windowStart);
            const endDate = new Date(windowEnd);
            if (!Number.isNaN(startDate.getTime()) && !Number.isNaN(endDate.getTime()) && endDate > startDate) {
                const diffDays = (endDate - startDate) / (1000 * 60 * 60 * 24);
                if (diffDays >= 1) {
                    return Math.round(diffDays);
                }
                return 1;
            }
        }

        if (typeof durationDays === 'number' && !Number.isNaN(durationDays)) {
            return durationDays >= 1 ? Math.round(durationDays) : 1;
        }
    }

    return DEFAULT_TREND_DAYS;
}

function updateTrendPeriodLabel() {
    const labelEl = document.getElementById('trend-period-label');
    if (!labelEl) {
        return;
    }

    if (!currentRunContext) {
        labelEl.textContent = '';
        return;
    }

    const durationLabel = formatDurationLabel(currentRunContext.durationDays ?? DEFAULT_TREND_DAYS);

    if (currentRunContext.windowStart && currentRunContext.windowEnd) {
        const startLabel = formatTimestamp(currentRunContext.windowStart);
        const endLabel = formatTimestamp(currentRunContext.windowEnd);
        labelEl.textContent = `${durationLabel} (${startLabel} → ${endLabel})`;
    } else {
        labelEl.textContent = durationLabel;
    }
}

function formatTimestamp(value) {
    if (!value) {
        return '—';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function buildStatusBadge(status) {
    const normalized = (status || '').toLowerCase();
    let badgeClass = 'bg-secondary';
    let label = 'Queued';

    if (normalized === 'running') {
        badgeClass = 'bg-info text-dark';
        label = 'Running';
    } else if (normalized === 'completed') {
        badgeClass = 'bg-success';
        label = 'Completed';
    } else if (normalized === 'error') {
        badgeClass = 'bg-danger';
        label = 'Error';
    } else if (normalized === 'idle') {
        badgeClass = 'bg-secondary';
        label = 'Idle';
    }

    return `<span class="badge ${badgeClass}">${label}</span>`;
}

function mergeRunContext(updates = {}) {
    const existing = currentRunContext || {};
    const timeWindowUpdate = updates.time_window || updates.timeWindow || {};

    currentRunContext = {
        runId: updates.runId ?? updates.run_id ?? existing.runId ?? null,
        keywords: updates.keywords ?? existing.keywords ?? [],
        durationDays: typeof updates.durationDays === 'number'
            ? updates.durationDays
            : (typeof updates.duration_days === 'number'
                ? updates.duration_days
                : (typeof existing.durationDays === 'number' ? existing.durationDays : null)),
        status: updates.status ?? existing.status ?? null,
        progress: updates.progress ?? existing.progress ?? '',
        stats: updates.stats ?? existing.stats ?? null,
        rawPostsCount: updates.raw_posts_count ?? updates.rawPostsCount ?? existing.rawPostsCount ?? 0,
        sentimentResultsCount: updates.sentiment_results_count ?? updates.sentimentResultsCount ?? existing.sentimentResultsCount ?? 0,
        startedAt: updates.started_at ?? updates.startedAt ?? existing.startedAt ?? null,
        completedAt: updates.completed_at ?? updates.completedAt ?? existing.completedAt ?? null,
        windowStart: updates.window_start
            ?? updates.windowStart
            ?? timeWindowUpdate.start
            ?? (existing.windowStart || (existing.time_window && existing.time_window.start) || null),
        windowEnd: updates.window_end
            ?? updates.windowEnd
            ?? timeWindowUpdate.end
            ?? (existing.windowEnd || (existing.time_window && existing.time_window.end) || null)
    };
}

function buildRunDetails(includeStats = false) {
    if (!currentRunContext) {
        return '';
    }

    const keywords = Array.isArray(currentRunContext.keywords) && currentRunContext.keywords.length
        ? currentRunContext.keywords.map(kw => escapeHtml(kw)).join(', ')
        : 'None';

    const durationLabel = formatDurationLabel(currentRunContext.durationDays);
    const runIdShort = currentRunContext.runId ? currentRunContext.runId.slice(0, 8) : 'n/a';
    const windowStart = currentRunContext.windowStart ? formatTimestamp(currentRunContext.windowStart) : null;
    const windowEnd = currentRunContext.windowEnd ? formatTimestamp(currentRunContext.windowEnd) : null;

    let html = `
        <div class="mt-1">
            <div class="text-muted small">Run ID: ${escapeHtml(runIdShort)}</div>
            <div class="text-muted small">Keywords: ${keywords}</div>
            <div class="text-muted small">Time Range: ${escapeHtml(durationLabel)}</div>
            ${(windowStart || windowEnd)
                ? `<div class="text-muted small">Window: ${escapeHtml(windowStart || '—')} → ${escapeHtml(windowEnd || '—')}</div>`
                : ''}
        </div>
    `;

    if (includeStats && currentRunContext.stats) {
        const totalPosts = currentRunContext.sentimentResultsCount
            || currentRunContext.rawPostsCount
            || currentRunContext.stats.total
            || 0;
        html += `
            <div class="text-muted small mt-1">Total Posts Processed: ${totalPosts}</div>
        `;
    }

    return html;
}
// === Analysis Modal and Workflow Functions ===

function showAnalysisModal() {
    const modalEl = document.getElementById('analysisModal');
    if (!modalEl) {
        return;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();

    const keywordsInput = document.getElementById('analysisKeywords');
    if (keywordsInput) {
        setTimeout(() => keywordsInput.focus(), 200);
    }
}

async function startAnalysis() {
    // Get input values
    const keywordsInput = document.getElementById('analysisKeywords');
    const durationSelect = document.getElementById('analysisDuration');
    
    const keywords = keywordsInput.value.trim();
    const duration = parseFloat(durationSelect.value);
    
    // Validate keywords
    if (!keywords) {
        alert('Please enter at least one keyword');
        return;
    }
    
    // Parse keywords (comma-separated)
    const keywordList = keywords.split(',').map(k => k.trim()).filter(k => k.length > 0);
    
    if (keywordList.length === 0) {
        alert('Please enter valid keywords');
        return;
    }
    
    // Close the modal
    const modalElement = document.getElementById('analysisModal');
    const modal = bootstrap.Modal.getInstance(modalElement);
    modal.hide();
    
    // Clear inputs for next time
    keywordsInput.value = '';
    durationSelect.value = '1';
    
    if (analysisStatusInterval) {
        clearInterval(analysisStatusInterval);
        analysisStatusInterval = null;
    }

    stopAutoRefresh();

    mergeRunContext({
        runId: null,
        keywords: keywordList,
        durationDays: duration,
        status: 'pending',
        progress: 'Initializing analysis...',
        stats: null,
        raw_posts_count: 0,
        sentiment_results_count: 0,
        started_at: null,
        completed_at: null
    });

    // Show progress feedback
    showAnalysisProgress('Initializing analysis...');
    
    try {
        // Start the analysis
        const response = await fetch('/api/pipeline/run_once', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keywords: keywordList,
                duration_days: duration
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            analysisJobId = result.job_id || null;

            mergeRunContext({
                runId: analysisJobId,
                status: 'queued',
                progress: 'Queued for execution',
                stats: null,
                raw_posts_count: 0,
                sentiment_results_count: 0
            });

            showAnalysisProgress('Queued for execution');
            
            // Start polling for status updates
            startAnalysisPolling();
        } else {
            showAnalysisError(result.message || 'Failed to start analysis');
            startAutoRefresh();
        }
    } catch (error) {
        console.error('Error starting analysis:', error);
        showAnalysisError('Failed to start analysis. Please try again.');
        startAutoRefresh();
    }
}

function showAnalysisProgress(message) {
    const statusDiv = document.getElementById('analysis-status');
    if (!statusDiv) {
        return;
    }

    const details = buildRunDetails(false);
    statusDiv.innerHTML = `
        <div class="alert alert-info d-flex align-items-start mb-0" role="alert">
            <div class="spinner-border spinner-border-sm me-2 mt-1" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>
                <div class="fw-semibold">${message}</div>
                ${details}
            </div>
        </div>
    `;
}

function showAnalysisSuccess() {
    const statusDiv = document.getElementById('analysis-status');
    if (!statusDiv) {
        return;
    }

    const details = buildRunDetails(true);
    statusDiv.innerHTML = `
        <div class="alert alert-success d-flex align-items-start mb-0" role="alert">
            <i class="fas fa-check-circle me-2 mt-1"></i>
            <div>
                <div class="fw-semibold">Analysis complete! Dashboard updated.</div>
                ${details}
            </div>
        </div>
    `;
    
    // Clear success message after 7 seconds
    setTimeout(() => {
        statusDiv.innerHTML = '';
    }, 7000);
}

function showAnalysisError(message) {
    const statusDiv = document.getElementById('analysis-status');
    if (!statusDiv) {
        return;
    }

    const details = buildRunDetails(false);
    statusDiv.innerHTML = `
        <div class="alert alert-danger d-flex align-items-start mb-0" role="alert">
            <i class="fas fa-exclamation-circle me-2 mt-1"></i>
            <div>
                <div class="fw-semibold">${message}</div>
                ${details}
            </div>
        </div>
    `;
    
    // Clear error message after 8 seconds
    setTimeout(() => {
        statusDiv.innerHTML = '';
    }, 8000);
}

function startAnalysisPolling() {
    if (analysisStatusInterval) {
        clearInterval(analysisStatusInterval);
    }

    analysisStatusInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/pipeline/status');
            const result = await response.json();

            if (!result.success) {
                return;
            }

            mergeRunContext(result);

            if (result.run_id && !analysisJobId) {
                analysisJobId = result.run_id;
            }

            const status = (result.status || '').toLowerCase();
            const progressMessage = result.progress || 'Processing...';

            if (status === 'queued') {
                showAnalysisProgress(progressMessage);
            } else if (status === 'running') {
                showAnalysisProgress(progressMessage);
            } else if (status === 'completed') {
                clearInterval(analysisStatusInterval);
                analysisStatusInterval = null;
                const completedRunId = analysisJobId;
                analysisJobId = null;
                showAnalysisSuccess();

                setTimeout(async () => {
                    await refreshRunOptions({ preserveSelection: false });
                    // Automatically select the completed run
                    const selector = document.getElementById('run-selector');
                    if (selector && completedRunId) {
                        selector.value = completedRunId;
                        await handleRunSelection(completedRunId);
                    } else {
                        loadInitialData();
                    }
                    startAutoRefresh();
                }, 1000);
            } else if (status === 'error') {
                clearInterval(analysisStatusInterval);
                analysisStatusInterval = null;
                analysisJobId = null;
                showAnalysisError(result.message || 'Analysis failed');
                setTimeout(() => {
                    startAutoRefresh();
                }, 500);
            } else if (status === 'idle') {
                clearInterval(analysisStatusInterval);
                analysisStatusInterval = null;
                analysisJobId = null;
                startAutoRefresh();
            }
        } catch (error) {
            console.error('Error checking analysis status:', error);
            // Keep polling; network errors might be transient
        }
    }, 2000);
}


