const form = document.getElementById("expense-form");
const dateInput = document.getElementById("date");
const categoryInput = document.getElementById("category");
const descriptionInput = document.getElementById("description");
const amountInput = document.getElementById("amount");
const formError = document.getElementById("form-error");

const filterCategory = document.getElementById("filter-category");
const filterMonth = document.getElementById("filter-month");

const totalAmountEl = document.getElementById("total-amount");
const breakdownEl = document.getElementById("category-breakdown");
const expensesBody = document.getElementById("expenses-body");
const emptyState = document.getElementById("empty-state");

const currency = (n) =>
  new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(n);

function buildQuery() {
  const params = new URLSearchParams();
  if (filterCategory.value) params.set("category", filterCategory.value);
  if (filterMonth.value) params.set("month", filterMonth.value);
  return params.toString();
}

async function loadExpenses() {
  const query = buildQuery();
  const res = await fetch(`/api/expenses${query ? `?${query}` : ""}`);
  const data = await res.json();
  renderSummary(data);
  renderTable(data.expenses);
}

function renderSummary(data) {
  totalAmountEl.textContent = currency(data.total);
  breakdownEl.innerHTML = "";
  const entries = Object.entries(data.by_category).sort((a, b) => b[1] - a[1]);
  for (const [category, amount] of entries) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = `${category}: ${currency(amount)}`;
    breakdownEl.appendChild(chip);
  }
}

function renderTable(expenses) {
  expensesBody.innerHTML = "";
  emptyState.hidden = expenses.length > 0;

  for (const e of expenses) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td data-label="Date">${e.date}</td>
      <td data-label="Category">${e.category}</td>
      <td data-label="Description">${e.description || ""}</td>
      <td data-label="Amount">${currency(e.amount)}</td>
      <td></td>
    `;

    const deleteCell = tr.lastElementChild;
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-btn";
    deleteBtn.textContent = "Delete";
    deleteBtn.addEventListener("click", () => deleteExpense(e.id));
    deleteCell.appendChild(deleteBtn);

    expensesBody.appendChild(tr);
  }
}

async function deleteExpense(id) {
  await fetch(`/api/expenses/${id}`, { method: "DELETE" });
  loadExpenses();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.textContent = "";

  const payload = {
    date: dateInput.value,
    category: categoryInput.value,
    description: descriptionInput.value,
    amount: amountInput.value,
  };

  const res = await fetch("/api/expenses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    formError.textContent = err.error || "Something went wrong.";
    return;
  }

  form.reset();
  loadExpenses();
});

filterCategory.addEventListener("change", loadExpenses);
filterMonth.addEventListener("change", loadExpenses);

loadExpenses();
