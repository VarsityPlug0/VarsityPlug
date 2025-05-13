(function () {
    // Configuration constants for dashboard behavior
    const CONFIG = {
        DISPLAY_INTERVAL: 7000,       // Interval for auto-cycling single display (ms)
        NOTIFICATION_DURATION: 5000,  // Notification display duration (ms)
        SUBMISSION_CHECK_INTERVAL: 45000, // Check for new submissions every 45s
        NOTIFICATION_CHANCE: 0.05,    // 5% chance to show random notification
        API_TIMEOUT: 15000,           // API request timeout (ms)
        CHAT_DEBOUNCE_DELAY: 500,     // Debounce delay for chat input (ms)
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

    // Notification System
    const notificationSystem = {
        isShowing: false,
        queue: [],
        showTimeout: null,
        getRandomName() { 
            return allNames[Math.floor(Math.random() * allNames.length)]; 
        },
        _displayNext() {
            if (this.isShowing || this.queue.length === 0) return;
            this.isShowing = true;
            const { message, isError } = this.queue.shift();
            const notificationPopup = document.getElementById('notificationPopup');
            const notificationMessage = document.getElementById('notificationMessage');
            if (!notificationPopup || !notificationMessage) {
                debugLog('Notification elements missing', { popup: !!notificationPopup, message: !!notificationMessage });
                alert(message);
                this.isShowing = false;
                setTimeout(() => this._displayNext(), 100);
                return;
            }
            notificationMessage.textContent = message;
            notificationPopup.classList.remove('bg-danger', 'bg-primary', 'bg-warning', 'bg-info', 'active');
            setTimeout(() => {
                notificationPopup.classList.add(isError ? 'bg-danger' : 'bg-primary', 'active');
                notificationPopup.setAttribute('role', isError ? 'alert' : 'status');
            }, 50);
            clearTimeout(this.showTimeout);
            this.showTimeout = setTimeout(() => {
                notificationPopup.classList.remove('active');
                this.isShowing = false;
                setTimeout(() => this._displayNext(), 500);
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
                this.showNotification(); 
            } 
        },
        init() {
            debugLog('Initializing notification system...');
            // Create notification elements if they don't exist
            if (!document.getElementById('notificationPopup')) {
                const popup = document.createElement('div');
                popup.id = 'notificationPopup';
                popup.className = 'notification-popup';
                popup.innerHTML = '<div id="notificationMessage"></div>';
                document.body.appendChild(popup);
            }
        }
    };

    // University Selection System
    const universitySystem = { 
        async selectUniversity(universityId, selectUrl = null) {
            const button = document.querySelector(`.select-university-btn[data-university-id="${universityId}"], .recommendation-select-btn[data-university-id="${universityId}"]`);
            let url = selectUrl || button?.dataset.url;
            const csrfToken = getCsrfToken();
            if (!url || !csrfToken || !universityId) { 
                debugLog('Select university data missing', { url: !!url, csrfToken: !!csrfToken, universityId });
                notificationSystem.showNotification('Error: Cannot select university (data missing). Please refresh.', true);
                return; 
            }
            url = getApiUrl(url);
            if (button) button.disabled = true;
            const originalButtonText = button ? button.innerHTML : 'Select';
            if (button) button.innerHTML = "<span class='spinner-border spinner-border-sm' role='status' aria-hidden='true'></span> Selecting...";

            try {
                const controller = new AbortController(); 
                const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);
                const response = await fetch(url, { 
                    method: 'POST', 
                    headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }, 
                    signal: controller.signal 
                }); 
                clearTimeout(timeoutId);
                const data = await response.json().catch(() => { throw new Error(`Invalid response from server (Status: ${response.status})`); });

                if (!response.ok) { 
                     // Give precedence to specific message from server for 403 (limit reached)
                    if (response.status === 403 && data.message) {
                        notificationSystem.showNotification(data.message, true); // data.message can contain HTML
                        if (button) { // Reset button state if action is disallowed
                           button.innerHTML = originalButtonText;
                           button.disabled = false;
                        }
                        return; 
                    }
                    throw new Error(data.message || `HTTP error! Status: ${response.status}`); 
                }

                if (data.success) {
                    notificationSystem.showNotification(data.message || 'University selected successfully!');
                    const appCountElement = document.getElementById('applicationCountDisplay');
                    if (appCountElement && data.application_count !== undefined) { 
                        appCountElement.textContent = data.application_count; 
                    }
                    if (button) {
                        button.innerHTML = "<i class='fas fa-check'></i> Selected";
                        button.classList.remove('btn-primary');
                        button.classList.add('btn-success');
                        button.disabled = true; 
                    }
                    // Consider a less disruptive update or selective reload if needed
                    debugLog('Reloading page after university selection (standard behavior).'); 
                    setTimeout(() => window.location.reload(), 1500);
                } else { 
                    throw new Error(data.message || 'Failed to select university.'); 
                }
            } catch (error) {
                debugLog('Error selecting university', { error: error.message, name: error.name, universityId });
                let message = error.name === 'AbortError' ? 'Request timed out. Please try again.' : (error.message || 'An unknown error occurred during selection.');
                notificationSystem.showNotification(`Selection Failed: ${message}`, true);
                if (button) { // Reset button only on error
                    button.innerHTML = originalButtonText;
                    button.disabled = false; 
                }
            }
        }
    };

    // Form Submission System
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
                const timeoutDuration = formElement.enctype === 'multipart/form-data' ? CONFIG.API_TIMEOUT * 3 : CONFIG.API_TIMEOUT * 2; 
                const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);
                const response = await fetch(formAction, { 
                    method: 'POST', 
                    headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' }, 
                    body: formData, 
                    signal: controller.signal 
                }); 
                clearTimeout(timeoutId);

                if (response.redirected) {
                    debugLog(`Form ${formElement.id} submitted, server redirected. Reloading.`);
                    if (successCallback) successCallback(response, null, true); // Indicate redirect
                    else setTimeout(() => window.location.href = response.url, 500); // Follow redirect
                    return;
                }
                
                const responseText = await response.text();
                if (response.ok) {
                    debugLog(`Form ${formElement.id} submitted successfully, Status: ${response.status}`);
                    if (successCallback) successCallback(response, responseText);
                    else {
                        notificationSystem.showNotification('Submission successful! Reloading...');
                        setTimeout(() => window.location.reload(), 1000);
                    }
                } else {
                    const errorData = (() => { try { return JSON.parse(responseText); } catch { return null; } })();
                    throw new Error(errorData?.error || errorData?.message || `Submission failed. Status: ${response.status}. Response: ${responseText.substring(0,100)}`);
                }
            } catch (error) { 
                debugLog(`Form (${formElement.id}) submission error`, { error: error.message, name: error.name }); 
                if (errorCallback) errorCallback(error); 
                else notificationSystem.showNotification(`Error: ${error.name === 'AbortError' ? 'Request timed out.' : error.message}`, true); 
            } finally { 
                this.isSubmitting = false; 
                if (submitButton) submitButton.disabled = false; 
            }
        },
        handleMarksSubmit(e) {
            e.preventDefault();
            debugLog("Handling marks form submit...");
            const form = e.target;
            
            // Validate form before submission
            const formData = new FormData(form);
            let hasEmptyFields = false;
            let hasInvalidMarks = false;
            
            for (let i = 0; i < 7; i++) {
                const subject = formData.get(`subject_${i}`);
                const mark = formData.get(`mark_${i}`);
                
                if (!subject || !mark) {
                    hasEmptyFields = true;
                    break;
                }
                
                const markNum = parseInt(mark);
                if (isNaN(markNum) || markNum < 0 || markNum > 100) {
                    hasInvalidMarks = true;
                    break;
                }
            }
            
            if (hasEmptyFields) {
                notificationSystem.showNotification("Please fill in all subject and mark fields.", true);
                return;
            }
            
            if (hasInvalidMarks) {
                notificationSystem.showNotification("Marks must be between 0 and 100.", true);
                return;
            }
            
            this.submitForm(form, 
                (response, responseText, isRedirect) => {
                    if (isRedirect) { 
                        window.location.href = response.url; 
                        return; 
                    }
                    
                    // Try to parse messages from response HTML
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = responseText;
                    const successAlert = tempDiv.querySelector('.alert-success');
                    const errorAlert = tempDiv.querySelector('.alert-danger');
                    
                    if (successAlert) {
                        notificationSystem.showNotification(successAlert.textContent.trim());
                    } else if (errorAlert) {
                        notificationSystem.showNotification(errorAlert.textContent.trim(), true);
                    } else {
                        notificationSystem.showNotification("Marks updated! Reloading to reflect changes.");
                    }
                    
                    // Store the expanded state in sessionStorage before reload
                    sessionStorage.setItem('marksSectionExpanded', 'true');
                    setTimeout(() => window.location.reload(), 1500);
                },
                (error) => {
                    notificationSystem.showNotification(`Marks Update Failed: ${error.message}`, true);
                    console.error('Marks submission error:', error);
                }
            );
        },
        handleUploadSubmit(e) { 
            e.preventDefault(); 
            const formElement = e.target;
            debugLog(`Handling upload form submit for form: ${formElement.id}`); 
            const isPopForm = formElement.id === 'popUploadForm'; 
            const baseSuccessMsg = isPopForm ? 'Proof of Payment uploaded successfully!' : 'Document uploaded successfully!'; 
            
            this.submitForm(formElement, 
                (response, responseText, isRedirect) => {
                    if (isRedirect) { window.location.href = response.url; return; }
                    // Try to parse messages from response HTML
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = responseText;
                    const successAlert = tempDiv.querySelector('.alert-success');
                    let message = baseSuccessMsg;
                    if (successAlert) message = successAlert.textContent.trim();
                    
                    notificationSystem.showNotification(message + " Reloading..."); 
                    if (isPopForm) { 
                        const popModalElement = document.getElementById('uploadPopModal'); 
                        if (popModalElement && bootstrap?.Modal) { 
                            const modalInstance = bootstrap.Modal.getInstance(popModalElement); 
                            if (modalInstance) modalInstance.hide(); 
                        } 
                    } 
                    setTimeout(() => window.location.reload(), 1500); 
                }, 
                (error) => { 
                    notificationSystem.showNotification(`Upload Failed: ${error.message}`, true); 
                }
            ); 
        },
        init() {
            // This init can be used to attach listeners to forms if not done elsewhere
            // For now, specific forms like marksForm, uploadForm, popUploadForm have listeners attached in DOMContentLoaded
            debugLog("Form system initialized (listeners attached elsewhere or dynamically).");
        }
    };

    // Chat System
    const chatSystem = { 
        isSubmitting: false, 
        debounceTimeout: null, 
        init() {
            debugLog("Initializing chat system...");
            const chatForm = document.getElementById("aiChatForm"); 
            const chatInput = document.getElementById("aiChatInput"); 
            const chatMessages = document.getElementById("aiChatMessages"); 
            const chatToggle = document.getElementById("aiChatToggle"); 
            const chatBody = document.getElementById("aiChatBody"); 
            let chatUrl = chatForm?.dataset.url;

            if (!chatForm || !chatInput || !chatMessages || !chatUrl) { 
                debugLog("Chat elements or URL missing", { chatForm: !!chatForm, chatInput: !!chatInput, chatMessages: !!chatMessages, chatUrl: !!chatUrl }); 
                return; 
            } 
            chatUrl = getApiUrl(chatUrl);

            const appendChatMessage = (message, type) => { 
                const messageDiv = document.createElement("div"); 
                if (type && type.includes(" ")) {
                    messageDiv.classList.add("chat-message", ...type.split(" "));
                } else {
                    messageDiv.classList.add("chat-message", type);
                }
                messageDiv.textContent = message; 
                chatMessages.appendChild(messageDiv); 
                if(chatBody) { setTimeout(() => { chatBody.scrollTop = chatBody.scrollHeight; }, 0); } 
                return messageDiv; 
            };

            const submitChatRequest = async () => { 
                if (this.isSubmitting) return; 
                this.isSubmitting = true; 
                const chatInput = document.getElementById("aiChatInput"); 
                const submitButton = document.querySelector("#aiChatForm button[type='submit']"); 
                const message = chatInput.value.trim(); 
                const chatUrl = chatForm.dataset.url;
                const csrfToken = getCsrfToken();
                
                if (!message) { 
                    this.isSubmitting = false; 
                    chatInput.disabled = false; 
                    if (submitButton) submitButton.disabled = false; 
                    return; 
                }

                if (!csrfToken) {
                    appendChatMessage("Error: Authentication issue. Please refresh.", "error");
                    this.isSubmitting = false;
                    chatInput.disabled = false;
                    if (submitButton) submitButton.disabled = false;
                    return;
                }

                if (!chatUrl) {
                    appendChatMessage("Error: Chat URL not configured. Please refresh.", "error");
                    this.isSubmitting = false;
                    chatInput.disabled = false;
                    if (submitButton) submitButton.disabled = false;
                    return;
                }
                
                appendChatMessage(message, "user"); 
                chatInput.value = ""; 
                const thinkingMsg = appendChatMessage("...", "ai thinking"); 
                try { 
                    const controller = new AbortController(); 
                    const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT); 
                    const response = await fetch(chatUrl, { 
                        method: "POST", 
                        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" }, 
                        body: JSON.stringify({ message }), 
                        signal: controller.signal 
                    }); 
                    clearTimeout(timeoutId); 

                    // Read the response body as text first, as it can only be read once.
                    const responseText = await response.text(); 

                    let data;
                    try {
                        // Try parsing the text as JSON
                        data = JSON.parse(responseText); 
                    } catch (parseError) {
                        // If JSON parsing fails, the raw text is already available
                        debugLog("Chat response JSON parse failed. Raw response:", responseText);
                        // Throw an error indicating parsing failed, but the original status might still be useful
                        throw new Error(`Invalid JSON response from AI (Status: ${response.status}). Check console log for raw response.`); 
                    }
                    
                    thinkingMsg.remove(); 
                    // Now check if the original response status was OK (e.g., 200)
                    if (!response.ok) { 
                        // Use error from parsed data if available, otherwise use status
                        throw new Error(data.error || `Assistant error! Status: ${response.status}`); 
                    } 
                    // Check if the valid JSON response contains an explicit error message
                    if (data.error) { 
                        throw new Error(data.error); 
                    } 
                    appendChatMessage(data.response || "Sorry, I couldn't respond.", "ai"); 
                } catch (error) { 
                    thinkingMsg.remove(); 
                    debugLog("Chat error", { error: error.message, name: error.name }); 
                    appendChatMessage(`Error: ${error.name === "AbortError" ? "Request timed out." : error.message}`, "error"); 
                } finally { 
                    this.isSubmitting = false;
                    chatInput.disabled = false;
                    if (submitButton) submitButton.disabled = false;
                    chatInput.focus();
                }
            };

            chatForm.addEventListener("submit", (e) => { 
                e.preventDefault(); 
                clearTimeout(this.debounceTimeout); 
                this.debounceTimeout = setTimeout(submitChatRequest, CONFIG.CHAT_DEBOUNCE_DELAY); 
            });

            if (chatToggle && chatBody) { 
                chatToggle.addEventListener("click", () => { 
                    const isHidden = chatBody.style.display === "none"; 
                    chatBody.style.display = isHidden ? "block" : "none"; 
                    chatToggle.textContent = isHidden ? "−" : "+"; 
                    if(isHidden) chatInput.focus(); 
                }); 
            }
            debugLog("Chat system initialized.");
        }
    };

    // Qualified Display System
    const qualifiedDisplaySystem = {
        displayElement: null,
        universities: [],
        currentIndex: 0,
        intervalId: null,
        intervalMs: 7000,
        isLoading: false,

        init() {
            debugLog('Starting qualified universities display initialization...');
            this.displayElement = document.getElementById('qualifiedUniversityDisplayArea');
            
            if (!this.displayElement) {
                debugLog('Qualified universities display element not found');
                return;
            }

            // Show loading state
            this.isLoading = true;
            this.displayElement.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading universities...</span>
                </div>
            `;

            // Try to get data from the script tag first
            const dataScript = document.getElementById('qualifiedUniversitiesData');
            if (dataScript) {
                try {
                    this.universities = JSON.parse(dataScript.textContent);
                    debugLog('Loaded qualified universities from script tag', { count: this.universities.length });
                    this.initializeDisplay();
                    return;
                } catch (error) {
                    debugLog('Error parsing universities data from script', { error });
                }
            }

            // Fallback to API call if script data is not available
            this.fetchUniversities();
        },

        fetchUniversities() {
            fetch('/universities/api/', {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                this.universities = data.universities || [];
                debugLog('Fetched qualified universities data', { count: this.universities.length });
                this.initializeDisplay();
            })
            .catch(error => {
                debugLog('Error fetching universities', { error });
                this.displayElement.innerHTML = `
                    <div class="alert alert-danger">
                        <p class="mb-0">Error loading universities. Please try refreshing the page.</p>
                    </div>
                `;
            })
            .finally(() => {
                this.isLoading = false;
            });
        },

        initializeDisplay() {
            if (!Array.isArray(this.universities) || this.universities.length === 0) {
                this.displayElement.innerHTML = `
                    <div class="alert alert-info">
                        <p class="mb-0">No qualified universities found.</p>
                    </div>
                `;
                return;
            }

            if (this.intervalId) {
                clearInterval(this.intervalId);
            }

            this.currentIndex = 0;
            this.displayNextUniversity();
            this.intervalId = setInterval(() => this.displayNextUniversity(), this.intervalMs);
        },

        displayNextUniversity() {
            if (!this.displayElement || this.isLoading) return;

            const uni = this.universities[this.currentIndex];
            if (!uni) return;

            const card = this.createUniversityCard(uni);
            this.displayElement.innerHTML = '';
            this.displayElement.appendChild(card);

            this.currentIndex = (this.currentIndex + 1) % this.universities.length;
        },

        createUniversityCard(uni) {
            const card = document.createElement('div');
            card.className = 'card h-100';
            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">${uni.name}</h5>
                    <p class="card-text">
                        <strong>Minimum APS:</strong> ${uni.minimum_aps}<br>
                        <strong>Application Fee:</strong> ${uni.application_fee}<br>
                        <strong>Due Date:</strong> ${uni.due_date}<br>
                        <strong>Province:</strong> ${uni.province}
                    </p>
                    <div class="d-flex justify-content-between">
                        <a href="${uni.detail_url}" class="btn btn-primary">View Details</a>
                        <a href="${uni.select_url}" class="btn btn-success">Select University</a>
                    </div>
                </div>
            `;
            return card;
        }
    };

    // Proof of Payment Modal Trigger Handling
    const popModalSystem = { 
        init() {
            debugLog("Initializing PoP modal system...");
            const popModalElement = document.getElementById('uploadPopModal'); 
            if (!popModalElement) { debugLog("PoP modal element not found."); return; }
            if (typeof bootstrap === 'undefined' || !bootstrap.Modal) { debugLog("Bootstrap Modal not found for PoP."); return; }
            
            let popModalInstance;
            try { popModalInstance = new bootstrap.Modal(popModalElement); } 
            catch (e) { debugLog("Error initializing PoP Bootstrap Modal", { error: e }); return; }

            const popUniversityName = document.getElementById('popUniversityName'); 
            const popUploadUniversityId = document.getElementById('popUploadUniversityId'); 
            const popUploadForm = document.getElementById('popUploadForm');

            if (!popUniversityName || !popUploadUniversityId || !popUploadForm) { 
                debugLog("Required elements in PoP modal not found."); return; 
            }

            document.querySelectorAll('.upload-pop-btn').forEach(button => { 
                button.addEventListener('click', () => { 
                    const uniId = button.dataset.uniId; 
                    const uniName = button.dataset.uniName; 
                    if (!uniId || !uniName) { 
                        notificationSystem.showNotification("Cannot open PoP form: missing university info.", true); return; 
                    } 
                    popUniversityName.textContent = uniName; 
                    popUploadUniversityId.value = uniId; 
                    if (popModalInstance) popModalInstance.show(); 
                }); 
            });
            if (!popUploadForm.dataset.listenerAttachedPop) { 
                popUploadForm.addEventListener('submit', (e) => formSystem.handleUploadSubmit(e)); 
                popUploadForm.dataset.listenerAttachedPop = 'true'; 
            }
            debugLog("PoP modal system initialized.");
        }
    };

    // University Recommendations System
    const universityRecommendationsSystem = {
        carousel: null,
        currentIndex: 0,
        universities: [],

        init() {
            debugLog('Initializing university recommendations system...');
            const carouselElement = document.getElementById('universitySlideshow');
            if (!carouselElement) {
                debugLog('University slideshow element not found');
                return;
            }

            // Initialize Bootstrap carousel
            this.carousel = new bootstrap.Carousel(carouselElement, {
                interval: 7000,
                wrap: true,
                keyboard: true
            });

            // Get universities data from the page
            const universitiesData = window.universitiesData || [];
            this.universities = universitiesData;

            // Set up event listeners
            this.setupEventListeners();
            debugLog('University recommendations system initialized');
        },

        setupEventListeners() {
            // Handle university selection
            document.querySelectorAll('.recommendation-select-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    e.preventDefault();
                    const universityId = parseInt(button.dataset.universityId, 10);
                    const universityName = button.dataset.universityName;
                    const url = button.dataset.url;

                    if (!universityId || !universityName || !url) {
                        debugLog('Missing university data', { universityId, universityName, url });
                        notificationSystem.showNotification('Error: Missing university data', true);
                        return;
                    }

                    try {
                        button.disabled = true;
                        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Selecting...';

                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': getCsrfToken(),
                                'Content-Type': 'application/json'
                            }
                        });

                        if (!response.ok) {
                            throw new Error('Failed to select university');
                        }

                        const data = await response.json();
                        if (data.success) {
                            notificationSystem.showNotification(`Successfully selected ${universityName}`);
                            // Remove the selected university from the carousel
                            this.removeUniversityFromCarousel(universityId);
                        } else {
                            throw new Error(data.message || 'Failed to select university');
                        }
                    } catch (error) {
                        debugLog('Error selecting university', { error: error.message });
                        notificationSystem.showNotification(error.message || 'Failed to select university', true);
                        button.disabled = false;
                        button.innerHTML = 'Select';
                    }
                });
            });

            // Handle carousel events
            const carouselElement = document.getElementById('universitySlideshow');
            if (carouselElement) {
                carouselElement.addEventListener('slide.bs.carousel', (e) => {
                    this.currentIndex = e.to;
                });
            }
        },

        removeUniversityFromCarousel(universityId) {
            const carouselElement = document.getElementById('universitySlideshow');
            if (!carouselElement) return;

            const item = carouselElement.querySelector(`[data-university-id="${universityId}"]`);
            if (!item) return;

            // Remove the carousel item
            item.remove();

            // Update carousel indicators
            const indicators = carouselElement.querySelectorAll('.carousel-indicators button');
            if (indicators.length > 0) {
                indicators[indicators.length - 1].remove();
            }

            // If no more items, show message
            const remainingItems = carouselElement.querySelectorAll('.carousel-item');
            if (remainingItems.length === 0) {
                carouselElement.innerHTML = `
                    <div class="alert alert-info m-3">
                        <h4 class="alert-heading">No More Recommendations</h4>
                        <p class="mb-0">You have selected all recommended universities. Check your selected universities section for more details.</p>
                    </div>
                `;
            }
        }
    };

    // Single DOMContentLoaded listener for all initializations
    document.addEventListener('DOMContentLoaded', function() {
        if (window.dashboardScriptInitialized) {
            debugLog('Dashboard JS already initialized, skipping DOMContentLoaded block.');
            return;
        }
        window.dashboardScriptInitialized = true;
        debugLog('DOM loaded, initializing all dashboard components...');

        try {
            // Initialize core systems in sequence
            const initSequence = async () => {
                // 1. Initialize notification system first (needed by other systems)
                notificationSystem.init();
                debugLog('Initializing notification system...');

                // 2. Initialize form system
                formSystem.init();
                debugLog('Form system initialized (listeners attached elsewhere or dynamically).');

                // 3. Initialize chat system
                chatSystem.init();
                debugLog('Initializing chat system...');
                debugLog('Chat system initialized.');

                // 4. Initialize PoP modal system
                popModalSystem.init();
                debugLog('Initializing PoP modal system...');
                debugLog('PoP modal system initialized.');

                // 5. Initialize university recommendations system
                universityRecommendationsSystem.init();
                debugLog('University recommendations system initialized.');

                // 6. Initialize qualified universities display
                qualifiedDisplaySystem.init();
                debugLog('Starting qualified universities display initialization...');

                // 7. Initialize marks section
                const marksSection = document.getElementById('marksSection');
                const marksHeader = document.querySelector('[data-bs-target="#marksSection"]');
                const chevronIcon = marksHeader?.querySelector('.fa-chevron-down');

                if (marksSection && marksHeader && typeof bootstrap !== 'undefined') {
                    const collapse = new bootstrap.Collapse(marksSection, { toggle: false });
                    if (chevronIcon) {
                        marksSection.addEventListener('show.bs.collapse', () => chevronIcon.style.transform = 'rotate(0deg)');
                        marksSection.addEventListener('hide.bs.collapse', () => chevronIcon.style.transform = 'rotate(-90deg)');
                    }
                    marksHeader.addEventListener('click', () => collapse.toggle());
                    
                    // Check if we should expand the marks section
                    if (sessionStorage.getItem('marksSectionExpanded') === 'true') {
                        collapse.show();
                        sessionStorage.removeItem('marksSectionExpanded');
                    }
                }

                // 8. Attach form listeners
                const marksForm = document.getElementById('marksForm');
                if (marksForm && !marksForm.dataset.listenerAttachedMarks) {
                    marksForm.addEventListener('submit', (e) => formSystem.handleMarksSubmit(e));
                    marksForm.dataset.listenerAttachedMarks = 'true';
                }

                const mainUploadForm = document.getElementById('uploadForm');
                if (mainUploadForm && !mainUploadForm.dataset.listenerAttachedMainUpload) {
                    mainUploadForm.addEventListener('submit', (e) => formSystem.handleUploadSubmit(e));
                    mainUploadForm.dataset.listenerAttachedMainUpload = 'true';
                }

                // 9. Set up recommendation select buttons
                document.querySelectorAll('.recommendation-select-btn').forEach(button => {
                    button.addEventListener('click', async function() {
                        const universityId = parseInt(this.dataset.universityId, 10);
                        const universityName = this.dataset.universityName;
                        const url = this.dataset.url;
                        if (universityId && universityName && url) {
                            universitySystem.selectUniversity(universityId, url);
                        }
                    });
                });

                // 10. Set up notification interval
                if (CONFIG.SUBMISSION_CHECK_INTERVAL > 0 && CONFIG.NOTIFICATION_CHANCE > 0) {
                    setInterval(() => notificationSystem.simulateNewSubmission(), CONFIG.SUBMISSION_CHECK_INTERVAL);
                }

                debugLog('All dashboard components and listeners initialized successfully.');
            };

            // Start initialization sequence
            initSequence().catch(error => {
                debugLog('Error during initialization sequence', { error: error.message, stack: error.stack });
                notificationSystem.showNotification('Error initializing dashboard. Please refresh the page.', true);
            });

        } catch (error) {
            debugLog('Critical error during dashboard initialization', { error: error.message, stack: error.stack });
            alert("A critical error occurred while loading the dashboard. Please refresh the page.");
        }
    });
})();