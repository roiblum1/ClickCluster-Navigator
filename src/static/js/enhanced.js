// ============= ENHANCED FEATURES =============

// Keyboard Shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+K - Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }

    // Ctrl+D - Toggle dark mode
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleDarkMode();
    }

    // Ctrl+R - Refresh (prevent default browser refresh)
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        loadClusters();
    }

    // Escape - Clear search
    if (e.key === 'Escape') {
        clearSearch();
    }
});

// Toast Notifications
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        error: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
        info: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
        warning: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
    };

    const icon = icons[type] || icons.info;

    toast.innerHTML = `
        ${icon}
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="toast-close">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>
    `;

    container.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Copy to Clipboard
function copyToClipboard(text, label = 'Text') {
    navigator.clipboard.writeText(text).then(() => {
        showToast(`${label} copied`, 'success', 1500);
    }).catch(() => {
        showToast('Copy failed', 'error', 2000);
    });
}

// Clear Search
function clearSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearch');
    searchInput.value = '';
    clearBtn.style.display = 'none';
    filterClusters();
}

// Export Clusters
function exportClusters() {
    const data = {
        exportDate: new Date().toISOString(),
        totalClusters: allClusters.length,
        totalSites: allSites.length,
        sites: allSites
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clusters-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);

    showToast(`Exported ${allClusters.length} clusters to JSON`, 'success');
}

// Show Sync Indicator
function showSyncIndicator(show = true) {
    const indicator = document.getElementById('syncIndicator');
    if (indicator) {
        indicator.style.display = show ? 'flex' : 'none';
    }
}

// Update search input to show clear button
setTimeout(() => {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const clearBtn = document.getElementById('clearSearch');
            if (clearBtn) {
                clearBtn.style.display = e.target.value ? 'flex' : 'none';
            }
        });
    }
}, 500);

// Add copy functionality to cluster cards
document.addEventListener('click', (e) => {
    // Copy segment on click
    if (e.target.classList.contains('segment-badge')) {
        copyToClipboard(e.target.textContent, 'Segment');
    }

    // Copy cluster name on click
    if (e.target.tagName === 'H4' && e.target.closest('.cluster-card')) {
        copyToClipboard(e.target.textContent, 'Cluster name');
    }
});

// Auto-refresh sync status
setInterval(() => {
    if (typeof loadSyncStatus === 'function') {
        loadSyncStatus();
    }
}, 60000); // Check every minute

// Welcome message
setTimeout(() => {
    if (!sessionStorage.getItem('welcomeShown')) {
        showToast('Welcome to OpenShift Cluster Navigator!', 'info', 4000);
        sessionStorage.setItem('welcomeShown', 'true');
    }
}, 1000);

// Console welcome message
console.log('%c🚀 OpenShift Cluster Navigator', 'font-size: 20px; font-weight: bold; color: #ee0000;');
console.log('%cEnhanced with: Keyboard shortcuts, Toast notifications, Export, Copy-to-clipboard', 'color: #666;');
console.log('%cKeyboard Shortcuts:', 'font-weight: bold; margin-top: 10px;');
console.log('  Ctrl+K - Focus search');
console.log('  Ctrl+D - Toggle dark mode');
console.log('  Ctrl+R - Refresh data');
console.log('  Escape - Clear search');
