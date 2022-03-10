_inExec.extendClass({
  name: 'intRange',
  ORDER_ASCENDING: 1,
  ORDER_DESCENDING: 2,

  initialize: function($inputs, order){
    this.$inputs = $inputs;
    this.order = order || this.ORDER_ASCENDING;
    if (this.order == this.ORDER_ASCENDING) {
      this.initialize_ascending();
    } else {
      this.initialize_descending();
    }
  },

  get_input_position: function($input){
    for (var i=0; i<this.$inputs.length; i++) {
      if ($input[0] == this.$inputs[i]) {
        return i;
      }
    }
  },

  get_next_input: function($input){
    var pos = this.get_input_position($input);
    return $(this.$inputs[pos + 1]);
  },

  get_previous_input: function($input){
    var pos = this.get_input_position($input);
    return $(this.$inputs[pos - 1]);
  },

  split_value: function($input){
      var val = $input.val() || '';
      if (val.indexOf('-') != -1) {
        return val.split('-');
      } else {
        return [null, null];
      }
  },

  setLowValue: function($input, val, diff){
    var high = this.number_or_empty_str(this.split_value($input)[1]);
    val = this.number_or_empty_str(val);
    if (_.isNumber(val) && diff != undefined) {
      val = val + diff;
    }
    $input.val(val + '-' + high);
  },

  setHighValue: function($input, val, diff){
    var low = this.number_or_empty_str(this.split_value($input)[0]);
    val = this.number_or_empty_str(val);
    if (_.isNumber(val) && diff != undefined) {
      val = val + diff;
    }
    $input.val(low + '-' + val);
  },

  number_or_empty_str: function(val){
    val = val || '';
    if (_.isString(val)) {
      val = val.trim();
    }
    if (val == '') {
      return val;
    }
    val = Number(val);
    if (_.isNumber(val)) {
      return val;
    }
    return ''
  },

  initialize_ascending: function(){
    var that = this;
    var $first = $(this.$inputs[0]);
    var $last = $(this.$inputs[this.$inputs.length - 1]);
    var high_list = [];
    this.$inputs.each(function(position, input){
      var $input = $(input);
      var feedback = $input.attr('data-field-feedback') || '';
      if (feedback != '') {
        $input.parents('.form-group').addClass('has-feedback');
        $('<span class="form-control-feedback text-muted">'+ feedback +'</span>').insertAfter($input);
      }
      var val = that.split_value($input);
      var low = val[0];
      var high = val[1];
      var $previous = that.get_previous_input($input);
      var $range = $('<div class="range-placeholder controls">'
                      + '<span class="low"></span>'
                      + ' to '
                      + '<input type="text" ignore-labelinplace class="form-control high" value="' + low + '"/>'
                   + '</div>');
      $range.insertBefore($input);
      $input.addClass('hide');
      var $high = $range.find('.high');
      $high.inputmask('integer');

      var $low = $range.find('.low');

      var val = that.split_value($input);
      var low = val[0];
      var high = val[1];
      $high.val(high);
      $low.text(low);

      $high.on('keyup', function(){
        var $current = $(this);
        var $realInput = $current.parent().siblings('input');
        var $next = that.get_next_input($realInput);

        var high = $current.val().trim();
        if (high != '') {
          high = Number(high);
          if (_.isNumber(high) == true) {
            high += 1;
          } else {
            high = '';
          }
        }
        $next.siblings('.range-placeholder').find('.low').text(high);
        that.setLowValue($next, high);
        that.setHighValue($realInput, high, diff=-1);
      });
      high_list.push($high);
    });

    _.each(high_list, function(item, i){
      $(item).trigger('keyup');
    });
  },
  initialize_descending: function(){
  }
});


_inExec.register({
  name: 'metric_edit',
  routes: ['^/settings/metrics/for/\\d+/\\d+/edit/$', '^/settings/metrics/for/\\d+/create/$' ],
  _editMode: false,
  _total: 0,
  initialize: function($container){
    this.$container = $container;
    this.setUp();
  },
  update: function(){
    this.setUp();
  },
  destroy: function(){
  },
  setUp: function(){
    // FIXME: Remove the below temp fix for right align
    $('.score-label-panel').find('.text-field').removeClass('text-field');
    // ENDFIX
    var that = this;
    this.$form = $('#metric-form');
    this.$updateFieldsBtn = $('#update-form-fields');
    this.$kind = $('#id_kind');
    this.$kind.on('change', function(){
      that.reloadForm();
    });
    var $intRange = this.$form.find('.range-input');
    if ($intRange.length > 0) {
      this.intRangeHandler = new _inExec.classes.intRange($intRange);
    }
  },
  reloadForm: function(){
    var $csrfField = $('input[name="csrfmiddlewaretoken"]');
    $csrfField.remove()
    this.$updateFieldsBtn.attr('href',
        this.$updateFieldsBtn.attr('base-href') + '?' + this.$form.serialize() + '&update_form=yes');
    this.$form.prepend($csrfField);
    this.$updateFieldsBtn.click();
  }
});
