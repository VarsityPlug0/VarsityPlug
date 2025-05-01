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
        // Use console.info for debug, console.error for errors to make filtering easier
        if (data && (data.error || data.name === 'AbortError' || message.toLowerCase().includes('error') || message.toLowerCase().includes('fail'))) {
             console.error(`[VarsityPlug ${timestamp}] ${message}`, data || '');
        } else {
             console.log(`[VarsityPlug ${timestamp}] ${message}`, data || '');
        }
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
            notificationPopup.classList.remove('bg-danger', 'bg-primary', 'bg-warning', 'bg-info', 'active'); // Clear previous types and active
             // Delay adding active class slightly to allow CSS transitions
             setTimeout(() => {
                notificationPopup.classList.add(isError ? 'bg-danger' : 'bg-primary', 'active'); // Default to primary, use danger for errors
                notificationPopup.setAttribute('role', isError ? 'alert' : 'status');
             }, 50); // Small delay

            // Clear any existing timeout before setting a new one
             clearTimeout(this.showTimeout);

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
            // Prevent multiple rapid calls to _displayNext if already processing queue
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
                       // TODO: Consider adding the university to the 'Selected Universities' table dynamically here
                       // This avoids a full page reload but requires more complex DOM manipulation
                       // For now, we still rely on reload as fallback. Consider removing reload if dynamic update is implemented.
                       debugLog('Reloading page after university selection (fallback).');
                       setTimeout(() => window.location.reload(), 1500); // Slightly longer delay
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
            if (!formElement || this.isSubmitting) {
                debugLog(`Form submission blocked for ${formElement?.id}`, { isSubmitting: this.isSubmitting, formElementExists: !!formElement });
                return;
            }

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
            debugLog(`Submitting form ${formElement.id} to ${formAction}`);

            try {
                 const controller = new AbortController();
                 // Longer timeout for uploads/marks potentially
                 const timeoutDuration = formElement.enctype === 'multipart/form-data' ? CONFIG.API_TIMEOUT * 3 : CONFIG.API_TIMEOUT * 2;
                 const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);

                const response = await fetch(formAction, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest' // Important for Django request.is_ajax()
                        // 'Content-Type' header is NOT set for FormData, browser handles it
                    },
                    body: formData,
                    signal: controller.signal
                });
                 clearTimeout(timeoutId);

                // Check for successful redirect or specific success status/JSON
                // Django form views often return 200 OK even on success if re-rendering the page with messages.
                // A redirect (3xx) is also common on success.
                // Let's assume success if status is 2xx or 3xx and check content for errors later.

                 if (response.ok || (response.status >= 300 && response.status < 400)) {
                      debugLog(`Form ${formElement.id} submitted, Status: ${response.status}, Redirected: ${response.redirected}`);

                      // If redirected, assume success (Django often redirects after successful POST)
                      if (response.redirected) {
                           if (successCallback) {
                               successCallback(response); // Callback might handle the redirect or further actions
                           } else {
                              notificationSystem.showNotification('Submission successful! Reloading...');
                              setTimeout(() => window.location.reload(), 1000); // Reload to see changes
                           }
                           return; // Stop processing here if redirected
                      }

                      // If not redirected but status is OK (200), check response content for error messages
                      // This handles cases where Django re-renders the form with errors.
                      const text = await response.text();
                      const parser = new DOMParser();
                      const doc = parser.parseFromString(text, 'text/html');
                      const errorMessages = Array.from(doc.querySelectorAll('.alert-danger, .errorlist li'))
                                             .map(el => el.textContent.trim())
                                             .filter(msg => msg)
                                             .join('; ');

                      if (errorMessages) {
                           // Found errors in the response HTML
                           throw new Error(errorMessages);
                      } else {
                           // No errors found in HTML, assume success (e.g., page re-rendered with success message)
                            if (successCallback) {
                                successCallback(response, text); // Pass text maybe useful for extracting success message
                            } else {
                               notificationSystem.showNotification('Submission successful!');
                               setTimeout(() => window.location.reload(), 1000); // Default reload
                            }
                      }

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
            debugLog("Handling marks form submit...");
            this.submitForm(e.target,
               (response, responseText) => { // Success callback
                   let successMessage = 'Marks updated successfully! Reloading...';
                    // Try to extract specific success message if Django renders it
                    if (responseText) {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(responseText, 'text/html');
                        const successAlert = doc.querySelector('.alert-success');
                         if (successAlert) successMessage = successAlert.textContent.trim();
                    }
                   notificationSystem.showNotification(successMessage);
                   setTimeout(() => window.location.reload(), 1500);
               },
               (error) => { // Error callback
                   notificationSystem.showNotification(`Marks Update Failed: ${error.message}`, true);
               }
            );
        },
        handleUploadSubmit(e) {
            e.preventDefault();
             debugLog(`Handling upload form submit for form: ${e.target.id}`);
            // Check if it's the PoP form being submitted via the modal
            const isPopForm = e.target.id === 'popUploadForm';
            const successMsg = isPopForm ? 'Proof of Payment uploaded successfully! Reloading...' : 'Document uploaded successfully! Reloading...';

            this.submitForm(e.target,
                (response, responseText) => { // Success callback
                   let extractedSuccessMsg = null;
                    if (responseText) {
                         const parser = new DOMParser();
                         const doc = parser.parseFromString(responseText, 'text/html');
                         const successAlert = doc.querySelector('.alert-success');
                          if (successAlert) extractedSuccessMsg = successAlert.textContent.trim();
                    }
                   notificationSystem.showNotification(extractedSuccessMsg || successMsg); // Use extracted if available
                    if (isPopForm) {
                         // Close the modal on success
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
                     // Optionally keep PoP modal open on error
                     // if (isPopForm) { ... }
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
                 // Sanitize potentially harmful HTML before setting textContent or innerHTML
                 // Using textContent is generally safer unless HTML formatting is explicitly needed and trusted.
                 messageDiv.textContent = message;
                 chatMessages.appendChild(messageDiv);
                  // Scroll to bottom
                 if(chatBody) {
                     // Use setTimeout to ensure scrolling happens after DOM update
                     setTimeout(() => { chatBody.scrollTop = chatBody.scrollHeight; }, 0);
                 }
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
                        if (response.status === 429) { // Rate limit specific error
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
                    // Use class toggling for better CSS control if needed
                    const isHidden = chatBody.style.display === 'none';
                    chatBody.style.display = isHidden ? 'block' : 'none'; // Simple toggle
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

             // *** ADDED DIAGNOSTIC LOGGING ***
             debugLog('Carousel init check:', {
                'Carousels Found': carousels.length,
                'Bootstrap Object Type': typeof bootstrap,
                'Bootstrap Carousel Type': typeof bootstrap?.Carousel // Use optional chaining safely
            });
             // **********************************

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
            } else { // Final attempt failed
                 // *** ADDED DIAGNOSTIC LOGGING FOR FAILURE ***
                 debugLog('Carousel initialization failed after retries. Final check state:', {
                    'Carousels Found': carousels.length,
                    'Bootstrap Object Type': typeof bootstrap,
                    'Bootstrap Carousel Type': typeof bootstrap?.Carousel
                });
                 // ******************************************

                 if (carousels.length > 0) {
                     // Carousels exist but Bootstrap object/class is missing after retries
                      debugLog('Reason: Bootstrap library not found or Carousel class missing.');
                     notificationSystem.showNotification('Slideshow functionality is unavailable (library missing).', true);
                 } else {
                     // No carousels found on the page
                      debugLog('Reason: No elements with class "carousel slide" found.');
                      // Don't show an error if no carousels are expected on the page
                 }
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

             // Initialize modal instance ONCE
             let popModalInstance = null;
             try {
                popModalInstance = new bootstrap.Modal(popModalElement);
             } catch (e) {
                 debugLog("Error initializing PoP Bootstrap Modal instance", { error: e });
                 return; // Cannot proceed without modal instance
             }

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

             // Use event delegation for dynamically added buttons if necessary,
             // but direct binding is fine if the buttons are present on initial load.
             document.querySelectorAll('.upload-pop-btn').forEach(button => {
                 button.addEventListener('click', (e) => {
                     // Prevent any default button behavior if necessary
                     // e.preventDefault();

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

                     // Show the modal using the initialized instance
                     if (popModalInstance) {
                          popModalInstance.show();
                     } else {
                          debugLog("PoP modal instance not available to show.");
                     }
                 });
             });
             debugLog("PoP modal button listeners attached.");

             // Attach submit handler to the specific PoP form
             // Make sure this listener isn't attached multiple times if init runs again
             if (!popUploadForm.dataset.listenerAttached) {
                  popUploadForm.addEventListener('submit', (e) => formSystem.handleUploadSubmit(e));
                  popUploadForm.dataset.listenerAttached = 'true'; // Mark as attached
                  debugLog("PoP form submit listener attached.");
             }

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

                 // Only start simulation interval if configured (optional)
                 if (CONFIG.SUBMISSION_CHECK_INTERVAL > 0 && CONFIG.NOTIFICATION_CHANCE > 0) {
                     setInterval(() => notificationSystem.simulateNewSubmission(), CONFIG.SUBMISSION_CHECK_INTERVAL);
                     debugLog(`Notification simulation started (Interval: ${CONFIG.SUBMISSION_CHECK_INTERVAL}ms, Chance: ${CONFIG.NOTIFICATION_CHANCE*100}%)`);
                 }


                // Attach form listeners using the refined formSystem
                const marksForm = document.getElementById('marksForm');
                const uploadForm = document.getElementById('uploadForm'); // Main upload form

                if (marksForm && !marksForm.dataset.listenerAttached) { // Prevent double-binding
                    marksForm.addEventListener('submit', (e) => formSystem.handleMarksSubmit(e));
                    marksForm.dataset.listenerAttached = 'true';
                    debugLog('Marks form listener attached');
                } else if (!marksForm) {
                    debugLog('Marks form not found');
                }

                if (uploadForm && uploadForm.id !== 'popUploadForm' && !uploadForm.dataset.listenerAttached) { // Prevent double-binding
                    uploadForm.addEventListener('submit', (e) => formSystem.handleUploadSubmit(e));
                     uploadForm.dataset.listenerAttached = 'true';
                    debugLog('Main Upload form listener attached');
                } else if (!uploadForm) {
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
             // Check if it already exists to prevent potential issues with hot-reloading dev servers
             if (!window.selectUniversity) {
                  window.selectUniversity = (universityId) => universitySystem.selectUniversity(universityId);
                  debugLog('selectUniversity function exposed globally.');
             } else {
                   debugLog('selectUniversity function already exposed.');
             }
         } else {
             debugLog('Window object not found, cannot expose selectUniversity globally.');
         }
    } catch (error) {
         debugLog('Error exposing selectUniversity globally', { error: error.message });
    }


    // Initialize event listeners safely
    try {
        // Check if the script is already initialized (simple flag)
         if (!window.dashboardScriptInitialized) {
            initEventListeners();
            window.dashboardScriptInitialized = true;
            debugLog('Dashboard JavaScript initialization sequence started.');
         } else {
             debugLog('Dashboard JavaScript initialization skipped (already initialized).');
         }
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