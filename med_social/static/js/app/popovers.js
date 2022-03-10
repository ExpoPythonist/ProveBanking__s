_inExec.register({
  name: 'popovers',
  routes: [''],
  initialize: function(){
    this.setupEvents();
  },
  update: function(){
    this.destroy();
    this.setupEvents();
  },
  destroy: function(){
    this.$popovers.popover('destroy');
    this.$popovers.off('click');
  },
  setupEvents: function(){
    $('[data-toggle="popover"]').popover();
    return;
    var that = this;
    this.$popovers = $('[data-toggle="popover"]');

    this.$popovers.not('[href]').popover({'trigger': 'manual', html: true});

    this.$popovers.filter('[href]').each(function(){
      var $this = $(this);
      $this.popover({
        trigger: 'manual',
        html: true,
        content: $($this.attr('href')).html()
      });
    });

    this.$popovers.on('click', function(ev){
      var $this = $(this);
      that.$popovers.not($this).popover('hide');
      $this.popover('toggle');
      $(document).one('click', function(){
        $this.popover('hide');
      });
      ev.stopPropagation();
      ev.preventDefault();
    });
  },
});
