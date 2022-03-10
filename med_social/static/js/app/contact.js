_inExec.register({
  name: 'contactSpecificUser',
  routes: ['^/projects/users/invite/\\d+/'],
  initialize: function($container){
    var $container = $container || $('body');
    this.update($container);
  },
  update: function($container){
    this.destroy($container);
    $container.find('#div_id_users').hide();
  },
  destroy: function($container){
  }
});

_inExec.register({
  name: 'contactUser',
  routes: ['^/projects/users/invite/'],
  initialize: function($container){
    this.$container = $container || $('body');
    this.update($container);
  },
  update: function($container){
    this.destroy($container);
    var selectizeName = 'invite-to-project-form_id_request';
    this.$request = _inExec.modules.autocomplete.$instances[selectizeName].$selectize;
    this.$request.on('change', $.proxy(this.requestChanged, this));
    this.$request.trigger('change', this.$request.getValue());
  },
  destroy: function($container){
  },
  requestChanged: function(newValue){
    if (newValue.trim() === "") {
      this.$container.find('#div_id_status').hide();
    } else {
      this.$container.find('#div_id_status').show();
    }
  }
});
