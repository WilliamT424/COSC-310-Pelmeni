const view = document.getElementById("view");
const customerTokenKey = "pelmeniCustomerToken";

// Small helpers -------------------------------------------------------------
function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  Object.assign(node, props);
  for (const child of children) {
    node.append(child);
  }
  return node;
}

async function api(path, options = {}) {
   const headers = new Headers(options.headers || {});

   if (PelmeniAuth.isLoggedIn()) {
     headers.set("Authorization", `Bearer ${PelmeniAuth.getToken()}`);
   }
   const response = await fetch(path, {
     ...options,
     headers
   });
  
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map(d => d.msg).join(", ");
    } catch (_) { /* non-JSON error body */ }
    const error = new Error(`${response.status}: ${detail}`);
    error.status = response.status;
    throw error;
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
    el("p", {}, el("a", { href: `#/cart/${id}` }, "View My Cart")),
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

// Cart API functions --------------------------------------------------------

async function getCustomerId() {
  const customer = await PelmeniAuth.getCurrentUser();
  return customer.customerId;
}

async function getCart(restaurantId) {
  const customerId = await getCustomerId();

  return api(
    `/customers/${customerId}/cart?restaurant_id=${restaurantId}`
  );
}

async function createOrGetCart(restaurantId) {
  const customerId = await getCustomerId();

  return api(
    `/customers/${customerId}/cart?restaurant_id=${restaurantId}`,
    { method: "POST" }
  );
}

async function addToCart(restaurantId, menuId, menuItemId, quantity = 1) {
  const customerId = await getCustomerId();

  return api(
    `/customers/${customerId}/cart/items`,
    jsonRequest("POST", {
      restaurant_id: restaurantId,
      menu_id: menuId,
      menu_item_id: menuItemId,
      quantity: quantity
    })
  );
}

async function updateCartItem(restaurantId, menuId, menuItemId, quantity) {
  const customerId = await getCustomerId();

  return api(
    `/customers/${customerId}/cart/items/${menuItemId}?restaurant_id=${restaurantId}&menu_id=${menuId}`,
    jsonRequest("PATCH", { quantity })
  );
}

async function removeCartItem(restaurantId, menuId, menuItemId) {
  const customerId = await getCustomerId();

  return api(
    `/customers/${customerId}/cart/items/${menuItemId}?restaurant_id=${restaurantId}&menu_id=${menuId}`,
    { method: "DELETE" }
  );
}

async function clearCart(restaurantId) {
  const customerId = await getCustomerId();

  return api(
    `/customers/${customerId}/cart?restaurant_id=${restaurantId}`,
    { method: "DELETE" }
  );
}

async function checkoutCart(restaurantId) {
  const customerId = await getCustomerId();

  return api(
    `/customers/${customerId}/checkout?restaurant_id=${restaurantId}`,
    { method: "POST" }
  );
}

async function getCustomerOrders() {
  const customerId = await getCustomerId();
  return api(`/customers/${customerId}/orders`);
}

