(function () {
    // Configuration constants
    const CONFIG = {
        SLIDE_INTERVAL: 5000, // Slide change interval in milliseconds
        NOTIFICATION_DURATION: 5000, // Notification display duration
        SUBMISSION_CHECK_INTERVAL: 10000, // Interval to check for new submissions
        NOTIFICATION_CHANCE: 0.3 // Probability of showing a notification
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

    // Notification System
    const notificationSystem = {
        getRandomName() {
            return allNames[Math.floor(Math.random() * allNames.length)];
        },

        showNotification() {
            const notificationPopup = document.getElementById('notificationPopup');
            const notificationMessage = document.getElementById('notificationMessage');
            
            if (!notificationPopup || !notificationMessage) {
                console.warn('Notification elements not found');
                return;
            }

            notificationMessage.textContent = `${this.getRandomName()} has sent their applications`;
            notificationPopup.classList.add('active');
            
            setTimeout(() => {
                notificationPopup.classList.remove('active');
            }, CONFIG.NOTIFICATION_DURATION);
        },

        simulateNewSubmission() {
            if (Math.random() < CONFIG.NOTIFICATION_CHANCE) {
                this.showNotification();
            }
        }
    };

    // Slideshow System
    const slideshowSystem = {
        slideIndex: 0,
        slideInterval: null,
        slides: document.querySelectorAll('.recommendations-section .slide'),
        dots: document.querySelectorAll('.recommendations-section .dot'),

        showSlides() {
            if (!this.slides.length || !this.dots.length) {
                console.warn('Slideshow elements not found');
                return;
            }

            // Hide all slides and remove active dot
            this.slides.forEach(slide => slide.classList.remove('active'));
            this.dots.forEach(dot => dot.classList.remove('active'));

            // Normalize slide index
            this.slideIndex = this.slideIndex >= this.slides.length ? 0 : 
                             this.slideIndex < 0 ? this.slides.length - 1 : this.slideIndex;

            // Show current slide and activate dot
            this.slides[this.slideIndex].classList.add('active');
            if (this.dots[this.slideIndex]) {
                this.dots[this.slideIndex].classList.add('active');
            }
        },

        moveSlide(n) {
            this.slideIndex += n;
            this.showSlides();
            this.resetSlideInterval();
        },

        setCurrentSlide(n) {
            this.slideIndex = n;
            this.showSlides();
            this.resetSlideInterval();
        },

        resetSlideInterval() {
            clearInterval(this.slideInterval);
            this.slideInterval = setInterval(() => {
                this.slideIndex++;
                this.showSlides();
            }, CONFIG.SLIDE_INTERVAL);
        },

        init() {
            if (this.slides.length && this.dots.length) {
                this.showSlides();
                this.resetSlideInterval();
            }
        }
    };

    // Form Popup System
    const formPopupSystem = {
        currentForm: null,

        showPopup(formType) {
            const popupOverlay = document.getElementById('popupOverlay');
            const popupMessage = document.getElementById('popupMessage');
            
            if (!popupOverlay || !popupMessage) {
                console.warn('Popup elements not found');
                return;
            }

            this.currentForm = formType === 'marks' ? document.getElementById('marksForm') : 
                              formType === 'upload' ? document.getElementById('uploadForm') : null;
            
            if (!this.currentForm) {
                console.warn('Form not found for type:', formType);
                return;
            }

            popupMessage.textContent = `Are you sure you want to submit your ${formType === 'marks' ? 'marks' : 'document'}?`;
            popupOverlay.classList.add('active');
        },

        hidePopup() {
            const popupOverlay = document.getElementById('popupOverlay');
            if (popupOverlay) {
                popupOverlay.classList.remove('active');
            }
            this.currentForm = null;
        },

        confirmAction() {
            if (this.currentForm) {
                this.currentForm.submit();
            }
            this.hidePopup();
        }
    };

    // Chat System
    const chatSystem = {
        toggleChat() {
            const chatContainer = document.getElementById('chatContainer');
            
            if (!chatContainer) {
                console.warn('Chat container not found');
                return;
            }

            chatContainer.classList.toggle('active');
        },

        sendMessage() {
            const input = document.getElementById('chatMessage');
            const message = input?.value.trim();
            
            if (!message) return;

            const chatBody = document.getElementById('chatBody');
            if (!chatBody) {
                console.warn('Chat body not found');
                return;
            }

            // Add user message
            const userMessage = document.createElement('div');
            userMessage.className = 'chat-message user';
            userMessage.textContent = message;
            chatBody.appendChild(userMessage);
            input.value = '';
            chatBody.scrollTop = chatBody.scrollHeight;

            // Send message to server
            fetch("/ai-chat/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
                },
                body: new URLSearchParams({ 'message': message })
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                const aiMessage = document.createElement('div');
                aiMessage.className = 'chat-message ai';
                aiMessage.textContent = data.response || data.error || 'Sorry, I couldn’t respond. Please try again.';
                chatBody.appendChild(aiMessage);
                chatBody.scrollTop = chatBody.scrollHeight;
            })
            .catch(error => {
                console.error('Chat error:', error);
                const errorMessage = document.createElement('div');
                errorMessage.className = 'chat-message ai';
                errorMessage.textContent = 'An error occurred. Please try again.';
                chatBody.appendChild(errorMessage);
                chatBody.scrollTop = chatBody.scrollHeight;
            });
        }
    };

    // Expose functions to global scope for HTML event handlers
    window.moveSlide = (n) => slideshowSystem.moveSlide(n);
    window.currentSlide = (n) => slideshowSystem.setCurrentSlide(n);
    window.showPopup = (formType) => formPopupSystem.showPopup(formType);
    window.hidePopup = () => formPopupSystem.hidePopup();
    window.confirmAction = () => formPopupSystem.confirmAction();
    window.toggleChat = () => chatSystem.toggleChat();
    window.sendMessage = () => chatSystem.sendMessage();

    // Event Listeners
    const initEventListeners = () => {
        document.addEventListener('DOMContentLoaded', () => {
            // Initialize slideshow
            slideshowSystem.init();

            // Start notification simulation
            setInterval(() => notificationSystem.simulateNewSubmission(), CONFIG.SUBMISSION_CHECK_INTERVAL);
        });
    };

    // Initialize
    initEventListeners();
})();