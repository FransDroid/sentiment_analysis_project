// Dashboard JavaScript for D3.js visualizations and data updates

let trendChart, pieChart;
let updateInterval;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    startAutoRefresh();
});

function initializeDashboard() {
    setupCharts();
    loadInitialData();
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
        updateLastRefreshTime();
    }).catch(error => {
        console.error('Error loading initial data:', error);
        showError('Failed to load dashboard data');
    });
}

async function fetchSentimentSummary() {
    try {
        const response = await fetch('/api/sentiment/summary');
        const result = await response.json();

        if (result.success) {
            updateOverviewStats(result.data);
            updatePieChart(result.data);
        }
    } catch (error) {
        console.error('Error fetching sentiment summary:', error);
    }
}

async function fetchSentimentTrends() {
    try {
        const days = document.getElementById('trend-period').value;
        const response = await fetch(`/api/sentiment/trends?days=${days}`);
        const result = await response.json();

        if (result.success) {
            updateTrendChart(result.data);
        }
    } catch (error) {
        console.error('Error fetching sentiment trends:', error);
    }
}

async function fetchTopPosts(sentiment) {
    try {
        const response = await fetch(`/api/posts/top?sentiment=${sentiment}&limit=5`);
        const result = await response.json();

        if (result.success) {
            updateTopPosts(sentiment, result.data);
        }
    } catch (error) {
        console.error(`Error fetching ${sentiment} posts:`, error);
    }
}

async function fetchOverviewStats() {
    try {
        const response = await fetch('/api/stats/overview');
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

function updateTrends() {
    fetchSentimentTrends();
}

function refreshData() {
    loadInitialData();
    showUpdateNotification();
}

function startAutoRefresh() {
    // Auto-refresh every 30 seconds
    updateInterval = setInterval(() => {
        loadInitialData();
    }, 30000);
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