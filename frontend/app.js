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

// Session (JWT from POST /auth/login) ---------------------------------------
// Kept in localStorage so a page refresh doesn't sign the customer out.
const TOKEN_KEY = "pelmeni_token";
const USER_KEY = "pelmeni_user";
const LAST_RESTAURANT_KEY = "pelmeni_last_restaurant";

function store(key, value) {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch (_) { /* storage blocked: session just won't persist */ }
}

function load(key) {
  try { return localStorage.getItem(key); } catch (_) { return null; }
}

function currentUser() {
  try { return JSON.parse(load(USER_KEY)); } catch (_) { return null; }
}

function signOut() {
  store(TOKEN_KEY, null);
  store(USER_KEY, null);
  renderNav();
}

// Navigate to a hash, re-rendering even if we are already on it
function go(hash) {
  if (location.hash === hash) route();
  else location.hash = hash;
}

// Views that need a customer call this first; returns the user, or null after redirecting to sign in
function requireLogin() {
  const user = currentUser();
  if (user && load(TOKEN_KEY)) return user;
  try { sessionStorage.setItem("pelmeni_return_to", location.hash); } catch (_) { /* ignore */ }
  go("#/login");
  return null;
}

async function api(path, options = {}) {
  const token = load(TOKEN_KEY);
  if (token) {
    options = { ...options, headers: { ...options.headers, Authorization: `Bearer ${token}` } };
  }
  const response = await fetch(path, options);
  if (!response.ok) {
    if (response.status === 401 && token) {
      // Token expired or the account was deactivated: the session is no longer valid
      signOut();
      go("#/login");
    }
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
    const addForm = itemForm(null, async data => {
      await api(`/restaurants/${id}/menus/${menu.id}/items`, jsonRequest("POST", data));
      detailView(id);
    });
    menusBox.append(el("h4", {}, menu.name), list, el("details", {}, el("summary", {}, "Add item"), addForm));
    try {
      // Items come from the dedicated menu-items endpoint
      const items = await api(`/restaurants/${id}/menus/${menu.id}/items`);
      list.replaceChildren(...items.map(item => itemCard(id, menu.id, item)));
    } catch (err) {
      list.append(el("p", { className: "error" }, err.message));
    }
  }
}

