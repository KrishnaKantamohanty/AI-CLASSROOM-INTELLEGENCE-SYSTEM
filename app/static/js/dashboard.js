document.addEventListener('DOMContentLoaded', () => {
    // Configuration for charts based on theme
    const getChartColors = () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            text: isDark ? '#94a3b8' : '#64748b',
            grid: isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(100, 116, 139, 0.1)',
            primary: '#4f46e5',
            primaryLight: 'rgba(79, 70, 229, 0.1)',
            success: '#10b981',
            danger: '#ef4444'
        };
    };

    // Number counters animation
    const counters = document.querySelectorAll('[data-counter]');
    counters.forEach(counter => {
        const target = +counter.getAttribute('data-counter');
        if (isNaN(target)) return;

        const duration = 1500;
        const step = target / (duration / 16); // 60fps

        let current = 0;
        const updateCounter = () => {
            current += step;
            if (current < target) {
                counter.innerText = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.innerText = target;
            }
        };
        updateCounter();
    });

    // Chart instances
    let trendChart, pieChart, dayWiseChart;

    // Initialize Charts
    const initCharts = async () => {
        const colors = getChartColors();
        Chart.defaults.color = colors.text;
        Chart.defaults.font.family = "'Inter', sans-serif";

        try {
            // 1. Attendance Trend Chart
            const trendCtx = document.getElementById('attendanceTrendChart');
            if (trendCtx) {
                const trendRes = await fetch('/api/attendance-trend');
                const trendData = await trendRes.json();

                trendChart = new Chart(trendCtx.getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: trendData.labels,
                        datasets: [{
                            label: 'Attendance Rate %',
                            data: trendData.rates,
                            borderColor: colors.primary,
                            backgroundColor: colors.primaryLight,
                            fill: true,
                            tension: 0.4,
                            borderWidth: 2,
                            pointRadius: 3,
                            pointBackgroundColor: colors.primary
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { min: 0, max: 100, grid: { color: colors.grid } },
                            x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } }
                        }
                    }
                });
            }

            // 2. Day-wise Bar Chart
            const dayCtx = document.getElementById('dayWiseChart');
            if (dayCtx) {
                const dayRes = await fetch('/api/day-wise');
                const dayData = await dayRes.json();

                dayWiseChart = new Chart(dayCtx.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: dayData.labels,
                        datasets: [{
                            label: 'Avg Attendance %',
                            data: dayData.data,
                            backgroundColor: colors.primary,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { min: 0, max: 100, grid: { color: colors.grid } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }

            // 3. Today's Distribution Pie Chart
            const pieCtx = document.getElementById('attendancePieChart');
            if (pieCtx) {
                // Get stats from HTML data attributes or fetch
                const statsRes = await fetch('/api/stats');
                const statsData = await statsRes.json();

                pieChart = new Chart(pieCtx.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Present', 'Absent'],
                        datasets: [{
                            data: [statsData.present_today, statsData.absent_today],
                            backgroundColor: [colors.success, colors.danger],
                            borderWidth: 0,
                            cutout: '75%'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });
            }

        } catch (error) {
            console.error('Error loading charts:', error);
        }
    };

    initCharts();

    // Handle Theme Change
    window.addEventListener('themeChanged', () => {
        if (!trendChart) return;
        const colors = getChartColors();
        Chart.defaults.color = colors.text;

        [trendChart, dayWiseChart].forEach(chart => {
            if (chart) {
                chart.options.scales.y.grid.color = colors.grid;
                chart.update();
            }
        });
    });

    // Real-time updates via API polling
    const updateDashboardData = async () => {
        try {
            // Update Occupancy
            const occRes = await fetch('/api/occupancy');
            const occData = await occRes.json();

            const liveCount = document.getElementById('liveCount');
            const occPct = document.getElementById('occupancyPct');
            const occBar = document.getElementById('occupancyBar');

            if (liveCount) liveCount.innerText = occData.current;
            if (occPct) occPct.innerText = `${occData.percentage}%`;
            if (occBar) occBar.style.width = `${occData.percentage}%`;

        } catch (e) {
            console.error('Polling error:', e);
        }
    };

    // Poll every 5 seconds for dashboard live stats
    setInterval(updateDashboardData, 5000);
});
