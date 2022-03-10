
_inExec.extendClass({
  name: 'lineChart',
  initialize: function(options) {
    var that = this;
    this.options = options;
    this.ctx = document.getElementById(options.canvasId).getContext("2d");
    this.data = options.data || [];
    this.chart = new Chart(this.ctx).Line(this.data, this.options.chartOptions);
    legend(document.getElementById(options.legend), this.data);
  },
});


_inExec.register({
  name: 'insight',
  routes: ['^/a/$'],
  initialize: function($container){
    $container = $container || $('body');
    Chart.defaults.global.responsive = true;
    this.update();
  },
  update: function($container){
    this.$charts = $("canvas.insight-chart");
    $('#FilterChartForm').on('change', $.proxy(this.updateChart, this));
    $('#FilterChartForm').trigger('change');
  },
  updateChart: function(){
    var that = this;
    this.$charts.each(function (i, value) {
      var $chart = $(that.$charts[i]);
      var chartId = $chart.attr('id');
      var url = $chart.attr('url');
      $.ajax({
        type: 'GET',
        url: url,
        data: $('#FilterChartForm').serialize(),
        success: function(response){
          $('#' + chartId).replaceWith('<canvas id="' + chartId + '" width="400" height="400" class="insight-chart" url="' + url + '"></canvas>')
          chartdata = {
          labels: ["January", "February", "March", "April", "May", "June", 
                   "July","August","September","October","November","December"],
          datasets: response['data'] 
          };
          new _inExec.classes.lineChart({
            canvasId: chartId,
            data: chartdata,
            legend: chartId + 'Legend',
            chartOptions: {
              pointHitDetectionRadius : 10,
              datasetFill : false,
              datasetStrokeWidth : 1,
              responsive: true,
            }
          });
        }
      })
    })
  },
  destroy: function($container){
    $('#FilterChartForm').off('change', this.updateChart);
  },
});

