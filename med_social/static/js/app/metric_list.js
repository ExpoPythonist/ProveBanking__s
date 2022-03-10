_inExec.register({
  name: 'metric_list',
  routes: ['^/settings/metrics/for/\\d+/$'],
  _editMode: false,
  _total: 0,
  initialize: function($container){
    this.$container = $container;
    this.$editWeightsBtn = this.$container.find('#edit-weights-btn');
    this.setUp();
  },
  update: function(){
    this.setUp();
  },
  destroy: function(){
    this.$editWeightsBtn.off('click');
    this._editMode = false;
  },
  setUp: function(){
    var that = this;
    this.$body = $('body');
    this.$editWeightsBtn = this.$container.find('#edit-weights-btn');
    this.$cancelEditBtn = this.$container.find('#cancel-edit-btn');
    this.$saveWeightsBtn = this.$container.find('#save-weights-btn');
    this.$weightInputFields = this.$container.find('input.weight-input');
    this.$metricLinks = this.$container.find('.panel-metrics')
                                       .find('.field-value > a');
    this.$totalWeight = this.$container.find('#total-weight');
    this.$totalWeightContainer = this.$container.find('.total-weight-container');

    this.$editWeightsBtn.on('click', function(){
      that.enterEditMode();
    });

    this.$saveWeightsBtn.on('click', function(){
      that.saveChanges();
    });

    this.$cancelEditBtn.on('click', function(ev){
      that.exitEditMode();
      ev.stopPropagation();
      ev.preventDefault();
    });

    this.$metricLinks.on('click', function(ev){
      if (that._editMode == true) {
        ev.stopPropagation();
        ev.preventDefault();
      }
    });

    //this.$weightInputFields.inputmask("99.99", {placeholder:"0", clearMaskOnLostFocus: true }); //default

    this.$weightInputFields.on('keyup', function(){
      that.calculateTotal();
      that.$totalWeight.text(that._total);
      if (that._total == 100) {
        that.$totalWeightContainer.removeClass('has-error').tooltip('hide');
      } else {
        that.$totalWeightContainer.addClass('has-error').tooltip('show');
      }
    });
  },

  calculateTotal: function(){
    this._total = _.reduce(
      _.map(this.$weightInputFields, function(i){return Number(i.value)}),
      function(x,y){return x+y}
    ).toFixed(2);
  },

  enterEditMode: function(){
    var that = this;
    that.calculateTotal();
    this.$body.addClass('edit-mode');
    /*
    that.$container.find('label').addClass('highlight-hint');
    setTimeout(function(){
      that.$container.find('label').removeClass('highlight-hint');
    }, 300);
    */
    this._editMode = true;
  },

  exitEditMode: function(){
    this.$body.removeClass('edit-mode');
    this._editMode = false;
  },
  saveChanges: function(){
    if (this._total == 100) {
      $('form#metric-weights').submit();
    } else {
      this.$container.find('.total-weight-container').tooltip('show');
      $('html, body').animate({
          scrollTop: $(".total-weight-container").offset().top
      }, 1000);
    }
  },
});
