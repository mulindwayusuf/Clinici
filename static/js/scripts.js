// Auto-dismiss alerts after 5 seconds
// setTimeout(() => {
//     const alerts = document.querySelectorAll('.alert');
//     alerts.forEach(alert => {
//         const bsAlert = new bootstrap.Alert(alert);
//         bsAlert.close();
//     });
// }, 5000);

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Stock history filter form enhancement
document.addEventListener('DOMContentLoaded', function() {
    const medicineSelect = document.getElementById('medicine');
    if (medicineSelect) {
        medicineSelect.classList.add('form-select');
    }
    
    const filterForm = document.querySelector('.stock-history-filter form');
    if (filterForm) {
        const submitButton = filterForm.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.classList.add('btn', 'btn-primary');
        }
    }
});

function updateTime() {
    let now = new Date();
    let hours = now.getHours().toString().padStart(2, '0');
    let minutes = now.getMinutes().toString().padStart(2, '0');
    let seconds = now.getSeconds().toString().padStart(2, '0');
    let dateStr = now.toDateString();
    document.getElementById("current-time").innerText = `${dateStr}, ${hours}:${minutes}:${seconds}`;

    // Force a reload at midnight (00:00:00) to get new backend data
    if (hours === "00" && minutes === "00" && seconds === "00") {
        location.reload();
    }
}

// Run updateTime every second
setInterval(updateTime, 1000);

// Run immediately on page load
document.addEventListener("DOMContentLoaded", updateTime);

