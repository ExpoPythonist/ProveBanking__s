_inExec.register({
  name: 'tooltips',
  //routes: [''],
  initialize: function($container){
    this.$container = $container || $('body');
    this.update($container);
  },
  update: function(){
    this.destroy();
    this.setupEvents();
  },
  destroy: function(container){
    $tooltips = this.$container.find('[data-toggle="tooltip"]');
    $tooltips.tooltip('hide');
    $tooltips.tooltip('destroy');
    $tooltips.off('click');
  },
  setupEvents: function(){
    var that = this;
    $tooltips = this.$container.find('[data-toggle="tooltip"][data-trigger!="click"]');
    $clickTooltips = this.$container.find('[data-toggle="tooltip"][data-trigger="click"]');
    $tooltips.tooltip({html: true});
    $clickTooltips.tooltip({trigger: 'manual', html: true});
    $clickTooltips.on('click', function(ev){
      var $this = $(this);
      $clickTooltips.not($this).tooltip('hide');
      $this.tooltip('toggle');
      $(document).one('click', function(){
        $this.tooltip('hide');
      });
      ev.stopPropagation();
      ev.preventDefault();
    });
  },
});
