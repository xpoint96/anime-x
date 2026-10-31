const sheet = document.getElementById("sheet");
const menuBtn = document.getElementById("menu-btn");
const themeBtn = document.getElementById("theme");
const filters = document.getElementById("filters");
const overlay = document.getElementById("login-overlay");
const authOpen = document.getElementById("auth-open");
const authClose = document.getElementById("login-close");

menuBtn.addEventListener("click", () => {
  sheet.hidden = !sheet.hidden;
});

themeBtn.addEventListener("click", () => {
  document.body.classList.toggle("light");
});

if (filters) {
  filters.querySelectorAll("input[type=radio]").forEach((input) => {
    input.addEventListener("change", () => filters.submit());
  });
}

function openAuth(pane = "login") {
  if (!overlay) return;
  overlay.hidden = false;
  document.body.classList.add("auth-open");
  setAuthPane(pane);
}

function closeAuth() {
  if (!overlay) return;
  overlay.hidden = true;
  document.body.classList.remove("auth-open");
}

function setAuthPane(pane) {
  document.querySelectorAll(".login-tab").forEach((tab) => {
    tab.classList.toggle("is-on", tab.dataset.pane === pane);
  });
  document.querySelectorAll(".login-pane").forEach((box) => {
    const on = box.dataset.pane === pane;
    box.classList.toggle("is-on", on);
    box.hidden = !on;
  });
}

if (authOpen) {
  authOpen.addEventListener("click", () => openAuth("login"));
}
if (authClose) {
  authClose.addEventListener("click", closeAuth);
}
if (overlay) {
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) closeAuth();
  });
  document.querySelectorAll(".login-tab").forEach((tab) => {
    tab.addEventListener("click", () => setAuthPane(tab.dataset.pane));
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAuth();
  });
}

document.querySelectorAll(".card").forEach((card) => {
  card.addEventListener("mousemove", (event) => {
    const box = card.querySelector(".poster");
    if (!box) return;
    const rect = box.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;
    box.style.transform = `perspective(600px) rotateX(${(-y * 10).toFixed(1)}deg) rotateY(${(x * 12).toFixed(1)}deg)`;
  });
  card.addEventListener("mouseleave", () => {
    const box = card.querySelector(".poster");
    if (box) box.style.transform = "";
  });
});
