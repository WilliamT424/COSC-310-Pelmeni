const view = document.getElementById("view");
const customerLink = document.getElementById("customer-link");

function setCustomerLink(customerId) {
  if (!customerLink) return;
  localStorage.setItem("pelmeniCustomerId", String(customerId));
  customerLink.href = `#/customers/${customerId}`;
}

const savedCustomerId = localStorage.getItem("pelmeniCustomerId");
if (savedCustomerId && /^\d+$/.test(savedCustomerId)) {
  setCustomerLink(savedCustomerId);
}

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
  card.append(el("details", {}, el("summary", {}, "Edit"), editForm));
  return card;
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

// Customer registration and account management ------------------------------
function customerRegistrationForm() {
  const message = el("p", { className: "error" });
  const form = el("form", { className: "edit" },
    field("Name", "name", "text", "", { required: true }),
    field("Email", "email", "email", "", { required: true }),
    field("Street", "street", "text", "", { required: true }),
    field("City", "city", "text", "", { required: true }),
    field("Province", "province", "text", "", { required: true }),
    field("Postal code", "postal_code", "text", "", { required: true }),
    field("Country", "country", "text", "", { required: true }),
    el("button", { type: "submit" }, "Create account"),
    message,
  );
  form.addEventListener("submit", async e => {
    e.preventDefault();
    try {
      const saved = await api("/customers", jsonRequest("POST", Object.fromEntries(new FormData(form))));
      setCustomerLink(saved.customerId);
      location.hash = `#/customers/${saved.customerId}`;
    } catch (err) {
      message.textContent = err.message;
    }
  });
  return form;
}

function editableCustomerField(customerId, label, key, value, type = "text") {
  const display = el("span", { className: "account-value" }, value || "—");
  const editButton = el("button", {
    type: "button",
    className: "edit-icon",
    title: `Edit ${label.toLowerCase()}`,
    "aria-label": `Edit ${label.toLowerCase()}`,
  }, "✎");
  const input = el("input", {
    name: key, type, value: value ?? "", required: true,
    "aria-label": label,
  });
  const message = el("span", { className: "error", role: "alert" });
  const cancelButton = el("button", { type: "button", className: "secondary" }, "Cancel");
  const editor = el("form", { className: "inline-editor", hidden: true },
    input,
    el("button", { type: "submit" }, "Save"),
    cancelButton,
    message,
  );

  editButton.addEventListener("click", () => {
    display.hidden = true;
    editButton.hidden = true;
    editor.hidden = false;
    input.focus();
  });
  cancelButton.addEventListener("click", () => {
    input.value = value ?? "";
    message.textContent = "";
    editor.hidden = true;
    display.hidden = false;
    editButton.hidden = false;
  });
  editor.addEventListener("submit", async e => {
    e.preventDefault();
    try {
      await api(`/customers/${customerId}`, jsonRequest("PATCH", { [key]: input.value }));
      await showCustomer(customerId);
    } catch (err) {
      message.textContent = err.message;
    }
  });

  return el("div", { className: "account-field" },
    el("span", { className: "account-label" }, `${label}:`), display, editButton, editor,
  );
}

async function customerView(id = null) {
  view.replaceChildren(el("h2", {}, "Customer accounts"));
  if (id) {
    await showCustomer(id);
    return;
  }

  view.append(
    el("h3", {}, "Create an account"), customerRegistrationForm(),
  );
}

async function showCustomer(id) {
  const customer = await api(`/customers/${id}`);
  const address = customer.deliveryAddress;
  const profile = el("section", { className: "account-details" },
    editableCustomerField(id, "Name", "name", customer.name),
    editableCustomerField(id, "Email", "email", customer.email, "email"),
    el("h4", {}, "Delivery address"),
    editableCustomerField(id, "Street", "street", address.street),
    editableCustomerField(id, "City", "city", address.city),
    editableCustomerField(id, "Province", "province", address.province),
    editableCustomerField(id, "Postal code", "postal_code", address.postal_code),
    editableCustomerField(id, "Country", "country", address.country),
  );
  const statusText = el("p", { className: customer.status ? "ok" : "muted" },
    customer.status ? "Account active" : "Account deactivated");
  const actions = [];
  if (customer.status) {
    const deactivateButton = el("button", { type: "button" }, "Deactivate account");
    deactivateButton.addEventListener("click", async () => {
      try {
        await api(`/customers/${id}/deactivate`, { method: "POST" });
        await showCustomer(id);
      } catch (err) {
        statusText.className = "error";
        statusText.textContent = err.message;
      }
    });
    actions.push(deactivateButton);
  }
  const logoutButton = el("button", { type: "button" }, "Log out");
  logoutButton.addEventListener("click", () => {
    localStorage.removeItem("pelmeniCustomerId");
    customerLink.href = "#/customers";
    location.hash = "#/customers";
  });
  actions.push(logoutButton);
  view.replaceChildren(
    el("h2", {}, `Customer account #${customer.customerId}`),
    statusText,
    el("h3", {}, "Profile"),
    profile,
    el("div", { className: "customer-actions" }, ...actions),
  );
}

// Router --------------------------------------------------------------------
async function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  try {
    if (parts.length === 0) await listView();
    else if (parts[0] === "new") await formView(null);
    else if (parts[0] === "customers" && parts[1]) await customerView(parts[1]);
    else if (parts[0] === "customers") await customerView();
    else if (parts[0] === "restaurant" && parts[2] === "edit") await formView(parts[1]);
    else if (parts[0] === "restaurant") await detailView(parts[1]);
    else view.replaceChildren(el("p", {}, "Page not found."));
  } catch (err) {
    showError(err);
  }
}

window.addEventListener("hashchange", route);
route();
