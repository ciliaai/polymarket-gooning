// Image Proxy - Handles CORS for Twitter profile images
// Vercel Serverless Function

export default async function handler(req, res) {
    const { url } = req.query;

    if (!url) {
        return res.status(400).json({ error: 'URL required' });
    }

    try {
        // Validate URL is from Twitter/X
        const parsedUrl = new URL(url);
        const allowedHosts = ['pbs.twimg.com', 'abs.twimg.com', 'twitter.com', 'x.com'];

        if (!allowedHosts.some(host => parsedUrl.hostname.includes(host))) {
            return res.status(403).json({ error: 'Only Twitter image URLs allowed' });
        }

        // Fetch the image
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; CiliaAI/1.0)'
            }
        });

        if (!response.ok) {
            return res.status(response.status).json({ error: 'Failed to fetch image' });
        }

        const contentType = response.headers.get('content-type');
        const buffer = await response.arrayBuffer();

        // Set CORS headers
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Content-Type', contentType || 'image/jpeg');
        res.setHeader('Cache-Control', 'public, max-age=86400'); // Cache for 24 hours

        res.send(Buffer.from(buffer));

    } catch (err) {
        console.error('Proxy error:', err);
        res.status(500).json({ error: 'Proxy failed' });
    }
}
