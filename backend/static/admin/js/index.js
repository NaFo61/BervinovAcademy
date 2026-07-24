document.addEventListener("DOMContentLoaded", function() {
  const activityCanvas = document.getElementById("userActivityChart");
  const coursesCanvas = document.getElementById("popularCoursesChart");
  if (!activityCanvas || !coursesCanvas || typeof Chart === "undefined") {
    return;
  }

  const userActivity = activityCanvas.getContext("2d");
  new Chart(userActivity, {
    type: "line",
    data: {
      labels: window.months || [],
      datasets: [{
        label: "Активные пользователи",
        data: window.activity_data || [],
        borderColor: "#8b5cf6",
        backgroundColor: "rgba(139,92,246,0.3)",
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } }
    }
  });

  const popularCourses = coursesCanvas.getContext("2d");
  new Chart(popularCourses, {
    type: "bar",
    data: {
      labels: window.course_names || [],
      datasets: [{
        label: "Записей",
        data: window.course_counts || [],
        backgroundColor: "#7c3aed"
      }]
    },
    options: { plugins: { legend: { display: false } } }
  });
});
