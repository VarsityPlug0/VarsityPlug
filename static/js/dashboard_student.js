(function () {
    // Configuration constants for dashboard behavior
    const CONFIG = {
        // Renamed SLIDE_INTERVAL to be more generic for the new display
        DISPLAY_INTERVAL: 7000,       // Interval for auto-cycling single display (ms)
        NOTIFICATION_DURATION: 5000,  // Notification display duration (ms)
        SUBMISSION_CHECK_INTERVAL: 45000, // Check for new submissions every 45s
        NOTIFICATION_CHANCE: 0.05,    // 5% chance to show random notification
        API_TIMEOUT: 15000,           // API request timeout (ms)
        CHAT_DEBOUNCE_DELAY: 500,     // Debounce delay for chat input (ms)
        // CAROUSEL constants are no longer needed
    };

    // Name arrays for random notification messages
    const southAfricanNames = [ "Thabo", "Nomalanga", "Sipho", "Ayanda", "Lerato", "Mpho", "Zanele", "Tshepo", "Nomvula", "Sibusiso", "Khanyi", "Mandla", "Palesa", "Bongani", "Thandi", "Lwazi", "Nkosana", "Zodwa", "Kagiso", "Nandi" ];
    const westernNames = [ "James", "Sarah", "Johan", "Anika", "Michael", "Emily", "Pieter", "Chloe", "David", "Lisa", "Willem", "Sophie", "Thomas", "Hannah", "Riaan", "Megan", "Andrew", "Jessica", "Dirk", "Emma" ];
    const allNames = [...southAfricanNames, ...westernNames];

    // Utility to get CSRF token
    function getCsrfToken() {
        let token = null;
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) { token = input.value; }
        if (!token && document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                    token = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                    break;
                }
            }
        }
        if (!token) { console.error("CSRF token not found in input or cookies."); }
        return token;
    }

    // Debug logging
    function debugLog(message, data = null) {
        const timestamp = new Date().toISOString();
        if (data && (data.error || data.name === 'AbortError' || message.toLowerCase().includes('error') || message.toLowerCase().includes('fail'))) {
             console.error(`[VarsityPlug ${timestamp}] ${message}`, data || '');
        } else {
             console.log(`[VarsityPlug ${timestamp}] ${message}`, data || '');
        }
    }

    // Ensure HTTPS for API URLs
    function getApiUrl(baseUrl) {
        if (window.location.protocol === 'https:' && baseUrl && baseUrl.startsWith('http:')) {
            return baseUrl.replace(/^http:/, 'https:');
        }
        return baseUrl;
    }

    // Notification System (remains the same)
    const notificationSystem = {
        isShowing: false, queue: [], showTimeout: null,
        getRandomName() { return allNames[Math.floor(Math.random() * allNames.length)]; },
        _displayNext() { /* ... (implementation as before) ... */
            if (this.isShowing || this.queue.length === 0) return;
            this.isShowing = true;
            const { message, isError } = this.queue.shift();
            const notificationPopup = document.getElementById('notificationPopup');
            const notificationMessage = document.getElementById('notificationMessage');
            if (!notificationPopup || !notificationMessage) {
                debugLog('Notification elements missing', { popup: !!notificationPopup, message: !!notificationMessage });
                alert(message); this.isShowing = false; setTimeout(() => this._displayNext(), 100); return;
            }
            notificationMessage.textContent = message;
            notificationPopup.classList.remove('bg-danger', 'bg-primary', 'bg-warning', 'bg-info', 'active');
            setTimeout(() => {
                notificationPopup.classList.add(isError ? 'bg-danger' : 'bg-primary', 'active');
                notificationPopup.setAttribute('role', isError ? 'alert' : 'status');
            }, 50);
            clearTimeout(this.showTimeout);
            this.showTimeout = setTimeout(() => {
                notificationPopup.classList.remove('active'); this.isShowing = false; setTimeout(() => this._displayNext(), 500);
            }, CONFIG.NOTIFICATION_DURATION);
        },
        showNotification(message, isError = false) { const defaultMessage = `${this.getRandomName()} has sent their applications`; this.queue.push({ message: message || defaultMessage, isError }); if (!this.isShowing) { this._displayNext(); } },
        simulateNewSubmission() { if (Math.random() < CONFIG.NOTIFICATION_CHANCE) { this.showNotification(); } }
    };

    // University Selection System (remains the same)
    const universitySystem = { async selectUniversity(universityId) { /* ... (implementation as before) ... */
            const button = document.querySelector(`button[data-url*="/select_university/${universityId}/"]`);
            let url = button?.dataset.url;
            const csrfToken = getCsrfToken();
            if (!url || !csrfToken || !universityId) { debugLog('Select university data missing', { url: !!url, csrfToken: !!csrfToken, universityId }); notificationSystem.showNotification('Error: Cannot select university (data missing). Please refresh.', true); return; }
            url = getApiUrl(url);
            if(button) button.disabled = true;
            try {
                const controller = new AbortController(); const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);
                const response = await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }, signal: controller.signal }); clearTimeout(timeoutId);
                const data = await response.json().catch(() => { throw new Error(`Invalid response from server (Status: ${response.status})`); });
                if (!response.ok) { throw new Error(data.message || `HTTP error! Status: ${response.status}`); }
                if (data.success) {
                    notificationSystem.showNotification(data.message || 'University selected successfully!');
                    const appCountElement = document.getElementById('applicationCountDisplay');
                    if (appCountElement && data.application_count !== undefined) { appCountElement.textContent = data.application_count; debugLog(`Updated application count to ${data.application_count}`); }
                    debugLog('Reloading page after university selection (fallback).'); setTimeout(() => window.location.reload(), 1500);
                } else { throw new Error(data.message || 'Failed to select university.'); }
            } catch (error) {
                debugLog('Error selecting university', { error: error.message, name: error.name, universityId });
                let message = error.name === 'AbortError' ? 'Request timed out. Please try again.' : (error.message || 'An unknown error occurred during selection.');
                notificationSystem.showNotification(`Selection Failed: ${message}`, true);
            } finally { if(button) button.disabled = false; }
        }
    };

    // Form Submission System (remains the same)
    const formSystem = { isSubmitting: false, async submitForm(formElement, successCallback, errorCallback) { /* ... (implementation as before) ... */
            if (!formElement || this.isSubmitting) { debugLog(`Form submission blocked for ${formElement?.id}`, { isSubmitting: this.isSubmitting, formElementExists: !!formElement }); return; }
            this.isSubmitting = true; const submitButton = formElement.querySelector('button[type="submit"]'); if (submitButton) submitButton.disabled = true; const csrfToken = getCsrfToken();
            if (!csrfToken) { debugLog(`Form (${formElement.id}) data missing CSRF token`); notificationSystem.showNotification('Error: Authentication issue. Please refresh.', true); this.isSubmitting = false; if (submitButton) submitButton.disabled = false; return; }
            const formData = new FormData(formElement); const formAction = getApiUrl(formElement.action); debugLog(`Submitting form ${formElement.id} to ${formAction}`);
            try {
                const controller = new AbortController(); const timeoutDuration = formElement.enctype === 'multipart/form-data' ? CONFIG.API_TIMEOUT * 3 : CONFIG.API_TIMEOUT * 2; const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);
                const response = await fetch(formAction, { method: 'POST', headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' }, body: formData, signal: controller.signal }); clearTimeout(timeoutId);
                if (response.ok || (response.status >= 300 && response.status < 400)) {
                    debugLog(`Form ${formElement.id} submitted, Status: ${response.status}, Redirected: ${response.redirected}`);
                    if (response.redirected) { if (successCallback) { successCallback(response); } else { notificationSystem.showNotification('Submission successful! Reloading...'); setTimeout(() => window.location.reload(), 1000); } return; }
                    const text = await response.text(); const parser = new DOMParser(); const doc = parser.parseFromString(text, 'text/html'); const errorMessages = Array.from(doc.querySelectorAll('.alert-danger, .errorlist li')).map(el => el.textContent.trim()).filter(msg => msg).join('; ');
                    if (errorMessages) { throw new Error(errorMessages); } else { if (successCallback) { successCallback(response, text); } else { notificationSystem.showNotification('Submission successful!'); setTimeout(() => window.location.reload(), 1000); } }
                } else { const errorData = await response.json().catch(() => null); throw new Error(errorData?.error || errorData?.message || `Submission failed. Status: ${response.status}`); }
            } catch (error) { debugLog(`Form (${formElement.id}) submission error`, { error: error.message, name: error.name }); if (errorCallback) { errorCallback(error); } else { let message = error.name === 'AbortError' ? 'Request timed out.' : error.message; notificationSystem.showNotification(`Error: ${message}`, true); } } finally { this.isSubmitting = false; if (submitButton) submitButton.disabled = false; }
        },
        handleMarksSubmit(e) { e.preventDefault(); debugLog("Handling marks form submit..."); this.submitForm(e.target, (response, responseText) => { let successMessage = 'Marks updated successfully! Reloading...'; if (responseText) { const parser = new DOMParser(); const doc = parser.parseFromString(responseText, 'text/html'); const successAlert = doc.querySelector('.alert-success'); if (successAlert) successMessage = successAlert.textContent.trim(); } notificationSystem.showNotification(successMessage); setTimeout(() => window.location.reload(), 1500); }, (error) => { notificationSystem.showNotification(`Marks Update Failed: ${error.message}`, true); }); },
        handleUploadSubmit(e) { e.preventDefault(); debugLog(`Handling upload form submit for form: ${e.target.id}`); const isPopForm = e.target.id === 'popUploadForm'; const successMsg = isPopForm ? 'Proof of Payment uploaded successfully! Reloading...' : 'Document uploaded successfully! Reloading...'; this.submitForm(e.target, (response, responseText) => { let extractedSuccessMsg = null; if (responseText) { const parser = new DOMParser(); const doc = parser.parseFromString(responseText, 'text/html'); const successAlert = doc.querySelector('.alert-success'); if (successAlert) extractedSuccessMsg = successAlert.textContent.trim(); } notificationSystem.showNotification(extractedSuccessMsg || successMsg); if (isPopForm) { const popModalElement = document.getElementById('uploadPopModal'); if (popModalElement && bootstrap?.Modal) { const modalInstance = bootstrap.Modal.getInstance(popModalElement); if (modalInstance) modalInstance.hide(); } } setTimeout(() => window.location.reload(), 1500); }, (error) => { notificationSystem.showNotification(`Upload Failed: ${error.message}`, true); }); }
    };

    // Chat System (remains the same)
    const chatSystem = { isSubmitting: false, debounceTimeout: null, init() { /* ... (implementation as before) ... */
            const chatForm = document.getElementById('aiChatForm'); const chatInput = document.getElementById('aiChatInput'); const chatMessages = document.getElementById('aiChatMessages'); const chatToggle = document.getElementById('aiChatToggle'); const chatBody = document.getElementById('aiChatBody'); let chatUrl = chatForm?.dataset.url;
            if (!chatForm || !chatInput || !chatMessages || !chatUrl) { debugLog('Chat elements or URL missing', { chatForm: !!chatForm, chatInput: !!chatInput, chatMessages: !!chatMessages, chatUrl: !!chatUrl }); return; } chatUrl = getApiUrl(chatUrl);
            const appendChatMessage = (message, type) => { const messageDiv = document.createElement('div'); messageDiv.classList.add('chat-message', type); messageDiv.textContent = message; chatMessages.appendChild(messageDiv); if(chatBody) { setTimeout(() => { chatBody.scrollTop = chatBody.scrollHeight; }, 0); } return messageDiv; };
            const submitChatRequest = async () => { if (this.isSubmitting) return; const message = chatInput.value.trim(); if (!message) return; this.isSubmitting = true; chatInput.disabled = true; const submitButton = chatForm.querySelector('button[type="submit"]'); if (submitButton) submitButton.disabled = true; const csrfToken = getCsrfToken(); if (!csrfToken) { debugLog('CSRF token missing for chat submission'); appendChatMessage('Error: Authentication issue.', 'error'); this.isSubmitting = false; chatInput.disabled = false; if (submitButton) submitButton.disabled = false; return; } appendChatMessage(message, 'user'); chatInput.value = ''; const thinkingMsg = appendChatMessage('...', 'ai thinking'); try { const controller = new AbortController(); const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT); const response = await fetch(chatUrl, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' }, body: JSON.stringify({ message }), signal: controller.signal }); clearTimeout(timeoutId); const data = await response.json().catch(() => { throw new Error(`Invalid response from AI assistant (Status: ${response.status})`); }); thinkingMsg.remove(); if (!response.ok) { if (response.status === 429) { throw new Error('Too many requests. Please try again later.'); } throw new Error(data.error || `Assistant error! Status: ${response.status}`); } if (data.error) throw new Error(data.error); appendChatMessage(data.response || 'Sorry, I couldn’t respond.', 'ai'); } catch (error) { thinkingMsg.remove(); debugLog('Chat error', { error: error.message, name: error.name }); let displayError = error.name === 'AbortError' ? 'Request timed out.' : error.message; appendChatMessage(`Error: ${displayError}`, 'error'); } finally { this.isSubmitting = false; chatInput.disabled = false; if (submitButton) submitButton.disabled = false; chatInput.focus(); } };
            chatForm.addEventListener('submit', (e) => { e.preventDefault(); clearTimeout(this.debounceTimeout); this.debounceTimeout = setTimeout(submitChatRequest, CONFIG.CHAT_DEBOUNCE_DELAY); });
            if (chatToggle && chatBody) { chatToggle.addEventListener('click', () => { const isHidden = chatBody.style.display === 'none'; chatBody.style.display = isHidden ? 'block' : 'none'; chatToggle.textContent = isHidden ? '−' : '+'; chatToggle.setAttribute('aria-label', isHidden ? 'Minimize chat window' : 'Expand chat window'); if(isHidden) chatInput.focus(); }); } else { debugLog('Chat toggle or body missing', { chatToggle: !!chatToggle, chatBody: !!chatBody }); }
        }
    };

    // **** REMOVED Bootstrap Carousel Initialization System ****
    // const carouselSystem = { ... };


    // **** NEW: System for Auto-Cycling Single University Display ****
    const qualifiedDisplaySystem = {
        displayElement: null,
        universities: [],
        currentIndex: -1,
        intervalId: null,
        intervalMs: CONFIG.DISPLAY_INTERVAL || 7000, // Use config or default

        init() {
            debugLog("Initializing Qualified Display System...");
            this.displayElement = document.getElementById('qualifiedUniversityDisplayArea');
            const dataScript = document.getElementById('qualifiedUniversitiesData');

            if (!this.displayElement) {
                debugLog("Qualified display area (#qualifiedUniversityDisplayArea) not found.");
                return; // Cannot proceed
            }
            if (!dataScript) {
                 debugLog("Qualified universities data script (#qualifiedUniversitiesData) not found.");
                 this.displayElement.innerHTML = '<p class="text-muted">Could not load university data.</p>'; // Inform user
                 return;
            }

            try {
                 this.universities = JSON.parse(dataScript.textContent || '[]');
                 debugLog(`Parsed ${this.universities.length} qualified universities from JSON.`);
            } catch (e) {
                 debugLog("Error parsing qualified universities JSON data.", { error: e });
                 this.universities = [];
                 this.displayElement.innerHTML = '<p class="text-danger">Error loading university data.</p>';
                 return;
            }

            if (this.universities.length === 0) {
                 debugLog("No qualified universities data to display.");
                 // The HTML template's {% else %} block should handle showing the message
                 // We can clear the placeholder just in case
                 this.displayElement.innerHTML = '';
                 return;
            }

            // Initial display
            this.displayNextUniversity();

            // Start cycling
            this.intervalId = setInterval(() => {
                this.displayNextUniversity();
            }, this.intervalMs);
             debugLog(`Started auto-cycling display interval (${this.intervalMs}ms).`);

        },

        generateUniversityCardHTML(uniData) {
             // Generates HTML for a single university card based on the data structure
             // Ensure data fields (like detail_url, select_url) are present from the view
             if (!uniData) return '<p class="text-warning">Error displaying university.</p>';

             // Using template literals for cleaner HTML construction
             // Added Font Awesome icons - ensure Font Awesome CSS is loaded
             return `
                <div class="card mx-auto" style="max-width: 500px; border: 1px solid #dee2e6; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-radius: 8px;">
                    <div class="card-body text-center">
                        <h3 class="card-title h5">${uniData.name || "Unknown University"}</h3>
                        <p class="card-text mb-1">
                           <i class="fas fa-map-marker-alt text-secondary"></i>
                           ${uniData.location || "South Africa"}
                        </p>
                        <p class="card-text mb-1">
                            <small class="text-muted">
                                <i class="fas fa-calendar-alt"></i> Due: ${uniData.due_date || "TBD"} |
                                <i class="fas fa-dollar-sign"></i> Fee: ${uniData.application_fee || "N/A"}
                            </small>
                        </p>
                        <div class="d-flex justify-content-center gap-2 mt-3">
                            <a href="${uniData.detail_url || '#'}" class="btn btn-outline-secondary btn-sm" aria-label="View details for ${uniData.name || 'university'}">View Details</a>
                            <button onclick="selectUniversity(${uniData.id})" class="btn btn-primary btn-sm" data-url="${uniData.select_url || '#'}" aria-label="Select ${uniData.name || 'university'}">Select</button>
                        </div>
                    </div>
                </div>
             `;
        },

        displayNextUniversity() {
            if (!this.universities || this.universities.length === 0) {
                 this.displayElement.innerHTML = ''; // Clear if list becomes empty unexpectedly
                 return;
            }

             // Cycle through index
            this.currentIndex++;
            if (this.currentIndex >= this.universities.length) {
                this.currentIndex = 0; // Loop back to start
            }

            const currentUni = this.universities[this.currentIndex];
            const cardHTML = this.generateUniversityCardHTML(currentUni);

            // Update the display area
             if (this.displayElement) {
                this.displayElement.innerHTML = cardHTML;
             } else {
                  debugLog("Display element not found when trying to update university card.");
             }
        },

        // Optional: Method to stop cycling if needed later
        stopCycling() {
             if (this.intervalId) {
                 clearInterval(this.intervalId);
                 this.intervalId = null;
                 debugLog("Stopped auto-cycling display.");
             }
        }
    };

    // Proof of Payment Modal Trigger Handling (remains the same)
    const popModalSystem = { init() { /* ... (implementation as before) ... */
             const popModalElement = document.getElementById('uploadPopModal'); if (!popModalElement) { debugLog("Proof of Payment modal element (#uploadPopModal) not found."); return; }
             if (typeof bootstrap === 'undefined' || !bootstrap.Modal) { debugLog("Bootstrap Modal class not found for PoP modal."); return; }
             let popModalInstance = null; try { popModalInstance = new bootstrap.Modal(popModalElement); } catch (e) { debugLog("Error initializing PoP Bootstrap Modal instance", { error: e }); return; }
             const popUniversityName = document.getElementById('popUniversityName'); const popUploadUniversityId = document.getElementById('popUploadUniversityId'); const popUploadForm = document.getElementById('popUploadForm');
             if (!popUniversityName || !popUploadUniversityId || !popUploadForm) { debugLog("Required elements within PoP modal not found.", { nameEl: !!popUniversityName, idInput: !!popUploadUniversityId, formEl: !!popUploadForm }); return; }
             document.querySelectorAll('.upload-pop-btn').forEach(button => { button.addEventListener('click', (e) => { const uniId = button.dataset.uniId; const uniName = button.dataset.uniName; if (!uniId || !uniName) { debugLog("Missing data attributes on PoP button.", { uniId, uniName }); notificationSystem.showNotification("Cannot open upload form: missing university info.", true); return; } popUniversityName.textContent = uniName; popUploadUniversityId.value = uniId; if (popModalInstance) { popModalInstance.show(); } else { debugLog("PoP modal instance not available to show."); } }); }); debugLog("PoP modal button listeners attached.");
             if (!popUploadForm.dataset.listenerAttached) { popUploadForm.addEventListener('submit', (e) => formSystem.handleUploadSubmit(e)); popUploadForm.dataset.listenerAttached = 'true'; debugLog("PoP form submit listener attached."); }
        }
    };


    // Event Listeners Setup
    const initEventListeners = () => {
        document.addEventListener('DOMContentLoaded', () => {
            debugLog('DOM loaded, initializing dashboard components...');
            try {
                // Initialize systems
                qualifiedDisplaySystem.init(); // **** CHANGED: Initialize new display system ****
                chatSystem.init();
                popModalSystem.init();

                 // Only start simulation interval if configured
                 if (CONFIG.SUBMISSION_CHECK_INTERVAL > 0 && CONFIG.NOTIFICATION_CHANCE > 0) {
                     setInterval(() => notificationSystem.simulateNewSubmission(), CONFIG.SUBMISSION_CHECK_INTERVAL);
                     debugLog(`Notification simulation started (Interval: ${CONFIG.SUBMISSION_CHECK_INTERVAL}ms, Chance: ${CONFIG.NOTIFICATION_CHANCE*100}%)`);
                 }

                // Attach form listeners
                const marksForm = document.getElementById('marksForm');
                const uploadForm = document.getElementById('uploadForm'); // Main upload form

                if (marksForm && !marksForm.dataset.listenerAttached) {
                    marksForm.addEventListener('submit', (e) => formSystem.handleMarksSubmit(e));
                    marksForm.dataset.listenerAttached = 'true';
                    debugLog('Marks form listener attached');
                } else if (!marksForm) { debugLog('Marks form not found'); }

                if (uploadForm && uploadForm.id !== 'popUploadForm' && !uploadForm.dataset.listenerAttached) {
                    uploadForm.addEventListener('submit', (e) => formSystem.handleUploadSubmit(e));
                     uploadForm.dataset.listenerAttached = 'true';
                    debugLog('Main Upload form listener attached');
                } else if (!uploadForm) { debugLog('Main Upload form not found'); }

                 debugLog('Dashboard component initialization complete.');

            } catch (error) {
                debugLog('Initialization error within DOMContentLoaded', { error: error.message, stack: error.stack });
                notificationSystem.showNotification('Error initializing dashboard components. Please refresh.', true);
            }
        });
    };

    // Expose selectUniversity globally (remains the same)
    try {
         if (typeof window !== 'undefined') {
             if (!window.selectUniversity) { window.selectUniversity = (universityId) => universitySystem.selectUniversity(universityId); debugLog('selectUniversity function exposed globally.'); } else { debugLog('selectUniversity function already exposed.'); }
         } else { debugLog('Window object not found, cannot expose selectUniversity globally.'); }
    } catch (error) { debugLog('Error exposing selectUniversity globally', { error: error.message }); }


    // Initialize event listeners safely (remains the same)
    try {
         if (!window.dashboardScriptInitialized) { initEventListeners(); window.dashboardScriptInitialized = true; debugLog('Dashboard JavaScript initialization sequence started.'); } else { debugLog('Dashboard JavaScript initialization skipped (already initialized).'); }
    } catch (error) { debugLog('Failed to start dashboard initialization', { error: error.message, stack: error.stack }); try { notificationSystem.showNotification('Critical Error initializing dashboard. Please refresh.', true); } catch (notifyError) { console.error("Fallback Notification Error:", notifyError); alert("Critical Error initializing dashboard. Please refresh."); } }

})(); // End IIFE