var setupAutocomplete = function($input){
  var that = this;
  this.$input = $input;
  this.$body = $('body');
  this.$controls = $input.parents('.controls');
  this.isSingleSelect = $input.attr('multiple') === undefined;
  this.itemKind = $input.attr('data-kind');
  this.createURL = $input.attr('selectize-create-url');
  this.lockOptgroupOrder = $input.attr('selectize-lockoptgrouporder') === 'yes';
  this.canCreate = $input.attr('selectize-create') !== undefined;
  this.$label = $('label[for=' + this.$input.attr('id') + ']');
  try{
    this.sortField = JSON.parse($input.attr('data-selectize-sortkey'));
  }catch(e){
    this.sortField = '$order';
  }
  this.config = {

    openOnFocus: this.$input.attr('data-open-on-focus') === 'false' ? false : true,
    valueField: 'pk',
    labelField: 'text',
    searchField: 'text',
    create: this.canCreate,
    sortField: that.sortField,
    lockOptgroupOrder: that.lockOptgroupOrder,
    placeholder: this.$input.attr('selectize-placeholder'),
    plugins: ['remove_button'],
    allowEmptyOption: this.$input.attr('selectize-allow-empty-option') === 'yes',
    onInitialize: function() {
      this.$wrapper.addClass('text-left');
      window.scrollTo(0, 0);
    },
    onItemAdd: function(){
      this.close();
    },

    render: {
      option: function(item, escape) {
        var label = item.text;
        var caption = item.caption;
        var logo = item.logo;
        if(item.clearbit){
          if(logo){
          return '<div class="media auto-complete-media">' +
          '<div class="pull-left"><img class="thumbnail" src='+ escape(logo) + ' height=50 width=50></div>'+
          '<div class="media-body"><h5 class="media-heading selectize-option-label">' + escape(label) + '</h5>' +
          (caption ? '<span class="selectize-option-caption small">' + escape(caption) + '</span>' : '') +
          '</div></div>';
          } else{
            return '<div class="media auto-complete-media">' +
            '<div class="pull-left"><img class="thumbnail" src="https://proven-cc.s3.amazonaws.com/static/images/defaults/placeholder-co.png" height=50 width=50></div>'+
            '<div class="media-body"><h5 class="media-heading selectize-option-label">' + escape(label) + '</h5>' +
            (caption ? '<span class="selectize-option-caption small">' + escape(caption) + '</span>' : '') +
            '</div></div>';
          }
        } 
        return '<div>' +
        '<span class="selectize-option-label">' + escape(label) + '</span>' +
        (caption ? '<span class="selectize-option-caption">' + escape(caption) + '</span>' : '') +
        '</div>';
        
      }
    }
  };

  

  if (this.createURL !== undefined) {
    this.config.onOptionAdd = function(value, data) {
      var selectize = this;
      var csrftoken = $('#csrf-middleware-token').attr('value');
      $.post(
          that.createURL,
          {'text': value, 'csrfmiddlewaretoken': csrftoken}
        )
        .done(function(data){
          if (data.pk !== undefined) {
            selectize.removeItem(value);
            selectize.updateOption(value, data);
            selectize.addItem(data.pk);
            selectize.refreshOptions();
            selectize.refreshItems();
          } else {
            selectize.removeOption(value);
            selectize.refreshOptions();
            selectize.refreshItems();
          }
        })
        .fail(function(){
          selectize.removeItem(value);
          selectize.removeOption(value);
          selectize.refreshOptions();
          selectize.refreshItems();
        });
    }
  }

  this.maxItems = $input.attr('selectize-maxItems');
  if (this.maxItems !== null) {
    this.config.maxItems = this.maxItems;
  }

  if (this.$input.attr('selectize-url') !== undefined) {
    var base_url = this.$input.attr('selectize-url');
    var url_parts = base_url.split('?');
    var path = url_parts[0];
    var params = url_parts[1];
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
    this.config.load = function(query, callback){
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
  };

  this.$select = this.$input.selectize(this.config);
  this.$selectize = this.$select[0].selectize;

  this.$controls.addClass('control-selectize');

  var externalSelect = function(ev){
    var $this = $(this);
    var pk = $this.attr('data-selectize-pk');

    if ($this.hasClass('active')) {
      that.$selectize.removeItem(pk);
      $this.removeClass('active');
    } else {
      if (that.$selectize.options[pk] === undefined) {
        that.$selectize.addOption({
          pk: $this.attr('data-selectize-pk'),
          text: $this.attr('data-selectize-name')
        });
        that.$selectize.refreshOptions();
      }
      that.$selectize.addItem(pk);
      $this.addClass('active');
    }
    ev.preventDefault();
    ev.stopPropagation();
  };

  $('.external-selectize').on('click', externalSelect);
  
  if (this.itemKind) {
    this.newItemCallback = function(ev){
      that.$selectize.addOption({pk: ev.pk, text: ev.text});
      that.$selectize.refreshOptions(false);
      that.$selectize.addItem(ev.pk);
      that.$selectize.refreshItems();
    };
    _inExec.modules.events.on('newItem:' + this.itemKind, this.newItemCallback);
  }

  this.destroy = function(){
    $('.external-selectize').off('click', externalSelect);
    var $input = $('#' + this.$input.attr('id'));
    //$input.children().remove();
    $input.show();
    var options = this.$selectize.options;
    for (var i=0; i<options.length; i++) {
      $input.append($('<option value="' + option.pk + '">' + option.text + '</option>'))
    }
    this.$selectize.destroy();

    if (this.itemKind) {
      _inExec.modules.events.off('newItem:' + this.itemKind, this.newItemCallback);
    }
  }
  return this;
}

_inExec.register({
  name: 'autocomplete',
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
  destroyInstances: function($container) {
    var $container = $container || this.$container;
    var that = this;
    _.each(this.$instances, function(instance, name){
      // Do no destroy in case the item is still on the page but not inside
      // currently initializing container
      var is_on_page = that.$body.find(instance.$input).length !== 0;
      var is_in_container = $container.find(instance.$input).length !== 0;
      if ((is_on_page === true) && (is_in_container == false)) {
      } else {
        instance.destroy();
        delete that.$instances[name];
      }
    });
  },
  initializeInstances: function($container) {
    var $container = $container || this.$container;
    var that = this;
    var $inputs = $container.find('input[data-selectize=yes], select[data-selectize=yes]').not('[ignore-enhance], [disabled]');
    if (_globalVars.isMobile === true) {
      var $inputs = $inputs.not('[ignore-enhance-mobile]');
    }
    for (var i=0; i<$inputs.length; i++) {
      var $input = $($inputs[i]);
      var formId = $input.parents('form').attr('id');
      var instanceName = formId + '_' + $input.attr('id');
      var $select = new setupAutocomplete($input);
      that.$instances[instanceName] = $select;
    }
  },
  getInstance: function(instanceName){
    return this.$instances[instanceName].$selectize;
  }
});
