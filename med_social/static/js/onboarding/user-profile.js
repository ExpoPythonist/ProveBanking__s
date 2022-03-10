_inExec.register({
  name: 'onboarding-user-profile',
  routes: ['^/u/\\d+/$', '^/users/.+/edit/$'],
  initialize: function($container){
    this.setUp();
  },
  update: function(){
    this.setUp();
  },
  destroy: function(){
  },
  setUp: function(){
    var that = this;

    this.$avatarForm = $('#avatar_form');

    this.$avatarField = $('#id_avatar');
    this.$avatarField.change(function(){
      if (that.$avatarField[0].files.length > 0) {
        $('#avatar_form').submit();
      }
    });

    $('img#avatar').on('click', function(){
      that.$avatarField.click();

    });

    this.$firstName = $('#id_first_name');
    this.$lastName = $('#id_last_name');
    this.$fullName = $('.user-full-name');
    var updateName = function(){
      that.$fullName.text(that.$firstName.val() + ' ' + that.$lastName.val());
    }
    this.$firstName.on('keyup', updateName);
    this.$lastName.on('keyup', updateName);

    this.$usernameInput = $('#id_username');
    this.$username = $('.username');
    var updateUserName = function(){
      that.$username.text(that.$usernameInput.val());
    }
    this.$usernameInput.on('keyup', updateUserName);
  }
});
