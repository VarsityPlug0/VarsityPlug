// Notification Pop-up JavaScript
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

function getRandomName() {
    return allNames[Math.floor(Math.random() * allNames.length)];
}

function showNotification() {
    const notificationPopup = document.getElementById('notificationPopup');
    const notificationMessage = document.getElementById('notificationMessage');
    if (notificationPopup && notificationMessage) {
        const name = getRandomName();
        notificationMessage.textContent = `${name} has sent their applications`;
        notificationPopup.classList.add('visible');
        setTimeout(() => {
            notificationPopup.classList.remove('visible');
        }, 5000);
    }
}

function simulateNewSubmission() {
    if (Math.random() < 0.3) {
        showNotification();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setInterval(simulateNewSubmission, 10000);
});

// Form Confirmation Pop-up JavaScript
let currentFormId = '';

function showPopup(formType) {
    currentFormId = formType === 'marks' ? 'marksForm' : 'uploadForm';
    const message = formType === 'marks' ? 'Are you sure you want to update your marks?' : 'Are you sure you want to upload this document?';
    const popupMessage = document.getElementById('popupMessage');
    const popupOverlay = document.getElementById('popupOverlay');
    if (popupMessage && popupOverlay) {
        popupMessage.textContent = message;
        popupOverlay.style.display = 'flex';
    }
}

function hidePopup() {
    const popupOverlay = document.getElementById('popupOverlay');
    if (popupOverlay) {
        popupOverlay.style.display = 'none';
        currentFormId = '';
    }
}

function confirmAction() {
    if (currentFormId) {
        const form = document.getElementById(currentFormId);
        if (form) {
            form.submit();
        }
    }
    hidePopup();
}

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        hidePopup();
    }
});

// Slideshow JavaScript
let slideIndex = 0;
const slides = document.getElementById('slides');
const dots = document.getElementsByClassName('dot');
let slideInterval;

function showSlides() {
    if (!slides || !dots.length) return;
    const slideCount = slides.children.length;
    if (slideIndex >= slideCount) slideIndex = 0;
    if (slideIndex < 0) slideIndex = slideCount - 1;
    slides.style.transform = `translateX(${-slideIndex * 100}%)`;
    for (let i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(' active', '');
    }
    if (dots[slideIndex]) {
        dots[slideIndex].className += ' active';
    }
}

function moveSlide(n) {
    slideIndex += n;
    showSlides();
    resetSlideInterval();
}

function currentSlide(n) {
    slideIndex = n;
    showSlides();
    resetSlideInterval();
}

function resetSlideInterval() {
    clearInterval(slideInterval);
    slideInterval = setInterval(() => {
        slideIndex++;
        showSlides();
    }, 5000);
}

if (slides && dots.length) {
    showSlides();
    resetSlideInterval();
}

// Chat Widget JavaScript
function toggleChat() {
    const chatBody = document.getElementById('chatBody');
    const chatInput = document.getElementById('chatInput');
    if (chatBody && chatInput) {
        const display = chatBody.style.display === 'block' ? 'none' : 'block';
        chatBody.style.display = display;
        chatInput.style.display = display;
    }
}

function sendMessage() {
    const input = document.getElementById('chatMessage');
    const message = input.value.trim();
    if (!message) return;

    const chatBody = document.getElementById('chatBody');
    if (chatBody) {
        const userMessage = document.createElement('div');
        userMessage.className = 'chat-message user';
        userMessage.textContent = message;
        chatBody.appendChild(userMessage);
        input.value = '';
        chatBody.scrollTop = chatBody.scrollHeight;

        fetch("{% url 'ai_chat' %}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': '{{ csrf_token }}',
            },
            body: new URLSearchParams({ 'message': message })
        })
        .then(response => response.json())
        .then(data => {
            const aiMessage = document.createElement('div');
            aiMessage.className = 'chat-message ai';
            aiMessage.textContent = data.response || data.error || 'Sorry, I couldn’t respond. Please try again.';
            chatBody.appendChild(aiMessage);
            chatBody.scrollTop = chatBody.scrollHeight;
        })
        .catch(error => {
            const errorMessage = document.createElement('div');
            errorMessage.className = 'chat-message ai';
            errorMessage.textContent = 'An error occurred. Please try again.';
            chatBody.appendChild(errorMessage);
            chatBody.scrollTop = chatBody.scrollHeight;
        });
    }
}