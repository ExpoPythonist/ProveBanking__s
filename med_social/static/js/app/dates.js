_inExec.register({
  name: 'datepicker',
  $instances: {},
  initialize: function($container){
    this.$container = $container;
    this.$body = $('body');
  },

  resetInstances: function($container){
    var $container = $container || this.$container;
    this.destroyInstances($container);
    this.initializeInstances($container);
  },

  destroyInstances: function($container){
    var that = this;
    var $container = $container || this.$container;
    _.each(this.$instances, function(instance, name){
      // Do no destroy in case the item is still on the page but not inside
      // currently initializing container
      var is_on_page = that.$body.find(instance.$node).length !== 0;
      var is_in_container = $container.find(instance.$node).length !== 0;
      if ((is_on_page === true) && (is_in_container == false)) {
      } else {
        instance.stop();
        delete that.$instances[name];
      }
    });
  },
  initializeInstances: function($container){
    var that = this;
    var $container = $container || this.$container;
    $container.find('input[data-widget=datepicker]:not(.selectized)').pickadate({
      monthsShort: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      weekdaysShort: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      format: 'd mmmm, yyyy',
      selectYears: 30,
      selectMonths: true,
      theme: 'classic',
      container: 'body',
    });
    $container.find('input[data-widget=datepicker]:not(.selectized)').each(function(i, input){
      var $input = $(input);
      var formId = $input.parents('form').attr('id');
      var instanceName = formId + '_' + $input.attr('id');
      that.$instances[instanceName] = $input.pickadate('picker');
    });
  },
});