function jsonRequest(method, body) {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

function itemCard(restaurantId, menuId, item) {
  const card = el("div", { className: "card" },
    el("span", { className: item.available ? "" : "unavailable" }, `${item.name} — $${item.price.toFixed(2)}`),
    el("div", { className: "muted" }, item.description + (item.available ? "" : " (unavailable)")),
  );
  const editForm = itemForm(item, async data => {
    await api(`/restaurants/${restaurantId}/menus/${menuId}/items/${item.id}`, jsonRequest("PATCH", data));
    detailView(restaurantId);
  });
  card.append(addToCartControl(restaurantId, menuId, item));
  card.append(el("details", {}, el("summary", {}, "Edit"), editForm));
  return card;
}

// Cart ----------------------------------------------------------------------
function money(amount) {
  return `$${Number(amount).toFixed(2)}`;
}

function addToCartControl(restaurantId, menuId, item) {
  if (!item.available) return el("span", {});
  const message = el("span", { className: "muted" });
  const quantity = el("input", { type: "number", min: 1, step: 1, value: 1, className: "qty" });
  const button = el("button", { type: "button" }, "Add to cart");
  button.addEventListener("click", async () => {
    const user = requireLogin();
    if (!user) return;
    button.disabled = true;
    try {
      await api(`/customers/${user.customerId}/cart/items`, jsonRequest("POST", {
        restaurant_id: Number(restaurantId),
        menu_id: menuId,
        menu_item_id: item.id,
        quantity: Number(quantity.value),
      }));
      store(LAST_RESTAURANT_KEY, String(restaurantId));
      message.className = "ok";
      message.replaceChildren("Added. ", el("a", { href: `#/cart/${restaurantId}` }, "View cart"));
    } catch (err) {
      message.className = "error";
      message.textContent = err.message;
    } finally {
      button.disabled = false;
    }
  });
  return el("div", { className: "add-to-cart" }, quantity, button, message);
}

// The cart is always re-fetched after a change so the total shown is the backend's, never computed here
async function cartView(restaurantId) {
  const user = requireLogin();
  if (!user) return;
  restaurantId = restaurantId || load(LAST_RESTAURANT_KEY);
  if (!restaurantId) {
    view.replaceChildren(el("h2", {}, "Your cart"),
      el("p", { className: "muted" }, "Your cart is empty. Pick a restaurant and add something from its menu."),
      el("a", { href: "#/" }, "Browse restaurants"));
    return;
  }
  store(LAST_RESTAURANT_KEY, String(restaurantId));

  const restaurant = await api(`/restaurants/${restaurantId}`);
  const cart = await api(`/customers/${user.customerId}/cart?restaurant_id=${restaurantId}`);
  const message = el("p");
  const base = `/customers/${user.customerId}/cart`;

  async function change(request) {
    try {
      await request();
      cartView(restaurantId);
    } catch (err) {
      message.className = "error";
      message.textContent = err.message;
    }
  }

  const lines = cart.items.map(line => {
    const quantity = el("input", { type: "number", min: 1, step: 1, value: line.quantity, className: "qty" });
    const query = `restaurant_id=${restaurantId}&menu_id=${line.menu_id}`;
    return el("div", { className: "card" },
      el("div", {}, `${line.name} — ${money(line.price)} each`),
      el("div", { className: "add-to-cart" },
        el("label", { className: "inline" }, "Qty", quantity),
        el("button", { type: "button", onclick: () => change(() =>
          api(`${base}/items/${line.menu_item_id}?${query}`, jsonRequest("PATCH", { quantity: Number(quantity.value) }))) }, "Update"),
        el("button", { type: "button", onclick: () => change(() =>
          api(`${base}/items/${line.menu_item_id}?${query}`, { method: "DELETE" })) }, "Remove"),
      ));
  });

  const checkoutButton = el("button", { type: "button", disabled: cart.items.length === 0 }, "Check out");
  checkoutButton.addEventListener("click", async () => {
    checkoutButton.disabled = true;
    try {
      const order = await api(`/customers/${user.customerId}/checkout?restaurant_id=${restaurantId}`, { method: "POST" });
      go(`#/order/${order.orderId}`);
    } catch (err) {
      // e.g. an item became unavailable: the cart is untouched, so the customer can fix it and retry
      message.className = "error";
      message.textContent = err.message;
      checkoutButton.disabled = false;
    }
  });

  view.replaceChildren(
    el("h2", {}, "Your cart"),
    el("p", {}, "From ", el("a", { href: `#/restaurant/${restaurantId}` }, restaurant.name)),
    ...(lines.length ? lines : [el("p", { className: "muted" }, "Your cart is empty.")]),
    el("p", {}, `Subtotal: ${money(cart.subtotal ?? 0)}`),
    el("p", {}, el("strong", {}, `Total: ${money(cart.total ?? 0)}`)),
    checkoutButton,
    message,
  );
}

// Orders --------------------------------------------------------------------
function orderSummary(order) {
  return el("div", {},
    el("p", {}, el("a", { href: `#/restaurant/${order.restaurant_id}` }, order.restaurant_name)),
    el("p", { className: "muted" }, `Status: ${order.status} · placed ${new Date(order.created_at).toLocaleString()}`),
    el("p", { className: "muted" },
      `Delivering to ${order.deliveryAddress.street}, ${order.deliveryAddress.city}, ${order.deliveryAddress.province} ${order.deliveryAddress.postal_code}`),
    ...order.items.map(line => el("div", {}, `${line.quantity} × ${line.name} — ${money(line.price)} each`)),
    el("p", {}, `Subtotal: ${money(order.subtotal)}`),
    el("p", {}, el("strong", {}, `Total: ${money(order.total)}`)),
  );
}

async function orderView(orderId) {
  if (!requireLogin()) return;
  const order = await api(`/orders/${orderId}`);
  view.replaceChildren(
    el("h2", {}, `Order #${order.orderId}`),
    el("p", { className: "ok" }, "Your order was placed."),
    orderSummary(order),
    el("p", {}, el("a", { href: "#/orders" }, "All my orders")),
  );
}

async function ordersView() {
  const user = requireLogin();
  if (!user) return;
  const { orders } = await api(`/customers/${user.customerId}/orders`);
  view.replaceChildren(
    el("h2", {}, "My orders"),
    ...(orders.length === 0 ? [el("p", { className: "muted" }, "No orders yet.")] :
      orders.slice().reverse().map(order => el("div", { className: "card" },
        el("a", { href: `#/order/${order.orderId}` }, `Order #${order.orderId}`),
        el("div", { className: "muted" }, `${order.restaurant_name} · ${order.status} · ${money(order.total)}`)))),
  );
}

// Register / sign in --------------------------------------------------------
async function signIn(email, password) {
  const { access_token } = await api("/auth/login", jsonRequest("POST", { email, password }));
  store(TOKEN_KEY, access_token);
  const me = await api("/auth/me");
  store(USER_KEY, JSON.stringify(me));
  renderNav();
  let target = "#/";
  try {
    target = sessionStorage.getItem("pelmeni_return_to") || target;
    sessionStorage.removeItem("pelmeni_return_to");
  } catch (_) { /* ignore */ }
  go(target.startsWith("#/login") || target.startsWith("#/register") ? "#/" : target);
}

function loginView() {
  const message = el("p", { className: "error" });
  const form = el("form", { className: "edit" },
    field("Email", "email", "email", "", { required: true }),
    field("Password", "password", "password", "", { required: true }),
    el("button", { type: "submit" }, "Sign in"),
  );
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(form));
    try {
      await signIn(values.email, values.password);
    } catch (err) {
      message.textContent = err.message;
    }
  });
  view.replaceChildren(el("h2", {}, "Sign in"), form, message,
    el("p", {}, "No account? ", el("a", { href: "#/register" }, "Register")));
}

