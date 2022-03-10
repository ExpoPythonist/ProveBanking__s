Messenger.options = {
    extraClasses: 'messenger-fixed messenger-on-bottom messenger-on-right',
    theme: 'flat',
};


var Actions = {
  new: function(options){
    var defaultOptions = {
      'showCloseButton': true
    };
    _.extend(defaultOptions, options);
    return window.Messenger().post(defaultOptions);
  }
};


window.Notifs = Actions;
module.exports = {
  'Actions': Actions,
};
