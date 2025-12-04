document.addEventListener("DOMContentLoaded", function() {
    // 1. Khởi tạo Tooltip của Bootstrap (cho nút upload ảnh)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Tự động tắt thông báo (Alert) sau 1 giây (1000ms)
    var alerts = document.querySelectorAll('.alert');
    if (alerts) {
        alerts.forEach(function(alert) {
            setTimeout(function() {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 1000);
        });
    }
});