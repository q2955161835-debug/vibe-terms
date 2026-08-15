import handler from "vinext/server/app-router-entry";
import { assetPathForRequest, canFetchStaticAssets } from "./static-path.mjs";

async function fetchAsset(request, env, pathname) {
  const assetUrl = new URL(assetPathForRequest(pathname), request.url);
  return env.ASSETS.fetch(new Request(assetUrl, request));
}

const worker = {
  async fetch(request, env, ctx) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    if (!canFetchStaticAssets(env)) {
      return handler.fetch(request, env, ctx);
    }

    const response = await fetchAsset(request, env, new URL(request.url).pathname);
    if (response.status !== 404) {
      return response;
    }

    const fallback = await fetchAsset(request, env, "/404.html");
    return new Response(fallback.body, {
      status: 404,
      headers: fallback.headers,
    });
  },
};

export default worker;
