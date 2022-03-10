_inExec.register({
  name: 'links',
  routes: [''],
  initialize: function(){
    var $document = $(document);
    //$document.pjaxr('a[href^="/"]:not([data-toggle])');
    /*
    $document.on('pjaxr:timeout', function(e){
      e.preventDefault();
      _inExec.modules.ui.showLoading();
    });
    $document.on('pjaxr:always', function(e){
      _inExec.modules.ui.hideLoading();
    });
    */
    this.setupEvents();
  },
  update: function(){
    this.setupEvents();
  },
  destroy: function(){
    $document.off('pjaxr:timeout');
    $document.off('pjaxr:always');
  },
  setupEvents: function(){
  }
});
