const isProd = !['localhost', '127.0.0.1'].includes(window.location.hostname);

const CSRF_COOKIE_NAME = 'csrftoken';
const CSRF_HEADER_NAME = 'X-CSRF-Token';
const SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS', 'TRACE'];

function readCsrfToken() {
    const prefix = `${CSRF_COOKIE_NAME}=`;
    const match = document.cookie
        .split('; ')
        .find((entry) => entry.startsWith(prefix));
    return match ? decodeURIComponent(match.slice(prefix.length)) : null;
}

// The server rejects a state-changing request whose token is missing or
// does not match the cookie. Every write goes through here, so this is the
// only place that has to echo it back.
function withCsrfToken(options) {
    const method = (options.method || 'GET').toUpperCase();
    if (SAFE_METHODS.includes(method)) {
        return options;
    }

    const token = readCsrfToken();
    if (!token) {
        return options;
    }

    return {
        ...options,
        headers: {...(options.headers || {}), [CSRF_HEADER_NAME]: token},
    };
}

async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, withCsrfToken(options));
        let payload = null;
        try {
            payload = await response.json();
        } catch {
            payload = null;
        }

        if (!response.ok) {
            const errorMessage =
                (payload && (payload.error || payload.detail || payload.message)) ||
                response.statusText ||
                'Request failed';
            if (!isProd) {
                console.error('API error:', response.status, errorMessage);
            }
            return {data: payload, error: errorMessage, status: response.status};
        }

        return {data: payload, error: null, status: response.status};
    } catch (error) {
        if (!isProd) {
            console.error('API network error:', error);
        }
        return {
            data: null,
            error: 'Network error. Please try again.',
            status: 0,
        };
    }
}

function apiGet(url) {
    return apiRequest(url);
}

function apiPost(url, payload) {
    return apiRequest(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
    });
}

function apiPut(url, payload) {
    return apiRequest(url, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
    });
}

function apiPatch(url, payload) {
    return apiRequest(url, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: payload ? JSON.stringify(payload) : null,
    });
}

function apiDelete(url) {
    return apiRequest(url, {method: 'DELETE'});
}
