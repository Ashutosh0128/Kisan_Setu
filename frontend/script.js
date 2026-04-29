// State Management
const API_BASE = '/api/';
const BACKEND_BASE = '';
let equipment = [];
let currentUser = null;

// Helper to get CSRF token from cookies
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

function resolveImage(path) {
    if (!path) return 'https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&q=80&w=800';
    if (path.startsWith('http')) return path;
    if (path.startsWith('/media/')) return `${BACKEND_BASE}${path}`;
    if (path.startsWith('assets/')) return `/static/${path}`; // Added to support moved static assets
    return path;
}

async function fetchAPI(endpoint, options = {}) {
    const csrftoken = getCookie('csrftoken');
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
        ...options.headers,
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        // If we get a 401 on an API call, we might have lost our session
        if (currentUser) logout();
        return null;
    }

    return response;
}

// DOM Elements
const equipmentGrid = document.getElementById('equipmentGrid');
const searchInput = document.getElementById('equipmentSearch');
const filterButtons = document.querySelectorAll('.filter-btn');
const navbar = document.getElementById('navbar');
const modal = document.getElementById('bookingModal');
const closeModal = document.querySelector('.close-modal');
const rentalForm = document.getElementById('rentalForm');
const themeToggle = document.getElementById('themeToggle');
const sunIcon = document.getElementById('sunIcon');
const moonIcon = document.getElementById('moonIcon');

// Initialize
async function init() {
    await checkAuth();
    await fetchEquipment();
    setupEventListeners();
    initTheme();
}

async function checkAuth() {
    try {
        const resp = await fetch(`${BACKEND_BASE}/current-user/`);
        if (resp && resp.ok) {
            const userData = await resp.json();
            if (userData.authenticated) {
                currentUser = {
                    id: userData.id,
                    name: userData.username,
                    email: userData.email,
                    role: userData.profile ? userData.profile.role : 'farmer'
                };
            } else {
                currentUser = null;
            }
        } else {
            currentUser = null;
        }
    } catch (e) {
        console.error("Auth check failed", e);
        currentUser = null;
    }
    updateUIForUser();
}

async function fetchEquipment() {
    try {
        const resp = await fetch(`${API_BASE}equipment/`);
        if (resp.ok) {
            equipment = await resp.json();
            renderEquipment(equipment);
        }
    } catch (e) {
        console.error("Failed to fetch equipment", e);
    }
}

// Theme Logic
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
}

function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    if (theme === 'dark') {
        sunIcon.style.display = 'none';
        moonIcon.style.display = 'flex';
    } else {
        sunIcon.style.display = 'flex';
        moonIcon.style.display = 'none';
    }
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

// Render Cards
function renderEquipment(data) {
    equipmentGrid.innerHTML = '';
    if (data.length === 0) {
        equipmentGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem;"><h3>No equipment found.</h3></div>';
        return;
    }
    data.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card animate-up';
        card.innerHTML = `
            <div class="card-image-container">
                <img src="${resolveImage(item.image)}" alt="${item.name}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&q=80&w=800'">
                <span class="card-tag">${item.category}</span>
            </div>
            <div class="card-content">
                <h3>${item.name}</h3>
                <p>${item.description}</p>
                <div class="card-meta">
                    <span class="price">₹${item.price.toLocaleString('en-IN')} <small>/ day</small></span>
                    <button class="btn btn-primary" onclick="openBooking('${item.id}')">Rent</button>
                </div>
            </div>
        `;
        equipmentGrid.appendChild(card);
    });
}

// Event Listeners
function setupEventListeners() {
    // Navbar Scroll Effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Theme Toggle
    themeToggle.addEventListener('click', toggleTheme);

    // Search
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = equipment.filter(item =>
            item.name.toLowerCase().includes(term) ||
            item.category.toLowerCase().includes(term)
        );
        renderEquipment(filtered);
    });

    // Filter Buttons
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filter = btn.dataset.filter;
            const approvedOnly = equipment.filter(e => e.status === 'approved');
            
            if (filter === 'all') {
                renderEquipment(approvedOnly);
            } else {
                const filtered = approvedOnly.filter(item => item.category === filter);
                renderEquipment(filtered);
            }
        });
    });

    // Modal Close
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    // Form Submit (Open Payment)
    rentalForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const activeId = modal.dataset.activeId;
        const item = equipment.find(et => et.id == activeId);
        const days = parseInt(document.querySelector('#rentalForm select').value);
        const total = item.price * days;

        modal.style.display = 'none';
        
        const paymentModal = document.getElementById('paymentModal');
        document.getElementById('paymentSummary').innerHTML = `
            <h3>${item.name}</h3>
            <p>${days} Day(s) Rental</p>
            <div class="total-price-tag">Amount to Pay: <span>₹${total.toLocaleString('en-IN')}</span></div>
        `;
        paymentModal.style.display = 'flex';
    });

    // Auth Form Logic (Wait until DOM is ready for these specific elements)
    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.addEventListener('submit', handleLogin);

    const registerForm = document.getElementById('registerForm');
    if (registerForm) registerForm.addEventListener('submit', handleRegister);
}

