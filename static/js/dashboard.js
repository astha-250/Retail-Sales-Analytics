document.addEventListener("DOMContentLoaded", () => {
    loadKPIs();
    loadSalesTrend();
    loadCategoryPerformance();
    loadCustomerSegments();
});

function loadKPIs() {
    fetch('/api/v1/kpis')
        .then(res => res.json())
        .then(data => {
            document.getElementById('kpi-sales').innerText = `$${data.total_sales.toLocaleString()}`;
            document.getElementById('kpi-profit').innerText = `$${data.total_profit.toLocaleString()}`;
            document.getElementById('kpi-orders').innerText = data.total_orders.toLocaleString();
            document.getElementById('kpi-returns').innerText = `${data.return_rate}%`;
        })
        .catch(err => console.error("Error loading KPIs:", err));
}

function loadSalesTrend() {
    fetch('/api/v1/sales-trend')
        .then(res => res.json())
        .then(data => {
            const ctx = document.getElementById('salesTrendChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [
                        { label: 'Sales ($)', data: data.sales, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.3 },
                        { label: 'Profit ($)', data: data.profit, borderColor: '#60a5fa', backgroundColor: 'rgba(96, 165, 250, 0.1)', fill: true, tension: 0.3 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                }
            });
        })
        .catch(err => console.error("Error loading Sales Trend:", err));
}

function loadCategoryPerformance() {
    fetch('/api/v1/category-performance')
        .then(res => res.json())
        .then(data => {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.categories,
                    datasets: [
                        { label: 'Sales ($)', data: data.sales, backgroundColor: '#34d399' },
                        { label: 'Profit ($)', data: data.profit, backgroundColor: '#818cf8' }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                }
            });
        })
        .catch(err => console.error("Error loading Category Performance:", err));
}

function loadCustomerSegments() {
    fetch('/api/v1/customer-segments')
        .then(res => res.json())
        .then(data => {
            const ctx = document.getElementById('segmentChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.segments,
                    datasets: [{
                        data: data.counts,
                        backgroundColor: ['#38bdf8', '#818cf8', '#f43f5e', '#fbbf24']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } }
                }
            });
        })
        .catch(err => console.error("Error loading Customer Segments:", err));
}

function makePrediction() {
    const quantity = document.getElementById('predQuantity').value;
    const unit_price = document.getElementById('predUnitPrice').value;
    const discount = document.getElementById('predDiscount').value;

    fetch('/api/v1/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity, unit_price, discount })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('resSales').innerText = `$${data.predicted_sales.toLocaleString()}`;
        document.getElementById('resProfit').innerText = `$${data.estimated_profit.toLocaleString()}`;
        document.getElementById('predResult').classList.remove('hidden');
    })
    .catch(err => console.error("Error making prediction:", err));
}