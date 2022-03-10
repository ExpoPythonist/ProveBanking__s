_inExec.register({
  name: 'ui',
  initialize: function(){
    $.fn.spin.presets.spinner = {
      lines: 8,
      speed: 1,
      length: 10,
      width: 4,
      radius: 10,
      top: '200px',
      hwaccel: true,
      color: '#fff'
    }
    var that = this;
    this.$spinnerModal = $('#spinnerModal');
    that.$spinnerModal.modal({show: false, keyboard: false, backdrop: 'static'});
    window.addEventListener('popstate', function(event) {
      that.hideLoading();
    });
    this.spinner = new Spinner($.fn.spin.presets.spinner);
  },
  showLoading: function(){
    this.spinner.spin();
    this.$spinnerModal.find('.spinner-container').append(this.spinner.el);
    this.$spinnerModal.modal('show');
  },
  hideLoading: function(){
    this.spinner.stop();
    this.$spinnerModal.modal('hide');
  },
});