function selectPayment(method) {
    const methods = document.querySelectorAll('.payment-method');
    methods.forEach(m => m.classList.remove('active'));
    
    const upiSection = document.getElementById('upiSection');
    const cardSection = document.getElementById('cardSection');

    if (method === 'upi') {
        methods[0].classList.add('active');
        upiSection.style.display = 'block';
        cardSection.style.display = 'none';
    } else {
        methods[1].classList.add('active');
        upiSection.style.display = 'none';
        cardSection.style.display = 'block';
    }
}

async function processPayment() {
    const btn = document.querySelector('#paymentModal .btn-primary');
    btn.innerText = 'Processing...';
    btn.disabled = true;

    // Send the actual booking request to backend
    if (!currentUser) {
        alert("Please login to complete booking.");
        return;
    }

    const activeId = modal.dataset.activeId;
    const days = parseInt(document.querySelector('#rentalForm select').value) || 1;

    try {
        const resp = await fetchAPI('bookings/', {
            method: 'POST',
            body: JSON.stringify({
                equipment: activeId,
                duration_days: days,
                start_date: new Date().toISOString().split('T')[0] // today's date
            })
        });

        if (resp && resp.ok) {
            document.getElementById('paymentModal').style.display = 'none';
            document.getElementById('successModal').style.display = 'flex';
            if (currentUser.role === 'farmer') {
                renderFarmerDashboard();
            }
        } else {
            alert('Failed to process booking. Please try again.');
        }
    } catch (e) {
        console.error("Booking error", e);
        alert('An error occurred during booking.');
    } finally {
        btn.innerText = 'Pay Now';
        btn.disabled = false;
    }
}

// Modal Toggle
function openBooking(id) {
    const item = equipment.find(e => e.id == id);
    if (!item) return;

    document.getElementById('modalTitle').innerText = `Rent: ${item.name}`;
    document.getElementById('modalDescription').innerText = item.description;
    
    // Reset pricing in form
    const durationSelect = document.querySelector('#rentalForm select');
    const totalDisplay = document.getElementById('totalPriceDisplay');
    
    function updatePrice() {
        const days = parseInt(durationSelect.value) || 1;
        const total = item.price * days;
        totalDisplay.innerHTML = `Total Amount: <span>₹${total.toLocaleString('en-IN')}</span>`;
    }

    durationSelect.onchange = updatePrice;
    updatePrice();

    modal.dataset.activeId = id;
    modal.style.display = 'flex';
}

function openListingModal() {
    document.getElementById('listingModal').style.display = 'flex';
}

function closeListingModal() {
    document.getElementById('listingModal').style.display = 'none';
}

async function handleNewEquipment(event) {
    if (event) event.preventDefault();
    if (!currentUser) {
        alert("Please login first to list equipment.");
        openAuthModal();
        return;
    }

    const name = document.getElementById('listName').value.trim();
    const category = document.getElementById('listCategory').value;
    const price = document.getElementById('listPrice').value;
    const desc = document.getElementById('listDesc').value.trim();
    const imageInput = document.getElementById('listImage');
    const image = imageInput ? imageInput.value.trim() : "";

    if (!name || !category || !price || !desc) {
        alert("Please fill in all details for your equipment.");
        return;
    }

    const priceNum = parseInt(price);
    if (isNaN(priceNum) || priceNum <= 0) {
        alert("Please enter a valid price greater than zero.");
        return;
    }

    try {
        const payload = {
            name: name,
            category: category,
            price: priceNum,
            description: desc
        };
        if (image) {
            payload.image = image;
        }

        const resp = await fetchAPI('add-equipment/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        if (resp && resp.ok) {
            closeListingModal();
            document.querySelector('#listingModal form').reset();
            alert("Equipment listed successfully! It will appear in the catalog after Admin approval.");
            await fetchEquipment();
            if (currentUser.role === 'owner') renderOwnerDashboard();
        } else {
            const data = await resp?.json();
            alert("Failed to submit listing: " + (data?.error || "Please check your inputs."));
        }
    } catch (e) {
        console.error("Listing error", e);
        alert("An error occurred while submitting your equipment.");
    }
}

