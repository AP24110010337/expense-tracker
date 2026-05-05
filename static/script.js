document.addEventListener("DOMContentLoaded", () => {
    initMobileMenu();
    initDashboard();
    initTransactionValidation();
    initAuthValidation();
    initDeleteConfirmation();
    initReportLinks();
});

const currencyFormatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
});

let categoryChart = null;
let trendChart = null;

function initMobileMenu() {
    const toggle = document.querySelector("[data-menu-toggle]");
    const closeButton = document.querySelector("[data-menu-close]");

    if (toggle) {
        toggle.addEventListener("click", () => {
            const isOpen = document.body.classList.toggle("menu-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });
    }

    if (closeButton) {
        closeButton.addEventListener("click", () => {
            document.body.classList.remove("menu-open");
            if (toggle) {
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    }
}

function initDashboard() {
    const monthSelect = document.getElementById("dashboardMonth");
    const categoryCanvas = document.getElementById("categoryChart");
    const trendCanvas = document.getElementById("trendChart");

    if (!monthSelect || !categoryCanvas || !trendCanvas || typeof Chart === "undefined") {
        return;
    }

    const selectedMonth = monthSelect.dataset.selectedMonth || monthSelect.value;
    loadDashboard(selectedMonth);

    monthSelect.addEventListener("change", () => {
        const month = monthSelect.value;
        const url = new URL(window.location.href);
        url.searchParams.set("month", month);
        window.history.replaceState({}, "", url);
        loadDashboard(month);
    });
}

async function loadDashboard(month) {
    try {
        const [summary, breakdown, trend] = await Promise.all([
            fetchJson(`/api/summary?month=${encodeURIComponent(month)}`),
            fetchJson(`/api/category-breakdown?month=${encodeURIComponent(month)}`),
            fetchJson("/api/monthly-trend")
        ]);

        renderSummary(summary);
        renderCategoryChart(breakdown);
        renderTrendChart(trend);
    } catch (error) {
        console.error("Dashboard failed to load", error);
    }
}

async function fetchJson(url) {
    const response = await fetch(url, {
        headers: { "Accept": "application/json" }
    });
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
}

function renderSummary(summary) {
    const income = document.getElementById("summaryIncome");
    const expense = document.getElementById("summaryExpense");
    const savings = document.getElementById("summarySavings");

    if (income) {
        income.textContent = currencyFormatter.format(summary.income || 0);
    }
    if (expense) {
        expense.textContent = currencyFormatter.format(summary.expense || 0);
    }
    if (savings) {
        const value = summary.savings || 0;
        savings.textContent = currencyFormatter.format(value);
        savings.classList.toggle("negative", value < 0);
        savings.classList.toggle("positive", value >= 0);
    }
}

function renderCategoryChart(items) {
    const canvas = document.getElementById("categoryChart");
    const empty = document.getElementById("categoryEmpty");
    if (!canvas) {
        return;
    }

    const labels = items.map((item) => item.category);
    const values = items.map((item) => Number(item.total));

    if (empty) {
        empty.hidden = values.length > 0;
    }

    if (categoryChart) {
        categoryChart.destroy();
    }

    categoryChart = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [
                {
                    data: values,
                    backgroundColor: [
                        "#7c3aed",
                        "#ef4444",
                        "#22c55e",
                        "#0ea5e9",
                        "#f97316",
                        "#14b8a6",
                        "#eab308",
                        "#64748b"
                    ],
                    borderColor: "#ffffff",
                    borderWidth: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        boxWidth: 14,
                        color: "#1e293b",
                        font: { weight: "700" }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const value = Number(context.raw || 0);
                            return `${context.label}: ${currencyFormatter.format(value)}`;
                        }
                    }
                }
            },
            cutout: "62%"
        }
    });
}

function renderTrendChart(items) {
    const canvas = document.getElementById("trendChart");
    if (!canvas) {
        return;
    }

    if (trendChart) {
        trendChart.destroy();
    }

    trendChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: items.map((item) => formatMonth(item.month)),
            datasets: [
                {
                    label: "Income",
                    data: items.map((item) => Number(item.income)),
                    backgroundColor: "#22c55e",
                    borderRadius: 6
                },
                {
                    label: "Expense",
                    data: items.map((item) => Number(item.expense)),
                    backgroundColor: "#ef4444",
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#64748b", font: { weight: "700" } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "#e2e8f0" },
                    ticks: {
                        color: "#64748b",
                        callback: (value) => currencyFormatter.format(value)
                    }
                }
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#1e293b",
                        font: { weight: "700" }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            return `${context.dataset.label}: ${currencyFormatter.format(context.raw || 0)}`;
                        }
                    }
                }
            }
        }
    });
}

function formatMonth(value) {
    const [year, month] = value.split("-").map(Number);
    return new Date(year, month - 1, 1).toLocaleDateString("en-US", {
        month: "short",
        year: "numeric"
    });
}

function initTransactionValidation() {
    const form = document.getElementById("transactionForm");
    const errorBox = document.getElementById("formError");

    if (!form || !errorBox) {
        return;
    }

    form.addEventListener("submit", (event) => {
        const type = form.querySelector("input[name='type']:checked");
        const amount = Number(form.amount.value);
        const category = form.category_id.value;
        const date = form.date.value;
        const errors = [];

        if (!type) {
            errors.push("Choose income or expense.");
        }
        if (!Number.isFinite(amount) || amount <= 0) {
            errors.push("Enter an amount greater than zero.");
        }
        if (!category) {
            errors.push("Choose a category.");
        }
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
            errors.push("Choose a valid date.");
        }

        if (errors.length > 0) {
            event.preventDefault();
            errorBox.textContent = errors.join(" ");
            errorBox.hidden = false;
        } else {
            errorBox.hidden = true;
            errorBox.textContent = "";
        }
    });
}

function initAuthValidation() {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const form = loginForm || registerForm;
    const errorBox = document.getElementById("authError");

    if (!form || !errorBox) {
        return;
    }

    form.addEventListener("submit", (event) => {
        const username = form.username.value.trim();
        const password = form.password.value;
        const errors = [];

        if (!/^[A-Za-z0-9_]{3,32}$/.test(username)) {
            errors.push("Username must be 3-32 characters using letters, numbers, or underscores.");
        }
        if (password.length < 8) {
            errors.push("Password must be at least 8 characters long.");
        }

        if (registerForm) {
            const confirmation = form.confirm_password.value;
            if (password !== confirmation) {
                errors.push("Passwords do not match.");
            }
        }

        if (errors.length > 0) {
            event.preventDefault();
            errorBox.textContent = errors.join(" ");
            errorBox.hidden = false;
        } else {
            errorBox.hidden = true;
            errorBox.textContent = "";
        }
    });
}

function initDeleteConfirmation() {
    document.querySelectorAll("[data-confirm-delete]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!window.confirm("Delete this transaction?")) {
                event.preventDefault();
            }
        });
    });
}

function initReportLinks() {
    const monthSelect = document.querySelector("[data-report-month]");
    const csvLink = document.querySelector("[data-export-csv]");
    const pdfLink = document.querySelector("[data-export-pdf]");

    if (!monthSelect || !csvLink || !pdfLink) {
        return;
    }

    const updateLinks = () => {
        const month = encodeURIComponent(monthSelect.value);
        csvLink.href = `/export/csv?month=${month}`;
        pdfLink.href = `/export/pdf?month=${month}`;
    };

    monthSelect.addEventListener("change", updateLinks);
    updateLinks();
}
