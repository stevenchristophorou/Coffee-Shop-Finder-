let accessToken = localStorage.getItem("accessToken") || "";

async function register() {
  const res = await fetch("/auth/register", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      username: document.getElementById("regUsername").value,
      email: document.getElementById("regEmail").value,
      password: document.getElementById("regPassword").value,
      role: document.getElementById("regRole").value
    })
  });
  const data = await res.json();
  document.getElementById("success-message").innerText = JSON.stringify(data);
}

async function login() {
  const res = await fetch("/auth/login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      username: document.getElementById("loginUsername").value,
      password: document.getElementById("loginPassword").value
    })
  });

  const data = await res.json();
  localStorage.setItem("accessToken", data.access_token);
  accessToken = data.access_token;
  document.getElementById("loginResult").innerText = JSON.stringify(data);

  // Redirect to different pages based on role
  if (data.role === "admin") {
    window.location.href = "/admin.html";
  } else if (data.role === "manager") {
    window.location.href = "/manager.html";
  } else {
    window.location.href = "/user.html";
  }
}

async function createShop() {
  const res = await fetch("/shops", {
    method: "POST",
    headers: {
      "Content-Type":"application/json",
      "Authorization": "Bearer " + accessToken
    },
    body: JSON.stringify({
      shop_name: document.getElementById("shopName").value,
      description: document.getElementById("shopDesc").value,
      phone_num: document.getElementById("shopPhone").value,
      website: document.getElementById("shopWebsite").value
    })
  });
  const data = await res.json();
  document.getElementById("shopResult").innerText = JSON.stringify(data);
}

async function addLocation() {
  const shopId = document.getElementById("locShopId").value;
  const res = await fetch(`/shops/${shopId}/locations`, {
    method: "POST",
    headers: {
      "Content-Type":"application/json",
      "Authorization": "Bearer " + accessToken
    },
    body: JSON.stringify({
      address: document.getElementById("locAddress").value,
      city: document.getElementById("locCity").value,
      state: document.getElementById("locState").value,
      zipcode: document.getElementById("locZip").value,
    })
  });
  const data = await res.json();
  document.getElementById("locationResult").innerText = JSON.stringify(data);
}

async function addMenuItem() {
  const shopId = document.getElementById("menuShopId").value;
  const res = await fetch(`/shops/${shopId}/menu`, {
    method: "POST",
    headers: {
      "Content-Type":"application/json",
      "Authorization": "Bearer " + accessToken
    },
    body: JSON.stringify({
      item_name: document.getElementById("menuName").value,
      price: parseFloat(document.getElementById("menuPrice").value),
      description: document.getElementById("menuDesc").value,
      category: document.getElementById("menuCategory").value
    })
  });
  const data = await res.json();
  document.getElementById("menuResult").innerText = JSON.stringify(data);
}

async function addReview() {
  const shopId = document.getElementById("revShopId").value;
  const res = await fetch(`/shops/${shopId}/reviews`, {
    method: "POST",
    headers: {
      "Content-Type":"application/json",
      "Authorization": "Bearer " + accessToken
    },
    body: JSON.stringify({
      rating: parseInt(document.getElementById("revRating").value),
      review_text: document.getElementById("revText").value
    })
  });
  const data = await res.json();
  document.getElementById("reviewResult").innerText = JSON.stringify(data);
}

async function listShops() {
  const res = await fetch("/shops");
  const data = await res.json();

  const container = document.getElementById("shopsList");
  data.forEach(shop => {
    const divContainer = document.createElement("div-container");
    divContainer.className = "shop-card-container";

    const div = document.createElement("div");
    div.className = "shop-card";

    div.innerHTML = `
      <h3>${shop.shop_name}</h3>
      <p>Id: ${shop.shop_id}<br>
      Description: ${shop.description}<br>
      Phone: ${shop.phone_num}<br>
      Website: ${shop.website}<br>
      </p>

    `;

    divContainer.appendChild(div);
    container.appendChild(divContainer);
  });
}

async function deleteUser() {
  const userId = document.getElementById("delUserId").value;

  const res = await fetch(`/users/${userId}`, {
    method: "DELETE",
    headers: {
      "Authorization": "Bearer " + accessToken
    }
  });

  const data = await res.json();
  document.getElementById("deleteUserResult").innerText = JSON.stringify(data);
}

