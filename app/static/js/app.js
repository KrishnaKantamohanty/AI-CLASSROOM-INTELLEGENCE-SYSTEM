document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Toggle
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 992 && sidebar.classList.contains('show')) {
                if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }

    // Live Clock
    const timeDisplay = document.getElementById('currentTime');
    if (timeDisplay) {
        const updateTime = () => {
            timeDisplay.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        };
        updateTime();
        setInterval(updateTime, 60000); // Update every minute
    }

    // Auto-dismiss Flash Messages
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Refresh button
    const refreshBtn = document.getElementById('refreshData');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.classList.add('fa-spin'); // if using fontawesome, or add custom animation class
            window.location.reload();
        });
    }
});