// --- Auth Logic ---
function openAuthModal() {
    document.getElementById('authModal').style.display = 'flex';
}

function closeAuthModal() {
    document.getElementById('authModal').style.display = 'none';
}

function switchAuthTab(tab) {
    const tabs = document.querySelectorAll('.auth-tab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    tabs.forEach(t => t.classList.remove('active'));
    if (tab === 'login') {
        tabs[0].classList.add('active');
        loginForm.style.display = 'flex';
        registerForm.style.display = 'none';
    } else {
        tabs[1].classList.add('active');
        loginForm.style.display = 'none';
        registerForm.style.display = 'flex';
    }
}

async function handleRegister(e) {
    if (e) e.preventDefault();
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.toLowerCase().trim();
    const pass = document.getElementById('regPass').value;
    const role = document.getElementById('regRole').value;

    if (!name || !email || !pass || !role) {
        alert("Please fill in all fields.");
        return;
    }

    const csrftoken = getCookie('csrftoken');
    try {
        const resp = await fetch(`${BACKEND_BASE}/signup/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                name: name,
                email: email,
                password: pass,
                profile: { role: role }
            })
        });

        const data = await resp.json();
        if (resp.ok) {
            alert("Registration successful! Welcome to Kisan Setu.");
            await checkAuth();
            closeAuthModal();
            scrollToDashboard();
        } else {
            alert("Registration failed: " + (data.error || "Please check your details and try again."));
        }
    } catch (e) {
        console.error("Registration error", e);
        alert("An error occurred during registration. Please try again.");
    }
}

async function handleLogin(e) {
    if (e) e.preventDefault();
    const email = document.getElementById('loginEmail').value.toLowerCase().trim();
    const pass = document.getElementById('loginPass').value;

    if (!email || !pass) {
        alert("Please enter both email and password.");
        return;
    }

    const csrftoken = getCookie('csrftoken');
    try {
        const resp = await fetch(`${BACKEND_BASE}/login/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                email: email,
                password: pass
            })
        });

        const data = await resp.json();
        if (resp.ok) {
            console.log("Login successful");
            await checkAuth();
            closeAuthModal();
            scrollToDashboard();
        } else {
            alert(data.error || "Invalid email or password.");
        }
    } catch (e) {
        console.error("Login error", e);
        alert("An unexpected error occurred during login.");
    }
}

