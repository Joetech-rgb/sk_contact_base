content = open('templates/contacts/sk_dashboard.html', encoding='utf-8').read()

old = '    </div>\n\n    <!-- CONTACTS'
new = (
    '    </div>\n'
    '\n'
    '      <!-- LINE CHART: 30-day registrations -->\n'
    '      <div class="sh"><div class="sh-title">30-Day Registration Trend</div><div class="sh-tag"><i class="fas fa-chart-line"></i> Daily signups</div><div class="sh-line"></div></div>\n'
    '      <div class="card" style="padding:20px;">\n'
    '        <canvas id="regChart" height="80"></canvas>\n'
    '      </div>\n'
    '\n'
    '    </div>\n\n    <!-- CONTACTS'
)
content = content.replace(old, new, 1)

# Add Chart.js script before closing </script>
old2 = "setTab('analytics');\nanimateBars();"
new2 = (
    "// Chart.js line chart\n"
    "(function(){\n"
    "  const labels = {{ chart_labels_json|safe }};\n"
    "  const values = {{ chart_values_json|safe }};\n"
    "  const ctx = document.getElementById('regChart');\n"
    "  if(!ctx) return;\n"
    "  new Chart(ctx, {\n"
    "    type: 'line',\n"
    "    data: {\n"
    "      labels: labels,\n"
    "      datasets: [{\n"
    "        label: 'Registrations',\n"
    "        data: values,\n"
    "        borderColor: '#1E6FD9',\n"
    "        backgroundColor: 'rgba(30,111,217,0.08)',\n"
    "        borderWidth: 2,\n"
    "        pointBackgroundColor: '#1E6FD9',\n"
    "        pointRadius: 3,\n"
    "        fill: true,\n"
    "        tension: 0.4\n"
    "      }]\n"
    "    },\n"
    "    options: {\n"
    "      responsive: true,\n"
    "      plugins: { legend: { display: false } },\n"
    "      scales: {\n"
    "        y: { beginAtZero: true, ticks: { stepSize: 1 } },\n"
    "        x: { ticks: { maxTicksLimit: 10 } }\n"
    "      }\n"
    "    }\n"
    "  });\n"
    "})();\n"
    "setTab('analytics');\nanimateBars();"
)
content = content.replace(old2, new2, 1)

# Add Chart.js CDN in <head> before </style>
old3 = '</style>\n</head>'
new3 = '</style>\n<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>\n</head>'
content = content.replace(old3, new3, 1)

open('templates/contacts/sk_dashboard.html', 'w', encoding='utf-8').write(content)
print('template patched OK')
