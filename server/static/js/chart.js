
// color line bar for distinct different level of engagement
const plugin = {
  id: 'custom_canvas_background_color',
  beforeDraw: (chart) => {
    const {ctx, chartArea: {left, top, right, bottom}, scales: {x, y}} = chart;
    ctx.save();
    let height_inc = (bottom -10) / 4;
    ctx.fillStyle = 'rgba(122,175,95,0.5)'; //dark green
    ctx.fillRect(left, top, right,height_inc);
    ctx.fillStyle = 'rgba(161,216,132,0.5)'; //light green
    ctx.fillRect(left, top+height_inc, right, height_inc);
    ctx.fillStyle = 'rgba(243,221,109,0.5)'; //yellow
    ctx.fillRect(left, bottom-(height_inc*2), right, height_inc);
    ctx.fillStyle = 'rgba(241,128,112,0.5)'; //red
    ctx.fillRect(left, bottom-height_inc, right, height_inc);
    ctx.restore();
  }
};

const eng_labels = {
  beforeDraw: (chart) => {
    const {ctx, chartArea: {left, top, right, bottom}, scales: {x, y}} = chart;
    ctx.save();
    let height_inc = (bottom -10) / 4;
    let l_padd = 10;
    let t_padd = 20;
    ctx.textAlign = "left"
    ctx.fillStyle = "#696969";
    ctx.fillText('Highly Engaged',left+l_padd,top+t_padd)
    ctx.fillText('Engaged',left+l_padd,top+height_inc+t_padd)
    ctx.fillText('Slightly Engaged',left+l_padd,bottom-(height_inc*2)+t_padd)
    ctx.fillText('Not Engaged',left+l_padd,bottom-height_inc+t_padd)
    ctx.restore();
  }
};

/* globals Chart:false, feather:false */
function createChart(){
  'use strict'

  feather.replace();

  // Graphs
  var ctx = document.getElementById('myChart');
  // eslint-disable-next-line no-unused-vars
  var myChart = new Chart(ctx, {
    type:'line',
    data: {
      labels: [],
      datasets: [{
        label: 'engagement level',
        data: [],
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 2,
        pointBackgroundColor: '#007bff',
        borderDash: [2, 2],
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          display: true,
          title: {
            display: true,
            text: 'engagement level'
          },
          min:0,
          max:1,
          ticks: {
            stepSize:0.25,
            format:{ maximumSignificantDigits: 3 },
          }
        }
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
    plugins: [plugin, eng_labels],
  });

  return myChart;
}

function addData(chart, label, data) {
  chart.data.labels.push(label);
  chart.data.datasets.forEach((dataset) => {
      dataset.data.push(data);
  });
  chart.update();
}
function flushData(chart) {
  chart.data.labels = [];
  chart.data.datasets.forEach((dataset) => {
    dataset.data = [];
});
  chart.update();
}
function shiftData(chart) {
  chart.data.labels.shift();
  chart.data.datasets.forEach((dataset) => {
      dataset.data.shift();
  });
  chart.update();
}
