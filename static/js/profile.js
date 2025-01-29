document.addEventListener("DOMContentLoaded", async function() {
    const username = localStorage.getItem('savedUsername');
    
    try {
        const response = await fetch('/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ "username": username }),
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById("name").textContent = data.username;
            document.getElementById("email").textContent = data.email;
        } else {
            console.error('Failed to fetch profile data');
        }
    } catch (error) {
        console.error('Error fetching profile:', error);
    }
});

function logout() {
    localStorage.clear();
    window.location.href = '/';
}