function registerView() {
  const message = el("p", { className: "error" });
  const form = el("form", { className: "edit" },
    field("Name", "name", "text", "", { required: true }),
    field("Email", "email", "email", "", { required: true }),
    field("Password (min 8 characters)", "password", "password", "", { required: true, minLength: 8 }),
    field("Street", "street", "text", "", { required: true }),
    field("City", "city", "text", "", { required: true }),
    field("Province", "province", "text", "", { required: true }),
    field("Postal code", "postal_code", "text", "", { required: true }),
    field("Country", "country", "text", "", { required: true }),
    el("button", { type: "submit" }, "Create account"),
  );
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(form));
    try {
      await api("/customers", jsonRequest("POST", values));
      await signIn(values.email, values.password);
    } catch (err) {
      message.textContent = err.message;
    }
  });
  view.replaceChildren(el("h2", {}, "Register"), form, message,
    el("p", {}, "Already registered? ", el("a", { href: "#/login" }, "Sign in")));
}

// Navigation bar ------------------------------------------------------------
function renderNav() {
  const nav = document.getElementById("nav");
  const user = currentUser();
  const links = [el("a", { href: "#/" }, "Restaurants"), el("a", { href: "#/new" }, "Add restaurant")];
  if (user) {
    links.push(
      el("a", { href: "#/cart" }, "Cart"),
      el("a", { href: "#/orders" }, "My orders"),
      el("span", {}, `Signed in as ${user.name}`),
      el("button", { type: "button", onclick: () => { signOut(); go("#/"); } }, "Sign out"),
    );
  } else {
    links.push(el("a", { href: "#/login" }, "Sign in"), el("a", { href: "#/register" }, "Register"));
  }
  nav.replaceChildren(...links);
}

// Shared add/edit form for a menu item; onSave(data) may throw, which is shown inline
function itemForm(item, onSave) {
  const message = el("p", { className: "error" });
  const available = el("input", { name: "available", type: "checkbox", checked: item?.available ?? true });
  const form = el("form", { className: "edit" },
    field("Name", "name", "text", item?.name ?? "", { required: true }),
    field("Description", "description", "text", item?.description ?? ""),
    field("Price", "price", "number", item?.price ?? "", { required: true, min: 0, step: "0.01" }),
    el("label", {}, "Available", available),
    el("button", { type: "submit" }, item ? "Save item" : "Add item"),
    message,
  );
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(form));
    try {
      await onSave({
        name: values.name,
        description: values.description,
        price: Number(values.price),
        available: available.checked,
      });
    } catch (err) {
      message.textContent = err.message;
    }
  });
  return form;
}

// Create / update restaurant ------------------------------------------------
async function formView(id) {
  const existing = id ? await api(`/restaurants/${id}`) : null;
  const message = el("p");
  const form = el("form", { className: "edit" },
    field("Name", "name", "text", existing?.name ?? "", { required: true }),
    field("Cuisine", "cuisine", "text", existing?.cuisine ?? "", { required: true }),
    field("Rating (0-5)", "rating", "number", existing?.rating ?? "", { required: true, min: 0, max: 5, step: "any" }),
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
        // The server assigns the id
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
    else if (parts[0] === "login") loginView();
    else if (parts[0] === "register") registerView();
    else if (parts[0] === "cart") await cartView(parts[1]);
    else if (parts[0] === "orders") await ordersView();
    else if (parts[0] === "order") await orderView(parts[1]);
    else if (parts[0] === "new") await formView(null);
    else if (parts[0] === "restaurant" && parts[2] === "edit") await formView(parts[1]);
    else if (parts[0] === "restaurant") await detailView(parts[1]);
    else view.replaceChildren(el("p", {}, "Page not found."));
  } catch (err) {
    showError(err);
  }
}

window.addEventListener("hashchange", route);
renderNav();
route();
