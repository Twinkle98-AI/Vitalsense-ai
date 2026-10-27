/**
 * VitalSense AI - Client-Side Enhancements
 * Handles delete confirmation dialogs, client-side search filtering,
 * form submission state/duplicate prevention, and dismissible alerts.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Lucide Icons if available
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 2. Delete Confirmation Modal Setup
    initDeleteModal();

    // 3. Client-Side Search Enhancement
    initClientSearch();

    // 4. Form Submit Prevention & Loading Indicator
    initFormSubmissions();

    // 5. Auto-dismiss alerts after 6 seconds (except error/danger alerts)
    initAlertAutoDismiss();
});

/**
 * Initializes Delete Confirmation Modal
 */
function initDeleteModal() {
    const modal = document.getElementById('deleteModal');
    const btnCancel = document.getElementById('btnCancelDelete');
    const deleteForm = document.getElementById('deleteForm');
    const deletePatientName = document.getElementById('deletePatientName');
    const deletePatientId = document.getElementById('deletePatientId');

    if (!modal) return;

    window.openDeleteModal = function (patientId, patientName) {
        if (deletePatientName) deletePatientName.textContent = patientName;
        if (deletePatientId) deletePatientId.textContent = '#' + patientId;
        if (deleteForm) deleteForm.action = `/patients/${encodeURIComponent(patientId)}/delete`;

        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
    };

    function closeModal() {
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
    }

    if (btnCancel) {
        btnCancel.addEventListener('click', closeModal);
    }

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('is-open')) {
            closeModal();
        }
    });
}

/**
 * Client-Side Instant Search Filter
 */
function initClientSearch() {
    const searchInput = document.getElementById('patientSearchInput');
    const table = document.getElementById('patientsTable');
    if (!searchInput || !table) return;

    const rows = table.querySelectorAll('tbody tr.table-row');
    if (!rows.length) return;

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase().trim();
        let visibleCount = 0;

        rows.forEach(row => {
            const nameEl = row.querySelector('.patient-name-link');
            const emailEl = row.querySelector('.email-text');
            const idEl = row.querySelector('.badge-id');

            const name = nameEl ? nameEl.textContent.toLowerCase() : '';
            const email = emailEl ? emailEl.textContent.toLowerCase() : '';
            const id = idEl ? idEl.textContent.toLowerCase() : '';

            const matches = !query || name.includes(query) || email.includes(query) || id.includes(query);

            if (matches) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Update badge counter dynamically
        const badge = document.getElementById('patient-count-badge');
        if (badge) {
            badge.textContent = `${visibleCount} record${visibleCount !== 1 ? 's' : ''}`;
        }
    });
}

/**
 * Form Submit Handling: Prevents duplicate submissions and shows loading feedback
 * while awaiting NVIDIA NIM inference.
 */
function initFormSubmissions() {
    const forms = document.querySelectorAll('#patientForm, #editPatientForm');

    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('.btn-submit-with-loader');
            if (submitBtn) {
                // If already submitted, prevent duplicate click
                if (submitBtn.classList.contains('btn-loading')) {
                    e.preventDefault();
                    return false;
                }

                // Add loading class to show spinner
                submitBtn.classList.add('btn-loading');
                const btnText = submitBtn.querySelector('.btn-text');
                if (btnText) {
                    btnText.textContent = 'Processing with NVIDIA NIM...';
                }
            }
        });
    });
}

/**
 * Auto-dismiss non-danger alerts after 6 seconds
 */
function initAlertAutoDismiss() {
    const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentElement) {
                alert.style.transition = 'opacity 0.4s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 400);
            }
        }, 6000);
    });
}
