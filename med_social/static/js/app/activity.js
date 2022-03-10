_inExec.register({
  name: 'activity',
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
    $( ".unread-event" ).each(function( index ) {
      var eventUrl = $(this).attr('data-unread-event-url');
      if (eventUrl){
        $.post(eventUrl);
      }
    });
  }
});