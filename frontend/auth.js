const PelmeniAuth = (() => {
    let accessToken = null;

    function getToken() {
        return accessToken;
    }

    function isLoggedIn() {
        return accessToken !== null;
    }

    async function login(email, password) {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        if (!response.ok) {
            throw new Error("Incorrect email or password");
        }

        const data = await response.json();

        if (!data.access_token) {
            throw new Error("No access token returned");
        }

        accessToken = data.access_token;

        return data;
    }

    function getAuthHeaders() {
        if (!accessToken) {
            return {};
        }

        return {
            "Authorization": `Bearer ${accessToken}`
        };
    }

    async function getCurrentUser() {
        if (!accessToken) {
            throw new Error("Please log in first");
        }

        const response = await fetch("/auth/me", {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                logout();
                window.dispatchEvent(new Event("authchange"));
            }

            throw new Error("Unable to retrieve account");
        }

        return response.json();
    }

    function logout() {
        accessToken = null;
    }

    return {
        login,
        logout,
        getToken,
        isLoggedIn,
        getAuthHeaders,
        getCurrentUser
    };
})();