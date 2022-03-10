_inExec.register({
  name: 'tags',
  $instances: {},
  initialize: function($container){
    this.$container = $container;
    this.update();
  },
  update: function(){
    this.destroy();
    this.initializeInstances(this.$container);
    this.$container.find('input[data-type=tags]').selectize({'create': true});
  },
  destroy: function(){
  },
  destroyInstances: function() {
  },
  initializeInstances: function() {
    var that = this;
    var $inputs = this.$container.find('input[data-type=tags]').not('[disabled]');

    for (var i=0; i<$inputs.length; i++) {
      var $input = $($inputs[i]);
      var base_url = $input.attr('selectize-url');
      var url_parts = base_url.split('?');
      var path = url_parts[0];
      var params = url_parts[1];

      config = {
        valueField: 'pk',
        labelField: 'name',
        searchField: 'name',
        create: true,
        plugins: ['remove_button'],

      }

      var maxItems = $input.attr('selectize-maxItems');
      if (maxItems !== undefined) {
        this.config.maxItems = maxItems;
      }
      //var [path, params] = base_url.split('?');
      // causes uglify to panick
      if (params === undefined) {
        params = {};
      } else {
        params = $.deparam(params);
      }
      var getQueryURL = function(query){
        params.q = query;
        return path + '?' + $.param(params);
      };

      config.load = function(query, callback){
        $.ajax({
            url: getQueryURL(query),
            type: 'GET',
            dataType: 'json',
            success: function(res) {
              callback(res);
            },
            error: function(data,err) {
              callback();
            },
        });
      };

      var $input = $($inputs[i]);
      var formId = $input.parents('form').attr('id');
      var instanceName = formId + '_' + $input.attr('id');
      that.$instances[instanceName] = $input.selectize(config);
    }
  },
  setupInstance: function($input){
    var createURL = $input.attr('selectize-create-url');
    var config = {
      valueField: 'pk',
      labelField: 'text',
      searchField: 'text',
    }
  },
});