function itemCard(restaurantId, menuId, item) {
  const card = el("div", { className: "card" },
    el("span", { className: item.available ? "" : "unavailable" }, `${item.name} — $${item.price.toFixed(2)}`),
    el("div", { className: "muted" }, item.description + (item.available ? "" : " (unavailable)")),
  );

  if (item.available) {
    const addButton = el("button", { type: "button" }, "Add to Cart");

    addButton.addEventListener("click", async () => {
      if (!PelmeniAuth.isLoggedIn()) {
        location.hash = "#/login";
        return;
      }

      addButton.disabled = true;
      addButton.textContent = "Adding...";

      try {
        await createOrGetCart(restaurantId);
        await addToCart(restaurantId, menuId, item.id, 1);

        addButton.textContent = "Added ✓";
      } catch (err) {
        addButton.textContent = "Add to Cart";
        alert(err.message);
      } finally {
        addButton.disabled = false;
      }
    });

    card.append(addButton);
  }
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

// Cart page ----------------------------------------------------------------

async function cartView(restaurantId) {
  if (!PelmeniAuth.isLoggedIn()) {
    location.hash = "#/login";
    return;
  }

  const container = el("section");
  container.append(el("h2", {}, "My Cart"));

  view.replaceChildren(container);

  try {
    let cart = await getCart(restaurantId);

    function renderCart() {
      const itemsBox = el("div");

      if (!cart.items || cart.items.length === 0) {
        itemsBox.append(el("p", { className: "muted" }, "Your cart is empty."));
      } else {
        for (const item of cart.items) {
          const itemBox = el("div", { className: "card" });

          itemBox.append(
            el("h3", {}, item.name),
            el("p", {}, `$${item.price.toFixed(2)} each`),
            el("p", {}, `Quantity: ${item.quantity}`),
            el("p", {}, `Item total: $${(item.price * item.quantity).toFixed(2)}`)
          );

          const quantityInput = el("input", {
            type: "number",
            min: 1,
            value: item.quantity
          });

          const updateButton = el("button", { type: "button" }, "Update quantity");

          updateButton.addEventListener("click", async () => {
            const quantity = Number(quantityInput.value);

            if (!Number.isInteger(quantity) || quantity < 1) {
              alert("Quantity must be at least 1.");
              return;
            }

            try {
              cart = await updateCartItem(
                restaurantId,
                item.menu_id,
                item.menu_item_id,
                quantity
              );

              renderCart();
            } catch (err) {
              alert(err.message);
            }
          });

          const removeButton = el("button", { type: "button" }, "Remove");

          removeButton.addEventListener("click", async () => {
            try {
              cart = await removeCartItem(
                restaurantId,
                item.menu_id,
                item.menu_item_id
              );

              renderCart();
            } catch (err) {
              alert(err.message);
            }
          });

          itemBox.append(quantityInput, updateButton, removeButton);
          itemsBox.append(itemBox);
        }
      }

      const totals = el("section", { className: "card" },
        el("h3", {}, "Order Summary"),
        el("p", {}, `Subtotal: $${cart.subtotal.toFixed(2)}`),
        el("p", {}, `Total: $${cart.total.toFixed(2)}`)
      );

      const clearButton = el("button", { type: "button" }, "Clear Cart");

      clearButton.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to clear your cart?")) return;

        try {
          cart = await clearCart(restaurantId);
          renderCart();
        } catch (err) {
          alert(err.message);
        }
      });

      const checkoutButton = el("button", { type: "button" }, "Checkout");

      checkoutButton.addEventListener("click", async () => {
        if (!confirm("Place your order?")) return;

        try {
          const order = await checkoutCart(restaurantId);
          alert("Order placed successfully!");
          location.hash = "#/orders";
        } catch (err) {
          alert(err.message);
        }
      });      

      container.replaceChildren(
        el("h2", {}, "My Cart"),
        itemsBox,
        ...(cart.items?.length ? [totals, clearButton, checkoutButton] : [])
      );
    }

    renderCart();

  } catch (err) {
    container.append(el("p", { className: "error" }, err.message));
  }
}

// Orders page ----------------------------------------------------------------

async function ordersView() {
  if (!PelmeniAuth.isLoggedIn()) {
    location.hash = "#/login";
    return;
  }

  const container = el("section");
  view.replaceChildren(
    el("h2", {}, "My Orders"),
    el("p", {}, "Loading orders...")
  );

  try {
    const data = await getCustomerOrders();
    const orders = data.orders || [];

    if (orders.length === 0) {
      container.append(
        el("h2", {}, "My Orders"),
        el("p", { className: "muted" }, "You haven't placed any orders yet.")
      );
    } else {
      container.append(el("h2", {}, "My Orders"));

      for (const order of orders) {
        const orderCard = el("div", { className: "card" });

        orderCard.append(
          el("h3", {}, `Order #${order.orderId}`),
          el("p", {}, `Status: ${order.status}`),
          el("p", {}, `Total: $${order.total.toFixed(2)}`)
        );

                const placedDate = order.created_at
          ? new Date(order.created_at).toLocaleString("en-CA", {
              month: "short",
              day: "numeric",
              year: "numeric",
              hour: "numeric",
              minute: "2-digit"
            })
          : "N/A";

        orderCard.append(
          el("p", {}, `Placed: ${placedDate}`)
        );

        container.append(orderCard);
      }
    }

    view.replaceChildren(container);

  } catch (err) {
    view.replaceChildren(
      el("h2", {}, "My Orders"),
      el("p", { className: "error" }, err.message)
    );
  }
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
async function customerApi(path, options, token = sessionStorage.getItem(customerTokenKey)) {
  const headers = new Headers(options?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  try {
    return await api(path, { ...options, headers });
  } catch (err) {
    if (err.status === 401 && sessionStorage.getItem(customerTokenKey) === token) {
      sessionStorage.removeItem(customerTokenKey);
    }
    throw err;
  }
}

function customerLoginForm(email) {
  const message = el("p", { className: "error", role: "alert" });
  const form = el("form", { className: "edit" },
    field("Email", "email", "email", email, { required: true, autocomplete: "username" }),
    field("Password", "password", "password", "", { required: true, autocomplete: "current-password" }),
    el("button", { type: "submit" }, "Sign in"),
    message,
  );
  form.addEventListener("submit", async e => {
    e.preventDefault();
    try {
      const session = await api("/auth/login", jsonRequest("POST", Object.fromEntries(new FormData(form))));
      sessionStorage.setItem(customerTokenKey, session.access_token);
      if (view.contains(form)) await route();
    } catch (err) {
      message.textContent = err.message;
    }
  });
  return form;
}

function customerRegistrationForm() {
  const message = el("p", { className: "error" });
  const form = el("form", { className: "edit" },
    field("Name", "name", "text", "", { required: true }),
    field("Email", "email", "email", "", { required: true }),
    field("Password", "password", "password", "", { required: true, minLength: 8, autocomplete: "new-password" }),
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
      if (view.contains(form)) showCustomerForms("Account created. Sign in to view your profile.", saved.email);
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
      await customerApi(`/customers/${customerId}`, jsonRequest("PATCH", { [key]: input.value }));
      if (view.contains(editor)) await route();
    } catch (err) {
      if (err.status === 401 && view.contains(editor)) {
        showCustomerForms("Your session expired. Sign in again.");
        return;
      }
      message.textContent = err.message;
    }
  });

  return el("div", { className: "account-field" },
    el("span", { className: "account-label" }, `${label}:`), display, editButton, editor,
  );
}

