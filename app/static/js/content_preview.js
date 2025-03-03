/**
 * Content Preview Functionality for LearningPulse
 * 
 * This script handles the content preview feature, allowing users to see
 * sample educational content for a topic before subscribing.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    const topicInput = document.getElementById('topic');
    const previewButton = document.getElementById('preview-button');
    const previewContainer = document.getElementById('preview-container');
    const difficultySelect = document.getElementById('preview-difficulty');
    const closePreviewButton = document.getElementById('close-preview');
    let previewLoading = false;
    
    // Only initialize if we have the necessary elements
    if (!topicInput || !previewContainer) return;
    
    // Create preview button if it doesn't exist
    if (!previewButton) {
        const topicGroup = topicInput.closest('.col-12');
        if (!topicGroup) return;
        
        // Create and append preview button
        const previewBtn = document.createElement('button');
        previewBtn.type = 'button';
        previewBtn.id = 'preview-button';
        previewBtn.className = 'btn btn-outline-info mt-2 w-100';
        previewBtn.innerHTML = '<i class="fas fa-eye me-1"></i> See Example Content';
        topicGroup.appendChild(previewBtn);
    }
    
    // Create difficulty select if it doesn't exist
    if (!difficultySelect) {
        const difficultyWrapper = document.createElement('div');
        difficultyWrapper.id = 'difficulty-wrapper';
        difficultyWrapper.className = 'd-none mt-2';
        difficultyWrapper.innerHTML = `
            <div class="d-flex">
                <select id="preview-difficulty" class="form-select me-2">
                    <option value="easy">Beginner</option>
                    <option value="medium" selected>Intermediate</option>
                    <option value="hard">Advanced</option>
                </select>
                <button id="refresh-preview" type="button" class="btn btn-outline-secondary">
                    <i class="fas fa-sync-alt"></i>
                </button>
            </div>
        `;
        
        const topicGroup = topicInput.closest('.col-12');
        if (topicGroup) {
            topicGroup.appendChild(difficultyWrapper);
        }
    }
    
    // Now get the elements that might have been just created
    const refreshButton = document.getElementById('refresh-preview');
    const difficultyWrapper = document.getElementById('difficulty-wrapper');
    
    // Event: Preview button click
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'preview-button' || e.target.closest('#preview-button')) {
            const topic = topicInput.value.trim();
            if (!topic) {
                showMessage('Please enter a topic first', 'warning');
                topicInput.focus();
                return;
            }
            
            // Show difficulty selector
            if (difficultyWrapper) {
                difficultyWrapper.classList.remove('d-none');
            }
            
            // Generate preview
            generatePreview(topic, 'medium');
        }
    });
    
    // Event: Refresh button click
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            const topic = topicInput.value.trim();
            const difficulty = document.getElementById('preview-difficulty').value;
            if (!topic) return;
            
            generatePreview(topic, difficulty);
        });
    }
    
    // Event: Difficulty change
    if (difficultySelect) {
        difficultySelect.addEventListener('change', function() {
            const topic = topicInput.value.trim();
            const difficulty = this.value;
            if (!topic) return;
            
            generatePreview(topic, difficulty);
        });
    }
    
    // Event: Close preview button
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'close-preview' || e.target.closest('#close-preview')) {
            closePreview();
        }
    });
    
    // Function to generate preview content
    async function generatePreview(topic, difficulty) {
        if (previewLoading) return;
        
        // Show loading state
        previewContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Generating content preview for "${topic}"...</p>
            </div>
        `;
        previewContainer.classList.remove('d-none');
        
        previewLoading = true;
        
        try {
            // Call the API
            const response = await fetch('/api/v1/preview/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    topic: topic,
                    difficulty: difficulty
                })
            });
            
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            
            const content = await response.text();
            
            // Show the preview
            previewContainer.innerHTML = `
                <div class="preview-header d-flex justify-content-between align-items-center mb-3">
                    <h3>Content Preview</h3>
                    <button id="close-preview" class="btn btn-sm btn-outline-secondary">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="preview-content">
                    ${content}
                </div>
                <div class="mt-3 text-center">
                    <button id="close-preview" class="btn btn-primary">
                        <i class="fas fa-check me-1"></i> Got it, continue subscription
                    </button>
                </div>
            `;
        } catch (error) {
            previewContainer.innerHTML = `
                <div class="alert alert-danger">
                    <p><strong>Error generating preview</strong></p>
                    <p>${error.message || 'Something went wrong. Please try again later.'}</p>
                    <button id="close-preview" class="btn btn-sm btn-outline-danger mt-2">Close</button>
                </div>
            `;
        } finally {
            previewLoading = false;
            
            // Scroll to preview
            previewContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    // Close preview
    function closePreview() {
        previewContainer.classList.add('d-none');
        previewContainer.innerHTML = '';
    }
    
    // Show message
    function showMessage(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show mt-2`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Insert after topic input
        const parent = topicInput.parentNode;
        parent.insertBefore(alert, topicInput.nextSibling);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    }
});