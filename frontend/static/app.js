const token = localStorage.getItem("crowd_api_token") || "";
const headers = {"Content-Type": "application/json", ...(token ? {"Authorization": `Bearer ${token}`} : {})};
let chart;
const $ = id => document.getElementById(id);
async function api(path, options = {}) {
  const requestHeaders = {...headers, ...(options.headers || {})};
  if (options.body instanceof FormData) delete requestHeaders["Content-Type"];
  const response = await fetch(path, {...options, headers: requestHeaders});
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : {detail: await response.text()};
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}
async function refresh() {
  try {
    const data = await api("/api/dashboard");
    $("occupancy").textContent = data.current_occupancy;
    $("entries").textContent = data.daily_entries;
    $("exits").textContent = data.daily_exits;
    $("last-updated").textContent = `Updated ${new Date().toLocaleTimeString()}`;
    const labels = data.history.map(x => `${x.date} ${String(x.hour).padStart(2,"0")}:00`);
    const values = data.history.map(x => x.people_present);
    if (chart) chart.destroy();
    chart = new Chart($("history-chart"), {type:"line", data:{labels, datasets:[{label:"People present",data:values,borderColor:"#57d6b1",backgroundColor:"#57d6b133",fill:true,tension:.35}]}, options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,grid:{color:"#223451"}},x:{grid:{color:"#223451"}}},plugins:{legend:{labels:{color:"#eaf2ff"}}}}});
  } catch (error) { $("last-updated").textContent = error.message; }
}
function isoToday() { return new Date().toISOString().slice(0,10); }
$("prediction-date").value = isoToday(); $("manual-date").value = isoToday();
$("prediction-form").addEventListener("submit", async e => { e.preventDefault(); const result = $("prediction-result"); result.hidden = false; result.textContent = "Loading...";
  try { const data = await api("/api/predict",{method:"POST",body:JSON.stringify({prediction_date:$("prediction-date").value,hour:+$("prediction-hour").value,is_exam_period:+$("exam").value,is_holiday:+$("holiday").value,days_to_exam:+$("days").value,is_semester_break:0,library_capacity:600})}); result.textContent = `${data.predicted_crowd} people predicted`; } catch (error) { result.textContent = error.message; }
});
$("manual-form").addEventListener("submit", async e => { e.preventDefault(); try { await api("/api/history/manual",{method:"POST",body:JSON.stringify({observation_date:$("manual-date").value,hour:+$("manual-hour").value,people_present:+$("people").value,entries:+$("manual-entries").value,exits:+$("manual-exits").value})}); $("manual-message").textContent="Record saved."; refresh(); } catch(error) { $("manual-message").textContent=error.message; }});
$("import-form").addEventListener("submit", async e => { e.preventDefault(); const form = new FormData(); form.append("file",$("csv").files[0]); try { const data = await api("/api/history/import",{method:"POST",body:form,headers:token?{"Authorization":`Bearer ${token}`}:{}}); $("import-message").textContent=`Imported ${data.imported} rows.`; refresh(); } catch(error) { $("import-message").textContent=error.message; }});
refresh(); setInterval(refresh, 5000);
