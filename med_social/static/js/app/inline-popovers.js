_inExec.register({
  name: 'inlinePopovers',
  routes: [''],
  initialize: function(){
    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
  },
  setup: function(){
    var that = this;
    this.$popovers = $('[data-toggle="inline-popover"]');

    this.$popovers.filter('[href]').on('click', function(e){
      e.preventDefault();
      e.stopPropagation();

      var $this = $(this);
      that.$popovers.not($this).filter('[href=' + $this.attr('href') + '].open').removeClass('open');
      var $popover = $($this.attr('href'));
      var $contents = $($this.attr('data-contents'));
      $popover.find('.popover-content').html($contents.html());
      if ($this.hasClass('open')) {
        $popover.addClass('hide');
        $this.removeClass('open');
      } else {
        $popover.removeClass('hide');
        $this.addClass('open');
      }
    });
  }
});
