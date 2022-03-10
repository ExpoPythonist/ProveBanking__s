_inExec.extendClass({
  name: 'proposedResourceFormFilter',

  initialize: function(options){
    var that = this;
    this.$form = options.$form;
    this.url = options.url;
    this.$container = options.$container;

    this.$changeField = this.$form.find('#id_resource, #id_location, #id_role, #id_skill_level');

    this.onChanged = function(){
      $.get(that.url, that.$changeField.serialize())
        .done(function(data, textStatus, jqXHR){
          var $selected = that.$form.find('input[name=rate_card]:checked');
          if ($selected.length !== 0) {
            var selectedClass = '.' + $selected.attr('class').split(' ').join('.');
          } else {
            var selectedClass = '';
          }
          var $result = $(data.trim());
          that.$container.children().remove();
          that.$container.append($result.children());
          if (selectedClass) {
            that.$form.find(selectedClass).attr('checked','checked');
          }
          that.$container.find('.field-group').off('click');
          that.$container.find('.field-group').on('click', that.onRowClicked);

          that.$container.find('input[name=rate_card]').off('change');
          that.$container.find('input[name=rate_card]').on('change', that.onSelected);
        });
    };

    this.onRowClicked = function(){
      var $input = $(this).find('input[type=radio]');
      $input.attr('checked', 'checked');
      that.onSelected($input);
    };

    this.onSelected = function($input) {
      if (this === that) {
        var $input = $input;
      } else {
        var $input = $(this);
      }
      var $parent = $input.parents('.field-group');
      $parent.addClass('selected');
      $parent.siblings().removeClass('selected');
    };

    this.$container.find('input[name=rate_card]').on('change', this.onSelected);
    this.$container.find('.field-group').on('click', this.onRowClicked);
    this.$changeField.on('change', this.onChanged);
    this.$container.find('input[name=rate_card]:checked').trigger('click');
  },

  refresh: function(){
    this.$container.find('input[name=rate_card]').off('change');
    this.$container.find('input[name=rate_card]').on('change', this.onSelected);

    this.$container.find('.field-group').off('click');
    this.$container.find('.field-group').on('click', this.onRowClicked);
  },

  selectResource: function($resource) {
    $resource.addClass('selected');
  },

  deselectResource: function($resource) {
    $resource.removeClass('selected');
  },

  destroy: function(){
    this.$form.find('input[name=rate_card]').off('change');
    this.$changeField.off('change');
  }
});


_inExec.register({
  name: 'proposeResources',
  routes: ['^/projects/\\d+/staff/add/$',
           '^/projects/\\d+/staff/\\d+/edit/$',
           '^/projects/\\d+/staff/\\d+/propose/$',
           '^/projects/\\d+/staff/proposed/\\d+/edit/$',
           ],
  initialize: function($container){
    var that = this;
    this.filters = [];
    this.$container = $container;
    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
    _inExec.modules.events.off('newItem:rate', this.newItemCallback);
    //this.$form.find('input[name=rate_card]').off('change', this.onSelected);
    // TODO: destroy filter instances
    //
    if (this.filter !== undefined) {
      this.filter.destroy();
      delete this.filter;
    }
  },
  setup: function(){
    var that = this;
    this.$form = $('#add-staff-direct-form');
    this.filter = new _inExec.classes.proposedResourceFormFilter({
          url: this.$form.attr('data-rate-suggestions-url'),
          $form: this.$form,
          $container: $('#suggested-cards')
    });
    this.$suggestedCards = $('#suggested-cards');
    this.newItemCallback = function(ev){
      $.get('/rates/' + ev.pk + '/')
        .done(function(data){
          var $as_field = $(data.trim());
          that.$suggestedCards.prepend($as_field);
          that.filter.refresh();
          $as_field.click();
          that.$suggestedCards.find('.field-group.placeholder').remove();
        })
    };
    _inExec.modules.events.on('newItem:rate', this.newItemCallback);

    this.$form.find('#id_hourly_rate').on('keyup', function(){
      var $this = $(this);
      var val = $this.val().trim();
      if (val.length > 0) {
        that.$suggestedCards.find('.block-cover-rates').removeClass('hide');
      } else {
        that.$suggestedCards.find('.block-cover-rates').addClass('hide');
      }
    });
    this.$form.find('#id_hourly_rate').trigger('keyup');
  },
});
