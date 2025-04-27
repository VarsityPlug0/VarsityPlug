(function () {
    // Configuration constants
    const CONFIG = {
        SLIDE_INTERVAL: 5000,              // Carousel slide interval (ms)
        NOTIFICATION_DURATION: 5000,       // Notification display duration (ms)
        SUBMISSION_CHECK_INTERVAL: 30000,  // Check for new submissions every 30s
        NOTIFICATION_CHANCE: 0.1,         // 10% chance to show notification
        API_TIMEOUT: 10000,               // API request timeout (ms)
        CHAT_DEBOUNCE_DELAY: 500          // Debounce delay for chat input (ms)
    };

    // Name arrays for notifications
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

    // Utility to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Debug logging
    function debugLog(message, data = null) {
        const timestamp = new Date().toISOString();
        console.log(`[VarsityPlug ${timestamp}] ${message}`, data || '');
    }

    // Notification System
    const notificationSystem = {
        isShowing: false,
        getRandomName() {
            return allNames[Math.floor(Math.random() * allNames.length)];
        },
        showNotification(message = null) {
            if (this.isShowing) return; // Prevent overlapping notifications
            this.isShowing = true;
            const notificationPopup = document.getElementById('notificationPopup');
            const notificationMessage = document.getElementById('notificationMessage');
            if (!notificationPopup || !notificationMessage) {
                debugLog('Notification elements not found');
                this.isShowing = false;
                return;
            }
            notificationMessage.textContent = message || `${this.getRandomName()} has sent their applications`;
            notificationPopup.classList.add('active');
            setTimeout(() => {
                notificationPopup.classList.remove('active');
                this.isShowing = false;
            }, CONFIG.NOTIFICATION_DURATION);
        },
        simulateNewSubmission() {
            if (Math.random() < CONFIG.NOTIFICATION_CHANCE) {
                this.showNotification();
            }
        }
    };

    // University Selection
    const universitySystem = {
        async selectUniversity(universityId) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);
                const response = await fetch(`/select-university/${universityId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.message || `HTTP error! Status: ${response.status}`);
                }
                if (data.success) {
                    notificationSystem.showNotification(data.message);
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    throw new Error(data.message || 'Failed to select university');
                }
            } catch (error) {
                debugLog('Error selecting university:', error);
                if (error.message.includes('limit')) {
                    notificationSystem.showNotification('Subscription limit reached. Please upgrade your plan.');
                } else {
                    notificationSystem.showNotification('Error: ' + error.message);
                }
            }
        }
    };

    // Form Submission System
    const formSystem = {
        isSubmitting: false,
        async submitMarksForm(e) {
            e.preventDefault();
            if (this.isSubmitting) return;
            this.isSubmitting = true;
            const form = document.getElementById('marksForm');
            if (!form) {
                debugLog('Marks form not found');
                this.isSubmitting = false;
                return;
            }
            const formData = new FormData(form);
            formData.append('submit_marks', 'true');
            try {
                const response = await fetch('/dashboard/student/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body: formData
                });
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                const messages = doc.querySelectorAll('.alert');
                let successMessage = 'Marks updated successfully!';
                for (const msg of messages) {
                    if (msg.classList.contains('alert-success')) {
                        const apsMatch = msg.textContent.match(/Your APS score is (\d+)/);
                        if (apsMatch) {
                            successMessage = `Marks updated! APS: ${apsMatch[1]}`;
                        }
                        break;
                    } else if (msg.classList.contains('alert-danger')) {
                        throw new Error(msg.textContent.trim() || 'Invalid marks submission');
                    }
                }
                notificationSystem.showNotification(successMessage);
                setTimeout(() => window.location.reload(), 1000);
            } catch (error) {
                debugLog('Marks submission error:', error);
                notificationSystem.showNotification('Error: ' + error.message);
            } finally {
                this.isSubmitting = false;
            }
        },
        async submitUploadForm(e) {
            e.preventDefault();
            if (this.isSubmitting) return;
            this.isSubmitting = true;
            const form = document.getElementById('uploadForm');
            if (!form) {
                debugLog('Upload form not found');
                this.isSubmitting = false;
                return;
            }
            const formData = new FormData(form);
            try {
                const response = await fetch('/dashboard/student/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body: formData
                });
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                const messages = doc.querySelectorAll('.alert');
                for (const msg of messages) {
                    if (msg.classList.contains('alert-success')) {
                        notificationSystem.showNotification('Document uploaded successfully!');
                        setTimeout(() => window.location.reload(), 1000);
                        return;
                    } else if (msg.classList.contains('alert-danger')) {
                        throw new Error(msg.textContent.trim() || 'Invalid document upload');
                    }
                }
                notificationSystem.showNotification('Document uploaded successfully!');
                setTimeout(() => window.location.reload(), 1000);
            } catch (error) {
                debugLog('Document upload error:', error);
                notificationSystem.showNotification('Error: ' + error.message);
            } finally {
                this.isSubmitting = false;
            }
        }
    };

    // Updated Chat System with Debouncing
    const updatedChatSystem = {
        isSubmitting: false,
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        init() {
            const chatForm = document.getElementById('aiChatForm');
            const chatInput = document.getElementById('aiChatInput');
            const chatMessages = document.getElementById('aiChatMessages');
            const chatToggle = document.getElementById('aiChatToggle');
            const chatBody = document.getElementById('aiChatBody');

            if (!chatForm || !chatInput || !chatMessages) {
                debugLog('Chat elements not found:', {
                    chatForm: !!chatForm,
                    chatInput: !!chatInput,
                    chatMessages: !!chatMessages
                });
                return;
            }

            const submitChat = this.debounce(async (e) => {
                e.preventDefault();
                if (this.isSubmitting) return;
                this.isSubmitting = true;
                chatInput.disabled = true;

                const message = chatInput.value.trim();
                if (!message) {
                    this.isSubmitting = false;
                    chatInput.disabled = false;
                    return;
                }

                const userMsg = document.createElement('div');
                userMsg.className = 'chat-message user';
                userMsg.textContent = message;
                chatMessages.appendChild(userMsg);
                chatInput.value = '';
                chatMessages.scrollTop = chatMessages.scrollHeight;

                try {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);
                    const response = await fetch('/ai-chat/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({ message }),
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);
                    if (!response.ok) {
                        if (response.status === 429) {
                            throw new Error('Too many requests. Please try again later.');
                        }
                        const data = await response.json();
                        throw new Error(data.error || `HTTP error! Status: ${response.status}`);
                    }
                    const data = await response.json();
                    if (data.error) throw new Error(data.error);

                    const aiMsg = document.createElement('div');
                    aiMsg.className = 'chat-message ai';
                    aiMsg.textContent = data.response || 'Sorry, I couldn’t respond.';
                    chatMessages.appendChild(aiMsg);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                } catch (error) {
                    debugLog('Chat error:', error);
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'chat-message error';
                    errorMsg.textContent = 'Error: ' + error.message;
                    chatMessages.appendChild(errorMsg);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                } finally {
                    this.isSubmitting = false;
                    chatInput.disabled = false;
                    chatInput.focus();
                }
            }, CONFIG.CHAT_DEBOUNCE_DELAY);

            chatForm.addEventListener('submit', submitChat);

            if (chatToggle && chatBody) {
                chatToggle.addEventListener('click', () => {
                    chatBody.style.display = chatBody.style.display === 'none' ? 'block' : 'none';
                    chatToggle.textContent = chatBody.style.display === 'none' ? '+' : '−';
                });
            } else {
                debugLog('Chat toggle or body not found:', {
                    chatToggle: !!chatToggle,
                    chatBody: !!chatBody
                });
            }
        }
    };

    // Bootstrap Carousel Initialization
    const carouselSystem = {
        init(attempts = 3, delay = 500) {
            const carousel = document.getElementById('universitySlideshow');
            if (carousel && typeof bootstrap !== 'undefined' && bootstrap.Carousel) {
                new bootstrap.Carousel(carousel, {
                    interval: CONFIG.SLIDE_INTERVAL,
                    ride: 'carousel'
                });
                debugLog('Carousel initialized');
            } else if (attempts > 0) {
                debugLog('Retrying carousel initialization', { attemptsLeft: attempts });
                setTimeout(() => this.init(attempts - 1, delay), delay);
            } else {
                debugLog('Carousel initialization failed:', {
                    carousel: !!carousel,
                    bootstrap: typeof bootstrap !== 'undefined',
                    carouselClass: !!(bootstrap && bootstrap.Carousel)
                });
                notificationSystem.showNotification('University slideshow is temporarily unavailable.');
            }
        }
    };

    // Event Listeners
    const initEventListeners = () => {
        document.addEventListener('DOMContentLoaded', () => {
            carouselSystem.init();
            updatedChatSystem.init();
            setInterval(() => notificationSystem.simulateNewSubmission(), CONFIG.SUBMISSION_CHECK_INTERVAL);

            const marksForm = document.getElementById('marksForm');
            const uploadForm = document.getElementById('uploadForm');
            if (marksForm) {
                marksForm.addEventListener('submit', formSystem.submitMarksForm);
                debugLog('Marks form listener attached');
            } else {
                debugLog('Marks form not found');
            }
            if (uploadForm) {
                uploadForm.addEventListener('submit', formSystem.submitUploadForm);
                debugLog('Upload form listener attached');
            } else {
                debugLog('Upload form not found');
            }
        });
    };

    // Expose selectUniversity for HTML
    window.selectUniversity = (universityId) => universitySystem.selectUniversity(universityId);

    // Initialize
    initEventListeners();
})();