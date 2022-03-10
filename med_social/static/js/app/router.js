_inExec.register({
  name: 'router',
  initialize: function(){
    var that = this;
    _inExec.$document.on('pjaxr:end', function(ev, jqXhr){
      if (!jqXhr) {
        return;
      }
      _inExec.route(that.pathFromUrl(jqXhr.url));
    });
  },
  pathFromUrl: function(str) {
    var a = document.createElement('a');
    a.href = str;
    return a.pathname;
  },
});
