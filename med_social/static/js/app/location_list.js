_inExec.register({
  name: 'location_list',
  routes: ['^/u/4/\\d+/location/$'],
  _editMode: false,
  _numeric: true,
  initialize: function($container){
    this.$container = $container;
    this.$editAllocationBtn = this.$container.find('#edit-allocation-btn');
    this.setUp();
  },
  update: function(){
    this.setUp();
  },
  destroy: function(){
    this.$editAllocationBtn.off('click');
    this._editMode = false;
  },
  setUp: function(){
    var that = this;
    this.$body = $('body');
    this.$editAllocationBtn = this.$container.find('#edit-allocation-btn');
    this.$cancelEditBtn = this.$container.find('#cancel-edit-btn');
    this.$saveAllocationButton = this.$container.find('#save-allocation-btn');
    this.$allocationInputFields = this.$container.find('input.allocation-input');
    this.$allocationLinks = this.$container.find('.panel-metrics')
                                       .find('.field-value > a');
    this.$totalAllocation = this.$container.find('#total-allocation');
    this.$totalAllocationContainer = this.$container.find('.total-allocation-container');

    this.$editAllocationBtn.on('click', function(){
      that.enterEditMode();
    });

    this.$saveAllocationButton.on('click', function(){
      that.saveChanges();
    });

    this.$cancelEditBtn.on('click', function(ev){
      that.exitEditMode();
      ev.stopPropagation();
      ev.preventDefault();
    });

    this.$allocationLinks.on('click', function(ev){
      if (that._editMode == true) {
        ev.stopPropagation();
        ev.preventDefault();
      }
    });

    //this.$allocationInputFields.inputmask("99.99", {placeholder:"0", clearMaskOnLostFocus: true }); //default

    this.$allocationInputFields.on('keyup', function(){
      that.calculateTotal();
      if (that._numeric == true) {
        that.$totalAllocationContainer.removeClass('has-error').tooltip('hide');
      } else {
        that.$totalAllocationContainer.addClass('has-error').tooltip('show');
      }
    });


    _inExec.modules.events.on('form:success#location-form', function(ev){
      var $form = $('#location-form');
      $form.parents('.modal').modal('hide');
      location.reload();
    });

  },

  calculateTotal: function(){
    that = this;
    this.$allocationInputFields.each(function(i, obj){
        that._numeric = !isNaN(Number(obj.value));
    });
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
    if (this._numeric == true) {
      $('form#location-allocations').submit();
    }
  },
});
