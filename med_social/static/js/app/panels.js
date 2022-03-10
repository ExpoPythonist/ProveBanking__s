_inExec.register({
  name: 'panels',
  routes: [''],
  initialize: function(){
    this.update();
  },
  update: function(){
    this.destroy();
    this.setupEvents();
  },
  destroy: function(){
  },
  setupEvents: function(){
    var that = this;
  },
});
