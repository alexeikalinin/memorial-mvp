/** Accept existing /app/m/:id QR URLs without trusting arbitrary external hosts. */
export function memorialPath(input: string): string | null {
  try {
    const url = new URL(input, 'https://vspomin.ai');
    if(url.username || url.password)return null;
    let path = url.pathname;
    if (url.protocol === 'vspomin:') path = url.hostname === 'm' ? `/m${path}` : path;
    else if (!['https:','http:'].includes(url.protocol) || !['vspomin.ai','www.vspomin.ai'].includes(url.hostname)) return null;
    const match = path.match(/^\/(?:app\/)?m\/(\d+)\/?$/);
    if(!match)return null;
    const id=Number(match[1]);
    return Number.isSafeInteger(id)&&id>0?`/m/${id}`:null;
  } catch { return null; }
}
