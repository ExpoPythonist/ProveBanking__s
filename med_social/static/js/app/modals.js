_inExec.register({
  name: 'modals',
  initialize: function(){
    var that = this;
    this.genericModalPlaceholder = $('#genericModal').find('.modal-content').html();
    $(document).on('pjaxr:always', function(e){
      $('.modal.in').not('[cross-page-modal]').modal('hide');
    });

    $(".modal[data-modal-is-remote=true]").on("show.bs.modal",function() {
      $(this).addClass('modal-loading');
    });

    $('body').on('loaded.bs.modal', '.modal', function(){
      var $this = $(this);
      $(this).removeClass('modal-loading');
      $this.find('form').each(function(index, form){
        _inExec.modules.formEnhance.setUp($(form));
      });
      _inExec.modules.popovers.update();
      _inExec.modules.inlinePopovers.update();
    });

    $('body').on('hidden.bs.modal', '.modal', function(){
      $(this).find('.modal-content').find('[data-toggle=popover]').popover('hide');
    });

    $('body').on('hidden.bs.modal', '.modal[data-modal-is-remote]', function(){
      var $this = $(this);
      $this.find('.modal-content').html(that.genericModalPlaceholder);
      $this.removeData('bs.modal');
    });
  }
});
