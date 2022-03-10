_inExec.extendClass({
  name: 'gridView',
  initialize: function(options){
    if (options.$list === undefined) {
      if (options.list === undefined) {
        throw 'gridView: expected `list` or `$list` attribute in options'
      }
      options.$list = $(options.list);
    }
    this.$list = options.$list;
    this.path = this.$list.attr('data-url');
    this.setupGrid(options);
  },
  destroy: function(){
  },
  setupGrid: function(options){
    var that = this;
    this.$list.waterfall({
      itemCls: 'grid-item',
      colWidth: options.colWidth || 250,
      maxCol: options.maxCol || 3,
      align: 'left',
      fitWidth: true,
      gutterWidth: options.gutterWidth || 60,
      gutterHeight: 60,
      checkImagesLoaded: false,
      dataType: 'html',
      isAnimated: true,
      isFadeIn: true,
      animationOptions: {
      },
      path: options.path,
      callbacks: {
        loadingError: function($message, xhr) {
          $message.text('');
        },
        renderData: function(data, dataType) {
          var retData = '';
          var $newPage = $(data.trim());
          for (var i=0; i<$newPage.length; i++) {
            window.items = $newPage;
            var item = $newPage[i];
            var $item = $(item);
            if ($item.hasClass('grid-item')) {
              if (that.$list.find('#'+$item.attr('id')).length == 0) {
                var $div = $('<div>');
                $div.append($item);
                retData += $div.html();
              }
            }
          }
          return retData;
        },
      }
    });
  },
});
