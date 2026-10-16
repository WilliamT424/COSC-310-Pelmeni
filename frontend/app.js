const view = document.getElementById("view");

// Small helpers -------------------------------------------------------------
function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  Object.assign(node, props);
  for (const child of children) {
    node.append(child);
  }
  return node;
}

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map(d => d.msg).join(", ");
    } catch (_) { /* non-JSON error body */ }
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json();
}

function showError(err) {
  view.replaceChildren(el("p", { className: "error" }, err.message));
}

function field(label, name, type = "text", value = "", extra = {}) {
  return el("label", {}, label, el("input", { name, type, value, ...extra }));
}

// Restaurant list + search/filter -------------------------------------------
async function listView() {
  const form = el("form", { className: "filters" },
    field("Name", "name"),
    field("Cuisine", "cuisine"),
    field("Min rating (0-5)", "min_rating", "number", "", { min: 0, max: 5 }),
    field("Max delivery (min)", "max_delivery_time", "number", "", { min: 0 }),
    el("button", { type: "submit" }, "Search"),
    el("button", { type: "button", onclick: () => { form.reset(); load(); } }, "Clear"),
  );
  const results = el("div");
  view.replaceChildren(el("h2", {}, "Restaurants"), form, results);

  async function load() {
    const params = new URLSearchParams();
    for (const [key, value] of new FormData(form)) {
      if (value !== "") params.set(key, value);
    }
    try {
      const data = await api(`/restaurants/search?${params}`);
      if (data.restaurants.length === 0) {
        results.replaceChildren(el("p", { className: "muted" }, "No restaurants match."));
        return;
      }
      results.replaceChildren(...data.restaurants.map(r =>
        el("div", { className: "card" },
          el("a", { href: `#/restaurant/${r.id}` }, r.name),
          el("div", { className: "muted" }, `${r.cuisine} · rating ${r.rating} · ${r.deliveryTime} min`),
        )));
    } catch (err) {
      results.replaceChildren(el("p", { className: "error" }, err.message));
    }
  }

  form.addEventListener("submit", e => { e.preventDefault(); load(); });
  load();
}

// Restaurant details, menus and items ---------------------------------------
async function detailView(id) {
  const restaurant = await api(`/restaurants/${id}`);
  const menusBox = el("div");
  view.replaceChildren(
    el("h2", {}, restaurant.name),
    el("p", { className: "muted" },
      `${restaurant.cuisine} · rating ${restaurant.rating} · ${restaurant.deliveryTime} min delivery`),
    el("p", {}, el("a", { href: `#/restaurant/${id}/edit` }, "Edit restaurant")),
    el("h3", {}, "Menu"),
    menusBox,
  );

  let menus = [];
  try {
    menus = await api(`/restaurants/${id}/menus`);
  } catch (err) {
    menusBox.append(el("p", { className: "muted" }, "No menu available."));
    return;
  }
  for (const menu of menus) {
    const list = el("div");
    menusBox.append(el("h4", {}, menu.name), list);
    try {
      // Items come from the dedicated menu-items endpoint
      const items = await api(`/restaurants/${id}/menus/${menu.id}/items`);
      list.replaceChildren(...items.map(item =>
        el("div", { className: "card" },
          el("span", { className: item.available ? "" : "unavailable" }, `${item.name} — $${item.price.toFixed(2)}`),
          el("div", { className: "muted" }, item.description + (item.available ? "" : " (unavailable)")),
        )));
    } catch (err) {
      list.append(el("p", { className: "error" }, err.message));
    }
  }
}

// Create / update restaurant ------------------------------------------------
async function formView(id) {
  const existing = id ? await api(`/restaurants/${id}`) : null;
  const message = el("p");
  const form = el("form", { className: "edit" },
    field("Name", "name", "text", existing?.name ?? "", { required: true }),
    field("Cuisine", "cuisine", "text", existing?.cuisine ?? "", { required: true }),
    field("Rating (0-5)", "rating", "number", existing?.rating ?? "", { required: true, min: 0, max: 5, step: existing ? "any" : 1 }),
    field("Delivery time (min)", "deliveryTime", "number", existing?.deliveryTime ?? "", { required: true, min: 0 }),
    el("button", { type: "submit" }, existing ? "Save changes" : "Create restaurant"),
  );
  view.replaceChildren(el("h2", {}, existing ? `Edit ${existing.name}` : "Add restaurant"), form, message);

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    data.rating = Number(data.rating);
    data.deliveryTime = Number(data.deliveryTime);
    try {
      let saved;
      if (existing) {
        saved = await api(`/restaurants/${id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
      } else {
        // The API requires a client-supplied id: use the next free one
        const all = await api("/restaurants");
        data.id = Math.max(0, ...all.restaurants.map(r => r.id)) + 1;
        saved = await api("/restaurants", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
      }
      location.hash = `#/restaurant/${saved.id}`;
    } catch (err) {
      message.className = "error";
      message.textContent = err.message;
    }
  });
}

// Router --------------------------------------------------------------------
async function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  try {
    if (parts.length === 0) await listView();
    else if (parts[0] === "new") await formView(null);
    else if (parts[0] === "restaurant" && parts[2] === "edit") await formView(parts[1]);
    else if (parts[0] === "restaurant") await detailView(parts[1]);
    else view.replaceChildren(el("p", {}, "Page not found."));
  } catch (err) {
    showError(err);
  }
}

window.addEventListener("hashchange", route);
route();
