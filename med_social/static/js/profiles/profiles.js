(function(){
  var Availabilty = function(){
    this.bind();
  };

  Availabilty.prototype.bind = function(){
    var that = this;
    this.$input = $('#availability-input.editable');
    if (this.$input.length == 0) {
      return;
    }
    this.$form = this.$input.parent();
    this.URL = this.$form.attr('action');
    this.METHOD = this.$form.attr('method');
    this.$panel = $('.panel-availability');
    this.$input.pickadate({
      min: 1,
      format: 'yyyy-mm-dd',
      onClose: function(){
        that.submit();
      }
    });
    this.picker = this.$input.pickadate('picker');
    this.$panel.on('click', function(ev){
      ev.preventDefault();
      ev.stopPropagation();
      setTimeout(function(){
        //that.picker.open();
        that.$input.pickadate('open');
      }, 1);
    });
  };

  Availabilty.prototype.submit = function(){
    var that = this;
    var date = this.$input.val();
    _inExec.modules.ui.block(this.$panel, '1x');
    $.ajax({
      type: that.METHOD,
      url: that.URL,
      data: that.$form.serializeArray(),
      dataType: 'html'
    }).success(function(data, textStatus, jqXHR){
      that.$panel.replaceWith($(data.trim()));
      that.bind();
    }).always(function(){
      _inExec.modules.ui.unblock(that.$panel);
    });
  };

  _inExec.register({
    name: 'profiles',
    initialize: function($container){
      if (this.availability != undefined) {
        delete(this.availability);
      }
      this.availability = new Availabilty();
    }
  });
})();
