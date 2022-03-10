_inExec.register({
  name: 'buttons',
  initialize: function(){
    this.$container = $('body');
    this.setUp();
  },
  destroy: function(){
  },
  setUp: function(){
    this.$container.on('click', '.btn-remove-item', function(){
      var $this = $(this);
      var $target = $($this.attr('data-target'));
      $target.remove();
    });

    this.$container.on('mouseover', 'button[data-hover], a[data-hover]',
      function(){
        var $this = $(this);
        $this.find('.text').text($this.attr('data-hover-text'));
        $this.find('.fa').attr('class', ($this.attr('data-hover-icon')));
      });

    this.$container.on('mouseout', 'button[data-hover], a[data-hover]',
      function(){
        var $this = $(this);
        $this.find('.text').text($this.attr('data-text'));
        $this.find('.fa').attr('class', ($this.attr('data-icon')));
      });
  }
});
