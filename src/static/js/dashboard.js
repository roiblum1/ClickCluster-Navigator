// Statistics Dashboard JavaScript

let dashboardCharts = {};

// Toggle dashboard visibility
function toggleDashboard() {
    const dashboard = document.getElementById('statisticsDashboard');
    const clustersSection = document.querySelector('.clusters-section');
    
    if (!dashboard || !clustersSection) return;
    
    if (dashboard.style.display === 'none' || !dashboard.style.display) {
        dashboard.style.display = 'block';
        clustersSection.style.display = 'none';
        loadStatistics();
    } else {
        dashboard.style.display = 'none';
        clustersSection.style.display = 'block';
        // Destroy charts when hiding
        Object.values(dashboardCharts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        dashboardCharts = {};
    }
}

// Load and display statistics
async function loadStatistics() {
    const API_BASE_URL = '/api';
    try {
        const response = await fetch(`${API_BASE_URL}/statistics`);
        if (!response.ok) {
            throw new Error('Failed to fetch statistics');
        }
        
        const stats = await response.json();
        
        // Update overview cards
        document.getElementById('statTotalClusters').textContent = stats.overview.total_clusters;
        document.getElementById('statTotalSites').textContent = stats.overview.total_sites;
        document.getElementById('statTotalSegments').textContent = stats.overview.total_segments;
        document.getElementById('statAvgSegments').textContent = stats.overview.average_segments_per_cluster;
        
        // Render charts
        renderClustersPerSiteChart(stats.clusters_per_site);
        renderSourceDistributionChart(stats.source_distribution);
        renderDomainDistributionChart(stats.domain_distribution);
        renderSegmentsPerSiteChart(stats.segments_per_site);
        
    } catch (error) {
        console.error('Failed to load statistics:', error);
        if (typeof showToast === 'function') {
            showToast('Failed to load statistics', 'error');
        }
    }
}

// Render clusters per site chart
function renderClustersPerSiteChart(data) {
    const ctx = document.getElementById('clustersPerSiteChart');
    if (!ctx) return;
    
    // Destroy existing chart if any
    if (dashboardCharts.clustersPerSite) {
        dashboardCharts.clustersPerSite.destroy();
    }
    
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    dashboardCharts.clustersPerSite = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Clusters',
                data: values,
                backgroundColor: 'rgba(238, 0, 0, 0.7)',
                borderColor: 'rgba(238, 0, 0, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Render source distribution chart
function renderSourceDistributionChart(data) {
    const ctx = document.getElementById('sourceDistributionChart');
    if (!ctx) return;
    
    if (dashboardCharts.sourceDistribution) {
        dashboardCharts.sourceDistribution.destroy();
    }
    
    dashboardCharts.sourceDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data).map(k => k === 'vlan-manager' ? 'VLAN Manager' : 'Manual'),
            datasets: [{
                data: Object.values(data),
                backgroundColor: [
                    'rgba(62, 134, 53, 0.7)',
                    'rgba(43, 154, 243, 0.7)'
                ],
                borderColor: [
                    'rgba(62, 134, 53, 1)',
                    'rgba(43, 154, 243, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Render domain distribution chart
function renderDomainDistributionChart(data) {
    const ctx = document.getElementById('domainDistributionChart');
    if (!ctx) return;
    
    if (dashboardCharts.domainDistribution) {
        dashboardCharts.domainDistribution.destroy();
    }
    
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    dashboardCharts.domainDistribution = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    'rgba(238, 0, 0, 0.7)',
                    'rgba(238, 0, 0, 0.5)',
                    'rgba(238, 0, 0, 0.3)',
                    'rgba(201, 25, 11, 0.7)',
                    'rgba(201, 25, 11, 0.5)'
                ],
                borderColor: 'rgba(255, 255, 255, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Render segments per site chart
function renderSegmentsPerSiteChart(data) {
    const ctx = document.getElementById('segmentsPerSiteChart');
    if (!ctx) return;
    
    if (dashboardCharts.segmentsPerSite) {
        dashboardCharts.segmentsPerSite.destroy();
    }
    
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    dashboardCharts.segmentsPerSite = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Segments',
                data: values,
                backgroundColor: 'rgba(43, 154, 243, 0.7)',
                borderColor: 'rgba(43, 154, 243, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