function showCustomerForms(message = "", email = "") {
  view.replaceChildren(
    el("h2", {}, "Customer accounts"),
    ...(message ? [el("p", { role: "status" }, message)] : []),
    el("h3", {}, "Sign in"), customerLoginForm(email),
    el("h3", {}, "Create an account"), customerRegistrationForm(),
  );
}

async function customerView() {
  const token = sessionStorage.getItem(customerTokenKey);
  if (!token) {
    showCustomerForms();
    return;
  }
  const requestedHash = location.hash;
  try {
    const { customerId } = await customerApi("/auth/me", undefined, token);
    const customer = await customerApi(`/customers/${customerId}`, undefined, token);
    if (location.hash === requestedHash && sessionStorage.getItem(customerTokenKey) === token) {
      showCustomer(customer);
    }
  } catch (err) {
    if (location.hash !== requestedHash) return;
    if (err.status !== 401) throw err;
    if (!sessionStorage.getItem(customerTokenKey)) showCustomerForms("Your session expired. Sign in again.");
  }
}

function showCustomer(customer) {
  const id = customer.customerId;
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
        await customerApi(`/customers/${id}/deactivate`, { method: "PATCH" });
        sessionStorage.removeItem(customerTokenKey);
        if (view.contains(deactivateButton)) showCustomerForms("Your account was deactivated.");
      } catch (err) {
        if (err.status === 401 && view.contains(deactivateButton)) {
          showCustomerForms("Your session expired. Sign in again.");
          return;
        }
        statusText.className = "error";
        statusText.textContent = err.message;
      }
    });
    actions.push(deactivateButton);
  }
  const logoutButton = el("button", { type: "button" }, "Log out");
  logoutButton.addEventListener("click", () => {
    sessionStorage.removeItem(customerTokenKey);
    showCustomerForms();
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

//Authentication


// Update navigation based on login status
function updateAuthNavigation() {
  const loggedIn = PelmeniAuth.isLoggedIn();
 
 
  document.getElementById("login-link").hidden = loggedIn;
  document.getElementById("account-link").hidden = !loggedIn;
  document.getElementById("logout-button").hidden = !loggedIn;
 }
 
 
 
 
 // Display the login page
 function loginView() {
  if (PelmeniAuth.isLoggedIn()) {
      location.hash = "#/account";
      return;
  }
 
 
  const container = document.createElement("section");
  container.className = "auth-card";
 
 
  const title = document.createElement("h2");
  title.textContent = "Welcome back!";
 
 
  const description = document.createElement("p");
  description.textContent = "Sign in to your Pelmeni account.";
 
 
  const form = document.createElement("form");
  form.className = "auth-form";
 
 
  // Email input
  const emailLabel = document.createElement("label");
  emailLabel.textContent = "Email";
 
 
  const emailInput = document.createElement("input");
  emailInput.type = "email";
  emailInput.name = "email";
  emailInput.required = true;
  emailInput.autocomplete = "username";
 
 
  emailLabel.appendChild(emailInput);
 
 
  // Password input
  const passwordLabel = document.createElement("label");
  passwordLabel.textContent = "Password";
 
 
  const passwordInput = document.createElement("input");
  passwordInput.type = "password";
  passwordInput.name = "password";
  passwordInput.required = true;
  passwordInput.autocomplete = "current-password";
 
 
  passwordLabel.appendChild(passwordInput);
 
 
  // Login button
  const loginButton = document.createElement("button");
  loginButton.type = "submit";
  loginButton.textContent = "Login";
 
 
  // Error message
  const message = document.createElement("p");
  message.className = "error";
  message.setAttribute("role", "alert");
 
 
  form.append(
      emailLabel,
      passwordLabel,
      loginButton,
      message
  );
 
 
  container.append(title, description, form);
 
 
  // Display the login page
  document.getElementById("view").replaceChildren(container);
 
 
  // Handle login submission
  form.addEventListener("submit", async (event) => {
      event.preventDefault();
 
 
      message.textContent = "";
      loginButton.disabled = true;
      loginButton.textContent = "Logging in...";
 
 
      try {
          await PelmeniAuth.login(
              emailInput.value,
              passwordInput.value
          );
 
 
          // Verify token by retrieving the customer
          await PelmeniAuth.getCurrentUser();
 
 
          updateAuthNavigation();
 
 
          location.hash = "#/account";
 
 
      } catch (error) {
          message.textContent = error.message;
 
 
      } finally {
          loginButton.disabled = false;
          loginButton.textContent = "Login";
      }
  });
 }
 
 
 
 
 // Display the customer's information after logging in
 async function accountView() {
  if (!PelmeniAuth.isLoggedIn()) {
      location.hash = "#/login";
      return;
  }
 
 
  const container = document.createElement("section");
  container.className = "auth-card";
 
 
  const loading = document.createElement("p");
  loading.textContent = "Loading account...";
 
 
  container.appendChild(loading);
  document.getElementById("view").replaceChildren(container);
 
 
  try {
      const customer = await PelmeniAuth.getCurrentUser();
 
 
      // Check whether the user navigated away
      if (location.hash !== "#/account") {
          return;
      }
 
 
      const title = document.createElement("h2");
      title.textContent = "My Account";
 
 
      const name = document.createElement("p");
      name.textContent = `Name: ${customer.name}`;
 
 
      const email = document.createElement("p");
      email.textContent = `Email: ${customer.email}`;
 
 
      const customerId = document.createElement("p");
      customerId.textContent = `Customer ID: ${customer.customerId}`;
 
 
      const success = document.createElement("p");
      success.className = "ok";
      success.textContent = "You are successfully authenticated!";
 
 
      const restaurantsLink = document.createElement("a");
      restaurantsLink.href = "#/";
      restaurantsLink.textContent = "Browse restaurants";

      const ordersLink = document.createElement("a");
      ordersLink.href = "#/orders";
      ordersLink.textContent = "My Orders";
      

      const accountLinks = document.createElement("div");
      accountLinks.className = "account-links";
      accountLinks.append(restaurantsLink, ordersLink);
 
 
      container.replaceChildren(
          title,
          name,
          email,
          customerId,
          success,
          accountLinks
      );
 
 
  } catch (error) {
      const message = document.createElement("p");
      message.className = "error";
      message.textContent = error.message;
 
 
      container.replaceChildren(message);
 
 
      if (!PelmeniAuth.isLoggedIn()) {
          updateAuthNavigation();
          location.hash = "#/login";
      }
  }
 }
 
 
 
 
 // Logout
 function logoutUser() {
  PelmeniAuth.logout();
 
 
  updateAuthNavigation();
 
 
  // Return to the restaurant list
  if (location.hash === "#/") {
      route();
  } else {
      location.hash = "#/";
  }
 }
 
 
 
 
 // Connect the logout button
 document.getElementById("logout-button")
  .addEventListener("click", logoutUser);
 
 
 // Set navigation visibility when the application starts
 updateAuthNavigation();
 
 
 window.addEventListener("authchange", updateAuthNavigation);
 

// Router --------------------------------------------------------------------
async function route() {
  const parts = location.hash.replace(/^#\//, "").split("/").filter(Boolean);
  try {
    if (parts.length === 0) await listView();
    else if (parts[0] === "new") await formView(null);
    else if (parts[0] === "customers") await customerView();
    else if (parts[0] === "restaurant" && parts[2] === "edit") await formView(parts[1]);
    else if (parts[0] === "restaurant") await detailView(parts[1]);
    else if (parts[0] === "login") loginView(); //login
    else if (parts[0] === "account") await accountView();
    else if (parts[0] === "cart") await cartView(parts[1]);
    else if (parts[0] === "orders") await ordersView();
    else view.replaceChildren(el("p", {}, "Page not found."));
  } catch (err) {
    showError(err);
  }
}

window.addEventListener("hashchange", route);
route();

