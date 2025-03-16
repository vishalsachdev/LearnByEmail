/**
 * Content Preview Functionality for LearnByEmail
 * 
 * This script handles the content preview feature, allowing users to see
 * sample educational content for a topic before subscribing.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Content preview script loaded');
    
    // Cache DOM elements
    const topicInput = document.getElementById('topic');
    console.log('Topic input found:', topicInput);
    
    const previewButton = document.getElementById('preview-button');
    console.log('Preview button found:', previewButton);
    
    const previewContainer = document.getElementById('preview-container');
    console.log('Preview container found:', previewContainer);
    
    const difficultySelect = document.getElementById('preview-difficulty');
    console.log('Difficulty select found:', difficultySelect);
    
    const refreshPreviewButton = document.getElementById('refresh-preview');
    console.log('Refresh button found:', refreshPreviewButton);
    
    const closePreviewButton = document.getElementById('close-preview');
    let previewLoading = false;
    
    // Debug all elements
    console.log('All elements in document:', document.querySelectorAll('*').length);
    console.log('All buttons in document:', document.querySelectorAll('button').length);
    console.log('All elements with ID preview-button:', document.querySelectorAll('#preview-button').length);
    
    // Only initialize if we have the necessary element - topic input is required
    if (!topicInput) {
        console.error('Topic input not found');
        return;
    }
    
    // If no preview container exists, create one
    if (!previewContainer) {
        // Find the form element
        const form = document.querySelector('form');
        if (!form) {
            console.error('Form not found');
            return;
        }
        
        // Create preview container
        previewContainer = document.createElement('div');
        previewContainer.id = 'preview-container';
        previewContainer.style.margin = '20px 0';
        previewContainer.style.display = 'none';
        
        // Insert after topic or before preferred time
        const preferredTimeGroup = document.querySelector('.form-group:nth-of-type(2)');
        if (preferredTimeGroup) {
            form.insertBefore(previewContainer, preferredTimeGroup);
        } else {
            form.appendChild(previewContainer);
        }
    }
    
    // Ensure we have a preview button
    if (!previewButton) {
        console.log('Creating preview button');
        previewButton = document.getElementById('preview-button');
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
    
    // Event: Preview button click - use both direct binding and backup event delegation
    // Direct binding first
    if (previewButton) {
        console.log('Adding direct click handler to preview button');
        previewButton.addEventListener('click', function(e) {
            console.log('Preview button direct click handler triggered');
            handlePreviewButtonClick(e);
        });
    }
    
    // Backup event delegation on document for redundancy
    document.addEventListener('click', function(e) {
        if (e.target && (e.target.id === 'preview-button' || e.target.closest('#preview-button'))) {
            console.log('Preview button delegation click handler triggered');
            handlePreviewButtonClick(e);
        }
    });
    
    // Shared handler function
    function handlePreviewButtonClick(e) {
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
        
        // Get currently selected difficulty
        const difficulty = document.getElementById('preview-difficulty')?.value || 'medium';
        
        // Generate preview with selected difficulty
        generatePreview(topic, difficulty);
    }
    
    // Event: Refresh button click - both direct and delegation
    if (refreshButton) {
        console.log('Adding direct click handler to refresh button');
        refreshButton.addEventListener('click', function() {
            console.log('Refresh button direct click handler triggered');
            handleRefreshButtonClick();
        });
    }
    
    // Backup event delegation for refresh
    document.addEventListener('click', function(e) {
        if (e.target && (e.target.id === 'refresh-preview' || e.target.closest('#refresh-preview'))) {
            console.log('Refresh button delegation click handler triggered');
            handleRefreshButtonClick();
        }
    });
    
    // Shared handler for refresh
    function handleRefreshButtonClick() {
        const topic = topicInput.value.trim();
        const difficulty = document.getElementById('preview-difficulty')?.value || 'medium';
        if (!topic) return;
        
        console.log('Refreshing preview for topic:', topic, 'difficulty:', difficulty);
        generatePreview(topic, difficulty);
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
    
    // Event: Use event delegation for close and continue buttons
    document.addEventListener('click', function(e) {
        // Close preview button - match both the X and the "Got it" button
        if (e.target && (e.target.id === 'close-preview' || e.target.closest('#close-preview'))) {
            closePreview();
        }
    });
    
    // Log to debug
    console.log('Preview button setup complete. Click handlers attached.');
    
    // Function to generate preview content
    async function generatePreview(topic, difficulty) {
        if (previewLoading) {
            console.log('Preview generation already in progress, skipping');
            return;
        }
        
        console.log('Starting preview generation for topic:', topic, 'difficulty:', difficulty);
        
        // First ensure preview container exists and is properly set up
        if (!previewContainer) {
            console.log('Creating preview container as it does not exist');
            previewContainer = document.getElementById('preview-container');
            
            if (!previewContainer) {
                // Create it if it still doesn't exist
                previewContainer = document.createElement('div');
                previewContainer.id = 'preview-container';
                previewContainer.className = 'mt-4 mb-4';
                
                // Insert after topic field
                const topicField = document.getElementById('topic');
                if (topicField && topicField.parentNode) {
                    const parentCol = topicField.closest('.col-12');
                    if (parentCol && parentCol.parentNode) {
                        parentCol.parentNode.insertBefore(previewContainer, parentCol.nextSibling);
                    } else {
                        // Alternative - insert after difficulty wrapper
                        const diffWrapper = document.getElementById('difficulty-wrapper');
                        if (diffWrapper && diffWrapper.parentNode) {
                            diffWrapper.parentNode.insertBefore(previewContainer, diffWrapper.nextSibling);
                        }
                    }
                }
            }
        }
        
        console.log('Preview container:', previewContainer);
        
        // Show loading state
        previewContainer.innerHTML = `
            <div class="card">
                <div class="card-body text-center py-5">
                    <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mb-0 mt-3 text-secondary">Generating content preview for <strong>${topic}</strong>...</p>
                </div>
            </div>
        `;
        previewContainer.classList.remove('d-none');
        previewContainer.style.display = 'block';
        
        // Add spin animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        console.log('Loading animation visible:', previewContainer.style.display);
        previewLoading = true;
        
        try {
            // Get auth token from cookie
            const cookies = document.cookie.split(';').reduce((acc, cookie) => {
                const [key, value] = cookie.trim().split('=');
                acc[key] = value;
                return acc;
            }, {});
            const token = cookies['access_token'];
            
            console.log('Using token for preview request:', token ? 'Token found' : 'No token found');
            
            // Try to get the CSRF token from various sources
            // First try to get from a form input
            let csrfToken = '';
            const csrfTokenInput = document.querySelector('input[name="csrf_token"]');
            if (csrfTokenInput) {
                csrfToken = csrfTokenInput.value;
                console.log('Found CSRF token in form input');
            } 
            
            // If not found in form, try to get from cookie
            if (!csrfToken) {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.startsWith('csrf_token=')) {
                        csrfToken = cookie.substring('csrf_token='.length, cookie.length);
                        console.log('Found CSRF token in cookie');
                        break;
                    }
                }
            }
            
            console.log('Using CSRF token for preview request:', csrfToken ? 'Token found' : 'No CSRF token found');
            if (csrfToken) {
                console.log('CSRF token begins with:', csrfToken.substring(0, 10) + '...');
            }
            
            // Call the API
            const response = await fetch('/api/v1/preview/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : '',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    topic: topic,
                    difficulty: difficulty
                }),
                credentials: 'include' // Include cookies in the request
            });
            
            console.log('Preview API response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Preview API error:', response.status, errorText);
                throw new Error(`Error ${response.status}: ${errorText}`);
            }
            
            const content = await response.text();
            console.log("Content received, length:", content.length);
            
            // Show the preview
            previewContainer.innerHTML = `
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Content Preview</h5>
                        <button id="close-preview" class="btn btn-sm btn-outline-light">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="card-body">
                        ${content}
                    </div>
                    <div class="card-footer text-center bg-white border-top-0 pt-0">
                        <button id="close-preview" class="btn btn-primary">
                            <i class="fas fa-check me-2"></i> Got it, continue subscription
                        </button>
                    </div>
                </div>
            `;
            
            // Ensure container is visible
            previewContainer.classList.remove('d-none');
            previewContainer.style.display = 'block';
            console.log("Preview container should be visible now:", previewContainer.style.display);
            
            // Force a reflow/repaint to ensure the content is visible
            void previewContainer.offsetHeight;
        } catch (error) {
            previewContainer.innerHTML = `
                <div class="card border-danger">
                    <div class="card-header bg-danger text-white">
                        <h5 class="mb-0">Error generating preview</h5>
                    </div>
                    <div class="card-body">
                        <p>${error.message || 'Something went wrong. Please try again later.'}</p>
                        <div class="text-center mt-3">
                            <button id="close-preview" class="btn btn-danger">
                                <i class="fas fa-times me-2"></i> Close
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            // Ensure container is visible
            previewContainer.style.display = 'block';
        } finally {
            previewLoading = false;
            
            // Scroll to preview
            previewContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    // Close preview
    function closePreview() {
        console.log('Closing preview');
        if (previewContainer) {
            previewContainer.style.display = 'none';
            previewContainer.innerHTML = '';
        }
        previewLoading = false;
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