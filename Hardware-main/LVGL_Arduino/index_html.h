#ifndef INDEX_HTML_H
#define INDEX_HTML_H

const char* index_html = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Icare Health Monitor</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="stylesheet" href="style.css">
  <style>
    body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; }
    @import url("https://fonts.googleapis.com/css2?family=Poppins:wght@200;300;400;500;600;700;800;900&display=swap");
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Poppins', sans-serif;
    }
    h1, h2 {
      font-family: sans-serif;
      font-weight: 400;
    }
    a {
      text-decoration: none;
    }
    li {
      list-style: none;
    }
    .flex {
      display: flex;
    }
    .flex_space {
      display: flex;
      justify-content: space-between;
    }
    button {
      border: none;
      border-radius: 30px;
      background: none;
      outline: none;
      transition: 0.5s;
      cursor: pointer;
    }
    .primary-btn {
      padding: 15px 40px;
      background: #7fc142;
      font-weight: bold;
      color: white;
    }
    .secondary-btn {
      padding: 15px 40px;
      background: none;
      border: 2px solid white;
      font-weight: bold;
      color: white;
    }
    .container {
      max-width: 85%;
      margin: auto;
    }
    /* Header Section */
    header {
      height: 10vh;
      line-height: 10vh;
      padding: 0 20px;
      margin-bottom: auto;
    }
    header img {
      margin: 20px 0;
    }
    header ul {
      display: inline-block;
    }
    header ul li {
      display: inline-block;
      text-transform: uppercase;
    }
    header ul li a {
      color: #000;
      margin: 0 10px;
      transition: 0.5s;
    }
    header ul li a:hover {
      color: #7fc142;
    }
    header i {
      margin: 0 20px;
    }
    header button {
      padding: 13px 40px;
    }
    header .navlinks span {
      display: none;
    }
    header .navlinks ul li .link {
      text-decoration: none;
      font-weight: 500;
      color: #000;
      padding-bottom: 15px;
      margin: 0 25px;
    }
    .link:hover, .active {
      border-bottom: 2px solid #fff;
    }
    #registerBtn {
      margin-left: 15px;
    }
    .btn.white-btn {
      background: rgba(255, 255, 255, 0.7);
    }
    /* Media Queries for Responsiveness */
    @media only screen and (max-width: 768px) {
      header ul {
        position: absolute;
        top: 100px;
        left: 0;
        width: 100%;
        height: 100vh;
        background: #009f7f;
        overflow: hidden;
        transition: max-height 0.5s;
        text-align: center;
        z-index: 9;
      }
      header ul li {
        display: block;
      }
      header ul li a {
        color: white;
      }
      header i {
        color: white;
      }
      header .navlinks span {
        color: black;
        display: block;
        cursor: pointer;
        line-height: 10vh;
        font-size: 20px;
      }
    }
    .container { max-width: 1200px; margin: auto; padding: 20px; }
    .card {
      background: linear-gradient(135deg, #42a5f5, #478ed1);
      color: white;
      border-radius: 10px;
      padding: 20px;
      margin: 15px;
      box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
      transition: transform 0.3s ease;
      cursor: pointer; 
    }
    .card:hover { transform: scale(1.05); }
    .modal {
      display: none;
      position: fixed;
      z-index: 1;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      overflow: auto;
      background-color: rgba(0,0,0,0.7);
      padding-top: 60px;
    }
    .modal-content {
      background: white;
      margin: 5% auto;
      padding: 20px;
      border: 1px solid #888;
      width: 80%;
      max-width: 1000px;
      border-radius: 10px;
    }
    .close { 
      color: #aaa;
      float: right;
      font-size: 28px;
      font-weight: bold;
    }
    .close:hover, .close:focus { color: black; text-decoration: none; cursor: pointer; }
    /* ECG Section */
    .ecg-container {
      margin-top: 50px;
      padding: 20px;
      background: white;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
      border-radius: 10px;
    }
    canvas { width: 100%; max-height: 400px; }
    /* Footer Section */
    footer {
      background: linear-gradient(to bottom, #2c3e50, #34495e);
      color: #ecf0f1;
      padding: 40px 0;
      margin-top: auto;
    }
    footer .container {
      display: flex;
      justify-content: space-between;
      gap: 40px;
      max-width: 1200px;
      margin: 0 auto;
    }
    footer .box { width: 30%; }
    footer .box h2 { margin-bottom: 20px; font-size: 22px; }
    footer .box ul { list-style-type: none; }
    footer .box ul li { margin-bottom: 10px; font-size: 16px; }
    footer .box .icon { display: flex; gap: 10px; margin-top: 15px; }
    footer .box .icon i { color: #ecf0f1; font-size: 20px; transition: 0.3s; }
    footer .box .icon i:hover { color: #3498db; }
    footer .box p { margin-bottom: 15px; }
    footer .box i { margin-right: 10px; }
    footer .box label { display: block; }
    /* Legal Section */
    .legal {
      background-color: #34495e;
      color: #ecf0f1;
      text-align: center;
      padding: 10px;
      margin-top: 50px;
      font-size: 14px;
    }
  </style>
</head>
<body>

<header>
  <div class="content flex_space">
    <div class="logo">
      <img src="images/icare_logo.png" height="80" alt="Icare Logo">
    </div>
    <h2>Icare Health Monitoring</h2>
    <div class="navlinks">
      <ul id="menulist">
        <li><a href="dashboard.html" class="link active">Home</a></li>
        <li><a href="#">Reports</a></li>
        <li><a href="#">Monitoring</a></li>
        <li><a href="#">Contact</a></li>
        <li><button class="primary-btn" id="loginbtn" onclick="login()">LOGIN</button></li>
        <li><button class="btn white-btn" id="registerBtn" onclick="register()">REGISTER</button></li>
      </ul>
    </div>
  </div>
</header>

<div class="container">
  <h1>Icare Health Monitor</h1>

  <!-- Clickable Cards -->
  <div class="card" onclick="openModal('stepCount')">
    <span class="data-title">Step Count:</span>
    <span class="data-value" id="stepCount">0</span>
  </div>

  <div class="card" onclick="openModal('bpm')">
    <span class="data-title">BPM:</span>
    <span class="data-value" id="bpm">0</span>
  </div>

  <div class="card" onclick="openModal('temperature')">
    <span class="data-title">Temperature:</span>
    <span class="data-value" id="temperature">0</span> °C
  </div>

  <div class="card" onclick="openModal('spo2')">
    <span class="data-title">SpO2:</span>
    <span class="data-value" id="spo2">0</span>%
  </div>

  <div class="card" onclick="openModal('fall')">
    <span class="data-title">Fall Detection:</span>
    <span class="data-value" id="fall">No</span>
  </div>
</div>

<!-- Modal Container -->
<div id="modal" class="modal">
  <div class="modal-content">
    <span class="close" onclick="closeModal()">&times;</span>
    <h2 id="modal-title"></h2>
    <canvas id="chartCanvas"></canvas>
  </div>
</div>

<!-- ECG Section -->
<div class="ecg-container">
  <h2>ECG Signal</h2>
  <canvas id="ecgChart"></canvas>
</div>

<script>
  // Variables to hold chart data for modal charts
  const chartData = {
      stepCount: { labels: [], data: [] },
      bpm: { labels: [], data: [] },
      temperature: { labels: [], data: [] },
      spo2: { labels: [], data: [] },
      fall: { labels: [], data: [] }
  };

  let currentChart = null;

  // ECG Chart Initialization using Chart.js
  const ecgCtx = document.getElementById('ecgChart').getContext('2d');
  const ecgChart = new Chart(ecgCtx, {
      type: 'line',
      data: {
          labels: [],
          datasets: [{
              label: 'ECG Signal',
              data: [],
              borderColor: 'red',
              borderWidth: 2,
              fill: false
          }]
      },
      options: {
          responsive: true,
          animation: false,
          scales: {
              x: { display: true },
              y: { display: true, min: -2, max: 2 }
          }
      }
  });

  // Modal Chart Functions
  function openModal(type) {
      document.getElementById('modal').style.display = 'block';
      document.getElementById('modal-title').innerText = type.toUpperCase();

      if (currentChart) currentChart.destroy();

      const ctx = document.getElementById('chartCanvas').getContext('2d');
      currentChart = new Chart(ctx, {
          type: 'line',
          data: {
              labels: chartData[type].labels,
              datasets: [{
                  label: type,
                  data: chartData[type].data,
                  borderColor: 'blue',
                  backgroundColor: 'rgba(0, 123, 255, 0.5)',
                  borderWidth: 2,
                  fill: true
              }]
          },
          options: { responsive: true, scales: { x: { display: true }, y: { display: true } } }
      });
  }

  function closeModal() {
      document.getElementById('modal').style.display = 'none';
      if (currentChart) currentChart.destroy();
  }

  // Update data from the ESP32 every 2 seconds
  function updateData() {
      fetch('/data')
          .then(response => response.json())
          .then(data => {
              // Update card values using JSON keys returned from ESP32
              document.getElementById('stepCount').textContent = data.stepCount;
              document.getElementById('bpm').textContent = data.hr; // hr key for heart rate
              document.getElementById('temperature').textContent = data.temperature;
              document.getElementById('spo2').textContent = data.spo2;
              document.getElementById('fall').textContent = data.fall ? "Yes" : "No";

              // (Optional) Update modal chart data if needed...
              
              // Update ECG Chart (simulate data for demonstration)
              const ecgValue = Math.sin(Date.now() / 1000) + (Math.random() - 0.5) * 0.1;
              ecgChart.data.labels.push(new Date().toLocaleTimeString());
              ecgChart.data.datasets[0].data.push(ecgValue);
              if (ecgChart.data.labels.length > 50) {
                  ecgChart.data.labels.shift();
                  ecgChart.data.datasets[0].data.shift();
              }
              ecgChart.update();
          })
          .catch(err => console.error("Error fetching data:", err));
  }
  setInterval(updateData, 2000);
</script>
</body>
</html>
)rawliteral";

#endif // INDEX_HTML_H