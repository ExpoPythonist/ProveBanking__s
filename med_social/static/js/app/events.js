_inExec.register({
  name: 'events',
  initialize: function(){
    this.$eventBus = $({});
  },
  on: function(eventName, callback) {
    this.$eventBus.on(eventName, callback);
  },
  off: function(eventName, callback) {
    if (callback === undefined) {
      this.$eventBus.off(eventName, callback);
    } else {
      this.$eventBus.off(eventName);
    }
  },
  trigger: function(eventName, context) {
    this.$eventBus.trigger(eventName, context);
  }
});
