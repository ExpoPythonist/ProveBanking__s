_inExec.register({
  name: 'profile',
  routes: ['/users/[\\w.-]+/$'],
  initialize: function($container){
    this.update();
  },
  update: function(){
  },
  destroy: function(){
  }
});