async function logout() {
    try {
        const csrftoken = getCookie('csrftoken');
        await fetch(`${BACKEND_BASE}/logout/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken }
        });
    } catch (e) {
        console.error("Logout error", e);
    }
    currentUser = null;
    updateUIForUser();
    location.reload();
}

function scrollToDashboard() {
    setTimeout(() => {
        const dashboardSection = document.getElementById('dashboards');
        if (dashboardSection) {
            dashboardSection.style.display = 'block';
            dashboardSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 300);
}

function updateUIForUser() {
    const loginBtn = document.getElementById('loginBtn');
    const userProfile = document.getElementById('userProfile');
    const userNameSpan = document.getElementById('userName');
    const dashboards = document.getElementById('dashboards');
    const adminView = document.getElementById('adminView');
    const ownerView = document.getElementById('ownerView');
    const farmerView = document.getElementById('farmerView');

    if (currentUser) {
        loginBtn.style.display = 'none';
        userProfile.style.display = 'flex';
        userNameSpan.innerText = `Hi, ${currentUser.name.split(' ')[0]}`;
        
        dashboards.style.display = 'block';
        if (currentUser.role === 'admin') {
            adminView.style.display = 'block';
            ownerView.style.display = 'none';
            if (farmerView) farmerView.style.display = 'none';
            renderAdminDashboard();
        } else if (currentUser.role === 'owner') {
            adminView.style.display = 'none';
            ownerView.style.display = 'block';
            if (farmerView) farmerView.style.display = 'none';
            renderOwnerDashboard();
        } else if (currentUser.role === 'farmer') {
            adminView.style.display = 'none';
            ownerView.style.display = 'none';
            if (farmerView) {
                farmerView.style.display = 'block';
                renderFarmerDashboard();
            }
        } else {
            dashboards.style.display = 'none';
        }
    } else {
        loginBtn.style.display = 'flex';
        userProfile.style.display = 'none';
        dashboards.style.display = 'none';
    }
}

// --- Dashboard Logic ---
async function renderOwnerDashboard() {
    const content = document.getElementById('ownerContent');
    if (!content) return;
    try {
        const resp = await fetchAPI('my-equipment/');
        if (resp && resp.ok) {
            const myListings = await resp.json();
            content.innerHTML = myListings.length ? '' : '<p>No listings yet.</p>';
            myListings.forEach(item => {
                const card = document.createElement('div');
                card.className = 'owner-card dashboard-card';
                let statusBadge = item.status === 'pending' ? 'status-pending' : 'status-approved';
                let statusText = item.status.charAt(0).toUpperCase() + item.status.slice(1);
                card.innerHTML = `
                    <div style="display: flex; gap: 1rem; align-items: flex-start; justify-content: space-between;">
                        <div>
                            <h3 style="margin: 0; margin-bottom: 0.5rem;">${item.name}</h3>
                            <span class="status-badge ${statusBadge}" style="margin-bottom: 1rem; display: inline-block;">${statusText}</span>
                        </div>
                        <button onclick="deleteOwnerEquipment(${item.id})" class="btn-delete-small">Delete</button>
                    </div>
                    <p><strong>Expected Price:</strong> ₹${item.price.toLocaleString('en-IN')}/day</p>
                    <p>${item.description.substring(0, 100)}...</p>
                `;
                content.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Dashboard error", e);
    }
}

async function deleteOwnerEquipment(id) {
    if (!confirm("Are you sure you want to delete this equipment?")) return;
    try {
        const resp = await fetchAPI(`delete-equipment/${id}/`, { method: 'DELETE' });
        if (resp && resp.ok) {
            renderOwnerDashboard();
            fetchEquipment();
        } else {
            alert("Delete failed. You may not be authorized.");
        }
    } catch (e) {
        console.error("Delete error", e);
    }
}

async function renderAdminDashboard() {
    renderPendingApprovals();
    renderContactMessages();
    renderFullFleet();
}

async function renderPendingApprovals() {
    const content = document.getElementById('adminContent');
    try {
        const resp = await fetchAPI('equipment/?status=pending');
        if (resp && resp.ok) {
            const pending = await resp.json();
            content.innerHTML = pending.length ? '' : '<p>No pending approvals.</p>';
            pending.forEach(item => {
                const card = document.createElement('div');
                card.className = 'admin-card dashboard-card';
                card.innerHTML = `
                    <h3>${item.name}</h3>
                    <p><strong>Owner:</strong> ${item.owner_name}</p>
                    <p><strong>Suggested Price:</strong> ₹${item.price}</p>
                    <div class="admin-actions">
                        <div class="admin-input-group">
                            <input type="number" id="price-${item.id}" value="${item.price}" class="admin-input">
                            <button onclick="approveEquipment(${item.id})" class="btn btn-primary" style="padding: 0.8rem 1.2rem;">Approve</button>
                        </div>
                    </div>
                `;
                content.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Admin dashboard error", e);
    }
}

async function renderContactMessages() {
    const content = document.getElementById('adminMessages');
    if (!content) return;
    try {
        const resp = await fetchAPI('contact/');
        if (resp && resp.ok) {
            const messages = await resp.json();
            content.innerHTML = messages.length ? '' : '<p>No messages yet.</p>';
            messages.forEach(msg => {
                const card = document.createElement('div');
                card.className = 'admin-card dashboard-card message-card';
                card.innerHTML = `
                    <h3>${msg.subject || 'No Subject'}</h3>
                    <p><strong>From:</strong> ${msg.name} (${msg.email})</p>
                    <p style="margin-top: 1rem; padding: 1rem; background: rgba(128,128,128,0.1); border-radius: 8px;">${msg.message}</p>
                    <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
                        <small style="color: var(--text-muted);">${new Date(msg.created_at).toLocaleDateString()}</small>
                        <button onclick="deleteMessage(${msg.id})" class="btn-delete-small">Delete</button>
                    </div>
                `;
                content.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Messages dashboard error", e);
    }
}

async function renderFullFleet() {
    const content = document.getElementById('adminFullFleet');
    if (!content) return;
    try {
        const resp = await fetchAPI('equipment/?status=all');
        if (resp && resp.ok) {
            const fleet = await resp.json();
            content.innerHTML = fleet.length ? '' : '<p>No equipment in fleet.</p>';
            fleet.forEach(item => {
                const card = document.createElement('div');
                card.className = 'admin-card dashboard-card';
                card.innerHTML = `
                    <div style="display: flex; gap: 1rem; align-items: center;">
                        <img src="${resolveImage(item.image)}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px;">
                        <div style="flex: 1;">
                            <h3 style="font-size: 1rem; margin: 0;">${item.name}</h3>
                            <span class="status-badge status-${item.status}">${item.status}</span>
                        </div>
                        <button onclick="deleteEquipment(${item.id})" class="btn-delete-small">Delete</button>
                    </div>
                `;
                content.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Fleet dashboard error", e);
    }
}

async function deleteMessage(id) {
    if (!confirm("Are you sure you want to delete this message?")) return;
    try {
        const resp = await fetchAPI(`contact/${id}/`, { method: 'DELETE' });
        if (resp && resp.ok) {
            renderContactMessages();
        }
    } catch (e) {
        console.error("Delete message error", e);
    }
}

async function deleteEquipment(id) {
    if (!confirm("Are you sure you want to remove this equipment from the platform?")) return;
    try {
        const resp = await fetchAPI(`equipment/${id}/`, { method: 'DELETE' });
        if (resp && resp.ok) {
            renderFullFleet();
            fetchEquipment();
        }
    } catch (e) {
        console.error("Delete equipment error", e);
    }
}

async function approveEquipment(id) {
    const finalPrice = parseInt(document.getElementById(`price-${id}`).value);
    try {
        const resp = await fetchAPI(`equipment/${id}/approve/`, {
            method: 'PATCH',
            body: JSON.stringify({ price: finalPrice })
        });
        if (resp && resp.ok) {
            alert(`Approved successfully at ₹${finalPrice}/day`);
            renderAdminDashboard();
            fetchEquipment();
        } else {
            alert("Approval failed.");
        }
    } catch (e) {
        console.error("Approval error", e);
    }
}

function checkOwnerAndOpenListing() {
    if (!currentUser) {
        alert("Please login first.");
        openAuthModal();
        return;
    }
    if (currentUser.role !== 'owner' && currentUser.role !== 'admin') {
        alert("Only Equipment Owners can list machinery.");
        return;
    }
    openListingModal();
}

// Start
init();

// Reveal Animation Logic
const revealElements = document.querySelectorAll('.reveal');
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
        }
    });
}, { threshold: 0.15 });

revealElements.forEach(el => revealObserver.observe(el));

// New Logic for Bookings and Contacts
async function renderFarmerDashboard() {
    const content = document.getElementById('farmerContent');
    if (!content) return;
    try {
        const resp = await fetchAPI('bookings/');
        if (resp && resp.ok) {
            const bookings = await resp.json();
            content.innerHTML = bookings.length ? '' : '<p>No bookings found.</p>';
            bookings.forEach(bk => {
                const card = document.createElement('div');
                card.className = 'farmer-card dashboard-card';
                card.innerHTML = `
                    <h3>${bk.equipment_name}</h3>
                    <span class="status-badge status-${bk.status.toLowerCase()}">${bk.status}</span>
                    <p><strong>Start Date:</strong> ${bk.start_date}</p>
                    <p><strong>Duration:</strong> ${bk.duration_days} Day(s)</p>
                    <p><strong>Total Price:</strong> ₹${bk.total_price.toLocaleString('en-IN')}</p>
                `;
                content.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Failed to load bookings", e);
    }
}

async function handleContactSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('contactName').value;
    const email = document.getElementById('contactEmail').value;
    const subject = document.getElementById('contactSubject').value;
    const message = document.getElementById('contactMessage').value;
    const btn = document.querySelector('#contactForm .btn-primary');
    
    btn.innerText = 'Sending...';
    btn.disabled = true;

    try {
        const resp = await fetch(`${API_BASE}contact/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, subject, message })
        });

        if (resp.ok) {
            alert("Your message has been sent successfully! We will get back to you soon.");
            document.getElementById('contactForm').reset();
        } else {
            alert("Failed to send message. Please try again.");
        }
    } catch (err) {
        console.error(err);
        alert("An error occurred while sending the message.");
    } finally {
        btn.innerText = 'Send Message';
        btn.disabled = false;
    }
}
