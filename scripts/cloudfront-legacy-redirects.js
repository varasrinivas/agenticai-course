// CloudFront Function (cloudfront-js-2.0, viewer-request) for the course site.
// 301-redirects pre-June-2026 flat-layout URLs to the new /courses/ structure.
// Deployed as "agenticai-legacy-redirects" on the site's CloudFront distribution
// (ID in the gitignored scripts/deploy-config.ps1).

function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // CC modules that were renumbered when the course moved under /courses/cc/
    var ccRenames = {
        '/cc/CC1-claude-md-and-memory.html': '/courses/cc/CC3-claude-md-and-memory.html',
        '/cc/CC2-permissions-and-sandbox.html': '/courses/cc/CC4-permissions-and-sandbox.html',
        '/cc/CC3-skills-and-commands.html': '/courses/cc/CC5-skills-and-commands.html',
        '/cc/CC4-subagents.html': '/courses/cc/CC6-subagents.html',
        '/cc/CC5-hooks.html': '/courses/cc/CC7-hooks.html',
        '/cc/CC6-mcp.html': '/courses/cc/CC9-mcp.html',
        '/cc/CC7-power-user-and-cicd.html': '/courses/cc/CC14-power-user-and-cicd.html'
    };

    // Course folders that moved from the bucket root to /courses/<same-name>/
    var movedPrefixes = ['/ai-cli-comparison/', '/cc/', '/gemini-cli/', '/mcp/', '/opensource/'];

    var target = null;

    if (ccRenames[uri]) {
        target = ccRenames[uri];
    } else if (uri.startsWith('/interview/')) {
        target = '/courses/claude-agents' + uri;
    } else {
        for (var i = 0; i < movedPrefixes.length; i++) {
            if (uri.startsWith(movedPrefixes[i])) {
                target = '/courses' + uri;
                break;
            }
        }
        // Old flat layout: every root-level page now lives in the main course folder
        if (!target && uri !== '/index.html' && /^\/[^\/]+\.html$/.test(uri)) {
            target = '/courses/claude-agents' + uri;
        }
    }

    if (target) {
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                'location': { value: target },
                'cache-control': { value: 'max-age=86400' }
            }
        };
    }

    return request;
}
