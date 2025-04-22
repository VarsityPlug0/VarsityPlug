(function () {
    // Configuration constants
    const CONFIG = {
        SLIDE_INTERVAL: 5000,
        NOTIFICATION_DURATION: 5000,
        SUBMISSION_CHECK_INTERVAL: 10000,
        NOTIFICATION_CHANCE: 0.3
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
            notificationPopup.classList.add('visible');
            
            setTimeout(() => {
                notificationPopup.classList.remove('visible');
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
        slides: document.querySelectorAll('.slide'),
        dots: document.querySelectorAll('.dot'),

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

    // Chat System
    const chatSystem = {
        toggleChat() {
            const chatBody = document.getElementById('chatBody');
            const chatInput = document.getElementById('chatInput');
            
            if (!chatBody || !chatInput) {
                console.warn('Chat elements not found');
                return;
            }

            const display = chatBody.style.display === 'block' ? 'none' : 'block';
            chatBody.style.display = display;
            chatInput.style.display = display;
        },

        sendMessage() {
            const input = document.getElementById('chatMessage');
            const message = input?.value.trim();
            
            if (!message) return;

            const chatBody = document.getElementById('chatBody');
            if (!chatBody) return;

            // Add user message
            const userMessage = document.createElement('div');
            userMessage.className = 'chat-message user';
            userMessage.textContent = message;
            chatBody.appendChild(userMessage);
            input.value = '';
            chatBody.scrollTop = chatBody.scrollHeight;

            // Send message to server
            fetch("{% url 'helper:ai_chat' %}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: new URLSearchParams({ 'message': message })
            })
            .then(response => response.json())
            .then(data => {
                const aiMessage = document.createElement('div');
                aiMessage.className = 'chat-message ai';
                aiMessage.textContent = data.message || data.error || 'Sorry, I couldn’t respond. Please try again.';
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

    // Event Listeners
    const initEventListeners = () => {
        document.addEventListener('DOMContentLoaded', () => {
            setInterval(() => notificationSystem.simulateNewSubmission(), CONFIG.SUBMISSION_CHECK_INTERVAL);
            slideshowSystem.init();

            // Slideshow navigation
            const prevButton = document.querySelector('.prev');
            const nextButton = document.querySelector('.next');
            if (prevButton) prevButton.addEventListener('click', () => slideshowSystem.moveSlide(-1));
            if (nextButton) nextButton.addEventListener('click', () => slideshowSystem.moveSlide(1));

            // Dot navigation
            slideshowSystem.dots.forEach((dot, index) => {
                dot.addEventListener('click', () => slideshowSystem.setCurrentSlide(index));
            });

            // Chat toggle and send
            const chatToggle = document.getElementById('chatToggle');
            const sendMessage = document.getElementById('sendMessage');
            if (chatToggle) chatToggle.addEventListener('click', chatSystem.toggleChat);
            if (sendMessage) sendMessage.addEventListener('click', chatSystem.sendMessage);
        });
    };

    // Initialize
    initEventListeners();
})();