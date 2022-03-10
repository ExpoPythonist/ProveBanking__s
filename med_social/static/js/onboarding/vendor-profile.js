Messenger.options = {
    extraClasses: 'messenger-fixed messenger-on-bottom messenger-on-right',
    theme: 'flat',
};

_inExec.register({
  name: 'vendorProfileOnboard',
  routes: ['^/u/\\d+/$',
           '^/u/\\d+/\\d+/$',
           '^/u/\\d+/extra/$',
           '^/u/\\d+/\\d+/project/$',
           '^/vendors/\\d+/clients/add/$',
           '^/vendors/.*',],
  initialize: function($container){
    var that = this;
    this.$container = $container;
    this.update();
  },
  update: function(){
    this.destroy();
    var that = this;
    this.$locationList = $('#location-list');
    this.$parent = $('#vendor-form-accordion');
    this.$basicCollapse = $('#collapseFirst');
    this.$basicTitle = $('.collapse-title[href=#' + this.$basicCollapse.attr('id') + ']');
    this.$vendorTitle = $('.collapse-title[href=#collapseSecond]');

    $('.panel-collapse').on('hide.bs.collapse', function(){
      var $this = $(this);
      var $heading = $this.siblings('.panel-heading');
      var $values = $heading.find('.values');
      var $name = $heading.find('.name');
      if ($values.html().trim() !== '') {
        $name.addClass('hide');
        $values.removeClass('hide');
      }
    });

    $('.panel-collapse').on('show.bs.collapse', function(){
      var $this = $(this);
      var $heading = $this.siblings('.panel-heading');
      var $values = $heading.find('.values');
      var $name = $heading.find('.name');
      $name.removeClass('hide');
      $values.addClass('hide');
    });

    if(!$('#id_use_alt_name').is(":checked")){
      $('#div_id_alt_name').addClass('hide');
    }

    $('#id_use_alt_name').on('change', function() { 
      // From the other examples
      if (this.checked) {
          $('#div_id_alt_name').removeClass('hide');
      }
      else{
        $('#div_id_alt_name').addClass('hide');
      }
    });

    $('.diversity_owned').on('change', function() { 
      // From the other examples
      $.post($(this).attr('data-url'), {checked: this.checked});
      console.log("====================")
    });

    $('.panel-collapse').not('.in').trigger('hide.bs.collapse');

    $('#vendors-search-form').attr('action', $('#vendors-endpoint').val());
    $('#advanced-request-form').attr('action', $('#advanced-endpoint').val());

    _inExec.modules.events.on('form:success#vendor-first-form', function(){
      $('.panel-second').removeClass('hide');
      $('#collapseSecond').collapse('show')
    });

   $('#location-next-button').on('click', function(){
      $('.panel-third').removeClass('hide');
      $('#collapseThird').collapse('show');
    });

    $(".word-count").on('keyup', function() {
      var words = this.value.length;
      if (words > 500) {
        // Split the string on first 200 words and rejoin on spaces
        var trimmed = $(this).val().split(/\s+/, 500).join(" ");
        // Add a space at the end to make sure more typing creates new words
        $(this).val(trimmed + " ");
      }
      else {
        $('.word-wrap').removeClass('hide');
        $('.word-left').text(500-words);
      }
    });

    _inExec.modules.events.on('form:success#location-form', function(ev){
      var $form = $('#location-form');
      $form.parents('.modal').modal('hide');
      location.reload();
    });

    _inExec.modules.events.on('form:success#primary-form', function(ev){
      var $form = $('#primary-form');
      $form.parents('.modal').modal('hide');
      location.reload();
    });
    
    _inExec.modules.events.on('form:success#status-form', function(ev){
      var $form = $('#status-form');
      $form.parents('.modal').modal('hide');
      location.reload();
    });


    _inExec.modules.events.on('form:success#diversity-form', function(ev){
      var $form = $('#diversity-form');
      $form.parents('.modal').modal('hide');
      location.reload();
    });

    
    _inExec.modules.events.on('form:success#edit-portfolio-form', function(ev){
      var $form = $('#edit-portfolio-form');
      $form.parents('.modal').modal('hide');
      var notif = window.Messenger().post({
        'showCloseButton': true,
        'type': 'success',
        'message': 'Project updated successfully'
      });
      location.reload();
    });
    
    _inExec.modules.events.on('form:success#procurement-form', function(ev){
      var $form = $('#procurement-form');
      $form.parents('.modal').modal('hide');
      var notif = window.Messenger().post({
        'showCloseButton': true,
        'type': 'success',
        'message': 'Procurement contact added successfully'
      });
      location.reload();
    });


    _inExec.modules.events.on('form:success#portfolio-form', function(ev){
      var $form = $('#portfolio-form');
      var $list = $('.project-list-items');
      var $new_obj = $form.find('#portfolio-objects').children();
      var $count = $('#project-count');
      var project_count = parseInt($count.attr('data-count'));
      $list.append($new_obj)
      
      $form.parents('.modal').modal('hide');
      setTimeout(function(){
        $new_obj.removeClass('hide');
        _inExec.modules.utils.animate($new_obj, 'fadeInDown');
      }, 300);

      $count.text(++project_count);

      var notif = window.Messenger().post({
        'showCloseButton': true,
        'type': 'success',
        'message': 'Project added successfully',
        'hideAfter': 3,
      });
    });

  },


  destroy: function(){
     _inExec.modules.events.off('form:success#vendor-first-form')
     _inExec.modules.events.off('form:success#location-form')
     _inExec.modules.events.off('form:success#portfolio-form')
     _inExec.modules.events.off('form:success#procurement-form')
  },
});