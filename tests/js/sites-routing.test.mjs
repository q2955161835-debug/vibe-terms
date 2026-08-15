import assert from "node:assert/strict";
import test from "node:test";

import {
  assetPathForRequest,
  canFetchStaticAssets,
} from "../../worker/static-path.mjs";

test("maps clean static routes to generated index files", () => {
  assert.equal(assetPathForRequest("/"), "/index.html");
  assert.equal(assetPathForRequest("/de/"), "/de/index.html");
  assert.equal(
    assetPathForRequest("/de/terms/authentication"),
    "/de/terms/authentication/index.html",
  );
});

test("preserves requests for generated assets and metadata", () => {
  assert.equal(assetPathForRequest("/assets/styles.css"), "/assets/styles.css");
  assert.equal(assetPathForRequest("/sitemap.xml"), "/sitemap.xml");
});

test("uses the asset binding only when the runtime provides it", () => {
  assert.equal(canFetchStaticAssets(undefined), false);
  assert.equal(canFetchStaticAssets({}), false);
  assert.equal(canFetchStaticAssets({ ASSETS: { fetch() {} } }), true);
});
