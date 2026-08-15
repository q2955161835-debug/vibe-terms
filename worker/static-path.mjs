export function assetPathForRequest(pathname) {
  if (pathname === "/") {
    return "/index.html";
  }

  if (pathname.endsWith("/")) {
    return `${pathname}index.html`;
  }

  const finalSegment = pathname.slice(pathname.lastIndexOf("/") + 1);
  if (!finalSegment.includes(".")) {
    return `${pathname}/index.html`;
  }

  return pathname;
}

export function canFetchStaticAssets(env) {
  return typeof env?.ASSETS?.fetch === "function";
}
