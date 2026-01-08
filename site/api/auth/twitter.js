// Twitter OAuth 2.0 - Initiate Login
// Vercel Serverless Function

export default function handler(req, res) {
    const clientId = process.env.TWITTER_CLIENT_ID;
    const redirectUri = process.env.TWITTER_REDIRECT_URI || 'https://your-domain.vercel.app/api/auth/callback';

    if (!clientId) {
        return res.status(500).json({ error: 'Twitter client ID not configured' });
    }

    // Generate state for CSRF protection
    const state = Math.random().toString(36).substring(2, 15);

    // PKCE code verifier and challenge
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = codeVerifier; // For plain method, or use S256 hash

    // Store in cookie for callback verification
    res.setHeader('Set-Cookie', [
        `oauth_state=${state}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600`,
        `code_verifier=${codeVerifier}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600`
    ]);

    // Twitter OAuth 2.0 authorization URL
    const authUrl = new URL('https://twitter.com/i/oauth2/authorize');
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('client_id', clientId);
    authUrl.searchParams.set('redirect_uri', redirectUri);
    authUrl.searchParams.set('scope', 'tweet.read users.read');
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('code_challenge', codeChallenge);
    authUrl.searchParams.set('code_challenge_method', 'plain');

    res.redirect(302, authUrl.toString());
}

function generateCodeVerifier() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
    let result = '';
    for (let i = 0; i < 64; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}
