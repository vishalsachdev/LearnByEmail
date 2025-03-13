document.addEventListener('DOMContentLoaded', function () {
    // Get form elements
    const bulkActionForm = document.getElementById('bulk-action-form');
    const bulkActionSelect = document.getElementById('bulk-action');
    const bulkApplyButton = document.getElementById('bulk-apply');
    const bulkActionOptions = document.getElementById('bulk-action-options');
    const selectAllCheckbox = document.getElementById('select-all');
    const subscriptionCheckboxes = document.querySelectorAll('.subscription-checkbox');

    // Initialize timezone list for use in the timezone selector
    const timezonePairs = [
        { value: 'America/New_York', label: 'Eastern Time (ET)' },
        { value: 'America/Chicago', label: 'Central Time (CT)' },
        { value: 'America/Denver', label: 'Mountain Time (MT)' },
        { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
        { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
        { value: 'Pacific/Honolulu', label: 'Hawaii Time (HT)' },
        { value: 'Europe/London', label: 'GMT/UTC' },
        { value: 'Europe/Paris', label: 'Central European Time (CET)' },
        { value: 'Asia/Tokyo', label: 'Japan Standard Time (JST)' },
        { value: 'Australia/Sydney', label: 'Australian Eastern Time (AET)' }
    ];

    // Add additional timezones if they exist in the document
    if (typeof additionalTimezones !== 'undefined') {
        timezonePairs.push(...additionalTimezones);
    }

    // Function to check if at least one subscription is selected
    function checkSelections() {
        const selectedCount = Array.from(subscriptionCheckboxes).filter(checkbox => checkbox.checked).length;
        if (selectedCount > 0 && bulkActionSelect.value) {
            bulkApplyButton.disabled = false;
        } else {
            bulkApplyButton.disabled = true;
        }
        
        // Update the apply button text with selected count
        if (selectedCount > 0) {
            bulkApplyButton.innerHTML = `<i class="fas fa-check"></i> Apply (${selectedCount})`;
        } else {
            bulkApplyButton.innerHTML = `<i class="fas fa-check"></i> Apply`;
        }
    }

    // Toggle all checkboxes when "select all" is clicked
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function () {
            const isChecked = this.checked;
            subscriptionCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            checkSelections();
        });
    }

    // Update select all checkbox when individual checkboxes change
    subscriptionCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (selectAllCheckbox) {
                const allChecked = Array.from(subscriptionCheckboxes).every(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
            }
            checkSelections();
        });
    });

    // Show different options based on selected bulk action
    bulkActionSelect.addEventListener('change', function () {
        const action = this.value;
        bulkActionOptions.innerHTML = '';
        
        if (action) {
            bulkActionOptions.classList.remove('d-none');
            
            switch (action) {
                case 'change_time':
                    const timeHTML = `
                        <div class="input-group">
                            <span class="input-group-text">New Time</span>
                            <input type="time" id="bulk-time" name="preferred_time" class="form-control" required>
                        </div>
                    `;
                    bulkActionOptions.innerHTML = timeHTML;
                    break;
                    
                case 'change_timezone':
                    let timezoneHTML = `
                        <div class="input-group">
                            <span class="input-group-text">New Timezone</span>
                            <select id="bulk-timezone" name="timezone" class="form-select" required>
                    `;
                    
                    timezonePairs.forEach(tz => {
                        timezoneHTML += `<option value="${tz.value}">${tz.label}</option>`;
                    });
                    
                    timezoneHTML += `
                            </select>
                        </div>
                    `;
                    bulkActionOptions.innerHTML = timezoneHTML;
                    break;
                    
                case 'delete':
                    const confirmHTML = `
                        <div class="alert alert-warning mb-0">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="confirm-delete" name="confirm_delete" value="1" required>
                                <label class="form-check-label" for="confirm-delete">
                                    Confirm deletion of selected subscriptions
                                </label>
                            </div>
                        </div>
                    `;
                    bulkActionOptions.innerHTML = confirmHTML;
                    
                    // Add event listener to the confirmation checkbox
                    document.getElementById('confirm-delete').addEventListener('change', checkSelections);
                    break;
            }
        } else {
            bulkActionOptions.classList.add('d-none');
        }
        
        checkSelections();
    });

    // Validate form before submission
    bulkActionForm.addEventListener('submit', function (event) {
        const action = bulkActionSelect.value;
        const selectedCount = Array.from(subscriptionCheckboxes).filter(checkbox => checkbox.checked).length;
        
        if (!action || selectedCount === 0) {
            event.preventDefault();
            alert('Please select at least one subscription and an action.');
            return;
        }
        
        if (action === 'delete') {
            const confirmed = document.getElementById('confirm-delete')?.checked;
            if (!confirmed) {
                event.preventDefault();
                alert('Please confirm deletion by checking the confirmation box.');
                return;
            }
            
            if (!confirm(`Are you sure you want to delete ${selectedCount} subscription(s)?`)) {
                event.preventDefault();
                return;
            }
        }
    });

    // Initial check
    checkSelections();
});