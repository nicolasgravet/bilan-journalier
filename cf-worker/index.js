export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }
    const response = await fetch(
      'https://api.github.com/repos/nicolasgravet/bilan-journalier/actions/workflows/generate.yml/dispatches',
      {
        method: 'POST',
        headers: {
          'Authorization': `token ${env.GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
          'User-Agent': 'Mecanicus-Bilan'
        },
        body: JSON.stringify({ ref: 'main' })
      }
    );
    return new Response(
      JSON.stringify({ ok: response.ok, status: response.status }),
      { headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } }
    );
  }
};
