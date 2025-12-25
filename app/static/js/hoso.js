document.addEventListener("DOMContentLoaded", function() {

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

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

document.addEventListener('DOMContentLoaded', function () {
    const avatarInput = document.getElementById('avatar-upload');
    const avatarContainer = document.getElementById('avatar-container');

    if (avatarInput) {

      avatarInput.addEventListener('change', async function () {
        const f = this.files[0];
        if (!f) return;
        const fd = new FormData();
        fd.append('file', f);

        const uploadUrl = this.dataset.url;

        try {
          const res = await fetch(uploadUrl,
            method: 'POST',
            body: fd,
          });
          const json = await res.json();
          if (json.success && json.image_url) {
            const img = avatarContainer.querySelector('img');
            if (img) img.setAttribute('src', json.image_url);

            location.reload();
          } else {
            alert(json.error || 'Upload thất bại');
          }
        } catch (e) {
          console.error(e);
          alert('Lỗi khi upload avatar');
        }
      });
    }
});