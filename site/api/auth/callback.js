// Twitter OAuth 2.0 - Callback Handler
// Vercel Serverless Function

export default async function handler(req, res) {
    const { code, state, error } = req.query;

    // Check for errors from Twitter
    if (error) {
        return res.redirect('/?error=' + encodeURIComponent(error));
    }

    // Verify state matches
    const cookies = parseCookies(req.headers.cookie);
    if (state !== cookies.oauth_state) {
        return res.redirect('/?error=invalid_state');
    }

    const codeVerifier = cookies.code_verifier;
    if (!codeVerifier) {
        return res.redirect('/?error=missing_verifier');
    }

    const clientId = process.env.TWITTER_CLIENT_ID;
    const clientSecret = process.env.TWITTER_CLIENT_SECRET;
    const redirectUri = process.env.TWITTER_REDIRECT_URI || 'https://your-domain.vercel.app/api/auth/callback';

    try {
        // Exchange code for access token
        const tokenResponse = await fetch('https://api.twitter.com/2/oauth2/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'Basic ' + Buffer.from(`${clientId}:${clientSecret}`).toString('base64')
            },
            body: new URLSearchParams({
                grant_type: 'authorization_code',
                code: code,
                redirect_uri: redirectUri,
                code_verifier: codeVerifier
            })
        });

        if (!tokenResponse.ok) {
            const errorData = await tokenResponse.text();
            console.error('Token error:', errorData);
            return res.redirect('/?error=token_failed');
        }

        const tokenData = await tokenResponse.json();
        const accessToken = tokenData.access_token;

        // Get user profile with profile image
        const userResponse = await fetch('https://api.twitter.com/2/users/me?user.fields=profile_image_url,username,name', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!userResponse.ok) {
            return res.redirect('/?error=user_fetch_failed');
        }

        const userData = await userResponse.json();
        const user = userData.data;

        // Get high-res profile image (replace _normal with _400x400)
        let profileImageUrl = user.profile_image_url || '';
        profileImageUrl = profileImageUrl.replace('_normal', '_400x400');

        // Clear OAuth cookies
        res.setHeader('Set-Cookie', [
            'oauth_state=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0',
            'code_verifier=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0'
        ]);

        // Redirect back with user data
        const params = new URLSearchParams({
            twitter_connected: 'true',
            username: user.username,
            name: user.name,
            pfp: profileImageUrl
        });

        res.redirect(`/?${params.toString()}`);

    } catch (err) {
        console.error('OAuth error:', err);
        return res.redirect('/?error=oauth_failed');
    }
}

function parseCookies(cookieHeader) {
    const cookies = {};
    if (!cookieHeader) return cookies;

    cookieHeader.split(';').forEach(cookie => {
        const [name, value] = cookie.trim().split('=');
        if (name && value) {
            cookies[name] = value;
        }
    });

    return cookies;
}
