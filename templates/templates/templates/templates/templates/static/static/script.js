document.addEventListener("DOMContentLoaded", () => {
  // Reveal elements with a small stagger, while keeping reduced-motion users in mind.
  document.querySelectorAll(".reveal").forEach((el, index) => {
    el.style.animationDelay = `${Math.min(index * 45, 360)}ms`;
  });

  // Count-up numbers for dashboard stats.
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll(".count-up").forEach((el) => {
    const target = Number(el.dataset.count || 0);
    if (!Number.isFinite(target)) return;
    if (reduceMotion) {
      el.textContent = Number.isInteger(target) ? String(target) : target.toFixed(1);
      return;
    }
    const decimals = String(target).includes(".") ? 1 : 0;
    const duration = 750;
    const start = performance.now();
    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = target * eased;
      el.textContent = decimals ? value.toFixed(1) : Math.round(value).toLocaleString("en-IN");
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });

  // Friendly local date label.
  const dateLabel = document.getElementById("todayLabel");
  if (dateLabel) {
    dateLabel.textContent = new Intl.DateTimeFormat("en", {
      weekday: "short", month: "short", day: "numeric"
    }).format(new Date()).toUpperCase();
  }

  // Dismiss flash messages.
  document.querySelectorAll(".flash-close").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash")?.remove());
  });

  // Workout category filters.
  const filterButtons = document.querySelectorAll("[data-filter]");
  const workoutCards = document.querySelectorAll(".workout-card[data-category]");
  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      filterButtons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      const filter = button.dataset.filter;
      workoutCards.forEach((card) => {
        const show = filter === "all" || card.dataset.category === filter;
        card.hidden = !show;
      });
    });
  });

  // Activity chart is only present on the dashboard.
  const canvas = document.getElementById("activityChart");
  if (canvas && window.fitverseChart && window.Chart) {
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 0, 220);
    gradient.addColorStop(0, "rgba(196,255,77,0.28)");
    gradient.addColorStop(1, "rgba(196,255,77,0.01)");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: window.fitverseChart.labels,
        datasets: [{
          label: "Completed workouts",
          data: window.fitverseChart.values,
          borderColor: "#c4ff4d",
          backgroundColor: gradient,
          borderWidth: 2,
          fill: true,
          tension: 0.38,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: "#c4ff4d",
          pointBorderColor: "#111511",
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#171d16",
            borderColor: "#35432b",
            borderWidth: 1,
            titleColor: "#f1f4ee",
            bodyColor: "#c4ff4d",
            displayColors: false,
            padding: 11
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: "#778272", font: { size: 10 } }, border: { display: false } },
          y: { beginAtZero: true, suggestedMax: 3, ticks: { color: "#778272", precision: 0, stepSize: 1, font: { size: 10 } }, grid: { color: "rgba(130,145,122,0.12)" }, border: { display: false } }
        }
      }
    });
  }
});
