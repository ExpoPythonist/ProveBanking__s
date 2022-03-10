_inExec.register({
  name: 'notifications',
  routes: [''],
  initialize: function(){
    this.$body = $('body');
    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
  },
  setup: function(){
    this.$dropdown = this.$body.find('.dropdown');
    this.$dropdown.on(
      'shown.bs.dropdown', $.proxy(this.markAsRead, this));
  },
  markAsRead: function(){
    var that = this;
    var list = this.$dropdown.find('.notice').map(
        function(){return $(this).attr('data-notification-id');}).get();
    $.post('/users/notifications/mark_read/', {'notifications': list})
     .success(function(data){
       that.$dropdown.find('.unread-count').text(data.unread_count);
       if (data.unread_count === 0) {
          that.$dropdown.find('.dropdown-toggle').removeClass('notif');
       } else {
          that.$dropdown.find('.dropdown-toggle').addClass('notif');
       }
     });
  }
});


_inExec.register({
  name: 'notifications-page',
  routes: ['^/users/notifications/unread/$', '^/users/notifications/all/$'],
  initialize: function(){
    this.$body = $('body');
    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
  },
  setup: function(){
    var that = this;
    this.$dropdown = this.$body.find('.dropdown');
    this.$notificationsList = this.$body.find('#notifications-list');
    setTimeout(function(){
      that.markAsRead();
    }, 2000);
  },
  markAsRead: function(){
    var that = this;
    var list = this.$notificationsList.find('.notice').map(
        function(){return $(this).attr('data-notification-id');}).get();

    $.post('/users/notifications/mark_read/', {'notifications': list})
     .success(function(data){
       that.$dropdown.find('.unread-count').text(data.unread_count);
       if (data.unread_count === 0) {
          that.$dropdown.find('.dropdown-toggle').removeClass('notif');
       } else {
          that.$dropdown.find('.dropdown-toggle').addClass('notif');
       }
     });
  }
});
