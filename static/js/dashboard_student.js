(function () {
    // Configuration constants for dashboard behavior
    const CONFIG = {
        SLIDE_INTERVAL: 7000,         // Carousel slide interval (ms) - Increased slightly
        NOTIFICATION_DURATION: 5000,  // Notification display duration (ms)
        SUBMISSION_CHECK_INTERVAL: 45000, // Check for new submissions every 45s (Reduced frequency)
        NOTIFICATION_CHANCE: 0.05,    // 5% chance to show random notification
        API_TIMEOUT: 15000,           // API request timeout (ms) - Increased slightly
        CHAT_DEBOUNCE_DELAY: 500,     // Debounce delay for chat input (ms)
        CAROUSEL_RETRY_ATTEMPTS: 3,     // Number of carousel init retries
        CAROUSEL_RETRY_DELAY: 500     // Delay between retries (ms)
    };

    // Name arrays for random notification messages
    const southAfricanNames = [
        "Thabo", "Nomalanga", "Sipho", "Ayanda", "Lerato", "Mpho", "Zanele", "Tshepo",
        "Nomvula", "Sibusiso", "Khanyi", "Mandla", "Palesa", "Bongani", "Thandi", "Lwazi",
        "Nkosana", "Zodwa", "Kagiso", "Nandi"
    ];
    const westernNames = [
        "James", "Sarah", "Johan", "Anika", "Michael", "Emily", "Pieter", "Chloe",
        "David", "Lisa", "Willem", "Sophie", "Thomas", "Hannah", "Riaan", "Megan",
        "Andrew", "Jessica", "Dirk", "Emma"
    ];
    const allNames = [...southAfricanNames, ...westernNames];

    // Utility to get CSRF token from cookies or hidden input
    function getCsrfToken() {
        let token = null;
        // Try input field first (common practice)
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) {
            token = input.value;
        }
        // Fallback to cookie
        if (!token) {
             if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                        token = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                        break;
                    }
                }
            }
        }
        if (!token) {
            console.error("CSRF token not found in input or cookies.");
        }
        return token;
    }


    // Debug logging with enhanced error context
    function debugLog(message, data = null) {
        const timestamp = new Date().toISOString();
        console.log(`[VarsityPlug ${timestamp}] ${message}`, data || '');
    }

    // Ensure HTTPS for API URLs in production
    function getApiUrl(baseUrl) {
        const isProduction = window.location.protocol === 'https:';
        // Basic check, might need refinement based on actual deployment URLs
        if (isProduction && baseUrl && baseUrl.startsWith('http:')) {
            return baseUrl.replace(/^http:/, 'https:');
        }
        return baseUrl;
    }

    // Notification System
    const notificationSystem = {
        isShowing: false,
        queue: [],
        showTimeout: null,
        getRandomName() {
            return allNames[Math.floor(Math.random() * allNames.length)];
        },
        _displayNext() {
            if (this.isShowing || this.queue.length === 0) {
                return;
            }
            this.isShowing = true;
            const { message, isError } = this.queue.shift();

            const notificationPopup = document.getElementById('notificationPopup');
            const notificationMessage = document.getElementById('notificationMessage');
            if (!notificationPopup || !notificationMessage) {
                debugLog('Notification elements missing', { popup: !!notificationPopup, message: !!notificationMessage });
                alert(message); // Fallback to alert
                this.isShowing = false;
                // Try displaying next immediately if elements missing
                setTimeout(() => this._displayNext(), 100);
                return;
            }

            notificationMessage.textContent = message;
            notificationPopup.classList.remove('bg-danger', 'bg-primary', 'bg-warning', 'bg-info'); // Clear previous types
            notificationPopup.classList.add(isError ? 'bg-danger' : 'bg-primary', 'active'); // Default to primary, use danger for errors
            notificationPopup.setAttribute('role', isError ? 'alert' : 'status');

            this.showTimeout = setTimeout(() => {
                notificationPopup.classList.remove('active');
                this.isShowing = false;
                 // Check queue again after hiding
                 setTimeout(() => this._displayNext(), 500); // Slight delay before showing next
            }, CONFIG.NOTIFICATION_DURATION);
        },
        showNotification(message, isError = false) {
            const defaultMessage = `${this.getRandomName()} has sent their applications`;
            this.queue.push({ message: message || defaultMessage, isError });
            if (!this.isShowing) {
                 this._displayNext();
            }
        },
        simulateNewSubmission() {
            if (Math.random() < CONFIG.NOTIFICATION_CHANCE) {
                this.showNotification(); // Show random success message
            }
        }
    };

    // University Selection System
    const universitySystem = {
        async selectUniversity(universityId) {
            const button = document.querySelector(`button[data-url*="/select_university/${universityId}/"]`); // More robust selector
            let url = button?.dataset.url; // Get URL from the data-url attribute
            const csrfToken = getCsrfToken();

            if (!url || !csrfToken || !universityId) {
                debugLog('Select university data missing', { url: !!url, csrfToken: !!csrfToken, universityId });
                notificationSystem.showNotification('Error: Cannot select university (data missing). Please refresh.', true);
                return;
            }
            url = getApiUrl(url);

            // Disable button during request
            if(button) button.disabled = true;

            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest' // Standard header for AJAX
                    },
                    // No body needed if the uni_id is in the URL as per view definition
                    // body: JSON.stringify({ university_id: universityId }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);

                const data = await response.json().catch(() => {
                    // Handle cases where response is not valid JSON (e.g., redirects, server errors)
                     throw new Error(`Invalid response from server (Status: ${response.status})`);
                });

                if (!response.ok) {
                    // Throw error with message from backend if available
                    throw new Error(data.message || `HTTP error! Status: ${response.status}`);
                }

                if (data.success) {
                    notificationSystem.showNotification(data.message || 'University selected successfully!');
                    // Update UI dynamically instead of full reload if possible
                    const appCountElement = document.getElementById('applicationCountDisplay');
                    if (appCountElement && data.application_count !== undefined) {
                       appCountElement.textContent = data.application_count;
                       debugLog(`Updated application count to ${data.application_count}`);
                       // Consider adding the university to the 'Selected Universities' table dynamically here
                       // This avoids a full page reload but requires more complex DOM manipulation
                    } else {
                        // Fallback to reload if dynamic update isn't feasible/implemented
                        debugLog('Reloading page after university selection.');
                         setTimeout(() => window.location.reload(), 1500); // Slightly longer delay
                    }
                } else {
                    // Handle specific failure messages from backend
                    throw new Error(data.message || 'Failed to select university.');
                }
            } catch (error) {
                debugLog('Error selecting university', { error: error.message, name: error.name, universityId });
                let message;
                if (error.name === 'AbortError') {
                    message = 'Request timed out. Please try again.';
                } else {
                    // Use the error message directly, which might come from the backend JSON
                    message = error.message || 'An unknown error occurred during selection.';
                }
                // Display potentially unsafe HTML from backend message safely
                notificationSystem.showNotification(`Selection Failed: ${message}`, true);

            } finally {
                 // Re-enable button
                if(button) button.disabled = false;
            }
        }
    };

    // Form Submission System (Refined AJAX handling)
    const formSystem = {
        isSubmitting: false,
        async submitForm(formElement, successCallback, errorCallback) {
            if (!formElement || this.isSubmitting) return;

            this.isSubmitting = true;
            const submitButton = formElement.querySelector('button[type="submit"]');
            if (submitButton) submitButton.disabled = true;

            const csrfToken = getCsrfToken();
            if (!csrfToken) {
                debugLog(`Form (${formElement.id}) data missing CSRF token`);
                notificationSystem.showNotification('Error: Authentication issue. Please refresh.', true);
                this.isSubmitting = false;
                 if (submitButton) submitButton.disabled = false;
                return;
            }

            const formData = new FormData(formElement);
            const formAction = getApiUrl(formElement.action);

            try {
                 const controller = new AbortController();
                 const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT * 2); // Longer timeout for uploads/marks

                const response = await fetch(formAction, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest' // Important for Django request.is_ajax()
                    },
                    body: formData,
                    signal: controller.signal
                });
                 clearTimeout(timeoutId);

                // Check for successful redirect (status 200 usually means form re-rendered with errors)
                // Or check for specific success status/JSON if view returns JSON on success
                 if (response.ok && response.redirected) { // Or status === 201 or custom header/JSON
                     if (successCallback) {
                         successCallback(response);
                     } else {
                        notificationSystem.showNotification('Submission successful!');
                        setTimeout(() => window.location.reload(), 1000); // Default reload
                     }

                 } else if (response.ok) { // Status 200 likely means form re-rendered with errors
                      // Attempt to parse and display errors from the re-rendered HTML
                      const text = await response.text();
                      const parser = new DOMParser();
                      const doc = parser.parseFromString(text, 'text/html');
                      const errorMessages = Array.from(doc.querySelectorAll('.alert-danger, .errorlist li')) // Common Django error indicators
                                             .map(el => el.textContent.trim())
                                             .filter(msg => msg) // Filter out empty messages
                                             .join('; ');
                      throw new Error(errorMessages || "Submission failed. Please check the form.");

                 } else {
                      // Handle other errors (4xx, 5xx)
                      const errorData = await response.json().catch(() => null); // Try parsing JSON error
                      throw new Error(errorData?.error || errorData?.message || `Submission failed. Status: ${response.status}`);
                 }

            } catch (error) {
                debugLog(`Form (${formElement.id}) submission error`, { error: error.message, name: error.name });
                 if (errorCallback) {
                     errorCallback(error);
                 } else {
                      let message = error.name === 'AbortError' ? 'Request timed out.' : error.message;
                      notificationSystem.showNotification(`Error: ${message}`, true);
                 }
            } finally {
                this.isSubmitting = false;
                if (submitButton) submitButton.disabled = false;
            }
        },
        // Specific handlers using the generic submitForm
        handleMarksSubmit(e) {
            e.preventDefault();
            this.submitForm(e.target,
               () => { // Success callback
                   notificationSystem.showNotification('Marks updated successfully! Reloading...');
                   setTimeout(() => window.location.reload(), 1500);
               },
               (error) => { // Error callback
                   notificationSystem.showNotification(`Marks Update Failed: ${error.message}`, true);
               }
            );
        },
        handleUploadSubmit(e) {
            e.preventDefault();
            // Check if it's the PoP form being submitted via the modal
            const isPopForm = e.target.id === 'popUploadForm';
             const successMsg = isPopForm ? 'Proof of Payment uploaded successfully! Reloading...' : 'Document uploaded successfully! Reloading...';

            this.submitForm(e.target,
                () => { // Success callback
                   notificationSystem.showNotification(successMsg);
                    if (isPopForm) {
                         // Optionally close the modal first
                         const popModalElement = document.getElementById('uploadPopModal');
                         if (popModalElement && bootstrap?.Modal) {
                            const modalInstance = bootstrap.Modal.getInstance(popModalElement);
                             if (modalInstance) modalInstance.hide();
                         }
                    }
                   setTimeout(() => window.location.reload(), 1500);
                },
                (error) => { // Error callback
                    notificationSystem.showNotification(`Upload Failed: ${error.message}`, true);
                     if (isPopForm) {
                         // Maybe keep the modal open on error?
                     }
                }
            );
        }
    };

    // Chat System with Debouncing
    const chatSystem = {
        isSubmitting: false,
        debounceTimeout: null,
        init() {
            const chatForm = document.getElementById('aiChatForm');
            const chatInput = document.getElementById('aiChatInput');
            const chatMessages = document.getElementById('aiChatMessages');
            const chatToggle = document.getElementById('aiChatToggle');
            const chatBody = document.getElementById('aiChatBody');
            let chatUrl = chatForm?.dataset.url;

            if (!chatForm || !chatInput || !chatMessages || !chatUrl) {
                debugLog('Chat elements or URL missing', { chatForm: !!chatForm, chatInput: !!chatInput, chatMessages: !!chatMessages, chatUrl: !!chatUrl });
                return;
            }
            chatUrl = getApiUrl(chatUrl);

            const appendChatMessage = (message, type) => {
                 const messageDiv = document.createElement('div');
                 messageDiv.classList.add('chat-message', type);
                 messageDiv.textContent = message; // Use textContent for security
                 chatMessages.appendChild(messageDiv);
                  // Scroll to bottom
                 if(chatBody) chatBody.scrollTop = chatBody.scrollHeight;
                 return messageDiv; // Return the element for potential removal
            };

            const submitChatRequest = async () => {
                if (this.isSubmitting) return;
                const message = chatInput.value.trim();
                if (!message) return;

                this.isSubmitting = true;
                chatInput.disabled = true;
                const submitButton = chatForm.querySelector('button[type="submit"]');
                if (submitButton) submitButton.disabled = true;

                const csrfToken = getCsrfToken(); // Get token just before sending
                if (!csrfToken) {
                    debugLog('CSRF token missing for chat submission');
                    appendChatMessage('Error: Authentication issue.', 'error');
                    this.isSubmitting = false;
                    chatInput.disabled = false;
                     if (submitButton) submitButton.disabled = false;
                    return;
                }

                appendChatMessage(message, 'user');
                chatInput.value = ''; // Clear input after displaying

                const thinkingMsg = appendChatMessage('...', 'ai thinking'); // Show thinking indicator

                try {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);
                    const response = await fetch(chatUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({ message }),
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);

                    const data = await response.json().catch(() => {
                        throw new Error(`Invalid response from AI assistant (Status: ${response.status})`);
                    });

                     thinkingMsg.remove(); // Remove thinking indicator

                    if (!response.ok) {
                        if (response.status === 429) {
                            throw new Error('Too many requests. Please try again later.');
                        }
                        throw new Error(data.error || `Assistant error! Status: ${response.status}`);
                    }
                    if (data.error) throw new Error(data.error); // Handle application-level errors

                    appendChatMessage(data.response || 'Sorry, I couldn’t respond.', 'ai');

                } catch (error) {
                     thinkingMsg.remove(); // Remove thinking indicator
                    debugLog('Chat error', { error: error.message, name: error.name });
                    let displayError = error.name === 'AbortError' ? 'Request timed out.' : error.message;
                    appendChatMessage(`Error: ${displayError}`, 'error');
                } finally {
                    this.isSubmitting = false;
                    chatInput.disabled = false;
                     if (submitButton) submitButton.disabled = false;
                    chatInput.focus();
                }
            };

            chatForm.addEventListener('submit', (e) => {
                 e.preventDefault();
                 // Debounce the submission logic
                 clearTimeout(this.debounceTimeout);
                 this.debounceTimeout = setTimeout(submitChatRequest, CONFIG.CHAT_DEBOUNCE_DELAY);
            });

            // Toggle chat window
            if (chatToggle && chatBody) {
                chatToggle.addEventListener('click', () => {
                    const isHidden = chatBody.style.display === 'none';
                    chatBody.style.display = isHidden ? 'block' : 'none';
                    chatToggle.textContent = isHidden ? '−' : '+'; // Update icon based on new state
                     chatToggle.setAttribute('aria-label', isHidden ? 'Minimize chat window' : 'Expand chat window');
                     if(isHidden) chatInput.focus(); // Focus input when opened
                });
                  // Optionally start minimized
                 // chatBody.style.display = 'none';
                 // chatToggle.textContent = '+';
                 // chatToggle.setAttribute('aria-label', 'Expand chat window');

            } else {
                debugLog('Chat toggle or body missing', { chatToggle: !!chatToggle, chatBody: !!chatBody });
            }
        }
    };

    // Bootstrap Carousel Initialization
    const carouselSystem = {
        init(attempts = CONFIG.CAROUSEL_RETRY_ATTEMPTS, delay = CONFIG.CAROUSEL_RETRY_DELAY) {
            // Select ALL carousels on the page
            const carousels = document.querySelectorAll('.carousel.slide');

            if (carousels.length > 0 && typeof bootstrap !== 'undefined' && bootstrap.Carousel) {
                carousels.forEach(carousel => {
                     const carouselId = carousel.id || 'carousel-' + Math.random().toString(36).substr(2, 9); // Generate random ID if none exists
                     carousel.id = carouselId; // Ensure it has an ID

                     // Prevent re-initialization
                     if (bootstrap.Carousel.getInstance(carousel)) {
                         debugLog(`Carousel #${carouselId} already initialized.`);
                         return;
                     }

                    try {
                        new bootstrap.Carousel(carousel, {
                            interval: CONFIG.SLIDE_INTERVAL,
                            ride: 'carousel' // Enable auto-sliding
                        });
                        debugLog(`Carousel #${carouselId} initialized successfully`);
                    } catch (error) {
                        debugLog(`Carousel #${carouselId} initialization error`, { error: error.message });
                        // Show specific error for this carousel if possible
                         notificationSystem.showNotification(`Error initializing slideshow: ${carouselId}.`, true);
                    }
                });
            } else if (attempts > 0) {
                // If Bootstrap JS might not be ready, retry
                debugLog('Retrying carousel initialization', { attemptsLeft: attempts - 1 });
                setTimeout(() => this.init(attempts - 1, delay), delay);
            } else if (carousels.length > 0) {
                 // Carousels exist but Bootstrap object/class is missing after retries
                  debugLog('Carousel initialization failed: Bootstrap library not found or Carousel class missing.', {
                      bootstrapDefined: typeof bootstrap !== 'undefined',
                      carouselClassExists: !!(typeof bootstrap !== 'undefined' && bootstrap.Carousel)
                  });
                 notificationSystem.showNotification('Slideshow functionality is unavailable (library missing).', true);
            } else {
                 // No carousels found on the page
                  debugLog('No carousels found to initialize.');
            }
        }
    };


    // Proof of Payment Modal Trigger Handling
    const popModalSystem = {
         init() {
             const popModalElement = document.getElementById('uploadPopModal');
             if (!popModalElement) {
                 debugLog("Proof of Payment modal element (#uploadPopModal) not found.");
                 return;
             }
             // Ensure Bootstrap Modal class is available
             if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
                  debugLog("Bootstrap Modal class not found for PoP modal.");
                  return;
             }

             const popModalInstance = new bootstrap.Modal(popModalElement);
             const popUniversityName = document.getElementById('popUniversityName');
             const popUploadUniversityId = document.getElementById('popUploadUniversityId');
             const popUploadForm = document.getElementById('popUploadForm'); // Get the form itself

             if (!popUniversityName || !popUploadUniversityId || !popUploadForm) {
                  debugLog("Required elements within PoP modal not found.", {
                     nameEl: !!popUniversityName,
                     idInput: !!popUploadUniversityId,
                     formEl: !!popUploadForm
                  });
                 return;
             }

             // Add listener to all PoP upload buttons
             document.querySelectorAll('.upload-pop-btn').forEach(button => {
                 button.addEventListener('click', () => {
                     const uniId = button.dataset.uniId;
                     const uniName = button.dataset.uniName;

                     if (!uniId || !uniName) {
                         debugLog("Missing data attributes on PoP button.", { uniId, uniName });
                         notificationSystem.showNotification("Cannot open upload form: missing university info.", true);
                         return;
                     }

                     // Populate modal content
                     popUniversityName.textContent = uniName;
                     popUploadUniversityId.value = uniId;

                     // Show the modal
                     popModalInstance.show();
                 });
             });
             debugLog("PoP modal listeners attached.");

             // Attach submit handler to the specific PoP form
             popUploadForm.addEventListener('submit', (e) => formSystem.handleUploadSubmit(e));
             debugLog("PoP form submit listener attached.");
         }
    };


    // Event Listeners Setup
    const initEventListeners = () => {
        // Use DOMContentLoaded for reliability
        document.addEventListener('DOMContentLoaded', () => {
            debugLog('DOM loaded, initializing dashboard components...');
            try {
                // Initialize core systems
                carouselSystem.init(); // Initialize ALL carousels
                chatSystem.init();
                popModalSystem.init(); // Initialize PoP modal triggers
                setInterval(() => notificationSystem.simulateNewSubmission(), CONFIG.SUBMISSION_CHECK_INTERVAL);

                // Attach form listeners using the refined formSystem
                const marksForm = document.getElementById('marksForm');
                const uploadForm = document.getElementById('uploadForm'); // Main upload form

                if (marksForm) {
                    marksForm.addEventListener('submit', (e) => formSystem.handleMarksSubmit(e));
                    debugLog('Marks form listener attached');
                } else {
                    debugLog('Marks form not found');
                }

                if (uploadForm) {
                     // Ensure this listener doesn't conflict with the PoP form listener if IDs are the same
                     // Since PoP form has its own listener via popModalSystem.init, we only attach to the main one here.
                     if (uploadForm.id !== 'popUploadForm') { // Prevent double-binding if IDs were the same
                        uploadForm.addEventListener('submit', (e) => formSystem.handleUploadSubmit(e));
                        debugLog('Main Upload form listener attached');
                    }
                } else {
                    debugLog('Main Upload form not found');
                }

                 debugLog('Dashboard component initialization complete.');

            } catch (error) {
                debugLog('Initialization error within DOMContentLoaded', { error: error.message, stack: error.stack });
                notificationSystem.showNotification('Error initializing dashboard components. Please refresh.', true);
            }
        });
    };

    // Expose selectUniversity globally for HTML onclick handlers
    // Ensure it's robustly attached to the window object
    try {
         if (typeof window !== 'undefined') {
             window.selectUniversity = (universityId) => universitySystem.selectUniversity(universityId);
              debugLog('selectUniversity function exposed globally.');
         } else {
             debugLog('Window object not found, cannot expose selectUniversity globally.');
         }
    } catch (error) {
         debugLog('Error exposing selectUniversity globally', { error: error.message });
    }


    // Initialize event listeners safely
    try {
        initEventListeners();
        debugLog('Dashboard JavaScript initialization sequence started.');
    } catch (error) {
        debugLog('Failed to start dashboard initialization', { error: error.message, stack: error.stack });
        // Attempt to show notification even if init failed early
        try {
             notificationSystem.showNotification('Critical Error initializing dashboard. Please refresh.', true);
        } catch (notifyError) {
             console.error("Fallback Notification Error:", notifyError);
             alert("Critical Error initializing dashboard. Please refresh."); // Final fallback
        }
    }

})(); // End IIFE